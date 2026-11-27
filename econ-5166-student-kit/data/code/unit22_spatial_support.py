"""Unit 2.2: version-bound GIS processing and independent saved-file checks.

Only the standardized Unit 2.1 CSV supplies accident observations. No raw accident
reader, geocoder, geometry repair, nearest assignment, or model is implemented.
"""
from pathlib import Path, PurePosixPath
import hashlib,json,zipfile,re
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely as s
from pyproj import Transformer
from IPython.display import display,Markdown

CSV_RULES={'encoding':'utf-8-sig','missing_sentinel':'__MISSING__','line_terminator':'LF','keep_default_na':False,'boolean_values':['True','False'],'candidate_id_arrays':'JSON sorted string arrays; []=queried with no hits; NA=not queried'}
STATES={
 'missing_coordinates':'1 原座標缺失，不建立Point',
 'invalid_coordinates':'2 非缺失但不可解析／非有限／候選經緯度越界或投影失敗',
 'outside_or_hole':'3 有效Point的within及covered_by均無候選',
 'boundary_nonunique':'4 共同邊界／頂點或單一邊界；不是唯一內部',
 'multiple_geometry':'5 多個內部或其他多重幾何候選，不任選第一筆',
 'predicate_mismatch':'6 within非covered_by子集或其他不一致',
 'original_district_unknown':'7 幾何唯一但來源區名無法確認',
 'district_conflict':'8 幾何唯一但來源區名與空間區名衝突',
 'address_conflict':'9 幾何唯一且來源區名一致，但可判讀地址與空間區名衝突',
 'conservative_success':'10 唯一內部、原區名明確一致、地址沒有明確空間衝突'}
GEOMETRY_STATES=['missing_coordinates','invalid_coordinates','outside_or_hole','shared_vertex','shared_boundary','single_boundary','multiple_interior','other_multiple','predicate_mismatch','unique_interior']
FEATURES=['morning_peak','evening_peak','late_night','weekend','intersection','rear_end','side_collision','pedestrian_collision','multi_injury']

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()

def show(title,frame,block=18):
 display(Markdown('**'+title+'**'))
 if not len(frame):print('無符合紀錄')
 for i in range(0,len(frame),block):display(frame.iloc[i:i+block])

def load_csv(path,contract):
 f=pd.read_csv(path,encoding=contract['csv']['encoding'],dtype='string',keep_default_na=False,na_values=[contract['csv']['missing_sentinel']])
 assert list(f)==[r['name'] for r in contract['columns']]
 for field in contract['columns']:
  col=field['name'];dtype=field['dtype'];v=f[col]
  if dtype=='boolean':
   assert v.dropna().isin(['True','False']).all(),col
   f[col]=v.map({'True':True,'False':False}).astype('boolean')
  elif dtype=='Int64':f[col]=pd.to_numeric(v,errors='raise').astype('Int64')
  elif dtype=='Float64':f[col]=v.map(lambda x:pd.NA if pd.isna(x) else float(x)).astype('Float64')
  else:assert dtype=='string'
 return f

def same_optional(a,b):
 """Both NA = same unassigned state; one NA differs; two IDs compare literally."""
 return ((a.isna()&b.isna())|a.eq(b).fillna(False)).astype('boolean')

def kind_of_change(village_changed,eligibility_changed):
 return pd.Series(np.select([village_changed&eligibility_changed,village_changed,eligibility_changed],['village_and_eligibility','village_only','eligibility_only'],default='unchanged'),index=village_changed.index,dtype='string')

def typed_frame(data,definitions):
 size=max(len(v) for v in data.values() if not pd.api.types.is_scalar(v))
 return pd.DataFrame({name:pd.Series([values]*size if pd.api.types.is_scalar(values) else values).reset_index(drop=True).astype(definitions[name]['dtype']) for name,values in data.items()})

