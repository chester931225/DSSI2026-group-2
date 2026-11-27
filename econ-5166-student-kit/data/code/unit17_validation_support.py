"""Unit 1.7 reproducible, memory-only diagnostics. No formal dataset writers.

Read by executed course notebooks; config and this module are hash-bound there.
Raw ZIP/CSV and earlier notebooks/crosswalks are never changed.
"""
from pathlib import Path, PurePosixPath
import hashlib, json, io, csv, zipfile, shutil, re, ast
from collections import Counter
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
import shapely as s
from pyproj import Transformer
from IPython.display import display, Markdown


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()


def safe_text(value):
    return str(value).encode('utf-8','backslashreplace').decode('utf-8')


def show(title, frame, block=18):
    display(Markdown('**'+title+'**'))
    if not len(frame): display(Markdown('無符合紀錄。'))
    for start in range(0,len(frame),block):
        part=frame.iloc[start:start+block].copy()
        for col in part:
            if part[col].dtype==object or isinstance(part[col].dtype,pd.StringDtype):
                part[col]=part[col].map(lambda v:safe_text(v) if isinstance(v,str) else v)
        display(part)


class Context:
    def __init__(self, root, config_hash):
        self.root=Path(root).resolve();self.temp=self.root/'data/temp/unit17_validation'
        self.temp.mkdir(parents=True,exist_ok=True)
        p=self.root/'data/code/unit17_validation_config.json'
        assert sha(p)==config_hash,'Configuration changed; review before accepting a new version'
        self.config=json.loads(p.read_text(encoding='utf-8'))
        self.inventory=self.config['raw_inventory'];self.cache={};self.summaries={}
        for relative in self.config['existing_bindings']:self.file(relative)
        self.boundary=gpd.read_file(self.file('data/raw/G97_A_CAVLGE_P.shp'),encoding='utf-8',engine='pyogrio')
        self.original_wkb=self.boundary.geometry.to_wkb().copy()
        assert len(self.boundary)==456 and self.boundary.crs.to_epsg()==3826
        self.boundary=self.boundary.reset_index(drop=True)
        self.vgeom=np.asarray(self.boundary.geometry.array,dtype=object)
        self.ids=self.boundary.CPTVID.astype(str).to_numpy();self.districts=self.boundary.TNAME.to_numpy()
        self.city=s.union_all(self.vgeom);self.study=self.city.buffer(2000)
        self.varea=s.area(self.vgeom);self.btree=s.STRtree(self.vgeom)
        self.cw=pd.read_csv(self.file('data/processed/village_crosswalk.csv'),encoding='utf-8-sig',dtype=str,keep_default_na=False)
        assert self.cw.village_id.is_unique and self.cw.population_code.is_unique
        assert set(self.cw.village_id)==set(self.ids)
        self.to3826=Transformer.from_crs(4326,3826,always_xy=True)
        self.base=pd.DataFrame({'village_id':self.ids,'district_name':self.districts,'village_name':self.boundary.VNAME,'area_km2':self.varea/1e6})

    def file(self,relative):
        p=(self.root/relative).resolve();assert p.is_relative_to(self.root/'data') and p.is_file(),relative
        item=next((r for r in self.inventory if r['path']==relative),None)
        expected=item['sha256'] if item else self.config['existing_bindings'].get(relative)
        if relative==self.config['evidence']['path']:expected=self.config['evidence']['sha256']
        if expected:assert sha(p)==expected,'Input changed: '+relative
        return p

    def family_items(self,family):return [r for r in self.inventory if r['family']==family]

    def extract(self,item,member):
        """Only selected sidecars; each read regenerates/checks from bound ZIP bytes."""
        path=self.file(item['path']);stem=member[:-4]
        target_root=(self.temp/'extracted'/item['sha256'][:12]).resolve()
        with zipfile.ZipFile(path) as z:
            for info in z.infolist():
                q=PurePosixPath(info.filename.replace('\\','/'))
                assert not q.is_absolute() and '..' not in q.parts and ':' not in info.filename
                assert ((info.external_attr>>16)&0o170000)!=0o120000
            names=[n for n in z.namelist() if n.startswith(stem+'.') and n[len(stem):].lower() in ['.shp','.shx','.dbf','.prj','.cpg','.qix','.sbn','.sbx','.shp.xml','.qmd']]
            assert {'.shp','.shx','.dbf'}.issubset({n[len(stem):].lower() for n in names})
            for name in names:
                out=(target_root/name).resolve();assert out.is_relative_to(target_root)
                out.parent.mkdir(parents=True,exist_ok=True)
                with z.open(name) as src:
                    body=src.read()  # largest chosen sidecar ~153MB; never the whole national dataset
                digest=hashlib.sha256(body).hexdigest()
                if out.exists() and sha(out)==digest:continue
                out.write_bytes(body);assert sha(out)==digest
        return target_root/member

    def text_csv(self,item):
        b=self.file(item['path']).read_bytes();encoding='cp950'
        errors=[]
        try:t=b.decode(encoding);strict=True
        except UnicodeDecodeError:
            t=b.decode(encoding,errors='surrogateescape');strict=False
            assert t.encode(encoding,errors='surrogateescape')==b
            for match in re.finditer('[\udc80-\udcff]',t):
                offset=len(t[:match.start()].encode(encoding,errors='surrogateescape'))
                errors.append(dict(byte_offset=offset,physical_line=b[:offset].count(b'\n')+1,hex=b[max(0,offset-5):offset+6].hex()))
        sep='\t' if '\t' in t.splitlines()[0] else ','
        f=pd.read_csv(io.StringIO(t),sep=sep,dtype=str,keep_default_na=False,engine='python')
        f['_source_row']=np.arange(len(f))+1;f['_source_path']=item['path']
        f['_decoding_valid']=~f.apply(lambda col:col.astype(str).str.contains('[\udc80-\udcff]',regex=True)).any(axis=1)
        f.attrs['encoding_diagnostic']=dict(encoding=encoding,strict=strict,byte_roundtrip=True,delimiter=repr(sep),invalid_byte_count=len(errors),invalid_bytes=errors)
        return f

    def load_family(self,family):
        if family in self.cache:return self.cache[family]
        result={};info=[]
        for item in self.family_items(family):
            path=self.file(item['path'])
            if path.suffix.lower()=='.csv':
                f=self.text_csv(item);result[item['path']]=f
                info.append(dict(path=item['path'],rows=len(f),**f.attrs['encoding_diagnostic']))
            elif family=='national_accidents':
                f,detail=self.national_read(item);result[item['path']]=f;info.extend(detail)
            else:
                members=[m['member'] for m in item['members'] if m['member'].lower().endswith('.shp')]
                if family=='osm':members=['gis_osm_roads_free_1.shp']
                for member in members:
                    shp=self.extract(item,member);meta=pyogrio.read_info(shp)
                    kw={}
                    if family=='osm':
                        bounds=gpd.GeoSeries([self.study],crs=3826).to_crs(4326).total_bounds
                        kw['bbox']=tuple(bounds)
                    f=gpd.read_file(shp,engine='pyogrio',fid_as_index=True,**kw)
                    f['_source_row']=f.index.to_numpy()+1;f['_source_path']=item['path'];f['_source_member']=member
                    result[item['path']+'::'+member]=f
                    info.append(dict(path=item['path'],member=member,total_features=int(meta['features']),loaded_rows=len(f),crs=str(f.crs),types=f.geom_type.value_counts().to_dict(),bounds=f.total_bounds.tolist(),invalid=int((~f.geometry.is_valid).sum()),null_geometry=int(f.geometry.isna().sum()),empty=int(f.geometry.is_empty.sum())))
        self.cache[family]=result;self.summaries[family]=info
        return result

    def national_read(self,item):
        columns=['發生年度','發生月份','發生日期','發生時間','事故類別名稱','處理單位名稱警局層','發生地點','光線名稱','事故位置大類別名稱','事故位置子類別名稱','事故類型及型態大類別名稱','事故類型及型態子類別名稱','當事者順位','當事者區分-類別-大類別名稱-車種','當事者區分-類別-子類別名稱-車種','死亡受傷人數','經度','緯度']
        selected=[];details=[]
        with zipfile.ZipFile(self.file(item['path'])) as z:
            for member in [m['member'] for m in item['members'] if re.search(r'年度A[12]交通事故資料',m['member']) and m['member'].endswith('.csv')]:
                with z.open(member) as src:header=next(csv.reader(io.TextIOWrapper(src,encoding='utf-8-sig',newline='')))
                assert set(columns).issubset(header),(member,set(columns)-set(header))
                total=party_rows=city_rows=city_first=agency_rows=0;months=Counter();non_observation=[]
                with z.open(member) as src:
                    reader=pd.read_csv(src,encoding='utf-8-sig',dtype=str,keep_default_na=False,usecols=columns,chunksize=50000)
                    for chunk in reader:
                        rows=np.arange(total+1,total+len(chunk)+1);total+=len(chunk)
                        city=chunk['發生地點'].str.startswith(('臺北市','台北市'))
                        agency=chunk['處理單位名稱警局層'].str.contains('臺北市|台北市',regex=True)
                        first=pd.to_numeric(chunk['當事者順位'],errors='coerce').eq(1)
                        observation=chunk['發生年度'].str.fullmatch(r'\d{4}')&pd.to_numeric(chunk['當事者順位'],errors='coerce').ge(1)&chunk['事故類別名稱'].isin(['A1','A2'])
                        party_rows+=int(observation.sum())
                        for pos in np.flatnonzero(~observation.to_numpy()):
                            non_observation.append(dict(source_row=int(rows[pos]),year_field=chunk.iloc[pos]['發生年度'],date_field=chunk.iloc[pos]['發生日期'],category_field=chunk.iloc[pos]['事故類別名稱']))
                        city_rows+=int(city.sum());city_first+=int((city&first).sum());agency_rows+=int((agency&first).sum())
                        months.update(chunk.loc[observation,'發生月份'].value_counts().to_dict())
                        keep=(city|agency)&first
                        f=chunk.loc[keep].copy();f['_source_row']=rows[keep.to_numpy()];f['_source_member']=member;f['_source_path']=item['path'];f['_city_address']=city[keep].to_numpy();f['_taipei_agency']=agency[keep].to_numpy()
                        selected.append(f)
                details.append(dict(path=item['path'],member=member,encoding='utf-8-sig',schema=header,national_raw_csv_rows=total,national_party_rows=party_rows,non_observation_rows=len(non_observation),footer_or_non_observation_records=non_observation,taipei_address_party_rows=city_rows,taipei_address_first=city_first,taipei_agency_first=agency_rows,observed_months=dict(months)))
        return pd.concat(selected,ignore_index=True),details

    def raw_report(self,family,crc=True):
        frames=self.load_family(family);meta=self.config['metadata'][family]
        display(pd.DataFrame([meta]).T.rename(columns={0:'source_metadata_and_limits'}))
        for item in self.family_items(family):
            display(pd.DataFrame([{k:v for k,v in item.items() if k not in ['members','encoding_checks']}]))
            if 'members' in item:
                show('ZIP原始成員清單；非解壓暫存資料來源',pd.DataFrame(item['members']))
                if crc:
                    with zipfile.ZipFile(self.file(item['path'])) as z:assert z.testzip() is None
                    print('ZIP 全成員CRC通過:',item['path'])
        show('實際讀取範圍／編碼／CRS／全國或地區計數',pd.DataFrame(self.summaries[family]))
        for name,f in frames.items():
            display(Markdown('### '+safe_text(name)))
            if isinstance(f,gpd.GeoDataFrame):
                print('Source CRS WKT:',f.crs.to_wkt() if f.crs else 'missing')
                sample=f.drop(columns='geometry').head(10)
                geom_stats=pd.DataFrame({'geometry_type':f.geom_type,'valid':f.geometry.is_valid,'empty':f.geometry.is_empty})
                show('幾何品質',geom_stats.value_counts(dropna=False).reset_index(name='N'))
            else:sample=f.head(10)
            show('實際前十列；全國資料表為篩選後臺北第一當事人，非全國母體',sample)
            d=f.drop(columns='geometry',errors='ignore')
            definitions=[]
            known={'road_width':'都市計畫／地籍路寬標註原字串，非實測車行寬度','angle':'原角度字串，單位及精確用途未獲欄位規格認證','rddate':'官方欄位說明為設置日期；1899占位及缺值另列，不證明已拆除歷史','rdlblg':'官方欄位稱長度；單位／構件語義未獲認證，0不當真實零長','rdlbwt':'官方欄位稱寬度；40等值不能未確認單位就當公尺','liarea':'官方欄位稱面積；0及缺值不取代幾何聯集面積','licode':'圖形標線代碼；本機觀測域不等於已取得完整官方碼表','keyid':'來源圖形鍵，須跨圖層檢查唯一性','osm_id':'OSM來源物件ID，可能分段重複，非所有幾何唯一鍵','fclass':'Geofabrik道路分類；研究分組另列','oneway':'F依線方向、T反向、B雙向，依Geofabrik現行共同欄位說明','layer':'相對層級，非完整節點拓樸','bridge':'來源橋梁標記，並非完整立交認證','tunnel':'來源隧道標記，並非完整立交認證','經度':'原經度數值，CRS證據依各來源分開','緯度':'原緯度數值，CRS證據依各來源分開','死亡受傷人數':'來源發布的死亡／受傷總量字串；不直接推定所有死亡時間窗口','VILLCODE':'來源官方村里代碼字串，透過既有crosswalk人口碼對照CPTVID','TOWNCODE':'來源行政區代碼，保留原格式，不任意截取','_source_row':'本次來源追溯列號；不是官方穩定事件或設施ID'}
            known.update({'發生時間':'斑點圖事故日期與分鐘時間字串；全國版則HHMMSS，來源分開解析','發生年度':'全國版西元事故年','發生月份':'事故月份','發生日期':'全國版YYYYMMDD事故日期','處理別':'事故A1／A2處理類別原碼；與既有處理別比較，不當作獨立時間語義認證','事故類別名稱':'全國公布A1／A2類別，官方定義見來源說明','肇事地點':'原事故位置文字，不等於當事人居住地','發生地點':'全國事故地址，臺北篩選及可逆移除市名前綴使用','座標-X':'事故原X值，採經度工作解讀但datum未獲正式認證','座標-Y':'事故原Y值，採緯度工作解讀但datum未獲正式認證','當事者順位':'同事故當事人順位，1作第一當事人候選口徑','處理單位名稱警局層':'處理警局名稱；另與臺北地址篩選比較，不當正式行政里','光線名稱':'事故發生時全國版光線中文類別，與地方照明／光線分年比較','事故位置大類別名稱':'事故位置上層中文類別','事故位置子類別名稱':'事故位置細類中文名稱','事故類型及型態大類別名稱':'事故型態上層中文類別','事故類型及型態子類別名稱':'事故型態細類中文名稱','當事者區分-類別-大類別名稱-車種':'當事者車種上層中文名稱','當事者區分-類別-子類別名稱-車種':'當事者車種細類中文名稱，不代表所有涉入車輛','流水號':'此號誌快照列示序號，不推定跨版本穩定ID','地點':'號誌路口名稱／位置描述','行政區':'來源所列行政區，與幾何歸區另核對','WGS經度座標':'WGS標記之經度欄；作4326工作解讀','WGS緯度座標':'WGS標記之緯度欄；作4326工作解讀','出入口名稱':'含站名的出入口位置描述，站名擷取僅診斷','出入口編號':'站內出入口編號，非車站唯一碼','項次':'來源序號，不推定跨版本穩定設施ID','是否為無障礙用':'來源無障礙用途標記；空白及代碼不自行猜測','COUNTYNAME':'來源縣市名稱','COUNTYCODE':'來源縣市代碼原字串','COUNTYID':'來源縣市識別碼','TOWNNAME':'來源鄉鎮市區名稱','TOWNID':'來源鄉鎮市區識別碼','VILLNAME':'來源村里名稱，保留原字形','VILLENG':'來源村里英文名','NOTE':'來源備註','code':'Geofabrik分類數字碼，非道路等級數值尺度','name':'OSM原道路名稱，可缺值','ref':'OSM道路編號／參考標記，可缺值','maxspeed':'來源速限值；0可能為未知，非測得零速度'})
            for col in d:
                definitions.append(dict(field=col,dtype=str(d[col].dtype),missing=int(d[col].isna().sum()+(d[col].eq('').sum() if d[col].dtype==object else 0)),distinct=int(d[col].nunique(dropna=False)),definition=known.get(col,'來源原始欄位；名稱／官方頁列示之外的精確產製語義未認證' if not col.startswith('_') else '本次僅記憶體追溯／診斷旗標，原始檔未新增欄')))
            show('各欄型態、缺失、觀測域及定義／未知',pd.DataFrame(definitions))
            numeric=d.select_dtypes(include='number')
            if len(numeric.columns):show('數值摘要（不把類別碼大小當實質尺度）',numeric.describe(percentiles=[.25,.5,.75]).T.reset_index())
            measure=[c for c in ['座標-X','座標-Y','經度','緯度','WGS經度座標','WGS緯度座標'] if c in d]
            if measure:
                measured=d[measure].apply(pd.to_numeric,errors='coerce');show('原字串座標解析診斷與摘要；原欄未改',measured.describe().T.reset_index())
                display(pd.DataFrame([dict(field=c,missing_or_unparseable=int(measured[c].isna().sum()),zero=int(measured[c].eq(0).sum())) for c in measure]))
            if family=='national_accidents':
                headers=list(dict.fromkeys(c for q in self.summaries[family] for c in q['schema']))
                show('全國CSV完整原欄結構（未讀取欄不冒稱已檢查缺失）',pd.DataFrame([dict(field=c,read_for_taipei_diagnostic=c in d,definition=known.get(c,'原始欄名；本次不選讀，精確語義／型態與缺失未驗證')) for c in headers]))
            print('原始屬性完整列重複（不含診斷追溯欄）',int(d.drop(columns=[c for c in d if c.startswith('_')]).duplicated().sum()))
            for col in ['fclass','licode','oneway','layer','bridge','tunnel','處理別','事故類別名稱']:
                if col in d:
                    tab=d[col].fillna('[missing]').value_counts(dropna=False).head(12).rename_axis(col).reset_index(name='N');tab['ratio_of_loaded_rows']=tab.N/len(d)
                    show('類別前12項：'+col,tab)
            if 'rddate' in d:
                dt=pd.to_datetime(d.rddate,errors='coerce');valid=dt.ge('1950-01-01')
                display(pd.DataFrame([dict(field='rddate',missing_or_unparseable=int(dt.isna().sum()),pre1950_placeholder=int((dt.notna()&~valid).sum()),eligible_survivors_2024=int((valid&dt.le('2024-12-31')).sum()),eligible_survivors_2025=int((valid&dt.le('2025-12-31')).sum()),post2025=int((valid&dt.gt('2025-12-31')).sum()))]))
        return frames

    def candidates(self):
        if 'candidates' in self.cache:return self.cache['candidates']
        out={}
        for y,basename in [(2024,'113年-臺北市死傷交通事故明細.csv'),(2025,'114年-臺北市死傷交通事故明細.csv')]:
            path='data/raw/'+basename;f=pd.read_csv(self.file(path),encoding='utf-8-sig',dtype=str,keep_default_na=False)
            f=f[pd.to_numeric(f['當事人序號'],errors='coerce').eq(1)].copy();f['_source_row']=f.index+1;f['_source_path']=path
            f['record_id']=[f'tpe-crash:{y}:{self.config["existing_bindings"][path]}:r{r:06d}' for r in f._source_row]
            f=f.reset_index(drop=True);f['_minute']=pd.to_datetime(dict(year=pd.to_numeric(f['發生年度'])+1911,month=pd.to_numeric(f['發生月']),day=pd.to_numeric(f['發生日'])),errors='coerce')+pd.to_timedelta(pd.to_numeric(f['發生時-Hours'],errors='coerce'),unit='h')+pd.to_timedelta(pd.to_numeric(f['發生分'],errors='coerce'),unit='m')
            f['_address']=f['肇事地點'];f['_address_valid']=True;f['_lon']=pd.to_numeric(f['座標-X'],errors='coerce');f['_lat']=pd.to_numeric(f['座標-Y'],errors='coerce')
            out[y]=f
        assert len(out[2024])==22368 and len(out[2025])==22762
        self.cache['candidates']=out;return out

    def assign(self,f,boundary=None):
        b=self.boundary if boundary is None else boundary
        bg=np.asarray(b.geometry.array,dtype=object);tree=s.STRtree(bg)
        lon=f['_lon'].to_numpy(float);lat=f['_lat'].to_numpy(float);ok=np.isfinite(lon)&np.isfinite(lat)&(abs(lon)<=180)&(abs(lat)<=90)
        idx=np.flatnonzero(ok);x=np.full(len(f),np.nan);y=x.copy();x[idx],y[idx]=self.to3826.transform(lon[idx],lat[idx])
        pts=s.points(x[idx],y[idx]);ws=[[] for _ in range(len(f))];cs=[[] for _ in range(len(f))]
        for pred,lists in [('within',ws),('covered_by',cs)]:
            q=tree.query(pts,predicate=pred)
            for a,j in zip(*q):lists[idx[a]].append(int(j))
        ids=b.CPTVID.astype(str).to_numpy();districts=b.TNAME.to_numpy()
        statuses=[];vill=[];district=[];covered=[]
        # Vertex extraction only needed when real boundary candidates exist.
        vertex_sets={}
        for i,(w,c) in enumerate(zip(ws,cs)):
            if not ok[i]:status='missing_or_unparseable'
            elif len(w)==len(c)==1 and w==c:status='unique_clear'
            elif len(w)>1:status='positive_area_overlap'
            elif len(c)>=2 and not w:
                for j in c:
                    if j not in vertex_sets:
                        pp=[bg[j]] if bg[j].geom_type=='Polygon' else list(bg[j].geoms)
                        vertex_sets[j]={tuple(xy[:2]) for p in pp for r in [p.exterior,*p.interiors] for xy in r.coords}
                status='shared_vertex' if sum((x[i],y[i]) in vertex_sets[j] for j in c)>=2 else 'shared_boundary'
            elif len(c)>1 or len(w)>1:status='other_multiple'
            elif len(c)==1 and not w:status='single_boundary_pending'
            else:status='outside_or_hole'
            statuses.append(status);vill.append(ids[c[0]] if status=='unique_clear' else '');district.append(districts[c[0]] if status=='unique_clear' else '');covered.append(';'.join(sorted(ids[c])))
        out=pd.DataFrame({'record_id':f['record_id'].to_numpy() if 'record_id' in f else np.arange(len(f)).astype(str),'status':statuses,'village_id':vill,'spatial_district':district,'covered_candidates':covered,'x':x,'y':y})
        rawdistrict=f['區序'].str.extract(r'^\d{2}(.+區)$',expand=False).fillna('') if '區序' in f else pd.Series('',index=f.index)
        addressdistrict=f['_address'].map(lambda a:m.group(1) if isinstance(a,str) and (m:=re.match(r'^(?:臺北市|台北市)?(中正區|萬華區|大安區|南港區|內湖區|大同區|北投區|松山區|中山區|文山區|士林區|信義區)',a)) else '')
        out['raw_district']=rawdistrict.to_numpy();out['address_district']=addressdistrict.to_numpy()
        out['district_conflict']=out.status.eq('unique_clear')&out.raw_district.ne('')&out.raw_district.ne(out.spatial_district)
        out['address_label_conflict']=out.raw_district.ne('')&out.address_district.ne('')&out.raw_district.ne(out.address_district)
        out['conservative_candidate']=out.status.eq('unique_clear')&~out.district_conflict&~out.address_label_conflict
        assert len(out)==len(f) and out.record_id.is_unique
        return out

    def historical_review(self):
        frames=self.load_family('historical_boundaries');hist={};info=[]
        for y in [2024,2025]:
            item=self.family_items('historical_boundaries')[y-2024]
            key=next(k for k in frames if k.startswith(item['path']+'::') and 'VILLAGE_NLSC_' in k)
            national=frames[key];b=national[national.COUNTYNAME.eq('臺北市')].copy()
            assert len(b)==456 and b.VILLCODE.is_unique
            joined=b.merge(self.cw[['population_code','village_id','district_name','standard_village_name']],left_on='VILLCODE',right_on='population_code',how='left',validate='one_to_one',indicator=True)
            assert joined['_merge'].eq('both').all() and joined.TOWNNAME.eq(joined.district_name).all()
            joined=joined.set_index('village_id').reindex(self.ids).reset_index();joined['CPTVID']=joined.village_id;joined['TNAME']=joined.TOWNNAME;joined['VNAME']=joined.VILLNAME
            projected=joined.to_crs(3826);assert projected.geometry.is_valid.all()
            hist[y]=projected
            info.append(dict(label=y,official_version='113年版' if y==2024 else '114年版',literal_member=key,national_primary_rows=len(national),taipei_rows=len(b),original_crs=str(b.crs),unique_codes=b.VILLCODE.is_unique,invalid_taipei=int((~b.geometry.is_valid).sum()),standard_name_mismatches=int(joined.VILLNAME.ne(joined.standard_village_name).sum())))
        show('官方年版、內部字串與精確日曆／全年適用限制分開',pd.DataFrame(info))
        diffs=[]
        for label,a,b in [('2024_fixed',hist[2024],self.boundary),('2025_fixed',hist[2025],self.boundary),('2024_2025',hist[2024],hist[2025])]:
            ga=np.asarray(a.geometry.array,dtype=object);gb=np.asarray(b.geometry.array,dtype=object)
            intersection=s.area(s.intersection(ga,gb));union=s.area(s.union(ga,gb));sym=s.area(s.symmetric_difference(ga,gb))
            for i in range(456):diffs.append(dict(comparison=label,village_id=self.ids[i],district=self.districts[i],fixed_name=self.boundary.VNAME.iloc[i],name_a=a.VNAME.iloc[i],name_b=b.VNAME.iloc[i],area_a_m2=ga[i].area,area_b_m2=gb[i].area,intersection_m2=intersection[i],symdiff_m2=sym[i],iou=intersection[i]/union[i],area_delta_m2=ga[i].area-gb[i].area))
        table=pd.DataFrame(diffs);show('456里三種比較的摘要',table.groupby('comparison')[['symdiff_m2','iou','area_delta_m2']].describe())
        show('實際差異最大前20；幾何差不直接認定為法定行政變更',table.sort_values('symdiff_m2',ascending=False).head(20))
        show('三套圖資完整逐里差異',table)
        self.hist=hist;self.boundary_differences=table;self.history_info=info
        return hist,table

    def historical_accident_review(self):
        candidates=self.candidates();audits={};summary=[];changes=[]
        for year,f in candidates.items():
            for label,b in [('fixed',self.boundary),('historical',self.hist[year])]:
                a=self.assign(f,b);audits[(year,label)]=a
                summary.append(dict(year=year,boundary=label,N=len(a),unique=int(a.status.eq('unique_clear').sum()),district_conflict=int(a.district_conflict.sum()),extra_address_conflict=int((a.status.eq('unique_clear')&~a.district_conflict&a.address_label_conflict).sum()),outside_or_hole=int(a.status.eq('outside_or_hole').sum()),missing=int(a.status.eq('missing_or_unparseable').sum()),multiple_or_boundary=int((~a.status.isin(['unique_clear','outside_or_hole','missing_or_unparseable'])).sum()),conservative=int(a.conservative_candidate.sum())))
            x=audits[(year,'fixed')];y=audits[(year,'historical')]
            changed=x.village_id.ne(y.village_id)|x.status.ne(y.status)
            changes.append(dict(year=year,status_changed=int(x.status.ne(y.status).sum()),village_or_status_changed=int(changed.sum()),district_changed=int(x.spatial_district.ne(y.spatial_district).sum()),old_district_conflicts_resolved=int((x.district_conflict&~y.district_conflict&y.status.eq('unique_clear')).sum()),new_district_conflicts=int((~x.district_conflict&y.district_conflict).sum())))
            show(f'{year}改變狀態／行政里紀錄完整清單',pd.DataFrame({'record_id':f.record_id,'address':f['_address'],'fixed_status':x.status,'historical_status':y.status,'fixed_village':x.village_id,'historical_village':y.village_id,'raw_district':x.raw_district,'fixed_district':x.spatial_district,'historical_district':y.spatial_district})[changed])
        summary=pd.DataFrame(summary);display(summary);display(pd.DataFrame(changes))
        fixed=summary[summary.boundary.eq('fixed')].set_index('year')
        assert fixed.unique.to_dict()=={2024:22351,2025:22732}
        assert fixed.conservative.to_dict()=={2024:21920,2025:22292}
        self.audits=audits;self.assignment_summary=summary;self.assignment_changes=changes
        return summary

    @staticmethod
    def canonical_address(address):
        """Diagnostic equivalence key, NOT a lossless address or geocertification.

        Original text stays in both source frames, so transformations are fully
        inspectable. Never drop house/lane numbers or use fuzzy/coordinate keys.
        Only city/district repetition, intersection delimiters/end marker, and
        zero-distance decorations are normalized. Nonzero offsets remain.
        """
        if not isinstance(address,str):return None
        district=re.match(r'^(中正區|萬華區|大安區|南港區|內湖區|大同區|北投區|松山區|中山區|文山區|士林區|信義區)',address)
        if not district:return None
        district=district.group(1);parts=re.split(r'\s*/\s*|與',address.strip());out=[]
        for part in parts:
            part=re.sub(r'^(臺北市|台北市)','',part.strip())
            if part.startswith(district):part=part[len(district):]
            part=re.sub(r'(?:前|後|旁)?0(?:\.0+)?公尺$','',part)
            part=re.sub(r'(號)(前|後|旁)$',r'\1',part)
            if len(parts)>1:part=re.sub(r'口+$','',part)
            if not part:return None
            out.append(part)
        return district,tuple(sorted(out))

    @staticmethod
    def event_match(local,other):
        """Unique minute+lossless address, then globally unique minute, never coordinates."""
        def keys(frame):
            valid=frame['_minute'].notna()&frame['_address_valid']
            key=[(str(t),a) if v else None for t,a,v in zip(frame['_minute'],frame['_address'],valid)]
            return key,Counter(k for k in key if k is not None)
        lk,lc=keys(local);rk,rc=keys(other);rmap={k:i for i,k in enumerate(rk) if k is not None and rc[k]==1}
        matched={};used=set()
        for i,k in enumerate(lk):
            if k is not None and lc[k]==rc.get(k)==1:matched[i]=(rmap[k],'A_unique_minute_exact_address');used.add(rmap[k])
        def canonical_keys(frame):
            keys=[]
            for t,a,valid in zip(frame['_minute'],frame['_address'],frame['_address_valid']):
                ca=Context.canonical_address(a) if valid else None
                keys.append((str(t),ca) if pd.notna(t) and ca else None)
            return keys,Counter(k for k in keys if k is not None)
        lcanon,lcc=canonical_keys(local);rcanon,rcc=canonical_keys(other)
        cmap={k:i for i,k in enumerate(rcanon) if k is not None and rcc[k]==1}
        for i,k in enumerate(lcanon):
            if i not in matched and k is not None and lcc[k]==rcc.get(k)==1 and cmap[k] not in used:
                matched[i]=(cmap[k],'C_unique_minute_normalized_address_candidate');used.add(cmap[k])
        lm=Counter(str(t) for t in local['_minute'] if pd.notna(t));rm=Counter(str(t) for t in other['_minute'] if pd.notna(t))
        rtime={str(t):i for i,t in enumerate(other['_minute']) if pd.notna(t) and rm[str(t)]==1}
        for i,t in enumerate(local['_minute']):
            if i in matched or pd.isna(t):continue
            k=str(t)
            if lm[k]==rm.get(k)==1 and rtime[k] not in used:
                j=rtime[k];matched[i]=(j,'B_unique_minute_without_coordinates');used.add(j)
        rows=[]
        for i in range(len(local)):
            if i in matched:j,grade=matched[i]
            else:j=-1;grade='E_unmatched_or_nonunique'
            rows.append(dict(local_index=i,other_index=j,match_grade=grade))
        result=pd.DataFrame(rows)
        assert result.local_index.is_unique and result.loc[result.other_index.ge(0),'other_index'].is_unique
        return result

    def supplementary_accidents(self,kind):
        frames=self.load_family(kind);out={}
        for index,(key,frame) in enumerate(frames.items()):
            year=2024+index;f=frame.copy()
            if kind=='accident_points':
                f['_minute']=pd.to_datetime(f['發生時間'],format='mixed',errors='coerce').dt.floor('min')
                f['_address']=f['肇事地點'];f['_address_valid']=f['_decoding_valid']
                f['_lon']=pd.to_numeric(f['座標-X'],errors='coerce');f['_lat']=pd.to_numeric(f['座標-Y'],errors='coerce')
                f['_handling']=f['處理別']
            else:
                # Primary city definition by explicit address; agency-only discrepancies retained in raw report.
                f=f[f['_city_address']].copy().reset_index(drop=True)
                dt=f['發生日期'].str.strip()+f['發生時間'].str.strip().str.zfill(6)
                f['_minute']=pd.to_datetime(dt,format='%Y%m%d%H%M%S',errors='coerce').dt.floor('min')
                original=f['發生地點'];prefix=original.str.extract(r'^(臺北市|台北市)',expand=False).fillna('')
                f['_address']=original.str.replace(r'^(臺北市|台北市)','',regex=True)
                assert (prefix+f['_address']).eq(original).all(),'Address prefix normalization must reconstruct exactly'
                f['_address_valid']=True;f['_lon']=pd.to_numeric(f['經度'],errors='coerce');f['_lat']=pd.to_numeric(f['緯度'],errors='coerce')
                f['_handling']=f['事故類別名稱'].map({'A1':'1','A2':'2'}).fillna('')
            f['record_id']=[f'{kind}:{year}:r{i+1}' for i in range(len(f))]
            assert f['_minute'].dt.year.dropna().eq(year).all()
            out[year]=f.reset_index(drop=True)
        return out

    def accident_cross_review(self,kind):
        local=self.candidates();other=self.supplementary_accidents(kind);matches={};summary=[];coordinate_rows=[];imputation=[];anomaly_rows=[]
        for year,l in local.items():
            r=other[year];m=self.event_match(l,r);matches[year]=m
            counts=m.match_grade.value_counts().to_dict()
            summary.append(dict(source=kind,year=year,local_N=len(l),other_city_first_N=len(r),exact_unique=int(counts.get('A_unique_minute_exact_address',0)),normalized_address_candidate=int(counts.get('C_unique_minute_normalized_address_candidate',0)),temporal_unique_candidate=int(counts.get('B_unique_minute_without_coordinates',0)),local_unmatched=int(m.other_index.lt(0).sum()),other_unmatched=len(r)-m.other_index.ge(0).sum(),other_key_duplicate_rows=int(r.duplicated(['_minute','_address'],keep=False).sum()),other_bad_address=int((~r['_address_valid']).sum()),other_missing_coordinates=int((~np.isfinite(r['_lon'])|~np.isfinite(r['_lat'])).sum())))
            details=[]
            fixed=self.audits[(year,'fixed')] if hasattr(self,'audits') else self.assign(l)
            anomaly_mask=(fixed.district_conflict|fixed.address_label_conflict|fixed.status.ne('unique_clear')).to_numpy()
            for row in m[m.other_index.ge(0)].itertuples(index=False):
                i,j=row.local_index,row.other_index;a=l.iloc[i];b=r.iloc[j]
                lok=np.isfinite(a['_lon']) and np.isfinite(a['_lat']);rok=np.isfinite(b['_lon']) and np.isfinite(b['_lat'])
                equal=lok and rok and a['_lon']==b['_lon'] and a['_lat']==b['_lat']
                delta=np.nan
                if lok and rok:
                    ax,ay=self.to3826.transform(a['_lon'],a['_lat']);bx,by=self.to3826.transform(b['_lon'],b['_lat']);delta=float(np.hypot(ax-bx,ay-by))
                address_conflict=bool(a['_address_valid'] and b['_address_valid'] and a['_address']!=b['_address'])
                # The city detailed files do NOT publish a handling column.
                # Do not invent one from death counts or silently equate fields.
                d=dict(year=year,local_index=i,other_index=j,record_id=a.record_id,match_grade=row.match_grade,local_address=a['_address'],other_address=safe_text(b['_address']),other_address_valid=bool(b['_address_valid']),address_conflict=address_conflict,coordinate_class='A_same' if equal else 'B_one_missing' if lok!=rok else 'C_different' if lok and rok else 'both_missing',difference_m=delta,local_lon=a['_lon'],local_lat=a['_lat'],other_lon=b['_lon'],other_lat=b['_lat'],local_handling='not_present_in_city_detail',handling=b['_handling'],handling_conflict='not_comparable_to_city_detail')
                details.append(d)
                if not lok and rok:imputation.append({**d,'source_path':b['_source_path'],'source_row':int(b['_source_row']),'source_member':b.get('_source_member',''),'status':'candidate_only_not_applied'})
                if anomaly_mask[i]:anomaly_rows.append({**d,'source':kind,'original_spatial_status':fixed.iloc[i].status,'original_district_conflict':bool(fixed.iloc[i].district_conflict)})
            detail=pd.DataFrame(details);coordinate_rows.append(detail)
            show(f'{kind} {year}配對等級與座標差異（配對鍵未使用座標）',detail.groupby(['match_grade','coordinate_class']).size().rename('N').reset_index())
            if len(detail):show('座標差分位數m；只對兩份均可解析且已配對紀錄',detail.groupby('match_grade').difference_m.describe(percentiles=[.25,.5,.75,.95,.99]).reset_index())
            show('地址／處理別交叉衝突；不作配對前提',detail.groupby(['match_grade','address_conflict','handling_conflict']).size().rename('N').reset_index())
            show(f'{year}地址衝突／座標差大於1m紀錄；不直接修正',detail[detail.address_conflict|detail.difference_m.gt(1)])
            show(f'{year}未配對或鍵不唯一的原始候選',l.loc[m.other_index.lt(0),['record_id','_minute','_address','座標-X','座標-Y']])
        result=pd.DataFrame(summary);display(result)
        self.cache[kind+'_aligned']=dict(other=other,matches=matches,details=pd.concat(coordinate_rows,ignore_index=True),summary=result,imputation=pd.DataFrame(imputation),anomalies=pd.DataFrame(anomaly_rows))
        show('缺座標候選補充清單（未套用）',pd.DataFrame(imputation))
        show('既有869區名／額外2地址／44界外／3缺座標之跨來源對照',pd.DataFrame(anomaly_rows))
        print('相同底層警方來源的吻合不是獨立地理認證；B級只時間唯一候選不冒充精確地址已確認。原始座標、事故數與政策均未改。')
        return result

    def casualty_review(self):
        aligned=self.cache['national_accidents_aligned'];local=self.candidates();comparison=[];r20=[];code_tables=[]
        n=__import__('nbformat').read(self.file('data/code/taipei_2024_2025_crash_validation.ipynb'),as_version=4)
        books=next(ast.literal_eval(ast.parse(c.source).body[0].value) for c in n.cells if c.cell_type=='code' and c.source.startswith('BOOKS ='))
        for year,l in local.items():
            r=aligned['other'][year];m=aligned['matches'][year]
            pairs=m[m.match_grade.isin(['A_unique_minute_exact_address','C_unique_minute_normalized_address_candidate'])].copy()
            a=l.iloc[pairs.local_index.to_numpy()].reset_index(drop=True);b=r.iloc[pairs.other_index.to_numpy()].reset_index(drop=True)
            parsed=b['死亡受傷人數'].str.extract(r'^死亡(\d+);受傷(\d+)$').apply(pd.to_numeric,errors='coerce')
            ld=pd.to_numeric(a['死亡人數'],errors='coerce');late=pd.to_numeric(a['2-30日死亡人數'],errors='coerce');inj=pd.to_numeric(a['受傷人數'],errors='coerce')
            comparison.append(dict(year=year,raw_exact_pairs=int(pairs.match_grade.eq('A_unique_minute_exact_address').sum()),normalized_address_candidates=int(pairs.match_grade.str.startswith('C_').sum()),address_supported_pairs=len(a),national_casualty_parse_fail=int(parsed.isna().any(axis=1).sum()),local_death_vs_national_mismatch=int(ld.ne(parsed[0]).sum()),local_death_plus_2_30_vs_national_mismatch=int((ld+late).ne(parsed[0]).sum()),injury_mismatch=int(inj.ne(parsed[1]).sum()),A1=int(b['_handling'].eq('1').sum()),A2=int(b['_handling'].eq('2').sum())))
            for local_col,nat_col,book in [('事故類型及型態','事故類型及型態子類別名稱','accident_type'),('事故位置','事故位置子類別名稱','position'),('車種','當事者區分-類別-子類別名稱-車種','vehicle'),('道路照明設備' if year==2024 else '光線','光線名稱','lighting')]:
                q=pd.DataFrame({'local_code':a[local_col],'national_label':b[nat_col]})
                q['prior_codebook_label']=pd.to_numeric(q.local_code,errors='coerce').map(books[book]['labels'])
                table=q.groupby(['local_code','prior_codebook_label','national_label'],dropna=False).size().rename('N').reset_index()
                show(f'{year} {local_col}之實際對應；實證對應不自動當完整官方碼表',table)
                code_tables.append(dict(year=year,field=local_col,local_code_count=q.local_code.nunique(),one_to_many_codes=int(q.groupby('local_code').national_label.nunique().gt(1).sum()),paired_rows=len(q)))
            suspicious=pd.to_numeric(l['受傷程度'],errors='coerce').eq(5)&pd.to_numeric(l['2-30日死亡人數'],errors='coerce').eq(0)
            assert int(suspicious.sum())=={2024:6,2025:4}[year]
            for i in np.flatnonzero(suspicious):
                match=m.loc[m.local_index.eq(i)].iloc[0];j=int(match.other_index)
                r20.append(dict(year=year,record_id=l.iloc[i].record_id,local_address=l.iloc[i]['_address'],local_party_injury=l.iloc[i]['受傷程度'],local_death=l.iloc[i]['死亡人數'],local_2_30=l.iloc[i]['2-30日死亡人數'],local_injury=l.iloc[i]['受傷人數'],match_grade=match.match_grade,national_casualty=r.iloc[j]['死亡受傷人數'] if j>=0 else '',national_handling=r.iloc[j]['_handling'] if j>=0 else '',limitation='全國版無同等個別受傷程度欄，事故總量吻合不能解除個別程度／2–30日疑點'))
        display(pd.DataFrame(comparison));show('R20十筆完整跨來源核對，保留原值',pd.DataFrame(r20))
        p=self.cache['accident_points_aligned']['details'];q=aligned['details']
        supported=['A_unique_minute_exact_address','C_unique_minute_normalized_address_candidate']
        h=p[p.match_grade.isin(supported)][['record_id','year','handling']].merge(q[q.match_grade.isin(supported)][['record_id','handling']],on='record_id',suffixes=('_point','_national'),validate='one_to_one')
        show('明細無處理別原欄；兩補充來源具地址支持A/C對應之A1／A2（C仍候選）',h.groupby(['year','handling_point','handling_national']).size().rename('N').reset_index())
        self.handling_summary=h.groupby(['year','handling_point','handling_national']).size().rename('N').reset_index().to_dict('records')
        display(Markdown('官方頁支持A1＝當場或24小時內死亡、A2＝受傷或超過24小時死亡；**並不直接認證臺北每個死亡欄的時間窗口**。全國發布的死亡受傷總量及原「死亡人數」「2–30日死亡人數」分別保留；關聯對應只作實證證據，R20不自動修正或結案。'))
        self.casualty_summary=comparison;self.r20=pd.DataFrame(r20);self.code_summary=code_tables
        print('本次全國原文精確地址A為0；C格式正規化地址僅候選。代碼／傷亡對應是C候選實證，不宣稱已取得官方事件對照或精確地理認證；B時間唯一者不納此對照。')
        return pd.DataFrame(comparison)

    def infrastructure_prepare(self):
        self.layers={};self.infrastructure_quality=[];self.time_diagnostics=[]
        for family in ['osm','signals','crossings','road_width','sidewalk','mrt']:
            loaded=self.load_family(family)
            if family in ['signals','mrt']:
                f=next(iter(loaded.values())).copy()
                loncol,latcol=('WGS經度座標','WGS緯度座標') if family=='signals' else ('經度','緯度')
                lon=pd.to_numeric(f[loncol],errors='coerce');lat=pd.to_numeric(f[latcol],errors='coerce')
                valid=np.isfinite(lon)&np.isfinite(lat)&lon.between(-180,180)&lat.between(-90,90)
                geom=np.empty(len(f),dtype=object);geom[:]=None
                x,y=self.to3826.transform(lon[valid],lat[valid]);geom[valid]=s.points(x,y)
                g=gpd.GeoDataFrame(f,geometry=geom,crs=3826)
                self.infrastructure_quality.append(dict(family=family,source_rows=len(g),invalid_coordinates=int((~valid).sum()),crs_evidence='官方WGS欄名與頁面，4326工作解讀' if family=='signals' else '經緯度欄與數值；4326工作假設，非本機datum認證'))
            else:
                g=gpd.GeoDataFrame(pd.concat(list(loaded.values()),ignore_index=True),geometry='geometry',crs=next(iter(loaded.values())).crs)
                assert g.crs is not None;g=g.to_crs(3826)
            source_columns=[c for c in g if not c.startswith('_') and c!='geometry']
            valid=g.geometry.notna()&~g.geometry.is_empty&g.geometry.is_valid
            within_buffer=g.geometry.intersects(self.study).fillna(False)
            q=dict(family=family,loaded_rows=len(g),geometry_types=g.geom_type.value_counts().to_dict(),null_or_empty=int((g.geometry.isna()|g.geometry.is_empty).sum()),invalid_geometry=int((g.geometry.notna()&~g.geometry.is_valid).sum()),exact_geometry_duplicate_rows=int(g.geometry.to_wkb().duplicated(keep=False).sum()),attribute_duplicate_rows=int(g[source_columns].astype(str).duplicated(keep=False).sum()),study_buffer_related=int(within_buffer.sum()))
            self.infrastructure_quality.append(q)
            if family in ['crossings','sidewalk']:
                dt=pd.to_datetime(g.rddate,errors='coerce');real=dt.ge('1950-01-01')
                self.time_diagnostics.append(dict(family=family,N=len(g),missing_date=int(dt.isna().sum()),pre1950_placeholder=int((dt.notna()&~real).sum()),current_survivors_eligible_2024=int((real&dt.le('2024-12-31')).sum()),current_survivors_eligible_2025=int((real&dt.le('2025-12-31')).sum()),post2025=int((real&dt.gt('2025-12-31')).sum()),limitation='現存快照設置日資格，不含已拆除／遷移歷史'))
                show(f'{family}圖形代碼域與長寬面積欄品質',pd.DataFrame([dict(field=c,missing=int(g[c].isna().sum()),zero=int(pd.to_numeric(g[c],errors='coerce').eq(0).sum()),positive=int(pd.to_numeric(g[c],errors='coerce').gt(0).sum())) for c in ['liarea','rdlblg','rdlbwt']]))
                show(f'{family}完整LICODE分布；不能由檔名決定所有圖徵語義',g.licode.fillna('[missing]').value_counts().rename_axis('licode').reset_index(name='records'))
            g['_geometry_eligible']=valid
            self.layers[family]=g
        show('各圖資實際幾何與重複／範圍品質',pd.DataFrame(self.infrastructure_quality))
        display(pd.DataFrame(self.time_diagnostics))
        osm=self.layers['osm']
        groups={
            'major':['motorway','trunk','primary','motorway_link','trunk_link','primary_link'],
            'secondary':['secondary','tertiary','secondary_link','tertiary_link'],
            'local':['unclassified','residential','living_street'],
            'service':['service','busway'],
            'walking':['pedestrian','footway','path','steps','bridleway'],
            'cycling':['cycleway'],
            'other_nonmotor_or_unconfirmed':['track','track_grade1','track_grade2','track_grade3','track_grade4','track_grade5','unknown']}
        mapping={value:group for group,values in groups.items() for value in values}
        osm['_research_road_group']=osm.fclass.map(mapping).fillna('unclassified_source_code')
        osm['_motor_candidate']=osm['_research_road_group'].isin(['major','secondary','local','service'])
        table=osm.groupby(['fclass','_research_road_group','_motor_candidate'],dropna=False).agg(records=('fclass','size'),represented_length_km=('geometry',lambda x:sum(g.length for g in x)/1000)).reset_index()
        show('逐fclass候選分組；major定義為研究選擇，非官方實體道路分級',table)
        show('方向與立交欄位觀測域',osm.groupby(['oneway','layer','bridge','tunnel'],dropna=False).size().rename('records').reset_index())
        self.road_mapping_table=table
        width=self.layers['road_width'];num=width.road_width.str.extract(r'^\s*(\d+(?:\.\d+)?)\s*[mM]\s*$',expand=False).pipe(pd.to_numeric,errors='coerce')
        width['_annotation_width_m']=num
        diff=abs(width.length-num)
        self.width_diagnostic=dict(records=len(width),parseable_annotation_width=int(num.notna().sum()),nonpositive=int(num.le(0).sum()),median_line_length_m=float(width.length.median()),median_annotation_width_m=float(num.median()),line_length_within_1cm_of_width=int(diff.le(.01).sum()),longitudinal_weighting_appropriate=False)
        display(pd.DataFrame([self.width_diagnostic]));show('原始路寬標註字串分布',width.road_width.value_counts().head(20).rename_axis('raw_annotation').reset_index(name='N'))
        print('路寬線長與標註寬度相近＋官方描述為都市計畫／地籍標註，支持橫向尺寸線判讀；不將其長度當縱向道路長度加權，不宣稱實測車行寬度。')
        sidewalk=self.layers['sidewalk'];cross=self.layers['crossings']
        known_cross={'08','A8','18','B8','09','A9'}
        self.sidewalk_diagnostic=dict(records=len(sidewalk),distinct_licodes=int(sidewalk.licode.nunique()),rows_in_known_crossing_codes=int(sidewalk.licode.isin(known_cross).sum()),exact_crossing_key_overlap=int(sidewalk.keyid.astype(str).isin(set(cross.keyid.astype(str))).sum()),sidewalk_filter_verified=False)
        display(pd.DataFrame([self.sidewalk_diagnostic]))
        print('未取得本機LICODE中標線型人行道的完整可靠篩選規則；此檔不得全當人行道，相關正式候選暫Blocked。')
        return self.layers

    def shared_boundaries(self):
        if hasattr(self,'shared_edges'):return self.shared_edges
        pair=self.btree.query(self.vgeom,predicate='intersects');pair=pair[:,pair[0]<pair[1]]
        edges=[[] for _ in range(456)]
        for i,j in zip(*pair):
            g=self.vgeom[i].boundary.intersection(self.vgeom[j].boundary)
            if g.length>0:edges[i].append(g);edges[j].append(g)
        self.shared_edges=[s.union_all(x) for x in edges]
        return self.shared_edges

    def line_diagnostics(self):
        roads=self.layers['osm'];road_ok=roads['_geometry_eligible']&roads['_motor_candidate']&roads.geometry.intersects(self.study)
        selected=roads.loc[road_ok].copy();geom=np.asarray(selected.geometry.array,dtype=object);groups=selected['_research_road_group'].to_numpy()
        tree=s.STRtree(geom);q=tree.query(self.vgeom,predicate='intersects');by=[[] for _ in range(456)]
        for i,j in zip(*q):by[i].append(int(j))
        edges=self.shared_boundaries();rows=[]
        def line_union(values):
            # Touch-only polygon intersections can include Point parts. Exclude
            # zero-length parts explicitly; do not repair or snap source lines.
            lines=[]
            def collect(g):
                if g.is_empty:return
                if g.geom_type in ['LineString','LinearRing']:lines.append(g)
                elif hasattr(g,'geoms'):
                    for part in g.geoms:collect(part)
            for g in values:collect(g)
            return s.union_all(lines)
        for i,v in enumerate(self.vgeom):
            ids=by[i];clips=s.intersection(geom[ids],v) if ids else []
            union=line_union(clips);shared=union.intersection(edges[i]);effective=union.difference(edges[i]) if not union.is_empty else union
            lengths={}
            for group in ['major','secondary','local','service']:
                local=[g for g,j in zip(clips,ids) if groups[j]==group]
                lu=line_union(local);lengths[group]=(lu.difference(edges[i]).length if not lu.is_empty else 0)/1000
            total=effective.length/1000
            rows.append(dict(village_id=self.ids[i],observed_road_length_km=total,observed_road_density=total/(self.varea[i]/1e6),major_road_ratio=lengths['major']/total if total>0 else np.nan,minor_road_ratio=lengths['local']/total if total>0 else np.nan,road_boundary_unallocated_km=shared.length/1000,source_line_records_intersecting=len(ids)))
        result=pd.DataFrame(rows);global_unique=s.union_all(geom).intersection(self.city)
        global_shared=global_unique.intersection(s.union_all(edges))
        self.road_summary=dict(eligible_regional_source_lines=len(selected),represented_unique_city_length_km=global_unique.length/1000,city_shared_boundary_length_km=global_shared.length/1000,sum_village_effective_length_km=float(result.observed_road_length_km.sum()),sum_village_shared_length_km=float(result.road_boundary_unallocated_km.sum()),meaning='OSM線表示聯集長度；保留平行雙向表示，不等於真實中心線／VKT')
        display(pd.DataFrame([self.road_summary]));self.road_features=result
        # Endpoints only; never count every 2D line crossing as a planar intersection.
        planar=selected[(selected.layer.eq(0))&selected.bridge.eq('F')&selected.tunnel.eq('F')]
        endpoint=Counter()
        for g in planar.geometry:
            endpoint[tuple(g.coords[0][:2])]+=1;endpoint[tuple(g.coords[-1][:2])]+=1
        pts=[s.Point(xy) for xy,degree in endpoint.items() if degree>=3]
        self.endpoint_candidates=gpd.GeoDataFrame({'candidate_degree':[endpoint[(p.x,p.y)] for p in pts]},geometry=pts,crs=3826)
        print('同層、非橋隧、至少3線端連接之候選位置',len(pts),'；缺OSM節點／轉向與分隔車道合併，不推薦直接作intersection_density。')
        return result

    def point_diagnostics(self,family):
        source=self.layers[family];g=source[source['_geometry_eligible']].copy()
        geom=np.asarray(g.geometry.array,dtype=object);q=self.btree.query(geom,predicate='covered_by');within=self.btree.query(geom,predicate='within')
        c=[[] for _ in range(len(g))];w=[[] for _ in range(len(g))]
        for i,j in zip(*q):c[i].append(int(j))
        for i,j in zip(*within):w[i].append(int(j))
        assigned=np.array([cs[0] if len(cs)==len(ws)==1 and cs==ws else -1 for cs,ws in zip(c,w)])
        status=np.array(['unique' if a>=0 else 'outside' if not cs else 'boundary_or_multiple' for a,cs in zip(assigned,c)])
        counts=np.bincount(assigned[assigned>=0],minlength=456)
        coords=g.geometry.to_wkb();same_coordinate=coords.duplicated(keep=False)
        coordinate_counts=np.zeros(456,int)
        for i in range(456):coordinate_counts[i]=coords[assigned==i].nunique()
        frame=pd.DataFrame({'village_id':self.ids,'observed_'+family+'_record_count':counts,'observed_'+family+'_density':counts/(self.varea/1e6),'observed_'+family+'_unique_locations':coordinate_counts})
        summary=dict(family=family,valid_points=len(g),unique_assigned=int((assigned>=0).sum()),boundary_multiple=int((status=='boundary_or_multiple').sum()),outside_fixed_city=int((status=='outside').sum()),unique_assignment_rate_all_source=float((assigned>=0).sum()/len(source)),source_coordinate_duplicate_rows=int(same_coordinate.sum()),zero_observed_villages=int((counts==0).sum()),interpretation='零為本檔未觀測，非證明真實無設施；未指派最近里')
        if family=='signals':
            summary['name_col']='地點';summary['source_id_unique']=bool(g['流水號'].is_unique)
            self.signal_points=g
            show('號誌未能唯一歸里之有效座標點（保留原位置，不自動修正）',g.loc[assigned<0,['流水號','地點','行政區','WGS經度座標','WGS緯度座標']])
            show('不同名稱但相同位置的完整紀錄',g.loc[same_coordinate,['流水號','地點','行政區','WGS經度座標','WGS緯度座標']])
        else:
            station=g['出入口名稱'].str.extract(r'^(.*?站)',expand=False)
            summary['station_code_present']=False;summary['observed_station_name_labels']=int(station.nunique());summary['station_name_unparsed']=int(station.isna().sum())
            counts_station=[station[assigned==i].nunique() for i in range(456)]
            frame['observed_mrt_station_name_count']=counts_station;frame['has_observed_mrt_entrance']=counts>0
            g['_station_name_diagnostic']=station
            summary['crossborder_points_within800m']=int(((assigned<0)&g.geometry.intersects(self.city.buffer(800)).to_numpy()).sum())
            self.mrt_assigned=assigned;self.mrt_points=g
        show(f'{family}點配對摘要',pd.DataFrame([summary]))
        self.summaries[family+'_assignment']=summary
        return frame

    def polygon_diagnostics(self,family):
        g=self.layers[family];valid=g[g['_geometry_eligible']].copy();geom=np.asarray(valid.geometry.array,dtype=object)
        tree=s.STRtree(geom);q=tree.query(self.vgeom,predicate='intersects');by=[[] for _ in range(456)]
        for i,j in zip(*q):by[i].append(int(j))
        areas=[];counts=[];overlaps=[]
        for i,v in enumerate(self.vgeom):
            ids=by[i];clips=s.intersection(geom[ids],v) if ids else []
            positive=[p for p in clips if p.area>0];union=s.union_all(positive)
            areas.append(union.area);counts.append(len(positive));overlaps.append(sum(p.area for p in positive)-union.area)
        name='observed_crossing_marking_area_ratio' if family=='crossings' else 'unclassified_marking_file_area_ratio_NOT_sidewalk'
        f=pd.DataFrame({'village_id':self.ids,name:np.asarray(areas)/self.varea,family+'_intersecting_polygon_records':counts,family+'_duplicate_overlap_area_m2':overlaps})
        summary=dict(family=family,valid_polygons=len(valid),positive_area_villages=int((np.asarray(areas)>0).sum()),zero_observed_villages=int((np.asarray(areas)==0).sum()),sum_polygon_intersections=int(sum(counts)),sum_village_unique_area_m2=float(sum(areas)),pairwise_overlap_removed_m2=float(sum(overlaps)),meaning='幾何聯集覆蓋，跨里圖形可在兩里各有部分；非設施完整個數，Polygon周長不當設施長度')
        display(pd.DataFrame([summary]));self.summaries[family+'_area']=summary
        return f

    def width_by_village(self):
        g=self.layers['road_width'];g=g[g['_geometry_eligible']&g['_annotation_width_m'].gt(0)].copy();geom=np.asarray(g.geometry.array,dtype=object);tree=s.STRtree(geom)
        q=tree.query(self.vgeom,predicate='intersects');by=[[] for _ in range(456)]
        for i,j in zip(*q):by[i].append(int(j))
        values=g['_annotation_width_m'].to_numpy();rows=[]
        for i,v in enumerate(self.vgeom):
            ids=[j for j in by[i] if geom[j].intersection(v).length>0]
            rows.append(dict(village_id=self.ids[i],observed_plan_width_annotation_median_m=float(np.median(values[ids])) if ids else np.nan,width_annotation_records=len(ids),length_weighted_mean_road_width=np.nan))
        return pd.DataFrame(rows)

    def mrt_accessibility(self):
        g=self.mrt_points;allpoints=np.asarray(g.geometry.array,dtype=object);inside=self.mrt_assigned>=0;rows=[];effect=[]
        for radius in [300,500,800]:
            buf=s.buffer(allpoints,radius,quad_segs=16);union=s.union_all(buf)
            inside_union=s.union_all(buf[inside])
            areas=s.area(s.intersection(self.vgeom,union));ratio=areas/self.varea
            assert np.all(ratio>=0) and np.all(ratio<=1+1e-9)
            rows.append(pd.DataFrame({'village_id':self.ids,'radius_m':radius,'observed_mrt_buffer_coverage_ratio':ratio}))
            effect.append(dict(radius_m=radius,city_coverage_km2=union.intersection(self.city).area/1e6,extra_coverage_from_crossborder_km2=union.difference(inside_union).intersection(self.city).area/1e6,raw_sum_buffer_area_km2=float(s.area(buf).sum()/1e6),union_total_area_km2=union.area/1e6,meaning='先聯集，保留合理跨界出入口；直線範圍非步行時間或路網可及性'))
        display(pd.DataFrame(effect));self.mrt_buffer_summary=effect;self.mrt_buffers=pd.concat(rows,ignore_index=True)
        return self.mrt_buffers

    def b3_diagnostics(self):
        if not hasattr(self,'layers'):self.infrastructure_prepare()
        road=self.line_diagnostics();signals=self.point_diagnostics('signals');mrt=self.point_diagnostics('mrt')
        cross=self.polygon_diagnostics('crossings');markings=self.polygon_diagnostics('sidewalk');width=self.width_by_village();access=self.mrt_accessibility()
        f=self.base.copy()
        for other in [road,signals,mrt,cross,markings,width]:f=f.merge(other,on='village_id',how='left',validate='one_to_one')
        f['observed_signals_per_road_km']=f.observed_signals_record_count/f.observed_road_length_km.replace(0,np.nan)
        for col in ['intersection_density','crosswalk_count','crosswalk_density','crosswalk_length_density','marked_sidewalk_length','marked_sidewalk_density','marked_sidewalk_area_ratio']:f[col]=np.nan
        assert len(f)==456 and f.village_id.is_unique
        show('全部456里B3診斷表；觀測量及Blocked特徵分開，非正式B3',f,block=12)
        cols=['observed_road_density','major_road_ratio','minor_road_ratio','observed_signals_density','observed_crossing_marking_area_ratio','observed_plan_width_annotation_median_m','observed_mrt_density','observed_signals_per_road_km']
        stats=[]
        for c in cols:
            d=f[c];stats.append(dict(feature=c,N=int(d.notna().sum()),unknown=int(d.isna().sum()),observed_zero=int(d.eq(0).sum()),**d.describe(percentiles=[.25,.5,.75]).to_dict()))
            show(c+'最高／最低各3里',pd.concat([f.nsmallest(3,c),f.nlargest(3,c)])[['village_id','district_name','village_name',c]])
        show('候選觀測量的缺失／零／分布',pd.DataFrame(stats))
        district=f.groupby('district_name').agg(villages=('village_id','size'),area_km2=('area_km2','sum'),road_km=('observed_road_length_km','sum'),signals=('observed_signals_record_count','sum'),entrances=('observed_mrt_record_count','sum'))
        district['road_density']=district.road_km/district.area_km2;district['observed_signal_density']=district.signals/district.area_km2;district['observed_entrance_density']=district.entrances/district.area_km2
        display(district)
        self.b3=f;self.b3_stats=stats;self.district_b3=district
        return f

    def feature_definitions(self):
        """Each record specifies source, unit, numerator/denominator and safeguards."""
        rows=[]
        def add(names,source,fields,unit,numerator,denominator,measurement,status,reason):
            for name in names.split('|'):
                rows.append(dict(feature=name,source='; '.join(r['path'] for r in self.family_items(source)),raw_fields=fields,observation_unit=unit,numerator=numerator,denominator=denominator,measurement_unit=measurement,working_CRS='EPSG:3826',time=self.config['metadata'][source]['period'],duplicate_rule='保留來源鍵；線／面採同類幾何聯集；點另報ID及同座標重複，不擅自合併實體',missing_rule='缺欄／無效／語義未證為NA；觀測0不表示現實不存在；零分母NA',boundary_rule='原456里；線扣共享界段另報；面正面積交集聯集；點唯一within/covered_by，邊界多配待審，無最近點強派',coverage='僅本機快照已觀測範圍；非普查完整性認證',status=status,use='事故分群後外部環境比較；不入Dataset A；非交通暴露',limitation=reason))
        ready='Ready with explicit assumptions';partial='Partially ready';blocked='Blocked'
        add('road_length_km|road_density','osm','osm_id,fclass,geometry','道路線表示','里內機動車候選線聯集長度，扣原里共享界段','1／原里面積km²（density）','km／km per km²',ready,'分車道平行線保留為表示方式，不等於實體中心線或VKT；一份2025快照套用兩年')
        add('major_road_ratio|minor_road_ratio','osm','fclass,geometry','分類道路線表示','研究映射major／local類線聯集長度（secondary另列分組，minor僅local）','同規則機動車候選路網聯集長度','0–1',ready,'分類為研究操作映射，非官方道路等級；跨類重合需另報，不能解讀為車流比例')
        add('intersection_density','osm','layer,bridge,tunnel,geometry','候選端點','需完整節點與平面連通拓樸之實體路口數','原里面積km²','個/km²',blocked,'僅可報layer0非橋隧端點degree>=3診斷；缺完整節點／轉向與高架連接資訊，不產出正式路口密度')
        add('signalized_intersection_count|signalized_intersection_density|signalized_intersections_per_road_km','signals','流水號,地點,行政區,WGS經度座標,WGS緯度座標','路口位置紀錄','唯一歸里已觀測路口位置紀錄數；同座標另報替代數','1／原里面積km²／已觀測道路km','筆／筆/km²／筆/km',ready,'不等於燈頭或設備數；ID、同位置重複與未認證快照日期需保留；路網跨來源時間不同')
        add('crosswalk_count|crosswalk_density|crosswalk_length_density','crossings','keyid,licode,geometry','標線面構件','需先確認完整設施單位／可用長度欄','1／原里面積km²','設施數／個/km²／m/km²',blocked,'一筆Polygon不必是一處完整行穿線；不以周長當穿越長度')
        add('crosswalk_area_ratio','crossings','licode,keyid,geometry','六個明示行穿線圖層面構件','里內有效標線面交集聯集面積','原里面積m²','0–1',partial,'可作已觀測行穿標線覆蓋；非完整設施數；2024快照不證明2025存量；日期占位與構件語義限制')
        add('length_weighted_mean_road_width|narrow_road_length_ratio|wide_road_length_ratio','road_width','road_width,angle,geometry','計畫路寬尺寸線','需縱向里內道路長度作權重／具依據門檻','有效縱向道路長度','m／0–1',blocked,'現有線是寬度標註，並無合適道路縱向權重；不任意設定窄寬門檻')
        add('median_road_width','road_width','road_width,geometry','計畫路寬標註','改名observed_plan_width_annotation_median_m：里內相交標註寬度中位數','有效相交標註筆數之中位數算子','m',partial,'樣本為計畫／地籍參考尺寸線，非里內道路長度代表樣本或實測車行寬度；跨界標註可同時入兩里')
        add('marked_sidewalk_length|marked_sidewalk_density|marked_sidewalk_area_ratio','sidewalk','licode,walkerroad,walkerstat,geometry','尚未識別的人行道子集','需正式類別規則及量測單位後才計算','1／原里面積km²／m²','m／m/km²／0–1',blocked,'2026混合標線檔含行穿線，未證人行道篩選碼；整檔面積診斷不得命名人行道')
        add('mrt_entrance_count|mrt_entrance_density','mrt','項次,出入口名稱,出入口編號,經度,緯度','出入口位置紀錄','唯一歸里有效出入口數，站名標籤數另列','1／原里面積km²','筆／筆/km²',ready,'一站多入口不能當多站；無正式車站碼及歷史設置日期，2026快照非研究年實際活動量')
        add('mrt_accessibility_ratio','mrt','經度,緯度,geometry','入口直線緩衝區','全來源入口300／500／800m buffer先union再與里相交面積（含跨市點）','原里面積m²','0–1',ready,'三種半徑均候選未定稿；非步行網路距離、流量或通勤可及性；2026時間錯配')
        result=pd.DataFrame(rows);show('完整B3候選變數操作定義與可用性（非最終選模）',result,block=4);self.feature_table=result
        return result

    def readiness(self):
        rows=[('事故標準化／跨年度','Ready with explicit assumptions','45,130候選；缺官方事件ID，依來源hash+列鍵；照明跨年差異、R20／死亡窗口仍保留'),('事故歸里','Ready with explicit assumptions','固定456原幾何、工作4326；主44,212、幾何敏感45,083維持；來源吻合不認證位置'),('固定行政里基礎','Ready with explicit assumptions','456原幾何面積；歷史年版只診斷，不取代固定界'),('Dataset A','Ready with explicit assumptions','八項基本組成與加入多人受傷的九項規格待Chapter2處理；缺值有效分母、低樣本及零事件NA'),('Dataset B1','Ready','承接Unit1.6；既有crosswalk及12/24月分子分母政策，糖廍里同規則納入，固定地理與設籍非暴露限制保留'),('Dataset B2','Partially ready','沿Unit1.6方案B；未覆蓋／未知不補零，105修復一致／38待審，不拖延核心'),('Dataset C','Ready with explicit assumptions','事故負擔非暴露校正率；死亡原值分列不冒稱全部官方24h認證'),('跨年度驗證架構','Ready with explicit assumptions','保留year與同里依賴；2024擬合／2025指派，B2/B3固定快照非年度獨立觀測'),('B3 OSM','Ready with explicit assumptions','已觀測道路表示密度與分類；路口密度Blocked'),('B3 signals','Ready with explicit assumptions','已觀測路口位置；時間未知、重複診斷保留'),('B3 crossings','Partially ready','僅已觀測幾何面積覆蓋；完整設施數與長度Blocked'),('B3 road width','Partially ready','僅計畫寬度標註樣本中位數；縱向加權及窄寬比Blocked'),('B3 sidewalk','Blocked','混合標線檔未證人行道子集、2026時間錯配'),('B3 MRT','Ready with explicit assumptions','2026出入口快照、含跨市buffer；非歷史或流量')]
        table=pd.DataFrame(rows,columns=['component','status','conditions']);show('Dataset Readiness；技術準備不等於正式資料已產出',table);self.readiness_table=table;return table

    def policy_review(self):
        points=self.cache.get('accident_points_aligned',{});national=self.cache.get('national_accidents_aligned',{})
        changes=sum(r['village_or_status_changed'] for r in getattr(self,'assignment_changes',[]))
        rows=[('固定456里','維持固定456','年版幾何與歸里診斷；變更事件'+str(changes),'維持；歷史界作敏感度候選，非自動替換','456里／45,130事件','低；歷史替代需重新人口面積及跨年可比性審查','主要固定單元一致；歷史比較影響列明'),('歷史敏感度','待新增證據','完整逐里IoU及兩年事件變更清單','保留一次歷史界敏感度候選；幾何差不等於法定邊界變更','456×3比較','中','反映空間歸屬穩健性，不變更糖廍決策'),('事故主／敏感規格','44,212／45,083','補充來源位置相同可能同源；未證869區衝突何者正確','維持原保守與幾何敏感規格；不自動採替代位置','869區名＋2額外地址＋44界外＋3缺座標','低','保留涵蓋與可信度取捨'),('座標修正／補值','不自行修改','斑點圖候選'+str(len(points.get('imputation',[])))+'；全國候選'+str(len(national.get('imputation',[]))),'僅提交配對等級、原值、來源列及候選；未套用','最多3筆既有缺座標，另有差異位置','中；須個案地址及地圖審查','有可能改變歸里／樣本，先學生決定'),('死亡欄時間定義','兩欄分列，語義待證','官方A1/A2定義＋高可信事件總量對應；個別R20未獲等義欄','保留原欄及來源差異，不直接改寫24h證據等級','R20為6／4筆；全部傷亡欄','低','限制C死亡解釋，不阻礙其餘A/B1'),('代碼對照','Unit1.1碼表','中文全國欄逐碼實際對應；跨年照明欄需分開','將實證對照作補充，照明不直接跨年共用，不覆寫既有表','已配對事件、四類欄位','低','支持代碼一致性檢查，未出現值不推定已驗證'),('B2','補充分析','本次未重跑，保留Unit1.6證據','維持Partially ready','456里','既有中高','不拖延D原版B1核心'),('B3角色','新候選','逐里試算及來源時間／單位檢查','道路密度、號誌觀測密度、MRT緩衝先列少量外部候選；B3整體不無條件升格','456里，各來源分項','中','只在事故分群後比較；不能當交通暴露或因果解釋')]
        t=pd.DataFrame(rows,columns=['decision','original_policy','new_evidence','proposal_not_adopted','affected','cost','impact']);t['student_review']='待學生／DA／PM審查；本單元不自動批准';show('既有政策逐項再評估',t,block=4);self.policy_table=t;return t

    def plots(self,kind):
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        font=Path('C:/Windows/Fonts/msjh.ttc')
        if font.exists():font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
        plt.rcParams['axes.unicode_minus']=False
        def finish(fig,name):
            fig.suptitle('Unit 1.7 資料驗證／診斷用途；非正式研究結果',fontsize=13);fig.tight_layout(rect=[0,0,1,.96]);fig.savefig(self.temp/name,dpi=140);display(fig);plt.close(fig)
        if kind=='accidents':
            fig,ax=plt.subplots(1,3,figsize=(18,6));d=self.boundary_differences.query("comparison=='2024_2025'").set_index('village_id')
            g=self.boundary.copy();g['symdiff_m2']=d.reindex(self.ids).symdiff_m2.to_numpy();g.plot(column='symdiff_m2',legend=True,ax=ax[0],cmap='OrRd',legend_kwds={'label':'對稱差面積 m²'});ax[0].set_title('兩個官方年版幾何差（非行政變更認證）')
            self.boundary.boundary.plot(ax=ax[1],color='grey',linewidth=.25)
            for y,f in self.candidates().items():
                a=self.audits[(y,'fixed')];q=a[a.district_conflict];ax[1].scatter(q.x,q.y,s=4,label=str(y),alpha=.6)
            ax[1].legend();ax[1].set_title('869筆原行政區標籤衝突')
            for source in ['accident_points','national_accidents']:
                z=self.cache[source+'_aligned']['details'];v=z.loc[z.difference_m.gt(0),'difference_m'];ax[2].hist(np.log10(v),bins=35,alpha=.5,label=source)
            ax[2].legend();ax[2].set_xlabel('log10(已配對正座標差 m)；零差另見表');ax[2].set_title('不以座標作鍵的跨來源位置差')
            for a in ax[:2]:a.set_axis_off()
            finish(fig,'accident_boundary_diagnostics.png')
        else:
            fig,axes=plt.subplots(2,3,figsize=(17,12));ax=axes.ravel()
            for a in ax:self.boundary.boundary.plot(ax=a,color='#888888',linewidth=.2);a.set_axis_off()
            road=self.layers['osm'];road[road._geometry_eligible].plot(column='_research_road_group',ax=ax[0],linewidth=.3,legend=True,legend_kwds={'fontsize':6},rasterized=True);ax[0].set_title('OSM道路分類／研究區外圍2km')
            self.signal_points.plot(ax=ax[1],markersize=2,color='firebrick');ax[1].set_title('已觀測號誌路口位置')
            self.layers['crossings'].geometry.representative_point().plot(ax=ax[2],color='navy',markersize=.5,rasterized=True);ax[2].set_title('行穿面構件位置（僅顯示點；仍按面積計量）')
            self.layers['road_width'].plot(ax=ax[3],linewidth=.4,color='darkgreen',rasterized=True);ax[3].set_title('計畫路寬標註尺寸線（非路網）')
            self.layers['sidewalk'].geometry.representative_point().plot(ax=ax[4],color='darkorange',markersize=.5,rasterized=True);ax[4].set_title('2026混合標線面位置；不得解讀為人行道')
            union=s.union_all(s.buffer(np.asarray(self.mrt_points.geometry.array,dtype=object),500));gpd.GeoSeries([union],crs=3826).plot(ax=ax[5],color='lightblue');self.mrt_points.plot(ax=ax[5],color='blue',markersize=3);ax[5].set_title('全部捷運入口及500m候選直線buffer')
            # An extreme source coordinate must not make the entire city map
            # invisible. Full outlier coordinates remain in the tables above.
            xmin,ymin,xmax,ymax=self.study.bounds
            for a in ax:a.set_xlim(xmin,xmax);a.set_ylim(ymin,ymax)
            ax[1].set_title('已觀測號誌位置（圖限城市外圍；界外另表）')
            finish(fig,'infrastructure_source_maps.png')
            fig,ax=plt.subplots(1,3,figsize=(17,5))
            for a,c in zip(ax,['observed_road_density','observed_signals_density','observed_mrt_density']):
                g=self.boundary.copy();g[c]=self.b3[c].to_numpy();g.plot(column=c,cmap='viridis',legend=True,ax=a);a.set_axis_off();a.set_title(c+'\n已觀測值；零非不存在')
            finish(fig,'b3_observed_feature_maps.png')
            fig,ax=plt.subplots(1,3,figsize=(17,5));w=self.layers['road_width'];ax[0].hist(w['_annotation_width_m'].dropna(),bins=45);ax[0].set_xlabel('計畫路寬標註m');ax[0].set_title('標註樣本寬度分布')
            for radius,g in self.mrt_buffers.groupby('radius_m'):ax[1].hist(g.observed_mrt_buffer_coverage_ratio,bins=20,alpha=.4,label=str(radius)+'m')
            ax[1].legend();ax[1].set_title('456里候選入口buffer覆蓋率')
            ax[2].set_axis_off();table=ax[2].table(cellText=[['OSM','2025-01-01 明示快照'],['號誌','檔名2023；實際觀測日未認證'],['行穿線','2024封裝；不完整代表2025'],['路寬','2023資源；非兩年實測'],['混合標線','2026；歷史僅現存資格'],['捷運','2026；無逐入口設置歷史']],colLabels=['來源','時間適用性'],loc='center',cellLoc='left',colWidths=[.25,.75]);table.auto_set_font_size(False);table.set_fontsize(9);table.scale(1,1.7);ax[2].set_title('全數非雙年獨立完整設施存量')
            finish(fig,'infrastructure_quality_and_time.png')

    def finish(self,kind):
        assert self.boundary.geometry.to_wkb().equals(self.original_wkb),'Original geometry changed in memory'
        for relative in self.config['existing_bindings']:self.file(relative)
        for item in self.inventory:self.file(item['path'])
        summary={'unit':'1.7','kind':kind,'formal_dataset_exports':0,'raw_files_unchanged':True,'input_hashes':{r['path']:r['sha256'] for r in self.inventory},'summaries':self.summaries}
        for a in ['assignment_changes','history_info','casualty_summary','code_summary','handling_summary','mrt_buffer_summary','road_summary','infrastructure_quality','width_diagnostic','sidewalk_diagnostic','time_diagnostics']:
            if hasattr(self,a):summary[a]=getattr(self,a)
        for a in ['assignment_summary','boundary_differences','b3','feature_table','readiness_table','policy_table','r20']:
            if hasattr(self,a):summary[a]=getattr(self,a).to_dict('records')
        for source in ['accident_points','national_accidents']:
            if source+'_aligned' in self.cache:
                a=self.cache[source+'_aligned'];summary[source]={k:a[k].to_dict('records') for k in ['summary','imputation','anomalies']}
                summary[source]['coordinate_summary']=a['details'].groupby(['year','match_grade','coordinate_class']).size().rename('N').reset_index().to_dict('records')
                summary[source]['difference_quantiles']=a['details'].groupby('year').difference_m.quantile([0,.5,.95,.99,1]).to_dict().__str__()
        # Regenerated diagnostic log only: never an input to a formal notebook.
        (self.temp/(kind+'_summary.json')).write_text(json.dumps(summary,ensure_ascii=True,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
        display(pd.DataFrame([{'formal_dataset_exports':0,'protected_inputs_verified':len(self.config['existing_bindings']),'new_raw_files_verified':len(self.inventory),'human_DA_PM_review':'尚待學生驗收／審查；Codex本地執行'}]))