class Context:
 def __init__(self,root,bindings):
  self.root=Path(root).resolve();self.bindings=bindings.copy();self.temp=self.root/'data/temp/unit22_validation';self.temp.mkdir(parents=True,exist_ok=True)
  self.summary={};self.base_defs={};self.assignment_defs={};self.outputs={}
  for rel in bindings:self.file(rel)
  self.upstream_contract=json.loads(self.file('data/processed/taipei_crashes_2024_2025_standardized_schema.json').read_text(encoding='utf-8'))
  assert self.upstream_contract['csv']['missing_sentinel']=='__MISSING__','Use actual bound schema, not prompt typography'
  self.accidents=load_csv(self.file('data/processed/taipei_crashes_2024_2025_standardized.csv'),self.upstream_contract)
  a=self.accidents;assert a.shape==(45130,191) and a.record_id.is_unique and a.record_id.notna().all()
  assert a.groupby('source_year').size().to_dict()=={2024:22368,2025:22762}
  self.config17=json.loads(self.file('data/code/unit17_validation_config.json').read_text(encoding='utf-8'))
  self.crosswalk=pd.read_csv(self.file('data/processed/village_crosswalk.csv'),encoding='utf-8-sig',dtype='string',keep_default_na=False)
  assert len(self.crosswalk)==456 and self.crosswalk.village_id.is_unique and self.crosswalk.population_code.is_unique
  show('固定正式輸入身分',pd.DataFrame([{'path':p,'sha256':h,'bytes':(self.root/p).stat().st_size} for p,h in bindings.items()]))
  print('事故正式輸入',a.shape,'schema明示dtype；原空字串與__MISSING__分開，不讀原始事故CSV。')

 def file(self,relative):
  rel=Path(relative);assert not rel.is_absolute() and '..' not in rel.parts
  p=(self.root/rel).resolve();assert p.is_relative_to(self.root/'data') and p.is_file(),relative
  assert relative in self.bindings and sha(p)==self.bindings[relative],('Input changed; stop',relative)
  return p

 @staticmethod
 def define(definitions,name,dtype,definition,unit='not applicable',source='',missing='NA不補0；原字串空白保留'):
  record=dict(name=name,dtype=dtype,definition=definition,unit=unit,source=source,missing_rule=missing)
  if name in definitions:assert definitions[name]==record,name
  definitions[name]=record

 def build_base(self):
  g=gpd.read_file(self.file('data/raw/G97_A_CAVLGE_P.shp'),encoding='utf-8',engine='pyogrio').reset_index(drop=True)
  assert len(g)==456 and g.CPTVID.astype('string').str.fullmatch(r'\d{10}').all() and g.CPTVID.is_unique
  assert g.TNAME.nunique()==12 and g.crs.to_epsg()==3826
  assert g.geometry.notna().all() and (~g.geometry.is_empty).all() and g.geometry.is_valid.all() and g.area.gt(0).all()
  self.fixed=g;self.fixed_wkb=g.geometry.to_wkb().copy();geom=np.asarray(g.geometry.array,dtype=object)
  cw=self.crosswalk.set_index('village_id').reindex(g.CPTVID.astype(str).to_numpy()).reset_index()
  assert cw.population_code.notna().all() and cw.boundary_code.eq(g.CPTVID.to_numpy()).all()
  assert cw.district_name.eq(g.TNAME.to_numpy()).all() and cw.boundary_village_name.eq(g.VNAME.to_numpy()).all()
  self.ids=g.CPTVID.astype(str).to_numpy();self.districts=g.TNAME.astype(str).to_numpy();self.city=s.union_all(geom)
  tree=s.STRtree(geom);pairs=tree.query(geom,predicate='intersects');pairs=pairs[:,pairs[0]<pairs[1]]
  count=np.zeros(456,int);overlap=[[] for _ in range(456)];positive=[]
  for i,j in zip(*pairs):
   intersection=geom[i].intersection(geom[j])
   if intersection.area>0:
    positive.append(dict(village_id_a=self.ids[i],village_id_b=self.ids[j],intersection_m2=intersection.area));count[i]+=1;count[j]+=1;overlap[i].append(intersection);overlap[j].append(intersection)
  holes=np.array([sum(len(p.interiors) for p in ([x] if x.geom_type=='Polygon' else x.geoms)) for x in geom])
  union_holes=sum(len(poly.interiors) for poly in s.get_parts(self.city))
  # Unit1.2's 335 refers to holes of the CITY UNION, not the sum of the
  # original individual polygons' interior rings (which is 1).
  assert len(positive)==157 and union_holes==335 and holes.sum()==1,'Unexpected geometry change; stop rather than repair'
  d={}
  def add(name,v,dtype,definition,unit='not applicable',source='固定SHP／既有crosswalk'):
   self.define(self.base_defs,name,dtype,definition,unit,source);d[name]=v
  for name in ['village_id','boundary_code','population_code','district_name','boundary_village_name','population_village_name','standard_village_name','match_method','verification_status']:
   meanings={'village_id':'共同研究10碼ID，原固定CPTVID；不得用歷史／人口碼取代','boundary_code':'固定界原10碼CPTVID','population_code':'既有crosswalk之11碼人口代碼','district_name':'固定里界／crosswalk確認的行政區名','boundary_village_name':'固定界原里名，包含糖蔀里原字形','population_village_name':'人口原里名，包含糖?里原字形','standard_village_name':'正式分析標準里名，糖廍里正常納入','match_method':'既有crosswalk方法原值，未重寫','verification_status':'既有證據狀態，provisional_match不限制糖廍分析資格'}
   add(name,cw[name].to_numpy(),'string',meanings[name])
  add('district_code_source',g.CPTID.astype(str),'string','原固定SHP七碼CPTID；不是原事故區序數字碼，未截取或推定順序')
  assert pd.DataFrame({'code':g.CPTID,'name':g.TNAME}).drop_duplicates().shape[0]==12
  add('village_area_m2',g.area,'Float64','原固定geometry在EPSG3826的面積；主固定分母','m²')
  add('village_area_km2',g.area/1e6,'Float64','原固定幾何面積／1e6；不得改用AREA或刪低事故里','km²')
  add('source_AREA_attribute',g.AREA,'Float64','原AREA屬性僅追溯；單位／產製口徑未由本次認證，不作主要分母','原欄單位未認證')
  add('source_geometry_crs','EPSG:3826','string','原固定PRJ支持的CRS')
  add('geometry_type',g.geom_type,'string','固定原幾何類型')
  add('geometry_valid',g.geometry.is_valid,'boolean','固定原面有效；未執行修復')
  add('interior_hole_count',holes,'Int64','原Polygon interior ring數，未填補','個')
  add('positive_overlap_neighbor_count',count,'Int64','具有嚴格正面積交集的其他原里數，不消除交集','里')
  add('positive_overlap_union_m2',[s.union_all(x).area for x in overlap],'Float64','每里與其他里正面積交集聯集，僅品質、不扣原面積','m²')
  quality=np.select([(holes>0)&(count>0),holes>0,count>0],['valid_original_holes_and_overlap','valid_original_holes','valid_original_overlap'],default='valid_original')
  add('geometry_quality_flag',quality,'string','原有效面之孔洞／正面積重疊診斷，未修補')
  add('fixed_geometry_wkb_sha256',[hashlib.sha256(x.wkb).hexdigest() for x in geom],'string','本次讀取原固定geometry WKB摘要，供版本／不變性核對')
  base=typed_frame(d,self.base_defs)
  self.histories={};self.extraction_manifest=[];histinfo=[]
  for year,path,member in [(2024,'data/raw/113村里界.zip','村里界歷史圖資_113/VILLAGE_NLSC_1131128.shp'),(2025,'data/raw/114村里界.zip','村里界歷史圖資_114/VILLAGE_NLSC_11401031.shp')]:
   p=self.extract(path,member);h=gpd.read_file(p,engine='pyogrio');assert h.crs.to_epsg()==3824
   national_N=len(h);h=h[h.COUNTYNAME.eq('臺北市')].copy();assert len(h)==456 and h.VILLCODE.is_unique
   h=h.merge(self.crosswalk[['population_code','village_id','district_name','standard_village_name']],left_on='VILLCODE',right_on='population_code',how='left',validate='one_to_one',indicator=True)
   assert h['_merge'].eq('both').all() and h.TOWNNAME.eq(h.district_name).all()
   h=h.set_index('village_id').reindex(self.ids).reset_index();assert h.geometry.notna().all()
   h=h.to_crs(3826);assert h.geometry.is_valid.all() and h.area.gt(0).all();self.histories[year]=h
   def histadd(stem,v,dtype,definition,unit='not applicable'):
    name=stem+'_'+str(year);self.define(self.base_defs,name,dtype,definition,unit,path+'::'+member);base[name]=pd.Series([v]*456 if pd.api.types.is_scalar(v) else v).reset_index(drop=True).astype(dtype)
   histadd('historical_boundary_code',h.VILLCODE,'string','歷史原11碼VILLCODE，經既有人口碼對照共同10碼ID，非截碼')
   histadd('historical_district_code',h.TOWNCODE.astype(str),'string','歷史原TOWNCODE，與固定CPTID分開保留')
   histadd('historical_village_name',h.VILLNAME,'string','歷史原里名；年版快照不宣稱全年每天有效')
   histadd('historical_area_m2',h.area,'Float64','該年版原面由3824轉3826後面積，歷史地理密度用此分母','m²')
   histadd('historical_area_km2',h.area/1e6,'Float64','該歷史年版投影面積／1e6，不冒充固定共同分母','km²')
   histadd('historical_match_status','one_to_one_existing_population_code_crosswalk','string','沿已接受crosswalk完整一對一，糖廍既定接受且provisional原狀態不變')
   histadd('historical_source_crs','EPSG:3824','string','歷史原始PRJ支持3824；計量轉至3826')
   hg=np.asarray(h.geometry.array,dtype=object);inter=s.area(s.intersection(hg,geom));union=s.area(s.union(hg,geom));sym=s.area(s.symmetric_difference(hg,geom))
   histadd('historical_fixed_iou',inter/union,'Float64','同研究里歷史與固定面之交集／聯集；不認定法定邊界變更','0–1')
   histadd('historical_fixed_symdiff_m2',sym,'Float64','同研究里歷史與固定面之對稱差面積','m²')
   histadd('historical_geometry_wkb_sha256',[hashlib.sha256(x.wkb).hexdigest() for x in hg],'string','轉3826後歷史geometry WKB摘要，沒有修復或替換原檔')
   histinfo.append(dict(year=year,path=path,member=member,national_primary_rows=national_N,taipei_rows=len(h),original_crs='EPSG:3824',working_crs='EPSG:3826',match='one-to-one existing population-code crosswalk',snapshot_caveat='官方年版單一快照；11401031保留原字串，不強解日期'))
  self.base=base;self.overlap_pairs=pd.DataFrame(positive);self.histinfo=histinfo
  assert len(base)==456 and base.village_id.is_unique and base.population_code.notna().all()
  sugar=base[base.standard_village_name.eq('糖廍里')];assert len(sugar)==1 and sugar.verification_status.iloc[0]=='provisional_match'
  self.summary['geometry_quality']={'fixed_villages':456,'districts':12,'positive_overlap_pairs':len(positive),'individual_polygon_interior_rings':int(holes.sum()),'city_union_interior_holes':int(union_holes),'source_geometry_unchanged':True}
  self.summary['history_sources']=histinfo
  show('固定／歷史基礎面積分布；AREA不作分母',base[['village_area_m2','village_area_km2','historical_area_m2_2024','historical_area_m2_2025']].describe().T.reset_index())
  show('歷史來源及既有碼對照',pd.DataFrame(histinfo));show('只解壓必要配套之來源紀錄',pd.DataFrame(self.extraction_manifest))
  show('糖廍同規則保留；原始名稱及provisional不改',sugar)
  show('固定原幾何品質分布',base.geometry_quality_flag.value_counts().rename_axis('quality').reset_index(name='villages'))
  return base

 def extract(self,relative,member):
  path=self.file(relative);target=(self.temp/'extracted'/self.bindings[relative][:12]).resolve();stem=member[:-4]
  with zipfile.ZipFile(path) as z:
   for info in z.infolist():
    q=PurePosixPath(info.filename.replace('\\','/'));assert not q.is_absolute() and '..' not in q.parts and ':' not in info.filename
    assert ((info.external_attr>>16)&0o170000)!=0o120000
   names=[stem+ext for ext in ['.shp','.shx','.dbf','.prj','.cpg']]
   assert all(n in z.namelist() for n in names)
   for name in names:
    body=z.read(name);p=(target/name).resolve();assert p.is_relative_to(target);p.parent.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(body).hexdigest()
    if not p.exists() or sha(p)!=digest:p.write_bytes(body)
    self.extraction_manifest.append(dict(raw_container=relative,member=name,bytes=len(body),sha256=digest,temp_is_original_download=False))
  return target/member

 def construct_points(self):
  a=self.accidents;lon=a.longitude_candidate.to_numpy(dtype=float,na_value=np.nan);lat=a.latitude_candidate.to_numpy(dtype=float,na_value=np.nan)
  finite=np.isfinite(lon)&np.isfinite(lat);global_ok=finite&(abs(lon)<=180)&(abs(lat)<=90)
  assert np.array_equal(finite,a.coordinate_parse_valid.to_numpy(bool))
  assert np.array_equal(global_ok,a.coordinate_global_range_valid.to_numpy(bool))
  missing=a.coordinate_missing_flag.to_numpy(bool);eligible=global_ok&~missing
  p=np.empty(len(a),dtype=object);p[:]=None
  original=gpd.GeoSeries(s.points(lon[eligible],lat[eligible]),crs=4326);projected=original.to_crs(3826)
  p[eligible]=np.asarray(projected.array,dtype=object)
  x=s.get_x(p);y=s.get_y(p);valid=eligible&np.isfinite(x)&np.isfinite(y)
  p[~valid]=None;self.points=p;self.point_valid=valid;self.point_missing=missing;self.x=x;self.y=y
  self.summary['points']={'candidates':len(a),'point_valid':int(valid.sum()),'missing':int(missing.sum()),'other_invalid':int((~valid&~missing).sum()),'original_crs':'EPSG:4326 working assumption; datum uncertified','working_crs':'EPSG:3826','point_source':'Unit2.1 standardized candidate lon/lat only','coordinate_imputation':False}
  names='|'.join(re.escape(n) for n in sorted(set(self.base.district_name)))
  self.original_district=a.district_label_source_raw.str.extract(r'^\d{2}('+names+r')$',expand=False).astype('string')
  self.address_district=a.accident_location_text_raw.str.extract(r'^(?:臺北市|台北市)?('+names+r')',expand=False).astype('string')
  self.original_district=self.original_district.where(self.original_district.isin(self.base.district_name))
  show('Point及CRS處理；不是datum官方認證',pd.DataFrame([self.summary['points']]))
  show('來源區名／地址可判讀程度',pd.DataFrame([{'year':int(year),'N':len(g),'original_district_readable':int(self.original_district.loc[g.index].notna().sum()),'address_district_readable':int(self.address_district.loc[g.index].notna().sum())} for year,g in a.groupby('source_year')]))

 @staticmethod
 def geometry_classify(w,c,point,geometries,vertices):
  if not set(w).issubset(c):return 'predicate_mismatch'
  if len(w)==len(c)==1 and w==c:return 'unique_interior'
  if len(w)>1:return 'multiple_interior'
  if not w and len(c)>=2:
   for j in c:
    if j not in vertices:
     gg=geometries[j];polygons=[gg] if gg.geom_type=='Polygon' else list(gg.geoms)
     vertices[j]={tuple(xy[:2]) for poly in polygons for ring in [poly.exterior,*poly.interiors] for xy in ring.coords}
   n=sum((point.x,point.y) in vertices[j] for j in c)
   return 'shared_vertex' if n>=2 else 'shared_boundary'
  if not w and len(c)==1:return 'single_boundary'
  if len(c)>1:return 'other_multiple'
  if not w and not c:return 'outside_or_hole'
  return 'predicate_mismatch'

 def _query(self,indices,boundary,historical=False):
  indices=np.asarray(indices);points=self.points[indices];valid=self.point_valid[indices];missing=self.point_missing[indices]
  geoms=np.asarray(boundary.geometry.array,dtype=object);tree=s.STRtree(geoms)
  village=boundary.village_id.astype(str).to_numpy() if historical else self.ids
  district=boundary.TOWNNAME.astype(str).to_numpy() if historical else self.districts
  original_code=boundary.VILLCODE.astype(str).to_numpy() if historical else self.ids
  ws=[[] for _ in indices];cs=[[] for _ in indices];local_valid=np.flatnonzero(valid)
  for predicate,containers in [('within',ws),('covered_by',cs)]:
   pair=tree.query(points[local_valid],predicate=predicate)
   for i,j in zip(*pair):containers[local_valid[i]].append(int(j))
  geom_states=[];geometric_id=[];spatial_district=[];origin_code=[];vertices={}
  for i,(w,c) in enumerate(zip(ws,cs)):
   status='missing_coordinates' if missing[i] else 'invalid_coordinates' if not valid[i] else self.geometry_classify(w,c,points[i],geoms,vertices)
   geom_states.append(status)
   # Selecting the sole candidate is allowed ONLY after exact uniqueness checks.
   if status=='unique_interior':
    j=w[0];geometric_id.append(village[j]);spatial_district.append(district[j]);origin_code.append(original_code[j])
   else:geometric_id.append(pd.NA);spatial_district.append(pd.NA);origin_code.append(pd.NA)
  f=pd.DataFrame(index=indices)
  f['geometry_status']=pd.Series(geom_states,index=indices,dtype='string')
  f['geometry_unique']=f.geometry_status.eq('unique_interior').astype('boolean')
  f['geometric_village_id']=pd.Series(geometric_id,index=indices,dtype='string')
  f['spatial_district']=pd.Series(spatial_district,index=indices,dtype='string')
  f['unique_original_boundary_code']=pd.Series(origin_code,index=indices,dtype='string')
  for name,lists in [('within',ws),('covered_by',cs)]:
   f[name+'_candidate_count']=pd.Series([len(v) if ok else pd.NA for v,ok in zip(lists,valid)],index=indices,dtype='Int64')
   f[name+'_candidate_ids']=pd.Series([json.dumps(sorted(village[j] for j in v),separators=(',',':')) if ok else pd.NA for v,ok in zip(lists,valid)],index=indices,dtype='string')
   f[name+'_original_codes']=pd.Series([json.dumps(sorted(original_code[j] for j in v),separators=(',',':')) if ok else pd.NA for v,ok in zip(lists,valid)],index=indices,dtype='string')
  raw=self.original_district.loc[indices];address=self.address_district.loc[indices]
  f['district_comparable']=(f.geometry_unique&raw.notna()).astype('boolean')
  f['district_match']=raw.eq(f.spatial_district).astype('boolean').where(f.district_comparable,pd.NA)
  f['district_conflict']=(~f.district_match).astype('boolean')
  f['address_comparable']=(f.geometry_unique&address.notna()).astype('boolean')
  f['address_match']=address.eq(f.spatial_district).astype('boolean').where(f.address_comparable,pd.NA)
  f['address_conflict']=(~f.address_match).astype('boolean')
  f['address_status']=pd.Series(np.select([address.isna(),~f.geometry_unique.to_numpy(bool),f.address_match.fillna(False).to_numpy(bool)],['unreadable','not_spatially_comparable','consistent'],default='conflict'),index=indices,dtype='string')
  conservative=f.geometry_unique&f.district_match.fillna(False)&~f.address_conflict.fillna(False)
  f['conservative_eligible']=conservative.astype('boolean')
  states=[]
  for i in indices:
   gs=f.at[i,'geometry_status']
   if gs in ['missing_coordinates','invalid_coordinates','outside_or_hole','predicate_mismatch']:state=gs
   elif gs in ['shared_vertex','shared_boundary','single_boundary']:state='boundary_nonunique'
   elif gs in ['multiple_interior','other_multiple']:state='multiple_geometry'
   elif pd.isna(raw.at[i]):state='original_district_unknown'
   elif bool(f.at[i,'district_conflict']):state='district_conflict'
   elif pd.notna(f.at[i,'address_conflict']) and bool(f.at[i,'address_conflict']):state='address_conflict'
   else:state='conservative_success'
   states.append(state)
  f['assignment_status']=pd.Series(states,index=indices,dtype='string')
  assert f.assignment_status.isin(STATES).all() and f.geometry_status.isin(GEOMETRY_STATES).all()
  assert f.conservative_eligible.equals(f.assignment_status.eq('conservative_success').astype('boolean'))
  # Distance to union of original district polygons, in metres; never used to assign.
  distance=pd.Series(pd.NA,index=indices,dtype='Float64');distance_ok=valid&raw.notna().to_numpy()
  for label in sorted(set(raw.dropna())):
   mask=raw.eq(label).fillna(False).to_numpy()&valid
   if not mask.any():continue
   union=s.union_all(geoms[district==label]);assert not union.is_empty
   distance.iloc[np.flatnonzero(mask)]=s.distance(points[mask],union)
  f['distance_to_original_district_m']=distance
  f['distance_valid']=pd.Series(distance_ok,index=indices,dtype='boolean')
  assert f.distance_to_original_district_m.notna().equals(f.distance_valid.astype(bool))
  return f

 def assign(self):
  if not hasattr(self,'points'):self.construct_points()
  a=self.accidents;fixed=self._query(a.index,self.fixed)
  hist=pd.concat([self._query(g.index,self.histories[int(year)],historical=True) for year,g in a.groupby('source_year')]).sort_index()
  assert hist.index.equals(a.index)
  self.fixed_audit=fixed;self.historical_audit=hist
  d={};defs=self.assignment_defs
  def add(name,value,dtype,meaning,unit='not applicable',source='Unit2.1／固定與年度歷史Spatial predicates'):
   self.define(defs,name,dtype,meaning,unit,source);d[name]=value
  for name in ['record_id','source_year','source_row_number','coordinate_x_raw','coordinate_y_raw','longitude_candidate','latitude_candidate','coordinate_parse_valid','coordinate_missing_flag']:
   field=next(r for r in self.upstream_contract['columns'] if r['name']==name)
   add(name,a[name],field['dtype'],field['definition'],field['unit'],'Unit2.1正式CSV：'+name)
  add('original_district_label_raw',a.district_label_source_raw,'string','原事故區序字串原值，數字部分不映射官方CPTID')
  add('original_district_name',self.original_district,'string','只取原區序明示12區名，正規式^兩數字＋區名$；不猜數字順序')
  add('original_district_readable',self.original_district.notna(),'boolean','原區序是否能明確確認行政區；未知不成立保守一致')
  add('accident_address_raw',a.accident_location_text_raw,'string','原事故地址，不改寫、不地理編碼、不表示居民地址')
  add('address_district_name',self.address_district,'string','只取地址開頭明確區名，可有臺北市／台北市前綴，不從路名猜測')
  add('address_district_readable',self.address_district.notna(),'boolean','地址區名可判讀；False不等於地址衝突')
  both=self.original_district.notna()&self.address_district.notna()
  add('raw_address_district_conflict',self.original_district.ne(self.address_district).where(both),'boolean','兩來源文字區名之衝突，與地址對空間衝突分開；不可比較NA')
  add('point_valid',self.point_valid,'boolean','來源旗標及全球範圍有效且投影有限；不是位置正確性認證')
  add('point_easting_3826_m',self.x,'Float64','工作4326→3826的Easting，無補值','m')
  add('point_northing_3826_m',self.y,'Float64','工作4326→3826的Northing，無補值','m')
  meanings={
   'geometry_status':'幾何互斥狀態；見schema geometry_states，唯一必須within／covered_by同一且各1',
   'geometry_unique':'唯一內部配對成立，單純covered_by唯一不成立',
   'geometric_village_id':'唯一內部時的共同10碼研究ID，否則NA',
   'spatial_district':'僅幾何唯一時之空間區名，其他NA',
   'unique_original_boundary_code':'唯一內部原圖資碼；固定10碼／歷史11碼，不混用',
   'within_candidate_count':'within候選數；有效Point無命中0，無Point為NA',
   'covered_by_candidate_count':'covered_by候選數；有效Point無命中0，無Point為NA',
   'within_candidate_ids':'排序JSON陣列之共同10碼within候選；[]查無命中，NA未查',
   'covered_by_candidate_ids':'排序JSON陣列之共同10碼covered_by候選；[]查無命中，NA未查',
   'within_original_codes':'排序JSON原圖資within碼，歷史11碼保留',
   'covered_by_original_codes':'排序JSON原圖資covered_by碼，歷史11碼保留',
   'district_comparable':'唯一幾何且原區名可判；此集合才作區名衝突率分母',
   'district_match':'原區名與空間區名是否一致；不可比較NA',
   'district_conflict':'原區名與空間區名明確衝突；不可比較NA，不當無衝突',
   'address_comparable':'唯一幾何且地址區名可判；地址衝突率獨立分母',
   'address_match':'地址區名與空間區名一致；不可比較NA',
   'address_conflict':'地址與空間區名明確衝突；未知NA不單獨排除保守配對',
   'address_status':'unreadable／not_spatially_comparable／consistent／conflict',
   'conservative_eligible':'幾何唯一、原區名可判且一致、地址無明確空間衝突',
   'assignment_status':'完整互斥主狀態，按schema priority定義，含0筆狀態',
   'distance_to_original_district_m':'Point距此版本原區名所屬里幾何聯集之距離；僅診斷，不重派',
   'distance_valid':'該版本距離可計算：Point有效且原區名明確'}
  for family,f in [('fixed',fixed),('historical',hist)]:
   for name in f:
    add(family+'_'+name,f[name],str(f[name].dtype),meanings[name],'m' if name.endswith('_m') else 'candidate count' if name.endswith('_count') else 'not applicable')
  for spec,eligible,ids in [('s0',fixed.conservative_eligible,fixed.geometric_village_id),('s1',fixed.geometry_unique,fixed.geometric_village_id),('s2',hist.conservative_eligible,hist.geometric_village_id),('s3',hist.geometry_unique,hist.geometric_village_id)]:
   add('eligible_'+spec,eligible,'boolean',spec.upper()+'納入資格；S0主，S1／S2／S3敏感，不刪不合格原事故')
   add('village_id_'+spec,ids.where(eligible),'string',spec.upper()+'資格成立之共同10碼研究ID，資格False必NA')
  add('historical_boundary_year',a.source_year,'Int64','所採官方歷史年版；不是認證全年每日有效','year')
  add('historical_boundary_code',hist.unique_original_boundary_code,'string','歷史幾何唯一時原11碼VILLCODE；仍須共同ID連接')
  out=typed_frame(d,defs)
  def change(name,values,meaning):
   self.define(defs,name,'boolean',meaning,source='四種正式規格逐筆比較；NA語義明示');out[name]=values.astype('boolean')
  for label,left,right in [('geometry','s1','s3'),('conservative','s0','s2')]:
   change('fixed_historical_'+label+'_assignment_same',same_optional(out['village_id_'+left],out['village_id_'+right]),'兩NA視同未指派；一NA與有效ID不同；兩有效ID字串相等才一致')
   change(label+'_eligibility_changed',out['eligible_'+left]^out['eligible_'+right],'固定與歷史'+label+'資格xor，不把NA→ID當兩個有效里之換里')
   change(label+'_assigned_to_unassigned',out['eligible_'+left]&~out['eligible_'+right],'固定有效→歷史無法納入（'+label+'）')
   change(label+'_unassigned_to_assigned',~out['eligible_'+left]&out['eligible_'+right],'固定無法納入→歷史有效（'+label+'）')
  both_geometry=out.eligible_s1&out.eligible_s3
  change('geometric_village_changed',both_geometry&out.village_id_s1.ne(out.village_id_s3).fillna(False),'兩邊都幾何唯一且研究里碼不同；缺一邊不稱兩有效里換里')
  change('geometric_district_changed',both_geometry&out.fixed_spatial_district.ne(out.historical_spatial_district).fillna(False),'兩邊都幾何唯一且空間行政區不同，不含失去／新增配對')
  change('geometry_status_changed',out.fixed_geometry_status.ne(out.historical_geometry_status),'幾何互斥狀態不同，非保守區名／地址狀態差')
  change('geometry_village_or_status_changed',~out.fixed_historical_geometry_assignment_same|out.geometry_status_changed,'與Unit1.7可比：幾何里碼（未指派作同一空狀態）或幾何狀態變更')
  change('district_or_assignment_availability_changed',~same_optional(out.fixed_spatial_district,out.historical_spatial_district),'空間區名或其可指派性改變；不冒充皆為有效區換區')
  change('district_conflict_to_consistent',out.fixed_district_conflict.fillna(False)&out.historical_district_match.fillna(False),'固定明確區名衝突→歷史明確一致；原239診斷口徑')
  change('district_consistent_to_conflict',out.fixed_district_match.fillna(False)&out.historical_district_conflict.fillna(False),'固定明確一致→歷史明確衝突；不含原未配對')
  change('new_district_conflict_including_unassigned',~out.fixed_district_conflict.fillna(False)&out.historical_district_conflict.fillna(False),'歷史新衝突，包括固定未可比較者；與原215診斷口徑對照')
  for family,qualification in [('geometry',out.geometry_eligibility_changed),('conservative',out.conservative_eligibility_changed)]:
   name=family+'_change_reason';self.define(defs,name,'string','換里＝兩邊幾何唯一ID不同；資格變更＝'+family+'資格xor；四類互斥',source='固定／年度歷史比較')
   out[name]=kind_of_change(out.geometric_village_changed,qualification)
  self.assignment=out
  self.validate_memory()
  return out

 def validate_memory(self):
  out=self.assignment;base=self.base;a=self.accidents
  assert len(out)==45130 and out.record_id.is_unique and set(out.record_id)==set(a.record_id)
  assert out.record_id.tolist()==a.record_id.tolist()
  assert out.groupby('source_year').size().to_dict()=={2024:22368,2025:22762}
  assert not (out.eligible_s0&~out.eligible_s1).any() and not (out.eligible_s2&~out.eligible_s3).any()
  for low,high in [('s0','s1'),('s2','s3')]:
   mask=out['eligible_'+low];assert out.loc[mask,'village_id_'+low].eq(out.loc[mask,'village_id_'+high]).all()
  for spec in ['s0','s1','s2','s3']:
   assert out['eligible_'+spec].equals(out['village_id_'+spec].notna().astype('boolean'))
   assert out.loc[out['eligible_'+spec],'village_id_'+spec].isin(base.village_id).all()
   assert not out.loc[out.coordinate_missing_flag,'eligible_'+spec].any()
  for family in ['fixed','historical']:
   assert out[family+'_assignment_status'].isin(STATES).all() and out[family+'_assignment_status'].notna().all()
   assert out[family+'_geometry_unique'].eq(out[family+'_geometry_status'].eq('unique_interior')).all()
  assert self.fixed.geometry.to_wkb().equals(self.fixed_wkb)

 def reconciliation(self):
  out=self.assignment;benchmarks={2024:{'eligible_s0':21920,'eligible_s1':22351,'eligible_s2':21931,'eligible_s3':22350,'fixed_district_conflict':431,'historical_district_conflict':419,'geometry_village_or_status_changed':544,'district_conflict_to_consistent':115,'new_district_conflict_including_unassigned':103},2025:{'eligible_s0':22292,'eligible_s1':22732,'eligible_s2':22302,'eligible_s3':22730,'fixed_district_conflict':438,'historical_district_conflict':426,'geometry_village_or_status_changed':585,'district_conflict_to_consistent':124,'new_district_conflict_including_unassigned':112}}
  comparison=[];states=[];geostates=[];distance=[];changes=[]
  for year,g in out.groupby('source_year'):
   for field,expected in benchmarks[int(year)].items():
    actual=int(g[field].sum());comparison.append(dict(year=int(year),item=field,prior_diagnostic=expected,formal_result=actual,difference=actual-expected))
   for family in ['fixed','historical']:
    for state in STATES:states.append(dict(year=int(year),boundary=family,status=state,N=int(g[family+'_assignment_status'].eq(state).sum()),priority_definition=STATES[state]))
    for state in GEOMETRY_STATES:geostates.append(dict(year=int(year),boundary=family,geometry_status=state,N=int(g[family+'_geometry_status'].eq(state).sum())))
    conflict=g[g[family+'_district_conflict'].fillna(False)];v=conflict[family+'_distance_to_original_district_m'].dropna()
    distance.append(dict(year=int(year),boundary=family,district_conflicts=len(conflict),distance_valid_N=len(v),at_most_100m=int(v.le(100).sum()),over_100m=int(v.gt(100).sum()),median_m=float(v.median()),maximum_m=float(v.max())))
   changes.append(dict(year=int(year),geometry_village_changed=int(g.geometric_village_changed.sum()),geometry_status_changed=int(g.geometry_status_changed.sum()),village_or_geometry_status_changed=int(g.geometry_village_or_status_changed.sum()),geometric_district_changed=int(g.geometric_district_changed.sum()),district_or_availability_changed=int(g.district_or_assignment_availability_changed.sum()),geometry_lost=int(g.geometry_assigned_to_unassigned.sum()),geometry_gained=int(g.geometry_unassigned_to_assigned.sum()),conservative_lost=int(g.conservative_assigned_to_unassigned.sum()),conservative_gained=int(g.conservative_unassigned_to_assigned.sum()),conflict_to_consistent=int(g.district_conflict_to_consistent.sum()),consistent_to_conflict=int(g.district_consistent_to_conflict.sum()),new_conflicts_including_prior_unassigned=int(g.new_district_conflict_including_unassigned.sum())))
  comparison=pd.DataFrame(comparison);states=pd.DataFrame(states);geostates=pd.DataFrame(geostates);distance=pd.DataFrame(distance);changes=pd.DataFrame(changes)
  self.summary['benchmark_comparison']=comparison.to_dict('records');self.summary['assignment_states']=states.to_dict('records');self.summary['geometry_states']=geostates.to_dict('records');self.summary['distance']=distance.to_dict('records');self.summary['changes']=changes.to_dict('records')
  show('正式配對對照既有診斷；不人工改值吻合',comparison)
  show('主狀態完整互斥；每家族／年度合計原候選N，保留0筆定義',states,block=10)
  show('幾何狀態與predicate細分，保留0筆類別',geostates,block=10)
  show('原區幾何距離m；不以距離改派',distance)
  show('固定／歷史變化：兩有效里換里與資格變更分開',changes)
  # All reference differences are explained/zero here. A mismatch stops export
  # and retains individual records in memory for investigation, never retargets.
  assert comparison.difference.eq(0).all(),'Unexplained benchmark differences; do not export as passed'
  assert distance.query("boundary=='fixed'").set_index('year').over_100m.to_dict()=={2024:111,2025:111}
  assert out.fixed_assignment_status.eq('outside_or_hole').sum()==44
  assert out.fixed_assignment_status.eq('address_conflict').sum()==2
  assert (~out.eligible_s0).sum()==918
  assert states.groupby(['year','boundary']).N.sum().to_dict()=={(2024,'fixed'):22368,(2024,'historical'):22368,(2025,'fixed'):22762,(2025,'historical'):22762}
  anomaly=out[~out.eligible_s0]
  cols=['record_id','source_year','original_district_label_raw','original_district_name','accident_address_raw','address_district_name','fixed_spatial_district','fixed_assignment_status','fixed_distance_to_original_district_m','village_id_s1','historical_spatial_district','historical_assignment_status','village_id_s2','village_id_s3']
  show('S0未納入918筆完整追溯清單；仍保留正式資料',anomaly[cols],block=10)
  show('跨地理配對變化前40筆；完整逐筆旗標已正式保存',out.loc[out.geometry_village_or_status_changed,['record_id','source_year','village_id_s0','village_id_s1','village_id_s2','village_id_s3','geometry_change_reason','conservative_change_reason']].head(40),block=10)
  byreason=[]
  for field in ['geometry_change_reason','conservative_change_reason']:
   q=out.groupby(['source_year',field]).size().rename('N').reset_index();q['change_definition']=field;byreason.append(q.rename(columns={field:'reason'}))
  self.change_reasons=pd.concat(byreason,ignore_index=True);show('換里／資格四類互斥變化分布',self.change_reasons)
  self.summary['change_reasons']=self.change_reasons.to_dict('records')
  return comparison

 def selection_diagnostics(self):
  a=self.accidents;out=self.assignment;district=[];features=[];distribution=[]
  for year,g in out.groupby('source_year'):
   idx=g.index
   for basis,column in [('original','original_district_name'),('fixed_unique','fixed_spatial_district'),('historical_unique','historical_spatial_district')]:
    group=g[column].fillna('[unreadable_or_unassigned]')
    for label,ids in group.groupby(group).groups.items():
     z=g.loc[ids];N=len(z)
     row=dict(year=int(year),district_basis=basis,district=label,candidates=N)
     for spec in ['s0','s1','s2','s3']:row[spec+'_N']=int(z['eligible_'+spec].sum());row[spec+'_rate']=float(z['eligible_'+spec].sum()/N)
     for family in ['fixed','historical']:
      denom=int(z[family+'_district_comparable'].sum());conflict=int(z[family+'_district_conflict'].sum());addrden=int(z[family+'_address_comparable'].sum());addr=int(z[family+'_address_conflict'].sum())
      row.update({family+'_district_conflicts':conflict,family+'_district_comparable_N':denom,family+'_district_conflict_rate':conflict/denom if denom else None,family+'_address_conflicts':addr,family+'_address_comparable_N':addrden,family+'_address_conflict_rate':addr/addrden if addrden else None,family+'_outside_N':int(z[family+'_assignment_status'].eq('outside_or_hole').sum()),family+'_outside_rate':float(z[family+'_assignment_status'].eq('outside_or_hole').sum()/N)})
     row['missing_coordinates_N']=int(z.coordinate_missing_flag.sum());row['missing_coordinates_rate']=float(z.coordinate_missing_flag.sum()/N);district.append(row)
   for included in [True,False]:
    ix=g.index[g.eligible_s0.eq(included)];sub=a.loc[ix];N=len(sub)
    for name in FEATURES:
     valid=int(sub[name+'_valid'].sum());true=int(sub[name].eq(True).sum());false=int(sub[name].eq(False).sum());missing=int(sub[name].isna().sum())
     features.append(dict(year=int(year),s0_included=included,feature=name,group_N=N,valid_N=valid,True_N=true,False_N=false,NA_N=missing,True_share_of_valid=true/valid if valid else None,NA_share_of_group=missing/N if N else None))
    for name in ['month','hour','weekend','accident_type_code','accident_position_code','injured_count_structural_valid','fatalities_source_count_structural_valid','fatalities_2_30d_count_structural_valid','conditional_casualty_inconsistency_flag']:
     v=sub[name];valid=int(v.notna().sum());missing=int(v.isna().sum());count=v.astype('string').fillna('[NA]').value_counts(dropna=False)
     for category,n in count.items():distribution.append(dict(year=int(year),s0_included=included,variable=name,category=category,N=int(n),group_N=N,valid_N=valid,NA_N=missing,share_of_valid=int(n)/valid if category!='[NA]' and valid else None,share_of_group=int(n)/N if N else None))
  district=pd.DataFrame(district);features=pd.DataFrame(features);distribution=pd.DataFrame(distribution)
  self.selection_district=district;self.selection_features=features;self.selection_distributions=distribution
  self.summary['district_coverage']=district.to_dict('records');self.summary['selection_features']=features.to_dict('records');self.summary['selection_distributions']=distribution.to_dict('records')
  show('按原／固定空間／歷史空間行政區的配對率；分母依欄明示',district,block=12)
  show('S0納入／未納入九特徵：各自有效分母與NA，不做推論',features,block=9)
  show('S0選擇性診斷：月／小時／平週末／型態／位置／傷亡品質',distribution,block=20)
  print('描述性差異僅提示選擇性排除風險，保留S1敏感度；不據此改S0、不作p值／模型或正式Finding。')
  return features

 def village_diagnostics(self):
  base=self.base;out=self.assignment
  skeleton=pd.MultiIndex.from_product([base.village_id.tolist(),[2024,2025]],names=['village_id','year']).to_frame(index=False)
  skeleton=skeleton.merge(base[['village_id','district_name','standard_village_name']],on='village_id',how='left',validate='many_to_one')
  summaries=[];zeros=[]
  for spec in ['s0','s1','s2','s3']:
   good=out[out['eligible_'+spec]]
   count=good.groupby(['village_id_'+spec,'source_year']).size().rename('observed_assigned_count_'+spec).reset_index().rename(columns={'village_id_'+spec:'village_id','source_year':'year'})
   skeleton=skeleton.merge(count,on=['village_id','year'],how='left',validate='one_to_one');col='observed_assigned_count_'+spec;skeleton[col]=skeleton[col].fillna(0).astype('Int64')
   assert skeleton.groupby('year')[col].sum().to_dict()==good.groupby('source_year').size().to_dict()
   for year,g in skeleton.groupby('year'):
    values=g[col]
    summaries.append(dict(year=int(year),specification=spec,villages=len(g),total_observed=int(values.sum()),zero_observed=int(values.eq(0).sum()),minimum=int(values.min()),median=float(values.median()),maximum=int(values.max()),**{'N_below_'+str(t):int(values.lt(t).sum()) for t in [5,10,20,30,50]}))
    for row in g[values.eq(0)].itertuples(index=False):zeros.append(dict(year=int(year),specification=spec,village_id=row.village_id,district_name=row.district_name,village_name=row.standard_village_name,meaning='本規格未觀測配對事故，不證明現實無事故'))
  assert len(skeleton)==912 and not skeleton.duplicated(['village_id','year']).any()
  skeleton['geometry_count_difference']=skeleton.observed_assigned_count_s3-skeleton.observed_assigned_count_s1
  skeleton['conservative_count_difference']=skeleton.observed_assigned_count_s2-skeleton.observed_assigned_count_s0
  self.village_counts=skeleton;self.village_summary=pd.DataFrame(summaries);self.zero_villages=pd.DataFrame(zeros)
  self.summary['village_coverage']=summaries;self.summary['zero_observed_villages']=zeros
  # This ignored, diagnostic log is regenerated from formal assignments and never
  # consumed by a notebook. No village-level Dataset A/C output is written.
  show('912組完整逐里觀測事故數診斷；不是正式Dataset A／C',skeleton,block=16)
  show('零觀測／低樣本多門檻診斷，未定排除門檻',self.village_summary)
  show('零觀測里完整清單；不刪里、不說現實零事故',self.zero_villages)
  show('歷史／固定觀測數差最大前30里年；差異不是統計顯著性',skeleton.assign(abs_change=skeleton.geometry_count_difference.abs()).nlargest(30,'abs_change'),block=15)
  return skeleton

 def synthetic_predicate_checks(self):
  """Small deterministic GIS checks, clearly separate from actual accidents."""
  p1=s.box(0,0,2,2);p2=s.box(2,0,4,2);p3=s.box(1,1,3,3)
  geoms=np.asarray([p1,p2],dtype=object);tree=s.STRtree(geoms)
  cases=[('inside',s.Point(1,1),'unique_interior'),('shared edge',s.Point(2,1),'shared_boundary'),('shared vertex',s.Point(2,0),'shared_vertex'),('single boundary',s.Point(0,1),'single_boundary'),('outside',s.Point(8,8),'outside_or_hole')]
  rows=[]
  for label,point,expected in cases:
   w=tree.query(point,predicate='within').tolist();c=tree.query(point,predicate='covered_by').tolist();got=self.geometry_classify(w,c,point,geoms,{})
   assert got==expected,(label,got);rows.append(dict(synthetic_case=label,within_count=len(w),covered_by_count=len(c),expected=expected,observed=got))
  overlap=np.asarray([p1,p3],dtype=object);point=s.Point(1.5,1.5);t=s.STRtree(overlap)
  assert self.geometry_classify(t.query(point,predicate='within').tolist(),t.query(point,predicate='covered_by').tolist(),point,overlap,{})=='multiple_interior'
  assert self.geometry_classify([0],[1],s.Point(1,1),geoms,{})=='predicate_mismatch'
  aa=pd.Series([pd.NA,pd.NA,'6300100002','6300100002'],dtype='string');bb=pd.Series([pd.NA,'6300100002',pd.NA,'6300100003'],dtype='string')
  assert same_optional(aa,bb).tolist()==[True,False,False,False]
  show('合成predicate／NA語義測試，非真實事故結果',pd.DataFrame(rows))

 def plots(self):
  import matplotlib.pyplot as plt
  from matplotlib import font_manager
  font=Path('C:/Windows/Fonts/msjh.ttc')
  if font.exists():
   font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name()
  plt.rcParams['axes.unicode_minus']=False
  out=self.assignment;g=self.fixed;x=self.x;y=self.y
  def boundary(ax):
   g.boundary.plot(ax=ax,color='#888888',linewidth=.3);ax.set_aspect('equal');ax.set_axis_off()
  def scatter(ax,mask,color,size=3,label=None):
   mask=np.asarray(mask,dtype=bool)&self.point_valid
   ax.scatter(x[mask],y[mask],s=size,c=color,alpha=.65,label=label,rasterized=True)
  def finish(fig,name):
   fig.suptitle('Unit 2.2 資料處理／空間品質診斷，非正式Finding；EPSG:3826',fontsize=13)
   fig.tight_layout(rect=[0,0,1,.95]);fig.savefig(self.temp/name,dpi=140);display(fig);plt.close(fig)
  fig,axes=plt.subplots(2,2,figsize=(13,12));ax=axes.ravel()
  for aa in ax:boundary(aa)
  ax[0].set_title('固定456里原幾何；保留重疊與孔洞')
  scatter(ax[1],out.eligible_s0,'#23918c',.3,'S0納入');scatter(ax[1],~out.eligible_s0,'#e67e22',3,'S0未納入且可定位');ax[1].legend(fontsize=8);ax[1].set_title('全45,130候選：3筆缺座標不在圖上')
  scatter(ax[2],out.fixed_district_conflict.fillna(False),'#c0392b',4,'區名衝突869');scatter(ax[2],out.fixed_assignment_status.eq('address_conflict'),'purple',22,'額外地址衝突2');ax[2].legend(fontsize=8);ax[2].set_title('固定界明確衝突；未移動點或重派')
  scatter(ax[3],out.fixed_assignment_status.eq('outside_or_hole'),'#d98d00',16,'界外／孔洞44');ax[3].legend(fontsize=8);ax[3].set_title('有效Point卻無候選；3筆缺座標另列統計')
  xmin,ymin,xmax,ymax=self.city.buffer(1500).bounds
  for aa in ax:aa.set_xlim(xmin,xmax);aa.set_ylim(ymin,ymax)
  finish(fig,'fixed_assignment_quality.png')
  fig,axes=plt.subplots(1,3,figsize=(18,6))
  q=self.selection_district.query("district_basis=='original'").pivot(index='district',columns='year',values='s0_rate');q.plot.bar(ax=axes[0]);axes[0].set_ylim(0,1);axes[0].set_ylabel('S0有效數／原區名候選數');axes[0].set_title('原始行政區保守配對保留率');axes[0].tick_params(axis='x',rotation=60)
  for year in [2024,2025]:
   z=out[out.source_year.eq(year)&out.fixed_district_conflict.fillna(False)].fixed_distance_to_original_district_m.dropna();axes[1].hist(np.log10(z+1),bins=30,alpha=.5,label=str(year))
  axes[1].axvline(np.log10(101),color='red',ls='--',label='100m');axes[1].legend(fontsize=8);axes[1].set_xlabel('log10(距原區幾何m＋1)');axes[1].set_title('區名衝突距離；不作重新指派門檻')
  boundary(axes[2]);scatter(axes[2],out.geometry_village_or_status_changed,'#d35400',3);axes[2].set_title('歷史界改變里別／狀態：544＋585筆')
  finish(fig,'district_retention_distance_history_changes.png')
  fig,axes=plt.subplots(1,3,figsize=(17,6))
  for aa,year in zip(axes[:2],[2024,2025]):
   z=self.village_counts[self.village_counts.year.eq(year)].set_index('village_id').reindex(self.ids);view=g.copy();view['observed']=z.observed_assigned_count_s0.to_numpy();view.plot(column='observed',cmap='viridis',legend=True,ax=aa,legend_kwds={'label':'S0已觀測配對事故筆數'});aa.set_axis_off();aa.set_title(str(year)+'：保留全部456里，0非真實無事故')
  z=self.village_counts.groupby('village_id').geometry_count_difference.sum().reindex(self.ids);view=g.copy();view['difference']=z.to_numpy();limit=max(1,int(abs(z).max()));view.plot(column='difference',cmap='RdBu_r',vmin=-limit,vmax=limit,legend=True,ax=axes[2],legend_kwds={'label':'兩年S3－S1觀測事故數差'});axes[2].set_axis_off();axes[2].set_title('歷史／固定幾何配對逐里差；非顯著性')
  finish(fig,'village_observed_assignment_counts.png')
  fig,axes=plt.subplots(1,2,figsize=(17,6))
  for year in [2024,2025]:
   for included in [True,False]:
    label=str(year)+(' S0納入' if included else ' S0未納入')
    z=self.selection_distributions.query("variable=='hour' and year==@year and s0_included==@included").copy();z['hour']=pd.to_numeric(z.category,errors='coerce');z=z.dropna(subset=['hour']).sort_values('hour');axes[0].plot(z.hour,z.share_of_valid,label=label,ls='-' if included else '--')
    z=self.selection_features.query('year==@year and s0_included==@included').set_index('feature').reindex(FEATURES);axes[1].plot(range(9),z.True_share_of_valid,marker='o',label=label,ls='-' if included else '--')
  axes[0].set_xlabel('來源事故小時');axes[0].set_ylabel('該納入組有效小時分布比例');axes[0].set_title('S0選擇性排除診斷：小時分布');axes[0].legend(fontsize=8)
  axes[1].set_xticks(range(9),FEATURES,rotation=55,ha='right');axes[1].set_ylabel('各特徵True／該組各自有效N');axes[1].set_title('缺失另列；差異不作推論或改S0規則');axes[1].legend(fontsize=8)
  finish(fig,'s0_selection_descriptive_checks.png')
  self.summary['diagnostic_png_count']=4

 def contract(self,kind):
  base=kind=='base';path='data/processed/taipei_village_base.csv' if base else 'data/processed/taipei_crash_spatial_assignment_2024_2025.csv'
  doc='data/processed/taipei_village_base_documentation.ipynb' if base else 'data/processed/taipei_crash_spatial_assignment_2024_2025_documentation.ipynb'
  return {'unit':'2.2','created_at':'2026-11-26','dataset_path':path,'role':'geographic_base' if base else 'spatial_assignment','observation_unit':'one fixed research village' if base else 'one original Unit2.1 candidate accident, all retained','expected_rows':456 if base else 45130,'producer':'data/code/prepare_taipei_village_base_and_crash_spatial_assignment.ipynb','helper':'data/code/unit22_spatial_support.py','documentation':doc,'source_inputs':self.bindings,'csv':CSV_RULES,'columns':list((self.base_defs if base else self.assignment_defs).values()),'crs':{'fixed_source':'EPSG:3826','history_source':'EPSG:3824','accident_source':'EPSG:4326 working assumption; source datum uncertified','measurement':'EPSG:3826 metre; areas m² and km²'},'id_namespaces':{'village_id':'fixed CPTVID 10 digits, string','population_code':'existing crosswalk 11 digits, string','historical_boundary_code':'VILLCODE 11 digits, string; join through existing population_code crosswalk','record_id':'unchanged Unit2.1 research ID, not official unique event'},'geometry_quality':self.summary['geometry_quality'],'historical_sources':self.histinfo,'assignment_specifications':{'s0':'PRIMARY: fixed geometry unique within=covered_by same sole village; original district readable and consistent; no explicit address/spatial conflict','s1':'SENSITIVITY: fixed geometry unique only; district/address conflicts retained','s2':'SENSITIVITY: source-year historical boundary plus same conservative tests as S0','s3':'SENSITIVITY: source-year historical geometry unique only'},'assignment_priority':STATES,'geometry_states':GEOMETRY_STATES,'NA_comparison':'both NA=equally unassigned; one NA vs ID=different eligibility; two valid IDs compare strings; geometric village change requires both valid','area_denominators':'S0/S1 use fixed original village_area; historical geographic density S2/S3 uses corresponding historical_area_year. An explicitly labelled common fixed-denominator comparison is different. No density constructed in Unit2.2.','limitations':['historical year editions are snapshots, not every-day legal validity','no fixed geometry snap/repair/hole fill/overlap removal','provisional_match Tangbu accepted for all main analyses; original names and status retained','no nearest village, external coordinate correction or geocoding','no final village-level Dataset A/B1/B2/B3/C or final low-count threshold','zero observed assigned accidents is not proof of no real accidents','description and technical acceptance do not imply DA/PM human review']}

 def serialized_outputs(self):
  result={}
  for kind,frame,stem in [('base',self.base,'taipei_village_base'),('assignment',self.assignment,'taipei_crash_spatial_assignment_2024_2025')]:
   contract=self.contract(kind)
   assert list(frame)==[f['name'] for f in contract['columns']]
   for field in contract['columns']:assert str(frame[field['name']].dtype)==field['dtype']
   assert not frame.select_dtypes(include='string').eq('__MISSING__').any(axis=None)
   result['data/processed/'+stem+'.csv']=frame.to_csv(index=False,na_rep='__MISSING__',lineterminator=chr(10)).encode('utf-8-sig')
   result['data/processed/'+stem+'_schema.json']=(json.dumps(contract,ensure_ascii=False,indent=2)+chr(10)).encode('utf-8')
  return result

 def export_and_verify(self):
  assert 'benchmark_comparison' in self.summary,'Run reconciliation before export'
  self.validate_memory();bodies=self.serialized_outputs();assert bodies==self.serialized_outputs(),'Non-deterministic serialization'
  for relative,body in bodies.items():
   p=(self.root/relative).resolve();assert p.is_relative_to(self.root/'data/processed') and relative not in self.bindings
   if p.exists():assert p.read_bytes()==body,'Existing output differs; stop rather than overwrite '+relative
   else:
    with p.open('xb') as f:f.write(body)
   self.outputs[relative]={'path':relative,'bytes':p.stat().st_size,'sha256':sha(p)}
  for kind,frame,stem in [('base',self.base,'taipei_village_base'),('assignment',self.assignment,'taipei_crash_spatial_assignment_2024_2025')]:
   con=json.loads((self.root/'data/processed'/f'{stem}_schema.json').read_text(encoding='utf-8'))
   saved=load_csv(self.root/'data/processed'/f'{stem}.csv',con)
   pd.testing.assert_frame_equal(frame,saved,check_dtype=True,check_exact=True)
  saved_base=load_csv(self.root/'data/processed/taipei_village_base.csv',self.contract('base'))
  saved_assignment=load_csv(self.root/'data/processed/taipei_crash_spatial_assignment_2024_2025.csv',self.contract('assignment'))
  validate_saved_pair(saved_base,saved_assignment,self.accidents)
  for relative in self.bindings:self.file(relative)
  assert self.fixed.geometry.to_wkb().equals(self.fixed_wkb)
  self.summary.update(status='passed',outputs=self.outputs,base_shape=list(self.base.shape),assignment_shape=list(self.assignment.shape),formal_datasets=2,formal_village_feature_datasets=0,all_source_hashes_unchanged=True,exact_roundtrip_values_and_dtypes=True,human_review='Codex assisted execution; DA acceptance / PM review pending')
  (self.temp/'processing_summary.json').write_text(json.dumps(self.summary,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
  show('兩正式CSV及兩schema：磁碟保存／獨立讀回／版本',pd.DataFrame(self.outputs).T)
  print('正式processed dataset=2；里層級A／B／C=0；完整45,130候選、456里均保留。')
  return self.outputs


def validate_saved_pair(base,assignment,upstream=None):
 """Consumer validation on saved tables; does not run GIS or read raw accidents."""
 assert len(base)==456 and base.village_id.is_unique and base.village_id.notna().all()
 valid_ids=set(base.village_id)
 assert base.village_id.str.fullmatch(r'\d{10}').all() and base.population_code.str.fullmatch(r'\d{11}').all()
 assert base.district_name.nunique()==12 and base.village_area_m2.gt(0).all()
 assert base.source_geometry_crs.eq('EPSG:3826').all() and base.geometry_valid.all()
 sugar=base[base.standard_village_name.eq('糖廍里')];assert len(sugar)==1 and sugar.verification_status.iloc[0]=='provisional_match'
 assert sugar.population_village_name.iloc[0]=='糖?里' and sugar.boundary_village_name.iloc[0]=='糖蔀里'
 for year in [2024,2025]:
  assert base[f'historical_boundary_code_{year}'].str.fullmatch(r'\d{11}').all()
  assert base[f'historical_boundary_code_{year}'].eq(base.population_code).all()
  assert base[f'historical_area_m2_{year}'].gt(0).all()
 assert len(assignment)==45130 and assignment.record_id.is_unique and assignment.record_id.notna().all()
 assert assignment.groupby('source_year').size().to_dict()=={2024:22368,2025:22762}
 for spec in ['s0','s1','s2','s3']:
  assert assignment['eligible_'+spec].equals(assignment['village_id_'+spec].notna().astype('boolean'))
  assert assignment.loc[assignment['eligible_'+spec],'village_id_'+spec].isin(base.village_id).all()
  assert not assignment.loc[assignment.coordinate_missing_flag,'eligible_'+spec].any()
 for low,high in [('s0','s1'),('s2','s3')]:
  assert not (assignment['eligible_'+low]&~assignment['eligible_'+high]).any()
  mask=assignment['eligible_'+low];assert assignment.loc[mask,'village_id_'+low].eq(assignment.loc[mask,'village_id_'+high]).all()
 for family in ['fixed','historical']:
  assert assignment[family+'_assignment_status'].isin(STATES).all() and assignment[family+'_assignment_status'].notna().all()
  unique=assignment[family+'_geometry_unique']
  assert unique.equals(assignment[family+'_geometry_status'].eq('unique_interior').astype('boolean'))
  for pred in ['within','covered_by']:
   ids=assignment[family+'_'+pred+'_candidate_ids'];counts=assignment[family+'_'+pred+'_candidate_count'];codes=assignment[family+'_'+pred+'_original_codes']
   assert ids.notna().equals(assignment.point_valid.astype(bool)) and counts.notna().equals(ids.notna())
   for text,n,original in zip(ids.dropna(),counts[ids.notna()],codes[ids.notna()]):
    values=json.loads(text);raw=json.loads(original);assert values==sorted(set(values)) and len(values)==n==len(raw)
    assert all(v in valid_ids for v in values)
    assert all(re.fullmatch(r'\d{11}' if family=='historical' else r'\d{10}',v) for v in raw)
  assert assignment.loc[unique,family+'_within_candidate_count'].eq(1).all() and assignment.loc[unique,family+'_covered_by_candidate_count'].eq(1).all()
  conservative=unique&assignment[family+'_district_match'].fillna(False)&~assignment[family+'_address_conflict'].fillna(False)
  target='s0' if family=='fixed' else 's2';assert assignment['eligible_'+target].equals(conservative.astype('boolean'))
 assert assignment.coordinate_missing_flag.sum()==3
 for label,left,right in [('geometry','s1','s3'),('conservative','s0','s2')]:
  assert assignment['fixed_historical_'+label+'_assignment_same'].equals(same_optional(assignment['village_id_'+left],assignment['village_id_'+right]))
 if upstream is not None:
  assert set(assignment.record_id)==set(upstream.record_id)
  join=upstream[['record_id','source_year']].merge(assignment[['record_id','source_year']],on='record_id',how='outer',validate='one_to_one',indicator=True)
  assert len(join)==45130 and join['_merge'].eq('both').all() and join.source_year_x.eq(join.source_year_y).all()
  columns=['longitude_candidate','latitude_candidate','coordinate_parse_valid','coordinate_missing_flag','coordinate_x_raw','coordinate_y_raw','source_row_number']
  left=assignment[['record_id',*columns]].set_index('record_id').sort_index();right=upstream[['record_id',*columns]].set_index('record_id').sort_index()
  for name in columns:pd.testing.assert_series_equal(left[name],right[name],check_names=False,check_exact=True)
 return True
