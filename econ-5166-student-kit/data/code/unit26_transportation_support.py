"""Unit2.6: fixed-village transportation snapshots; no exposure/causal claims.

Reuses Unit2.5 schema reader / hashing / full-table display only. Unit1.7
classification, archive inspection and strict point assignment inform this
implementation; no earlier notebook is executed and no prior output is changed.
"""
from pathlib import Path,PurePosixPath
import hashlib,json,itertools,zipfile,re,platform
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely as s
import pyogrio,pyproj
from pyproj import Transformer
from unit25_zoning_support import sha,read_csv,show

STEM='taipei_dataset_b3';HELPER='data/code/unit26_transportation_support.py';PRODUCER='data/code/prepare_taipei_dataset_b3.ipynb'
CORE=['osm_road_density','osm_major_road_ratio','observed_signal_location_density','crosswalk_area_ratio','median_annotated_road_width','mrt_entrance_buffer_500m_ratio','mrt_entrance_density']
RADII=[300,500,800];AREA_ATOL=.1;LENGTH_ATOL=.1
GROUPS={'major':['motorway','trunk','primary','motorway_link','trunk_link','primary_link'],
 'secondary':['secondary','tertiary','secondary_link','tertiary_link'],
 'local':['unclassified','residential','living_street'],'service':['service','busway'],
 'walking':['pedestrian','footway','path','steps','bridleway'],'cycling':['cycleway'],
 'other_nonmotor_or_unconfirmed':['track','track_grade1','track_grade2','track_grade3','track_grade4','track_grade5','unknown']}
MAPPING={v:k for k,values in GROUPS.items() for v in values}
INCLUDED=set(sum([GROUPS[k] for k in ['major','secondary','local','service']],[]));MAJOR=set(GROUPS['major'])
CLASS_DESCRIPTIONS={'motorway':'高速道路','trunk':'重要幹道','primary':'主要道路','secondary':'次要道路','tertiary':'第三級道路',
 'unclassified':'較小地方道路，並非未知碼','residential':'住宅區道路','living_street':'行人優先街道','pedestrian':'行人專用街道',
 'busway':'公車專用道路','service':'出入建物或停車場等服務道路','track':'農林等產業道路','bridleway':'騎馬路徑','cycleway':'自行車道',
 'footway':'步行路徑','path':'未指定用途路徑','steps':'階梯','unknown':'未定道路或路徑種類'}
for key in ['motorway','trunk','primary','secondary','tertiary']:CLASS_DESCRIPTIONS[key+'_link']=CLASS_DESCRIPTIONS[key]+'連接匝道'
for i in range(1,6):CLASS_DESCRIPTIONS['track_grade'+str(i)]='產業道路路面等級'+str(i)
FORMAT_EVIDENCE={'url':'https://download.geofabrik.de/osm-data-in-gis-formats-free.pdf','document_version':'2026-04-02','reviewed_at':'2026-11-27',
 'scope':'general field/class definitions, not certification of all 2025 export semantics; actual PRJ/fields/fclass read from frozen 2025 ZIP',
 'previous_capture':'Unit1.7 geofabrik_road_fields_web.json contains an access error; retained unchanged, not treated as a successful PDF archive',
 'research_major':'Unit1.7 narrow six-class major group retained; official document major heading also includes secondary/tertiary, which are not silently added here'}
CSV={'encoding':'utf-8-sig','line_terminator':'LF','missing_sentinel':'__MISSING__','keep_default_na':False,'boolean_values':['True','False'],'original_empty_strings':'preserved'}
BLOCKED={'intersection_density':'缺完整節點／轉向／立體拓樸，平面交叉不當實體路口',
 'complete_topological_intersection_count':'免費線圖層缺完整節點與立體道路拓樸',
 'complete_crosswalk_count':'一Polygon不是完整設施','crosswalk_length_density':'標線面構件不提供可靠穿越長度',
 'length_weighted_road_width':'尺寸線不是縱向道路權重','narrow_road_length_ratio':'無可靠縱向分母與窄寬門檻',
 'wide_road_length_ratio':'無可靠縱向分母與窄寬門檻',
 'marked_sidewalk_density':'混合標線未驗證人行道子集','complete_signalized_intersection_count':'位置紀錄未認證實體路口單位',
 'marked_sidewalk_area_ratio':'混合標線未驗證人行道子集，不能計算正式面積或覆蓋率',
 'traffic_volume_or_VKT':'沒有交通流量或行駛公里暴露資料','walking_network_accessibility':'直線緩衝不是步行路網'}
LIMITATIONS=['B3僅分群後外部環境比較，不直接加入Dataset A主要分群；D原版為主，D改良版／Prediction暫緩',
 'OSM指定類線表示，非完整實體中心線、道路容量、流量或VKT；平行分離車道保留，平面union可能合併不同立體層級',
 '主要道路是Unit1.7研究六類分組，不是臺灣法定道路等級或交通量占比',
 '號誌為已觀測唯一座標位置，不是完整實體號誌路口、燈頭或管制能力；LCS單位未認證，包含／排除另報',
 '行穿僅標線面聯集，不是完整設施數、穿越長度、配置完整性或安全程度',
 '計畫路寬為尺寸標註樣本，不是實測可通行寬度、車道數或長度代表樣本；中點唯一歸里為明示操作假設',
 'MRT為2026出入口快照，不是2024／2025完整存量；入口數不是站數、搭乘人次或行人暴露',
 '300／500／800m為EPSG3826直線buffer候選；500m不是已認證通用步行門檻，非路網、時間或通勤人流',
 '來源日期語義不同，沒有同時點完整設施普查或兩套年度獨立觀測；不得冒充事前環境／預測資料',
 '觀測0不證明現實不存在；無路寬樣本為NA，Blocked不填0，處理失敗保留ID與NA，不完整案例刪里',
 '固定原里界孔洞／微量重疊不修補，城市union與逐里和不同；source snapshot completeness unverified',
 'B3不提供交通暴露、真正事故風險或因果識別；未作正式EDA／模型／推論或最終整合',
 '本輪Codex協助；DE交付確認、DA驗收、PM審查及學生本人Git提交待完成']

def verify(root,bindings):
 for rel,h in bindings.items():assert (root/rel).is_file() and sha(root/rel)==h,('INPUT HASH MISMATCH',rel)
def geometry_digest(geoms):
 h=hashlib.sha256()
 for b in s.to_wkb(np.asarray(geoms,dtype=object)):
  value=b'' if b is None else bytes(b);h.update(len(value).to_bytes(8,'little'));h.update(value)
 return h.hexdigest()

def components(g,kind):
 if g is None or g.is_empty:return []
 if (kind=='line' and g.geom_type in ['LineString','LinearRing']) or (kind=='polygon' and g.geom_type=='Polygon'):return [g]
 if hasattr(g,'geoms'):return [p for child in g.geoms for p in components(child,kind)]
 return []
def union_parts(values,kind):
 parts=[p for g in values for p in components(g,kind)]
 return s.union_all(parts) if parts else (s.LineString() if kind=='line' else s.Polygon())
def clipped_measure(geoms,domain,kind='length'):
 geoms=np.asarray(geoms,dtype=object);s.prepare(domain)
 inside=s.covers(domain,geoms);cross=s.intersects(domain,geoms)&~inside;values=np.zeros(len(geoms),float)
 measure=s.length if kind=='length' else s.area
 values[inside]=measure(geoms[inside]);values[cross]=measure(s.intersection(geoms[cross],domain))
 return values
def point_assign(points,villages):
 points=np.asarray(points,dtype=object);tree=s.STRtree(villages)
 covered=tree.query(points,predicate='covered_by');within=tree.query(points,predicate='within')
 c=[[] for _ in points];w=[[] for _ in points]
 for i,j in covered.T:c[int(i)].append(int(j))
 for i,j in within.T:w[int(i)].append(int(j))
 assigned=np.array([a[0] if len(a)==len(b)==1 and a==b else -1 for a,b in zip(c,w)],dtype=int)
 status=np.array(['unique_interior' if i>=0 else 'outside' if not a else 'boundary_or_multiple' for i,a in zip(assigned,c)],dtype=object)
 return assigned,status,np.array([len(v) for v in c]),np.array([len(v) for v in w])

class Context:
 def __init__(self,root,bindings,handoff_bindings,project_context=None):
  self.root=Path(root).resolve();self.temp=self.root/'data/temp/unit26_processing';self.temp.mkdir(parents=True,exist_ok=True)
  self.bindings=bindings;self.handoff_bindings=handoff_bindings;verify(self.root,bindings);verify(self.root,handoff_bindings)
  self.config=json.loads((self.root/'data/code/unit17_validation_config.json').read_text(encoding='utf-8'))
  self.raw_items={r['family']:r for r in self.config['raw_inventory'] if r['family'] in ['osm','signals','crossings','road_width','sidewalk','mrt']}
  for item in self.raw_items.values():assert bindings[item['path']]==item['sha256']
  bcontract=json.loads((self.root/'data/processed/taipei_village_base_schema.json').read_text(encoding='utf-8'))
  self.base=read_csv(self.root/'data/processed/taipei_village_base.csv',bcontract).sort_values('village_id').reset_index(drop=True)
  assert self.base.shape==(456,41) and self.base.village_id.is_unique and self.base.district_name.nunique()==12
  b=gpd.read_file(self.root/'data/raw/G97_A_CAVLGE_P.shp',encoding='utf-8',engine='pyogrio')
  assert len(b)==456 and b.crs.to_epsg()==3826 and b.CPTVID.is_unique
  self.boundary=b.set_index('CPTVID').loc[self.base.village_id].reset_index();self.bwkb=self.boundary.geometry.to_wkb().copy()
  self.v=np.asarray(self.boundary.geometry.array,dtype=object);self.area=self.base.village_area_m2.astype(float).to_numpy();self.area_km2=self.base.village_area_km2.astype(float).to_numpy()
  assert s.is_valid(self.v).all() and (self.area>0).all()
  np.testing.assert_allclose(s.area(self.v),self.area,rtol=0,atol=1e-6)
  self.city=s.union_all(self.v);self.study=self.city.buffer(2000);self.tree=s.STRtree(self.v)
  self.districts={d:s.union_all(self.v[self.base.district_name.eq(d).to_numpy()]) for d in sorted(self.base.district_name.unique())}
  self.project_context=project_context
  self.to3826=Transformer.from_crs(4326,3826,always_xy=True);self.extracted=[];self.sources={};self.layers={};self.failures={};self.arrays={};self.crs={};self.diagnostics={};self.original_geometry_hashes={}
  self.facts={'fixed_villages':456,'districts':12,'city_union_km2':self.city.area/1e6,'village_area_sum_km2':float(self.area.sum()/1e6),
   'versions':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'geopandas':gpd.__version__,'shapely':s.__version__,'GEOS':s.geos_version_string,'pyproj':pyproj.__version__,'pyogrio':pyogrio.__version__},
   'working_crs':'EPSG:3826','area_tolerance_m2':AREA_ATOL,'length_tolerance_m':LENGTH_ATOL,'raw_source_count':6,'human_acceptance':'Codex assisted; DE / DA / PM pending'}
  print('Input hashes, fixed 456 original villages and formal area denominators passed',flush=True)

 def extract(self,family,member):
  item=self.raw_items[family];path=self.root/item['path'];stem=member[:-4]
  with zipfile.ZipFile(path) as z:
   for info in z.infolist():
    q=PurePosixPath(info.filename.replace('\\','/'))
    assert not q.is_absolute() and '..' not in q.parts and ':' not in info.filename
    assert ((info.external_attr>>16)&0o170000)!=0o120000
   names=[n for n in z.namelist() if n.startswith(stem+'.') and n[len(stem):].lower() in ['.shp','.shx','.dbf','.prj','.cpg']]
   assert {'.shp','.shx','.dbf','.prj'}.issubset({n[len(stem):].lower() for n in names})
   target=(self.temp/'extracted'/item['sha256'][:12]/hashlib.sha256(member.encode('utf-8')).hexdigest()[:8]).resolve();target.mkdir(parents=True,exist_ok=True)
   for name in names:
    out=(target/PurePosixPath(name).name).resolve();assert out.is_relative_to(target)
    h=hashlib.sha256()
    with z.open(name) as src:
     for chunk in iter(lambda:src.read(4*1024*1024),b''):h.update(chunk)
    digest=h.hexdigest()
    if not out.exists() or sha(out)!=digest:
     with z.open(name) as src,out.open('wb') as dst:
      for chunk in iter(lambda:src.read(4*1024*1024),b''):dst.write(chunk)
    assert sha(out)==digest
    info=z.getinfo(name);self.extracted.append({'family':family,'archive':item['path'],'member':name,'bytes':info.file_size,'crc32':f'{info.CRC:08x}','sha256':digest,'temp_path':out.relative_to(self.root).as_posix()})
  return target/PurePosixPath(member).name

 def load(self):
  for family in ['osm','crossings','road_width']:
   item=self.raw_items[family];members=['gis_osm_roads_free_1.shp'] if family=='osm' else [m['member'] for m in item['members'] if m['member'].endswith('.shp')]
   frames=[];details=[]
   for member in members:
    path=self.extract(family,member);info=pyogrio.read_info(path);kwargs={}
    if family=='osm':kwargs['bbox']=tuple(gpd.GeoSeries([self.study],crs=3826).to_crs(4326).total_bounds)
    f=gpd.read_file(path,engine='pyogrio',fid_as_index=True,**kwargs);epsg=f.crs.to_epsg() if f.crs else None
    assert epsg==(4326 if family=='osm' else 3826),(family,member,str(f.crs))
    details.append({'member':member,'total_features':int(info['features']),'loaded':len(f),'raw_crs':str(f.crs),'raw_bounds':f.total_bounds.tolist(),'types':f.geom_type.value_counts().to_dict()})
    f['_source_row']=f.index.to_numpy()+1;f['_source_member']=member
    f['_source_id']=[item['sha256'][:12]+':'+hashlib.sha256(member.encode()).hexdigest()[:8]+':'+str(i) for i in f['_source_row']]
    f['_source_original_geometry']=pd.Series(np.asarray(f.geometry.array,dtype=object),index=f.index,dtype=object)
    f=f.to_crs(3826);frames.append(f)
   g=gpd.GeoDataFrame(pd.concat(frames,ignore_index=True),geometry='geometry',crs=3826)
   ok=g.geometry.notna()&~g.geometry.is_empty&g.geometry.is_valid
   allowed=g.geom_type.isin(['LineString','MultiLineString']) if family in ['osm','road_width'] else g.geom_type.isin(['Polygon','MultiPolygon'])
   g['_geometry_valid']=ok&allowed;self.layers[family]=g
   self.crs[family]={'raw':'EPSG:4326' if family=='osm' else 'EPSG:3826','work':'EPSG:3826','evidence_grade':'A metadata','evidence':'actual archive PRJ; coordinate accuracy itself not certified'}
   self.sources[family]={'members':details,'loaded_rows':len(g),'invalid_or_empty_or_wrong_type':int((~g._geometry_valid).sum()),'raw_WKB_duplicate_rows':int(g.geometry.to_wkb().duplicated(keep=False).sum()),'types':g.geom_type.value_counts().to_dict()}
   self.original_geometry_hashes[family]=geometry_digest(g['_source_original_geometry'])
   self.sources[family]['original_geometry_WKB_digest']=self.original_geometry_hashes[family]
   print('Loaded',family,len(g),'invalid',int((~g._geometry_valid).sum()),flush=True)
  for family in ['signals','mrt']:
   item=self.raw_items[family];f=pd.read_csv(self.root/item['path'],encoding='cp950',sep='\t' if family=='signals' else ',',dtype='string',keep_default_na=False)
   loncol,latcol=('WGS經度座標','WGS緯度座標') if family=='signals' else ('經度','緯度')
   lon=pd.to_numeric(f[loncol],errors='coerce').to_numpy(dtype=float,na_value=np.nan);lat=pd.to_numeric(f[latcol],errors='coerce').to_numpy(dtype=float,na_value=np.nan)
   valid=np.isfinite(lon)&np.isfinite(lat)&(abs(lon)<=180)&(abs(lat)<=90);geoms=np.full(len(f),None,dtype=object)
   x,y=self.to3826.transform(lon[valid],lat[valid]);projected=np.isfinite(x)&np.isfinite(y)
   good_ids=np.flatnonzero(valid)[projected];geoms[good_ids]=s.points(np.asarray(x)[projected],np.asarray(y)[projected])
   f['_longitude']=lon;f['_latitude']=lat;f['_source_row']=np.arange(len(f))+1;f['_source_id']=[item['sha256'][:12]+':'+str(i+1) for i in range(len(f))]
   f['_coordinate_valid']=np.array([g is not None and not g.is_empty and g.is_valid for g in geoms]);f['_zero_coordinate_pair']=(lon==0)&(lat==0)
   self.layers[family]=gpd.GeoDataFrame(f,geometry=geoms,crs=3826)
   self.crs[family]={'raw':'EPSG:4326 working interpretation','work':'EPSG:3826','evidence_grade':'B working convention','evidence':'Unit1.7 source-specific coordinate fields and official page; no file-specific datum certification'}
   self.sources[family]={'loaded_rows':len(f),'valid_world_coordinates':int(valid.sum()),'valid_projected_points':len(good_ids),'missing_or_invalid_coordinates':int((~valid).sum()),'projection_failure':int(valid.sum()-len(good_ids)),'zero_coordinate_pairs':int(f._zero_coordinate_pair.sum()),'encoding':'CP950 strict','separator':'TAB' if family=='signals' else 'comma'}
  self.sources['sidewalk']={'processing_status':'Blocked','features_not_computed':True,'existing_verified_rows':43016,'existing_licodes':30,'existing_known_crossing_code_rows':20494,'existing_crossing_key_overlap':19643,'evidence':'Unit1.7 notebook/helper/config, read only; no mixed-layer extraction or new classification'}
  return self.sources

 def measure(self,g,kind,source):
  result=np.full(456,np.nan)
  for district,shape in self.districts.items():
   ids=np.flatnonzero(self.base.district_name.eq(district).to_numpy())
   try:
    clip=g.intersection(shape);xs=s.intersection(self.v[ids],clip)
    result[ids]=s.area(xs) if kind=='area' else s.length(xs)
   except s.errors.GEOSException:
    for i in ids:
     try:result[i]=self.v[i].intersection(g).area if kind=='area' else self.v[i].intersection(g).length
     except s.errors.GEOSException as error:self.failures.setdefault(source,{}).setdefault(int(i),[]).append(str(error))
  check=np.array([0,100,200,300,455]);direct=s.intersection(self.v[check],g)
  np.testing.assert_allclose(result[check],s.area(direct) if kind=='area' else s.length(direct),rtol=1e-10,atol=.01)
  return result

 def road_features(self):
  roads=self.layers['osm'];roads['_research_group']=roads.fclass.map(MAPPING).fillna('unmapped_source_class')
  roads['_included_motor_candidate']=roads.fclass.isin(INCLUDED);roads['_major_candidate']=roads.fclass.isin(MAJOR)
  regional=roads.geometry.intersects(self.study);selected=roads.loc[roads._geometry_valid&roads._included_motor_candidate&regional].copy()
  self.selected_roads=selected;geom=np.asarray(selected.geometry.array,dtype=object)
  self.road_classification=[]
  for cls,frame in roads.groupby('fclass',dropna=False):
   name=str(cls);self.road_classification.append({'fclass':name,'source_definition':CLASS_DESCRIPTIONS.get(name,'未取得來源類別定義'),
    'research_group':MAPPING.get(name,'unmapped_source_class'),'included':name in INCLUDED,'major':name in MAJOR,
    'inclusion_reason':'Unit1.7機動車候選研究規格' if name in INCLUDED else '步行／自行車／產業道路或未知類別，依Unit1.7不納主要機動候選',
    'bbox_source_records':len(frame),'regional_records':int(regional[frame.index].sum()),'source_documentation':FORMAT_EVIDENCE['url']})
  pair=self.tree.query(self.v,predicate='intersects');pair=pair[:,pair[0]<pair[1]]
  edges=[[] for _ in range(456)];overlaps=[]
  for i,j in pair.T:
   shared=union_parts([self.v[i].boundary.intersection(self.v[j].boundary)],'line')
   if shared.length>0:edges[int(i)].append(shared);edges[int(j)].append(shared)
   overlaps.append(self.v[i].intersection(self.v[j]))
  self.shared_edges=[union_parts(e,'line') for e in edges];shared_union=union_parts(self.shared_edges,'line');multi_coverage=s.union_all(overlaps)
  self.village_pair_intersections=overlaps
  tree=s.STRtree(geom);q=tree.query(self.v,predicate='intersects');by=[[] for _ in self.v]
  for i,j in q.T:by[int(i)].append(int(j))
  data={k:np.full(456,np.nan) for k in ['road','major','inclusive','shared','major_inclusive','major_shared','major_other_overlap','raw_clipped_sum','duplicate_removed','source_records']}
  major_mask=selected._major_candidate.to_numpy();rows=[]
  for i,v in enumerate(self.v):
   ids=by[i]
   try:
    clips=s.intersection(geom[ids],v) if ids else [];u=union_parts(clips,'line')
    mu=union_parts([g for g,j in zip(clips,ids) if major_mask[j]],'line');ou=union_parts([g for g,j in zip(clips,ids) if not major_mask[j]],'line')
    shared=u.intersection(self.shared_edges[i]);effective=union_parts([u.difference(self.shared_edges[i])],'line')
    major_effective=union_parts([mu.difference(self.shared_edges[i])],'line')
    values={'road':effective.length,'major':major_effective.length,'inclusive':u.length,'shared':shared.length,'major_inclusive':mu.length,
     'major_shared':mu.intersection(self.shared_edges[i]).length,'major_other_overlap':mu.intersection(ou).length,
     'raw_clipped_sum':sum(g.length for g in clips),'duplicate_removed':sum(g.length for g in clips)-u.length,'source_records':sum(g.length>0 for g in clips)}
    for k,val in values.items():data[k][i]=val
   except s.errors.GEOSException as error:self.failures.setdefault('osm',{}).setdefault(i,[]).append(str(error))
  whole=union_parts(geom,'line');major=union_parts(geom[major_mask],'line');other=union_parts(geom[~major_mask],'line');city=whole.intersection(self.city);city_major=major.intersection(self.city)
  raw_city=clipped_measure(geom,self.city);normalized=s.to_wkb(s.normalize(geom))
  stratified=[];layer_unions=[]
  for layer,g in selected.groupby('layer',dropna=False):
   u=union_parts(np.asarray(g.geometry.array,dtype=object),'line');layer_unions.append(u)
   stratified.append({'layer':str(layer),'records':len(g),'represented_union_city_length_m':u.intersection(self.city).length})
  crosslevel=union_parts([a.intersection(b) for a,b in itertools.combinations(layer_unions,2)],'line')
  self.road_direction_table=selected.groupby(['layer','bridge','tunnel','oneway'],dropna=False).size().rename('source_records').reset_index()
  self.arrays['osm']=data;self.road_union=whole;self.major_union=major
  self.sources['osm'].update({'national_source_features':self.sources['osm']['members'][0]['total_features'],'bbox_loaded':len(roads),'study_related':int(regional.sum()),
   'regional_included_lines':len(selected),'included_fclasses':sorted(set(selected.fclass)),'unknown_mapping_rows':int(roads._research_group.eq('unmapped_source_class').sum()),
   'selected_raw_WKB_duplicate_rows':int(pd.Series(s.to_wkb(geom)).duplicated(keep=False).sum()),'selected_normalized_geometry_duplicate_rows':int(pd.Series(normalized).duplicated(keep=False).sum()),
   'osm_id_duplicate_rows':int(selected.osm_id.duplicated(keep=False).sum()),'selected_reference_length_sum_m':float(s.length(geom).sum()),'selected_line_union_length_m':whole.length,
   'city_road_length_m':city.length,'city_major_length_m':city_major.length,'city_raw_clipped_length_sum_m':float(raw_city.sum()),'city_duplicate_overlap_removed_m':float(raw_city.sum()-city.length),
   'city_major_other_overlap_m':major.intersection(other).intersection(self.city).length,'city_cross_layer_exact_overlap_m':crosslevel.intersection(self.city).length,
   'layer_strata':stratified,'city_shared_boundary_road_length_m':city.intersection(shared_union).length,
   'city_multi_village_coverage_length_m':city.intersection(multi_coverage).length,'village_road_effective_sum_m':float(np.nansum(data['road'])),
   'village_inclusive_sum_m':float(np.nansum(data['inclusive'])),'village_shared_sum_m':float(np.nansum(data['shared'])),
   'inclusive_sum_minus_city_m':float(np.nansum(data['inclusive'])-city.length),'effective_sum_minus_city_m':float(np.nansum(data['road'])-city.length),
   'boundary_policy':'exclude exact shared original-village boundary line segments from all primary village road lengths; retain inclusive and unallocated shared lengths; no first-village allocation',
   'format_evidence':FORMAT_EVIDENCE})
  good=np.isfinite(data['road']);assert (data['road'][good]>=0).all() and (data['major'][good]>=0).all()
  assert (data['major'][good]<=data['road'][good]+LENGTH_ATOL).all()
  np.testing.assert_allclose((data['road']+data['shared'])[good],data['inclusive'][good],rtol=0,atol=LENGTH_ATOL)
  print('Road unions and actual 456-village clipping passed; city km',city.length/1000,flush=True)
  return self.sources['osm']

 def assign_source_points(self,family):
  g=self.layers[family];valid=g._coordinate_valid.to_numpy();ids=np.flatnonzero(valid)
  assigned=np.full(len(g),-1,dtype=int);status=np.full(len(g),'missing_or_invalid_coordinate',dtype=object);nc=np.zeros(len(g),int);nw=nc.copy()
  a,st,c,w=point_assign(np.asarray(g.geometry.array,dtype=object)[ids],self.v);assigned[ids]=a;status[ids]=st;nc[ids]=c;nw[ids]=w
  g['_assigned_index']=assigned;g['_assignment_status']=status;g['_covered_matches']=nc;g['_within_matches']=nw
  g['_village_id']=pd.Series([str(self.base.village_id.iloc[i]) if i>=0 else pd.NA for i in assigned],dtype='string')
  self.sources[family].update({'unique_assigned':int((assigned>=0).sum()),'outside':int(((status=='outside')&valid).sum()),
   'boundary_or_multiple':int((status=='boundary_or_multiple').sum()),'unassigned_invalid':int((~valid).sum())})
  assert int((assigned>=0).sum())+int((status=='outside').sum())+int((status=='boundary_or_multiple').sum())+int((~valid).sum())==len(g)
  return assigned,status

 def signal_features(self):
  g=self.layers['signals'];assigned,status=self.assign_source_points('signals');valid=g._coordinate_valid.to_numpy()
  g['_name_readable']=g['地點'].str.strip().ne('');g['_explicit_test']=g['地點'].str.contains('機房測試用',regex=False)
  g['_lcs']=g['地點'].str.contains('LCS',case=False,regex=False);g['_source_district_normalized']=g['行政區'].str.strip()
  g['_district_recognized']=g._source_district_normalized.isin(set(self.base.district_name))
  spatial_district=pd.Series([str(self.base.district_name.iloc[i]) if i>=0 else '' for i in assigned],dtype='string')
  g['_district_match']=(assigned>=0)&g._district_recognized&g._source_district_normalized.eq(spatial_district)
  g['_district_conflict']=(assigned>=0)&g._district_recognized&~g._source_district_normalized.eq(spatial_district)
  original=['流水號','地點','行政區','WGS經度座標','WGS緯度座標'];g['_exact_duplicate_record']=g[original].duplicated(keep=False)
  g['_same_coordinate']=False;g['_same_coordinate_different_names']=False;g['_coordinate_group_district_conflict']=False
  vectors={k:np.zeros(456,dtype=int) for k in ['raw_assigned_records','main_records','main_locations','geometry_locations','main_without_lcs_locations','geometry_without_lcs_locations',
   'test_records','lcs_records','district_conflict_records','district_unknown_records','duplicate_coordinate_records','multi_name_location_groups','conflicting_district_location_groups']}
  rows=[]
  for (lon,lat),part in g.loc[valid].groupby(['_longitude','_latitude'],sort=True,dropna=False):
   ids=part.index.to_numpy();a=np.unique(assigned[ids]);unique=len(a)==1 and a[0]>=0
   vi=int(a[0]) if unique else -1
   basic=part.loc[part._name_readable&~part._explicit_test];nontest_nonlcs=basic.loc[~basic._lcs]
   known_districts=sorted(set(part.loc[part._district_recognized,'_source_district_normalized']))
   many_names=part['地點'].nunique()>1;many_districts=len(known_districts)>1
   g.loc[ids,'_same_coordinate']=len(part)>1;g.loc[ids,'_same_coordinate_different_names']=many_names
   g.loc[ids,'_coordinate_group_district_conflict']=many_districts
   A=bool(unique and len(basic)>0 and basic._district_recognized.all() and basic._district_match.all())
   B=bool(unique and len(basic)>0)
   no_lcs=bool(len(nontest_nonlcs)>0)
   location_id=self.raw_items['signals']['sha256'][:12]+':location:'+hashlib.sha256((float(lon).hex()+','+float(lat).hex()).encode()).hexdigest()[:16]
   row={'location_id':location_id,'longitude':float(lon),'latitude':float(lat),'source_records':len(part),'source_ids_json':json.dumps(part._source_id.tolist(),ensure_ascii=False),
    'names_json':json.dumps(sorted(set(part['地點'])),ensure_ascii=False),'source_districts_json':json.dumps(sorted(set(part['行政區'])),ensure_ascii=False),
    'unique_interior_assignment':unique,'village_id':str(self.base.village_id.iloc[vi]) if vi>=0 else None,
    'same_coordinate_records':len(part)>1,'different_names':bool(many_names),'conflicting_recognized_districts':many_districts,
    'unknown_district_member':bool((~basic._district_recognized).any()),'explicit_test_records':int(part._explicit_test.sum()),'lcs_records':int(part._lcs.sum()),
    'main_A':A,'geometry_B':B,'main_A_without_LCS':A and no_lcs,'geometry_B_without_LCS':B and no_lcs,'basic_records':len(basic)}
   rows.append(row)
   if vi>=0:
    values={'raw_assigned_records':len(part),'main_records':len(basic) if A else 0,'main_locations':int(A),'geometry_locations':int(B),
     'main_without_lcs_locations':int(A and no_lcs),'geometry_without_lcs_locations':int(B and no_lcs),'test_records':int(part._explicit_test.sum()),
     'lcs_records':int(part._lcs.sum()),'district_conflict_records':int(part._district_conflict.sum()),'district_unknown_records':int((~part._district_recognized).sum()),
     'duplicate_coordinate_records':len(part) if len(part)>1 else 0,'multi_name_location_groups':int(many_names),'conflicting_district_location_groups':int(many_districts)}
    for key,val in values.items():vectors[key][vi]+=val
  self.signal_location_ledger=pd.DataFrame(rows);self.arrays['signals']=vectors
  self.sources['signals'].update({'source_id_unique':bool(g['流水號'].is_unique),'raw_explicit_test_names':int(g._explicit_test.sum()),
   'raw_LCS_names':int(g._lcs.sum()),'valid_coordinate_LCS_names':int((valid&g._lcs).sum()),'valid_coordinate_test_names':int((valid&g._explicit_test).sum()),
   'exact_duplicate_record_rows':int(g._exact_duplicate_record.sum()),'same_coordinate_duplicate_rows':int(g._same_coordinate.sum()),
   'same_coordinate_different_name_rows':int(g._same_coordinate_different_names.sum()),'raw_assigned_district_conflicts':int(g._district_conflict.sum()),
   'raw_district_unknown':int((~g._district_recognized).sum()),'raw_unique_valid_coordinate_locations':len(rows),
   'main_A_records':int(vectors['main_records'].sum()),'main_A_locations':int(vectors['main_locations'].sum()),'geometry_B_locations':int(vectors['geometry_locations'].sum()),
   'main_A_without_LCS_locations':int(vectors['main_without_lcs_locations'].sum()),'geometry_B_without_LCS_locations':int(vectors['geometry_without_lcs_locations'].sum()),
   'primary_policy':'A: exact coordinate location with basic readable non-test records; strict unique interior and ALL eligible members recognized source district agrees with spatial district; unknown differs from conflict; no first-record choice',
   'alternative_policy':'B: same basic and geometry rules, no district agreement requirement; both A/B retain LCS, and exclusions of LCS-only locations are separately saved without reclassifying LCS as nonfacility',
   'test_policy':'only exact explicit 機房測試用 substring excluded, five source names support nonformal test interpretation',
   'deduplication':'unique exact parsed numeric coordinate pairs only; no proximity merge or physical-intersection dedup claim',
   'readiness_reason':'Partially ready: location record unit, LCS meaning/completeness/time and 118 source-district discrepancies not certified as actual intersections'})
  assert vectors['raw_assigned_records'].sum()==(assigned>=0).sum()
  for col,key in [('main_A','main_locations'),('geometry_B','geometry_locations'),('main_A_without_LCS','main_without_lcs_locations'),('geometry_B_without_LCS','geometry_without_lcs_locations')]:
   assert int(self.signal_location_ledger[col].sum())==int(vectors[key].sum())
  assert (vectors['main_locations']<=vectors['geometry_locations']).all() and (vectors['main_without_lcs_locations']<=vectors['main_locations']).all()
  print('Signal records / exact-coordinate groups / A and B policies reconciled',flush=True)
  return self.sources['signals']

 def crossing_features(self):
  g=self.layers['crossings'];valid=g._geometry_valid.to_numpy();geom=np.asarray(g.geometry.array,dtype=object)
  if not valid.all():raise ValueError('New crossing geometry invalidity: no arbitrary automatic repair; source needs review')
  normalized=s.to_wkb(s.normalize(geom));g['_normalized_duplicate_geometry']=pd.Series(normalized).duplicated(keep=False)
  union=union_parts(geom,'polygon');areas=self.measure(union,'area','crossings')
  tree=s.STRtree(geom);pair=tree.query(self.v,predicate='intersects');counts=np.zeros(456,int);raw_areas=np.zeros(456,float);dup_counts=np.zeros(456,int)
  for start in range(0,pair.shape[1],5000):
   left,right=pair[:,start:start+5000];aa=s.area(s.intersection(self.v[left],geom[right]));positive=aa>0
   np.add.at(counts,left[positive],1);np.add.at(raw_areas,left,aa)
   dup=g._normalized_duplicate_geometry.to_numpy()[right]&positive;np.add.at(dup_counts,left[dup],1)
  dt=pd.to_datetime(g.rddate,errors='coerce');real=dt.ge('1950-01-01')
  self.arrays['crossings']={'area':areas,'source_records':counts,'raw_intersection_area':raw_areas,'overlap_removed':raw_areas-areas,'duplicate_source_records':dup_counts}
  self.crossing_union=union
  self.sources['crossings'].update({'normalized_duplicate_geometry_rows':int(g._normalized_duplicate_geometry.sum()),'raw_polygon_area_sum_m2':float(s.area(geom).sum()),
   'polygon_union_area_m2':union.area,'duplicate_overlap_removed_total_m2':float(s.area(geom).sum()-union.area),
   'city_union_area_m2':union.intersection(self.city).area,'village_union_area_sum_m2':float(np.nansum(areas)),
   'village_sum_minus_city_m2':float(np.nansum(areas)-union.intersection(self.city).area),'observed_zero_villages':int((areas==0).sum()),
   'licodes':{str(k):int(v) for k,v in g.licode.value_counts(dropna=False).items()},'missing_rddate':int(dt.isna().sum()),'pre1950_placeholder_dates':int((dt.notna()&~real).sum()),
   'semantic_unit':'six-layer crossing-marking polygon components; union area only, not complete facilities/length; 2024 packaging not annual census'})
  assert (areas[np.isfinite(areas)]>=0).all() and (areas<=self.area+AREA_ATOL).all()
  print('Six crossing layers unioned across duplicates and clipped to 456 original villages',flush=True)
  return self.sources['crossings']

 def width_features(self):
  g=self.layers['road_width'];w=pd.to_numeric(g.road_width.str.extract(r'^\s*(\d+(?:\.\d+)?)\s*[mM]\s*$',expand=False),errors='coerce').to_numpy(dtype=float,na_value=np.nan)
  geom=np.asarray(g.geometry.array,dtype=object);valid=g._geometry_valid.to_numpy()&np.isfinite(w)&(w>0)
  g['_annotation_width_m']=w;g['_length_annotation_difference_m']=abs(s.length(geom)-w)
  norm=s.to_wkb(s.normalize(geom));g['_normalized_geometry_hex']=[bytes(b).hex() if b is not None else '' for b in norm]
  duplicate=g.loc[valid,['_normalized_geometry_hex','_annotation_width_m']].duplicated(keep=False)
  g['_exact_geometry_width_duplicate']=False;g.loc[valid,'_exact_geometry_width_duplicate']=duplicate
  # Statistical sample is a set of exact geometry+width annotations. No retained
  # source record is selected as authoritative; every source ID remains linked.
  groups=g.loc[valid].groupby(['_normalized_geometry_hex','_annotation_width_m'],sort=True,dropna=False)
  rows=[];sample_geoms=[]
  conflict_keys=set(g.loc[valid].groupby('_normalized_geometry_hex')._annotation_width_m.nunique().loc[lambda a:a>1].index)
  for (hexgeom,width),part in groups:
   shape=s.from_wkb(bytes.fromhex(hexgeom));sample_geoms.append(shape)
   rows.append({'sample_id':hashlib.sha256((hexgeom+'|'+float(width).hex()).encode()).hexdigest()[:20],'width_m':float(width),
    'source_rows':len(part),'source_ids_json':json.dumps(part._source_id.tolist(),ensure_ascii=False),'same_geometry_conflicting_width':hexgeom in conflict_keys,
    'line_length_m':shape.length,'annotation_length_difference_m':abs(shape.length-width)})
  samples=pd.DataFrame(rows);sample_geoms=np.asarray(sample_geoms,dtype=object);mid=s.line_interpolate_point(sample_geoms,.5,normalized=True)
  assigned,status,nc,nw=point_assign(mid,self.v);samples['assigned_index']=assigned;samples['assignment_status']=status
  samples['village_id']=[str(self.base.village_id.iloc[i]) if i>=0 else None for i in assigned]
  query=self.tree.query(sample_geoms,predicate='intersects');positive_counts=np.zeros(len(samples),int);intersect_by_v=[[] for _ in self.v]
  for start in range(0,query.shape[1],5000):
   left,right=query[:,start:start+5000];positive=s.length(s.intersection(sample_geoms[left],self.v[right]))>0
   np.add.at(positive_counts,left[positive],1)
   for i,j in zip(left[positive],right[positive]):intersect_by_v[int(j)].append(int(i))
  samples['positive_line_intersection_villages']=positive_counts;samples['cross_village_dimension_line']=positive_counts>1
  samples['whole_line_covered_by_assigned_village']=[bool(self.v[a].covers(shape)) if a>=0 else False for a,shape in zip(assigned,sample_geoms)]
  midxy=np.column_stack((s.get_x(mid),s.get_y(mid)));samples['midpoint_xy_key']=[float(x).hex()+','+float(y).hex() for x,y in midxy]
  coincident_different_width=set(samples.groupby('midpoint_xy_key').width_m.nunique().loc[lambda a:a>1].index)
  samples['same_midpoint_distinct_width_flag']=samples.midpoint_xy_key.isin(coincident_different_width)
  keys=['count','median','q1','q3','min','max','cross_line_count','source_rows','same_geometry_conflict_count','same_midpoint_distinct_width_count','line_intersection_samples','line_intersection_median','excluding_conflict_median']
  data={k:np.full(456,np.nan) for k in keys}
  for i in range(456):
   f=samples.loc[assigned==i];values=f.width_m.to_numpy();allline=samples.iloc[intersect_by_v[i]];without=f.loc[~f.same_geometry_conflicting_width,'width_m']
   data['count'][i]=len(f);data['source_rows'][i]=f.source_rows.sum();data['cross_line_count'][i]=f.cross_village_dimension_line.sum()
   data['same_geometry_conflict_count'][i]=f.same_geometry_conflicting_width.sum();data['same_midpoint_distinct_width_count'][i]=f.same_midpoint_distinct_width_flag.sum()
   data['line_intersection_samples'][i]=len(allline);data['line_intersection_median'][i]=allline.width_m.median() if len(allline) else np.nan
   data['excluding_conflict_median'][i]=float(without.median()) if len(without) else np.nan
   for key,func in [('median',np.median),('min',np.min),('max',np.max)]:data[key][i]=float(func(values)) if len(values) else np.nan
   if len(values):data['q1'][i],data['q3'][i]=np.quantile(values,[.25,.75],method='linear')
  self.width_sample_ledger=samples;self.width_sample_geoms=sample_geoms;self.arrays['road_width']=data
  # Original Unit1.7 all-line-intersection scope is recomputed only as a narrow
  # definition comparison here, not by rerunning the Chapter1 notebook.
  old_query=self.tree.query(geom[valid],predicate='intersects');old_ids=np.flatnonzero(valid);old_sets=[[] for _ in self.v]
  for li,vi in old_query.T:
   ri=old_ids[int(li)]
   if geom[ri].intersection(self.v[int(vi)]).length>0:old_sets[int(vi)].append(int(ri))
  old_medians=np.array([np.median(w[ids]) if ids else np.nan for ids in old_sets])
  self.width_scope_comparison=pd.DataFrame({'village_id':self.base.village_id,'original_line_intersection_count':[len(ids) for ids in old_sets],
   'original_line_intersection_median_m':old_medians,'deduplicated_line_intersection_count':data['line_intersection_samples'],
   'deduplicated_line_intersection_median_m':data['line_intersection_median'],'unique_midpoint_count':data['count'],'unique_midpoint_median_m':data['median']})
  self.sources['road_width'].update({'parseable_width':int(np.isfinite(w).sum()),'positive_valid_annotations':int(valid.sum()),
   'line_length_within_1cm_of_annotation':int((g._length_annotation_difference_m<=.01).sum()),'raw_exact_geometry_width_duplicate_rows':int(g._exact_geometry_width_duplicate.sum()),
   'distinct_geometry_width_samples':len(samples),'same_geometry_conflicting_width_groups':len(conflict_keys),'same_midpoint_distinct_width_positions':len(coincident_different_width),
   'midpoint_unique_assigned_samples':int((assigned>=0).sum()),'midpoint_outside_samples':int((status=='outside').sum()),'midpoint_boundary_or_multiple_samples':int((status=='boundary_or_multiple').sum()),
   'cross_village_dimension_line_samples':int(samples.cross_village_dimension_line.sum()),'full_line_not_covered_by_midpoint_village_samples':int(((assigned>=0)&~samples.whole_line_covered_by_assigned_village.to_numpy()).sum()),
   'original_line_intersection_valid_villages':int(np.isfinite(old_medians).sum()),'new_midpoint_valid_villages':int(np.isfinite(data['median']).sum()),
   'new_no_sample_villages':int((data['count']==0).sum()),'changed_village_medians':int((np.isfinite(old_medians)&np.isfinite(data['median'])&~np.isclose(old_medians,data['median'],rtol=0,atol=1e-12)).sum()),
   'policy':'one exact normalized-geometry + parsed-width sample; direction normalization only, no snapping/proximity merge; midpoint strict unique interior attribution; retain different widths and flag conflicts; no longitudinal weighting',
   'limitations':'planned/cadastral dimension annotation sample, not measured passable road width or representative road-length sample; co-located distinct geometries not automatically errors'})
  assert int(data['count'].sum())==int((assigned>=0).sum()) and np.isnan(data['median'][data['count']==0]).all()
  print('Width annotation samples deduplicated exactly and assigned by strict midpoint; no-sample villages',int((data['count']==0).sum()),flush=True)
  return self.sources['road_width']

 def mrt_features(self):
  g=self.layers['mrt'];assigned,status=self.assign_source_points('mrt');valid=g._coordinate_valid.to_numpy()
  g['_station_label']=g['出入口名稱'].str.extract(r'^(.*?站)',expand=False)
  cols=['項次','出入口名稱','出入口編號','經度','緯度','是否為無障礙用'];g['_exact_duplicate_record']=g[cols].duplicated(keep=False)
  # Distinct source IDs / station entrances remain separate. In this frozen
  # file IDs are unique; no unsupported physical entrance merge is made.
  assert g['項次'].is_unique,'Conflicting MRT IDs require review, not first-record selection'
  counts=np.bincount(assigned[assigned>=0],minlength=456);geoms=np.asarray(g.geometry.array,dtype=object)[valid]
  self.arrays['mrt']={'count':counts};self.mrt_buffers={};effects=[]
  inside=assigned[valid]>=0;points_outside=geoms[~inside]
  for radius in RADII:
   buffers=s.buffer(geoms,radius,quad_segs=16);union=union_parts(buffers,'polygon');inside_union=union_parts(buffers[inside],'polygon')
   areas=self.measure(union,'area','mrt');extra=self.measure(union.difference(inside_union),'area','mrt')
   self.arrays['mrt'][str(radius)+'_area']=areas;self.arrays['mrt'][str(radius)+'_crossborder_extra_area']=extra;self.mrt_buffers[radius]=union
   city_area=union.intersection(self.city).area
   effects.append({'radius_m':radius,'city_union_area_m2':city_area,'village_area_sum_m2':float(np.nansum(areas)),
    'village_sum_minus_city_m2':float(np.nansum(areas)-city_area),'extra_city_area_from_outside_entrances_m2':union.difference(inside_union).intersection(self.city).area,
    'raw_sum_individual_buffer_area_m2':float(s.area(buffers).sum()),'all_entrance_buffer_union_area_m2':union.area,
    'total_buffer_overlap_removed_m2':float(s.area(buffers).sum()-union.area)})
   assert (areas>=0).all() and (areas<=self.area+AREA_ATOL).all()
  data=self.arrays['mrt'];assert (data['300_area']<=data['500_area']+AREA_ATOL).all() and (data['500_area']<=data['800_area']+AREA_ATOL).all()
  distances=s.distance(points_outside,self.city) if len(points_outside) else np.array([])
  self.mrt_outside_distance_ledger=g.loc[valid&(assigned<0),['_source_id','項次','出入口名稱','出入口編號','經度','緯度']].copy()
  self.mrt_outside_distance_ledger['distance_to_original_city_m']=distances
  self.sources['mrt'].update({'source_id_unique':True,'station_name_labels':int(g._station_label.nunique()),'station_label_unparsed':int(g._station_label.isna().sum()),
   'source_exact_duplicate_rows':int(g._exact_duplicate_record.sum()),'same_coordinate_rows':int(g.loc[valid].geometry.to_wkb().duplicated(keep=False).sum()),
   'outside_entrances_within_800m':int((distances<=800).sum()),'zero_entrance_villages':int((counts==0).sum()),'buffer_effects':effects,
   'buffer_policy':'all valid source entrances including outside-city points; union before actual village polygon intersection; EPSG3826, quad_segs=16; no historical-date filtering',
   'unit':'entrance records, not stations or ridership; exact station labels are diagnostic, no official station code',
   'snapshot':'2026-08-04 current snapshot, not 2024/2025 pre-accident or independent annual observation'})
  assert counts.sum()==self.sources['mrt']['unique_assigned']
  print('MRT entrances and nested 300/500/800m unions passed, including outside entrances',flush=True)
  return self.sources['mrt']

def build_dataset(ctx):
 data={};definitions=[]
 def add(name,values,dtype,definition,unit='not applicable',source='Unit2.6 explicit processing',missing='source-specific missing/zero rules; processing failure => NA'):
  assert name not in data,('DUPLICATE COLUMN',name)
  series=pd.Series([values]*456) if pd.api.types.is_scalar(values) else pd.Series(values).reset_index(drop=True)
  data[name]=series.astype(dtype)
  definitions.append({'name':name,'dtype':dtype,'definition':definition,'unit':unit,'source':source,'missing_rule':missing})
 for col in ['village_id','boundary_code','district_name','standard_village_name','verification_status','geometry_quality_flag']:
  add(col,ctx.base[col],'string','Unit2.2固定里主表欄位；verification_status是里碼配對證據，糖廍正常納入','not applicable','formal village base','nonmissing; no eligibility restriction from provisional_match')
 add('fixed_village_area_m2',ctx.base.village_area_m2,'Float64','完整原固定里面積；非AREA欄，不修界／填洞','m²','Unit2.2 village_area_m2','positive, nonmissing')
 add('fixed_village_area_km2',ctx.base.village_area_km2,'Float64','人口與設施密度共用原固定面積分母','km²','Unit2.2 village_area_km2','positive, nonmissing')
 for name,value,meaning in [('analysis_role','external_environment_transportation','事故分群後外部環境比較，非A主要分群輸入'),
  ('working_crs','EPSG:3826','各來源依各自證據轉換，並非全部直接指定'),('osm_snapshot_time','2025-01-01T21:21:00Z','OSM包內README實際快照時間'),
  ('signal_filename_date','2023-07-06','只代表來源檔名日期'),('signal_observation_date_status','not_certified','實際號誌觀測／設置日未認證，資源更新另見schema'),
  ('crosswalk_packaging_date','2024-07-12','封裝標記，不是2024全年或2025完整設施存量'),('road_width_resource_date','2023-12-28','計畫尺寸標註資源時間，不是研究年實測'),
  ('mrt_snapshot_date','2026-08-04','入口當期快照，無完整設置／撤除史'),('marked_sidewalk_readiness','Blocked','混合標線沒有可靠人行道子集；不建立數值')]:
  add(name,value,'string',meaning,source='source metadata / Unit1.7 / Unit2.6 specification',missing='known metadata strings retained; no imputation of actual observation dates')
 add('year_specific_observation',False,'boolean','沒有兩套獨立年度B3；不建立S0–S3重複')
 add('mrt_pre_accident_environment_verified',False,'boolean','2026入口不可冒稱2024／2025事故前環境')
 a=ctx.arrays['osm'];area=pd.Series(ctx.area,dtype='Float64');area_km2=pd.Series(ctx.area_km2,dtype='Float64')
 roadcols={'road':('osm_road_length_m','主要指定OSM機動候選線聯集，扣原共同里界線段'),
  'major':('osm_major_road_length_m','六個研究major類同規則聯集線長；major為全部候選子集'),
  'inclusive':('osm_inclusive_road_length_m','逐里完整覆蓋線長，含共界，不能互斥加總成城市總量'),
  'shared':('osm_shared_boundary_unallocated_length_m','從本里主要線長扣除的原共同里界線段'),
  'major_inclusive':('osm_inclusive_major_road_length_m','major含共界線長'),('major_shared'):('osm_major_shared_boundary_length_m','major原共界未歸屬線長'),
  'major_other_overlap':('osm_major_other_overlap_length_m','major與其他納入類別重合線長；保留分類重疊診斷'),
  'raw_clipped_sum':('osm_raw_clipped_length_sum_m','原線逐里交集長度和，僅稽核，不當唯一道路長度'),
  'duplicate_removed':('osm_raw_minus_union_length_m','原線交集和減同域union，浮點微負值保留作數值診斷'),
  'source_records':('osm_positive_intersection_source_count','與里有正線長交集的原始候選線數，不是實體道路條數')}
 for key,(name,meaning) in roadcols.items():add(name,a[key],'Int64' if key=='source_records' else 'Float64',meaning,'source line records' if key=='source_records' else 'm','frozen OSM source + original village polygon')
 add('osm_road_length_km',a['road']/1000,'Float64','主要候選線表示長度換算','km','osm_road_length_m / 1000')
 add('osm_major_road_length_km',a['major']/1000,'Float64','同口徑major線表示長度換算','km','osm_major_road_length_m / 1000')
 add('osm_road_density',data['osm_road_length_km']/area_km2,'Float64','已觀測指定道路線表示km／完整里面積km²；不是VKT或容量','km/km²','osm_road_length_km / fixed_village_area_km2')
 ratio=np.divide(a['major']/1000,a['road']/1000,out=np.full(456,np.nan),where=np.isfinite(a['road'])&(a['road']>0))
 add('osm_major_road_ratio',ratio,'Float64','六類研究major線聯集長／相同全部候選線聯集長；不是官方等級或流量占比','fraction','same-scope major / all road union','zero road denominator => NA; processing failure => NA')
 sig=ctx.arrays['signals'];scols={
  'raw_assigned_records':('signal_raw_unique_assigned_record_count','基本品質過濾前，幾何唯一歸里的原紀錄'),
  'main_records':('observed_signal_record_count','屬主要A口徑位置之可讀、非機房測試原紀錄數，尚未座標去重'),
  'main_locations':('observed_unique_signal_location_count','主要A口徑唯一原數值座標位置數，不是完整實體路口數'),
  'geometry_locations':('signal_geometry_only_unique_location_count','B口徑：相同基本品質與唯一內部幾何，允許區名不一致'),
  'main_without_lcs_locations':('signal_main_without_lcs_location_count','A口徑排除僅由LCS紀錄支持的位置，並非認定LCS不是設施'),
  'geometry_without_lcs_locations':('signal_geometry_without_lcs_location_count','B口徑排除僅由LCS支持的位置'),
  'test_records':('signal_explicit_test_record_count','幾何可歸里的機房測試用原紀錄'),
  'lcs_records':('signal_lcs_record_count','幾何可歸里的LCS原紀錄；其實際設備單位尚未認證'),
  'district_conflict_records':('signal_source_district_conflict_record_count','可判讀來源區名與空間歸區明確不一致的原紀錄'),
  'district_unknown_records':('signal_source_district_unknown_record_count','幾何歸里但來源區名不可判讀，與明確衝突分開'),
  'duplicate_coordinate_records':('signal_same_coordinate_record_count','幾何歸里之同位置重複群原紀錄數，非多餘筆數'),
  'multi_name_location_groups':('signal_same_coordinate_multiple_name_group_count','同座標多名稱群數，不任意近距離併路口'),
  'conflicting_district_location_groups':('signal_same_coordinate_conflicting_district_group_count','同位置原紀錄有互相衝突已識別區名的群數')}
 for key,(name,meaning) in scols.items():add(name,sig[key],'Int64',meaning,'coordinate locations' if key.endswith('locations') or key.endswith('groups') else 'source records','frozen signals TAB source / exact-coordinate grouping')
 for name,numerator,meaning in [
  ('observed_signal_location_density','observed_unique_signal_location_count','主要A口徑，全部非測試有效成員區名皆已識別且吻合'),
  ('signal_geometry_only_location_density','signal_geometry_only_unique_location_count','B幾何口徑，區名衝突不作主要資格條件'),
  ('signal_main_without_lcs_location_density','signal_main_without_lcs_location_count','A排除LCS-only位置敏感度'),
  ('signal_geometry_without_lcs_location_density','signal_geometry_without_lcs_location_count','B排除LCS-only位置敏感度')]:
  add(name,data[numerator]/area_km2,'Float64',meaning+'；唯一觀測位置／完整里面積，不認證實體路口','locations/km²',numerator+' / fixed_village_area_km2')
 per_km=np.divide(sig['main_locations'],a['road']/1000,out=np.full(456,np.nan),where=np.isfinite(a['road'])&(a['road']>0))
 add('observed_signal_locations_per_osm_road_km',per_km,'Float64','補充：主要A位置／同口徑OSM線表示km，跨來源時點不同','locations/km','main signal locations / osm_road_length_km','zero road denominator => NA')
 cross=ctx.arrays['crossings']
 for name,values,meaning,unit in [
  ('observed_crosswalk_area_m2',cross['area'],'六明示行穿標線層union後與原里面交集，非設施數','m²'),
  ('observed_crosswalk_area_km2',cross['area']/1e6,'已觀測行穿標線面積換算','km²'),
  ('crosswalk_area_ratio',pd.Series(cross['area'],dtype='Float64')/area,'標線聯集面積／完整里面積，非完整性／安全評分','fraction'),
  ('crosswalk_raw_intersection_area_sum_m2',cross['raw_intersection_area'],'原構件交集面積和，僅比較重複，不當可靠聯集面積','m²'),
  ('crosswalk_raw_minus_union_area_m2',cross['overlap_removed'],'原構件交集和減聯集之診斷差，微量負值保留','m²')]:add(name,values,'Float64',meaning,unit,'frozen six-layer crossing source / polygon union')
 add('crosswalk_positive_intersection_source_count',cross['source_records'],'Int64','原Polygon正面積交集筆數，非完整行穿設施數','source polygon components')
 add('crosswalk_duplicate_geometry_source_intersection_count',cross['duplicate_source_records'],'Int64','來源正規化重複面中與此里正面積相交之筆數','source polygon components')
 width=ctx.arrays['road_width'];wcols={
  'count':('annotated_road_width_sample_count','精確geometry＋width去重後，中點唯一歸里的標註樣本數','Int64','annotation samples'),
  'median':('median_annotated_road_width','中點唯一歸里標註樣本中位數，非實測通行路寬','Float64','m'),
  'q1':('annotated_road_width_q1','標註樣本25百分位，線性分位算子','Float64','m'),
  'q3':('annotated_road_width_q3','標註樣本75百分位，線性分位算子','Float64','m'),
  'min':('annotated_road_width_min','標註樣本最小值，不刪極端值','Float64','m'),
  'max':('annotated_road_width_max','標註樣本最大值，不刪極端值','Float64','m'),
  'source_rows':('annotated_road_width_assigned_source_record_count','本里去重樣本對應原始來源筆數，保留追溯','Int64','source annotations'),
  'cross_line_count':('annotated_road_width_cross_village_line_sample_count','中點歸本里但整線與多里有正長度交集之樣本','Int64','annotation samples'),
  'same_geometry_conflict_count':('annotated_road_width_same_geometry_conflict_sample_count','相同幾何不同寬度之樣本，未任取第一筆','Int64','annotation samples'),
  'same_midpoint_distinct_width_count':('annotated_road_width_same_midpoint_distinct_width_sample_count','同中點不同寬度旗標，並非一律錯誤或自動合併','Int64','annotation samples'),
  'line_intersection_samples':('annotated_road_width_line_intersection_sample_count','診斷：精確去重後全線與此里正長相交樣本數，可跨里重複','Int64','annotation samples'),
  'line_intersection_median':('annotated_road_width_line_intersection_median','診斷：精確去重後全線相交樣本中位數，不作主值','Float64','m'),
  'excluding_conflict_median':('annotated_road_width_excluding_geometry_conflicts_median','診斷：排除同幾何異寬樣本後中位數，主值不任意合併','Float64','m')}
 for key,(name,meaning,dtype,unit) in wcols.items():add(name,width[key],dtype,meaning,unit,'frozen planned/cadastral width dimension lines','no valid samples => count 0, summary NA; never length-weight or impute')
 add('annotated_road_width_no_valid_samples',width['count']==0,'boolean','缺標註樣本，統計值為NA而非0')
 mrt=ctx.arrays['mrt'];add('observed_mrt_entrance_count',mrt['count'],'Int64','2026快照中唯一內部歸里的出入口紀錄數，非站數','entrance records','frozen MRT CSV')
 add('mrt_entrance_density',data['observed_mrt_entrance_count']/area_km2,'Float64','入口紀錄／完整里面積；零入口不等於無可及性','entrances/km²','observed_mrt_entrance_count / fixed_village_area_km2')
 for radius in RADII:
  add(f'mrt_entrance_buffer_{radius}m_area_m2',mrt[str(radius)+'_area'],'Float64',f'全部有效含市外入口{radius}m buffer先union後與原里面相交；quad_segs=16','m²','frozen MRT all-entrance union + original villages')
  add(f'mrt_entrance_buffer_{radius}m_ratio',pd.Series(mrt[str(radius)+'_area'],dtype='Float64')/area,'Float64',f'{radius}m直線覆蓋／完整里面積，非步行路網或流量','fraction','buffer union area / fixed_village_area_m2')
  add(f'mrt_entrance_buffer_{radius}m_crossborder_extra_area_m2',mrt[str(radius)+'_crossborder_extra_area'],'Float64','保留市外入口相較僅市內入口新增覆蓋面積，不重複加總','m²','all-source buffer union minus within-city-entrance buffer union')
 coverage_names=['crosswalk_area_ratio']+[f'mrt_entrance_buffer_{r}m_ratio' for r in RADII]
 cvalues=np.asarray([data[c].to_numpy(dtype=float,na_value=np.nan) for c in coverage_names]);bad_coverage=np.isnan(cvalues).any(axis=0)
 roundoff=pd.Series(np.any((cvalues<0)|(cvalues>1),axis=0),dtype='boolean').mask(bad_coverage,pd.NA)
 excess=np.nanmax(np.vstack([np.zeros(456),data['observed_crosswalk_area_m2'].to_numpy(dtype=float,na_value=np.nan)-ctx.area]+[mrt[str(r)+'_area']-ctx.area for r in RADII]),axis=0)
 excess[bad_coverage]=np.nan
 add('coverage_ratio_roundoff_flag',roundoff,'boolean','行穿／MRT覆蓋比例微量超0–1旗標，保留原比例，不作排除或clip')
 add('coverage_ratio_max_excess_m2',excess,'Float64','四項覆蓋面積超完整里面積之最大正超額，只作數值診斷','m²')
 add('osm_major_ratio_roundoff_flag',data['osm_major_road_ratio'].lt(0)|data['osm_major_road_ratio'].gt(1),'boolean','major比例微量超界診斷，原比例不clip')
 frame=pd.DataFrame(data)
 specs=feature_specs(ctx)
 for feature,spec in specs.items():
  value=frame[feature];states=[]
  for i,v in enumerate(value):
   if pd.isna(v):
    state='no_valid_annotation_samples' if feature=='median_annotated_road_width' and width['count'][i]==0 else 'zero_observed_road_denominator' if feature=='osm_major_road_ratio' and a['road'][i]==0 else 'spatial_processing_failed'
   elif v==0:
    state='zero_entrances_not_zero_accessibility' if feature=='mrt_entrance_density' else 'locations_excluded_by_primary_quality_policy' if feature=='observed_signal_location_density' and sig['geometry_locations'][i]>0 else 'observed_zero_not_confirmed_absent'
   else:state='observed_positive_with_source_limits'
   states.append(state)
  add(feature+'_readiness_status',spec['readiness_status'],'string','來源與方法的逐特徵技術readiness；不是人工研究驗收',source='feature readiness matrix')
  add(feature+'_value_state',states,'string','區分觀測零、無樣本、零分母與處理失敗；不作完整案例刪里',source='actual feature / denominator / sample count')
 failed=np.zeros(456,bool)
 for failures in ctx.failures.values():
  for i in failures:failed[int(i)]=True
 add('any_spatial_processing_failed',failed,'boolean','任一空間處理實際失敗；每個特徵另有value_state，不一概把所有特徵設NA')
 add('any_core_feature_missing',frame[CORE].isna().any(axis=1),'boolean','七核心任一缺失，不刪除該行政里')
 add('source_complete_census_certified',False,'boolean','所有快照均不冒充同時點完整設施普查')
 frame=pd.DataFrame(data);assert list(frame)==[d['name'] for d in definitions]
 validate_dataset(frame,ctx.base)
 return frame,definitions,specs

def feature_specs(ctx):
 explicit='Ready with explicit assumptions';partial='Partially ready'
 def spec(source,unit,numerator,denominator,status,use,why):
  item=ctx.raw_items[source]
  return {'source':item['path'],'source_sha256':item['sha256'],'observation_unit':unit,'numerator':numerator,'denominator':denominator,
   'raw_crs':ctx.crs[source]['raw'],'working_crs':'EPSG:3826','crs_evidence':ctx.crs[source]['evidence_grade'],
   'time_reference':ctx.config['metadata'][source]['period'],'spatial_completeness':'source coverage not certified as a full census; frozen original villages preserved',
   'readiness_status':status,'recommended_analytical_use':use,'key_limitations':why,'human_acceptance':'DE / DA / PM pending'}
 specs={
 'osm_road_density':spec('osm','specified motor-candidate line representation','same-class-independent all included line union km excluding shared boundary','fixed_village_area_km2',explicit,'priority external comparison candidate','not centerline / traffic / VKT; fixed OSM snapshot, 2D union, class and boundary assumptions'),
 'osm_major_road_ratio':spec('osm','six-class narrow research major line representation','major line union km in same primary boundary policy','osm_road_length_km',explicit,'priority external comparison candidate','Unit1.7 six classes, not official road hierarchy or traffic share; no road denominator => NA'),
 'observed_signal_location_density':spec('signals','unique exact coordinate locations in conservative A policy','readable non-test, unique interior, all basic member districts recognized and matching locations','fixed_village_area_km2',partial,'conditional priority; DA review of A/B and LCS sensitivity','not physical intersections; uncertain LCS meanings/date/completeness, duplicate and source district conflicts retained'),
 'crosswalk_area_ratio':spec('crossings','six-layer crossing-marking polygon union','observed marking union area_m2','fixed_village_area_m2',partial,'supplementary observed markings comparison','components not full facilities; source coverage and historical stock unknown'),
 'median_annotated_road_width':spec('road_width','unique exact geometry + width annotation, assigned by midpoint','median of unique-midpoint valid positive annotation widths','median operator over sample count',partial,'supplementary planned annotation sample description','not measured road width / length-representative sample; midpoint assumption; no samples => NA'),
 'mrt_entrance_density':spec('mrt','unique-interior source entrance records','observed_mrt_entrance_count','fixed_village_area_km2',explicit,'supplementary 2026 current-environment description only','not stations/ridership; not 2024/2025 pre-accident environment'),
 'mrt_entrance_buffer_500m_ratio':spec('mrt','all entrance 500m straight-line buffer union including outside entrances','mrt_entrance_buffer_500m_area_m2','fixed_village_area_m2',explicit,'supplementary 500m operational candidate only','quad_segs16, Euclidean not walking network, 2026 snapshot not prediction input')}
 for radius in [300,800]:
  specs[f'mrt_entrance_buffer_{radius}m_ratio']=spec('mrt',f'all entrance {radius}m straight-line buffer union',f'mrt_entrance_buffer_{radius}m_area_m2','fixed_village_area_m2',explicit,'supplementary radius sensitivity','all external entrance points retained; current 2026 snapshot, no travel or exposure inference')
 for name,definition in [('signal_geometry_only_location_density','geometry B ignores district conflict as an eligibility rule'),('signal_main_without_lcs_location_density','conservative A excludes LCS-only supporting locations'),('signal_geometry_without_lcs_location_density','geometry B excludes LCS-only supporting locations')]:
  specs[name]=spec('signals',definition,'corresponding exact-coordinate location count','fixed_village_area_km2',partial,'sensitivity to main conservative signal candidate','same basic non-test/readable and unique-interior rules; not a complete physical intersection count')
 return specs

def validate_dataset(f,base):
 assert len(f)==456 and f.village_id.is_unique and f.village_id.notna().all() and f.district_name.nunique()==12
 assert set(f.village_id)==set(base.village_id) and f.village_id.str.fullmatch(r'\d{10}').all() and not f.columns.duplicated().any()
 assert 'year' not in f and 'specification' not in f and f.year_specific_observation.eq(False).all()
 lookup=base.set_index('village_id')
 for col in ['boundary_code','district_name','standard_village_name','verification_status','geometry_quality_flag']:assert f[col].eq(f.village_id.map(lookup[col])).all()
 assert f.fixed_village_area_m2.eq(f.village_id.map(lookup.village_area_m2)).all() and f.fixed_village_area_km2.eq(f.village_id.map(lookup.village_area_km2)).all()
 assert f.fixed_village_area_m2.gt(0).all()
 for col in f:
  if str(f[col].dtype)=='Int64':assert f[col].dropna().ge(0).all(),col
 nonnegative=['osm_road_length_m','osm_major_road_length_m','osm_road_density','observed_signal_location_density','observed_crosswalk_area_m2','crosswalk_area_ratio','observed_mrt_entrance_count','mrt_entrance_density']
 nonnegative += [f'mrt_entrance_buffer_{r}m_area_m2' for r in RADII]
 for col in nonnegative:assert f[col].dropna().ge(0).all(),col
 assert (f.osm_major_road_length_m.dropna()<=f.osm_road_length_m.dropna()+LENGTH_ATOL).all()
 zero=f.osm_road_length_m.eq(0);assert f.loc[zero,'osm_major_road_ratio'].isna().all()
 assert f.osm_major_road_ratio.dropna().between(0,1+1e-10).all()
 expected_major=f.osm_major_road_length_km/f.osm_road_length_km
 valid_major=expected_major.notna()&~zero
 np.testing.assert_allclose(f.loc[valid_major,'osm_major_road_ratio'].astype(float),expected_major.loc[valid_major].astype(float),rtol=0,atol=0)
 assert f.coverage_ratio_max_excess_m2.dropna().between(0,AREA_ATOL).all()
 for col in ['crosswalk_area_ratio']+[f'mrt_entrance_buffer_{r}m_ratio' for r in RADII]:
  valid=f[col].notna();tol=AREA_ATOL/f.loc[valid,'fixed_village_area_m2']
  assert (f.loc[valid,col]>=-tol).all() and (f.loc[valid,col]<=1+tol).all(),col
 for r0,r1 in [(300,500),(500,800)]:assert (f[f'mrt_entrance_buffer_{r0}m_area_m2']<=f[f'mrt_entrance_buffer_{r1}m_area_m2']+AREA_ATOL).all()
 no_width=f.annotated_road_width_sample_count.eq(0)
 for col in ['median_annotated_road_width','annotated_road_width_q1','annotated_road_width_q3','annotated_road_width_min','annotated_road_width_max']:
  assert f.loc[no_width,col].isna().all() and f.loc[~no_width,col].dropna().gt(0).all(),col
 assert f.annotated_road_width_no_valid_samples.eq(no_width).all()
 assert f.marked_sidewalk_readiness.eq('Blocked').all() and 'marked_sidewalk_density' not in f
 assert (f.observed_unique_signal_location_count<=f.signal_geometry_only_unique_location_count).all()
 assert (f.signal_main_without_lcs_location_count<=f.observed_unique_signal_location_count).all()
 assert (f.signal_geometry_without_lcs_location_count<=f.signal_geometry_only_unique_location_count).all()
 np.testing.assert_allclose(f.osm_road_density.astype(float),f.osm_road_length_km.astype(float)/f.fixed_village_area_km2.astype(float),rtol=0,atol=0,equal_nan=True)
 for numerator,density in [('observed_unique_signal_location_count','observed_signal_location_density'),('observed_mrt_entrance_count','mrt_entrance_density')]:
  np.testing.assert_allclose(f[density].astype(float),f[numerator].astype(float)/f.fixed_village_area_km2.astype(float),rtol=0,atol=0,equal_nan=True)
 for vid in ['6300700015','6301100044']:assert int(f.village_id.eq(vid).sum())==1
 assert f.any_core_feature_missing.eq(f[CORE].isna().any(axis=1)).all()
 return True

def handoff_check(root,b3,bindings):
 verify(root,bindings);result=[];stems=[f'taipei_dataset_{k}_{period}' for k in ['a','b1','c'] for period in ['annual','pooled']]+['taipei_dataset_b2']
 right=b3[['village_id','fixed_village_area_m2','fixed_village_area_km2','any_core_feature_missing']].rename(columns={'fixed_village_area_m2':'b3_area_m2','fixed_village_area_km2':'b3_area_km2'})
 for stem in stems:
  schema=json.loads((root/f'data/processed/{stem}_schema.json').read_text(encoding='utf-8'));assert schema['csv']['missing_sentinel']=='__MISSING__'
  names=[c['name'] for c in schema['columns']];keys=[c for c in ['village_id','year','specification'] if c in names]
  areas=[c for c in ['fixed_village_area_m2','fixed_village_area_km2','village_area_m2','village_area_km2'] if c in names]
  if not areas:assert stem.startswith('taipei_dataset_a_'),'unexpected missing area denominator'
  input_maps=[v for v in schema.values() if isinstance(v,dict) and 'data/processed/taipei_village_base.csv' in v]
  assert len(input_maps)==1 and input_maps[0]['data/processed/taipei_village_base.csv']=='db0a225df3568ddb2a47eab1e1d28843e1594dec37956c57eea926e444968209'
  left=read_csv(root/f'data/processed/{stem}.csv',schema,keys+areas)
  merged=left.merge(right,on='village_id',how='left',validate='many_to_one',indicator=True)
  assert len(left)==len(merged) and merged._merge.eq('both').all() and merged.village_id.nunique()==456
  for col in areas:
   expected=merged.b3_area_km2 if col.endswith('km2') else merged.b3_area_m2
   pd.testing.assert_series_equal(merged[col],expected,check_names=False,check_exact=True)
  result.append({'dataset':stem,'rows_before':len(left),'rows_after':len(merged),'unmatched':0,'distinct_villages':456,
   'merge':'many_to_one','area_fields_verified':areas,'common_village_base_hash_verified':True,
   'area_scope':'direct fields checked' if areas else 'composition ratios have no area denominator; same fixed village-base provenance verified',
   'B3_partial_or_missing_rows_retained':int(merged.any_core_feature_missing.sum()),
   'source_feature_values_used_for_B3':False,'snapshot_repeated_not_annual_observation':True})
 return result

def feature_statistics(frame,columns):
 rows=[]
 for col in columns:
  v=frame[col]
  row={'feature':col,'valid_N':int(v.count()),'missing_N':int(v.isna().sum()),'zero_N':int(v.eq(0).sum())}
  row.update({k:float(value) if not pd.isna(value) else None for k,value in [('min',v.min()),('q25',v.quantile(.25)),('median',v.median()),('q75',v.quantile(.75)),('max',v.max()),('mean',v.mean()),('std_ddof1',v.std())]})
  rows.append(row)
 return rows

def diagnostics(ctx,frame,specs):
 stats=feature_statistics(frame,list(specs))
 denominators=feature_statistics(frame,['fixed_village_area_km2','osm_road_length_km','observed_signal_record_count','observed_unique_signal_location_count','crosswalk_positive_intersection_source_count','annotated_road_width_sample_count','observed_mrt_entrance_count'])
 matrix=[]
 for feature,spec in specs.items():
  row={'feature':feature,**spec};row.update(next(r for r in stats if r['feature']==feature))
  states=frame[feature+'_value_state'].value_counts(dropna=False)
  row.update({'value_state_counts':{str(k):int(v) for k,v in states.items()},'source_validity':ctx.sources[[k for k,v in ctx.raw_items.items() if v['path']==spec['source']][0]],
   'spatial_processing_valid_values':int(frame[feature].count()),'formal_analysis_selected':False})
  matrix.append(row)
 blocked=[{'feature':feature,'readiness_status':'Blocked','key_limitations':reason,'formal_numeric_column_created':False,'recommended_analytical_use':'do not use'} for feature,reason in BLOCKED.items()]
 district=[]
 for d,ids in frame.groupby('district_name').groups.items():
  f=frame.loc[ids];area=f.fixed_village_area_km2.sum();road=f.osm_road_length_km.sum()
  row={'district':d,'villages':len(f),'fixed_area_sum_km2':float(area),'road_sum_km':float(road),
   'osm_road_density_area_weighted':float(road/area),'osm_major_road_ratio_length_weighted':float(f.osm_major_road_length_km.sum()/road) if road>0 else None,
   'signal_main_locations':int(f.observed_unique_signal_location_count.sum()),'signal_geometry_locations':int(f.signal_geometry_only_unique_location_count.sum()),
   'signal_district_conflict_records':int(f.signal_source_district_conflict_record_count.sum()),'signal_density_area_weighted':float(f.observed_unique_signal_location_count.sum()/area),
   'crosswalk_union_village_area_sum_m2':float(f.observed_crosswalk_area_m2.sum()),'crosswalk_ratio_area_weighted':float(f.observed_crosswalk_area_m2.sum()/(area*1e6)),
   'width_valid_villages':int(f.median_annotated_road_width.notna().sum()),'width_missing_villages':int(f.median_annotated_road_width.isna().sum()),
   'width_annotation_samples':int(f.annotated_road_width_sample_count.sum()),'width_cross_village_line_samples':int(f.annotated_road_width_cross_village_line_sample_count.sum()),
   'mrt_entrances':int(f.observed_mrt_entrance_count.sum()),'mrt_zero_entrance_villages':int(f.observed_mrt_entrance_count.eq(0).sum()),
   'mrt_entrance_density_area_weighted':float(f.observed_mrt_entrance_count.sum()/area),'mrt500_ratio_area_weighted':float(f.mrt_entrance_buffer_500m_area_m2.sum()/(area*1e6))}
  for feature in CORE:
   row[feature+'_valid_N']=int(f[feature].count());row[feature+'_missing_N']=int(f[feature].isna().sum());row[feature+'_zero_N']=int(f[feature].eq(0).sum())
   row[feature+'_village_mean']=float(f[feature].mean()) if f[feature].notna().any() else None
   row[feature+'_village_median']=float(f[feature].median()) if f[feature].notna().any() else None
  district.append(row)
 print('Feature statistics and district quality assembled; reconciling geometry coverage',flush=True)
 pair_geoms=np.asarray(ctx.village_pair_intersections,dtype=object)
 # Index source lines against only the relevant original village-pair geometry.
 # This is the same union-covered pair length without repeatedly overlaying the
 # entire city network. Touch-only Point parts have no length.
 road_geoms=np.asarray(ctx.selected_roads.geometry.array,dtype=object);query=s.STRtree(road_geoms).query(pair_geoms,predicate='intersects')
 by_pair=[[] for _ in pair_geoms]
 for start in range(0,query.shape[1],5000):
  left,right=query[:,start:start+5000];clips=s.intersection(road_geoms[right],pair_geoms[left])
  for i,g in zip(left,clips):
   if g.length>0:by_pair[int(i)].append(g)
 road_pair_length=float(sum(union_parts(gs,'line').length for gs in by_pair))
 positive_area_pairs=np.asarray([union_parts([g],'polygon') for g in pair_geoms if g.area>0],dtype=object)
 r=ctx.sources['osm'];inclusive_excess=r['inclusive_sum_minus_city_m'];assert inclusive_excess>=-LENGTH_ATOL and inclusive_excess<=road_pair_length+LENGTH_ATOL,('ROAD MULTIPLE COVERAGE ACCOUNTING',inclusive_excess,road_pair_length)
 np.testing.assert_allclose(r['village_road_effective_sum_m']+r['village_shared_sum_m'],r['village_inclusive_sum_m'],rtol=0,atol=LENGTH_ATOL)
 reconciliation=[{'source':'osm','measure':'length_m','city_union':r['city_road_length_m'],'village_inclusive_sum':r['village_inclusive_sum_m'],
  'village_primary_sum':r['village_road_effective_sum_m'],'shared_village_sum':r['village_shared_sum_m'],'city_shared_union':r['city_shared_boundary_road_length_m'],
  'inclusive_sum_minus_city':inclusive_excess,'pairwise_multiple_coverage_upper_bound':road_pair_length,'tolerance':LENGTH_ATOL}]
 for name,g,values in [('crossings',ctx.crossing_union,ctx.arrays['crossings']['area'])]+[(f'mrt_{radius}',ctx.mrt_buffers[radius],ctx.arrays['mrt'][str(radius)+'_area']) for radius in RADII]:
  city=g.intersection(ctx.city).area;total=float(np.nansum(values));pair_area=float(clipped_measure(positive_area_pairs,g,'area').sum()) if len(positive_area_pairs) else 0.;difference=total-city
  assert difference>=-AREA_ATOL and difference<=pair_area+AREA_ATOL,(name,'POLYGON MULTIPLE COVERAGE ACCOUNTING',difference,pair_area)
  reconciliation.append({'source':name,'measure':'area_m2','city_union':city,'village_sum':total,'sum_minus_city':difference,'pairwise_multiple_coverage_upper_bound':pair_area,'tolerance':AREA_ATOL})
 comparisons=[{'quantity':'OSM city represented km','unit17':3706.203383,'unit26':r['city_road_length_m']/1000,'reason':'same included fclass and original-village policy; float differences retained'},
  {'quantity':'OSM regional included lines','unit17':40322,'unit26':r['regional_included_lines'],'reason':'same 2km regional selection'},
  {'quantity':'signal unique assigned raw records','unit17':2697,'unit26':ctx.sources['signals']['unique_assigned'],'reason':'before explicit test / district / coordinate-position quality rules'},
  {'quantity':'width valid villages','unit17':453,'unit26':ctx.sources['road_width']['new_midpoint_valid_villages'],'reason':'unique midpoint and exact-geometry+width dedup; distribution may differ although N equal'}]
 for radius,benchmark in [(300,28.002336),(500,58.374045),(800,92.927724)]:
  actual=next(e for e in ctx.sources['mrt']['buffer_effects'] if e['radius_m']==radius)['city_union_area_m2']/1e6
  comparisons.append({'quantity':f'MRT {radius}m city union km2','unit17':benchmark,'unit26':actual,'difference':actual-benchmark,'reason':'all 390 entrance snapshot points including outside; quad_segs16 same convention'})
 w=ctx.width_scope_comparison
 width_changes={'deduplication_changed_village_medians':int((w.original_line_intersection_median_m.notna()&w.deduplicated_line_intersection_median_m.notna()&~np.isclose(w.original_line_intersection_median_m,w.deduplicated_line_intersection_median_m,rtol=0,atol=1e-12)).sum()),
  'midpoint_changed_vs_deduplicated_line_medians':int((w.deduplicated_line_intersection_median_m.notna()&w.unique_midpoint_median_m.notna()&~np.isclose(w.deduplicated_line_intersection_median_m,w.unique_midpoint_median_m,rtol=0,atol=1e-12)).sum()),
  'total_changed_vs_unit17_village_medians':ctx.sources['road_width']['changed_village_medians']}
 extreme_cols=['village_id','district_name','standard_village_name','fixed_village_area_km2']
 extremes={feature:frame[extreme_cols+[feature]].sort_values(feature,ascending=False,na_position='last').head(8).to_dict('records') for feature in CORE}
 empty_width=frame.loc[frame.annotated_road_width_sample_count.eq(0),extreme_cols+['annotated_road_width_sample_count','median_annotated_road_width']]
 return {'feature_statistics':stats,'denominator_statistics':denominators,'feature_readiness':matrix,'blocked_features':blocked,'district_quality':district,
  'reconciliation':reconciliation,'unit17_comparison':comparisons,'width_definition_comparison':width_changes,
  'no_width_sample_villages':json.loads(empty_width.to_json(orient='records',force_ascii=False)),'extreme_villages':extremes,
  'missing_core_villages':int(frame.any_core_feature_missing.sum()),'any_spatial_failure_villages':int(frame.any_spatial_processing_failed.sum()),
  'coverage_roundoff_villages':int(frame.coverage_ratio_roundoff_flag.sum()),'coverage_roundoff_max_excess_m2':float(frame.coverage_ratio_max_excess_m2.max()),
  'major_ratio_roundoff_villages':int(frame.osm_major_ratio_roundoff_flag.sum())}

def schema(ctx,frame,definitions,diag):
 return {'unit':'2.6','created_at':'2026-11-27','dataset_path':f'data/processed/{STEM}.csv','producer':PRODUCER,'helper':HELPER,
  'documentation':f'data/processed/{STEM}_documentation.ipynb','role':'external_environment_transportation','expected_rows':456,
  'processing_environment':ctx.facts['versions'],'reviewed_project_context':ctx.project_context,
  'observation_unit':'one fixed research village, one mixed-date source snapshot; no annual/pooled or S0-S3 duplication','primary_key':['village_id'],
  'csv':CSV,'columns':definitions,'source_inputs':ctx.bindings,'handoff_only_inputs':ctx.handoff_bindings,
  'core_candidate_features':CORE,'source_metadata':{k:ctx.config['metadata'][k] for k in ctx.raw_items},'source_crs':ctx.crs,
  'source_quality':ctx.sources,'road_classification':ctx.road_classification,'format_documentation_evidence':FORMAT_EVIDENCE,
  'attribution':'© OpenStreetMap contributors, Open Database License 1.0; Geofabrik extract; government sources per source_metadata',
  'feature_readiness':[{k:v for k,v in row.items() if k!='source_validity'} for row in diag['feature_readiness']],
  'blocked_features':diag['blocked_features'],'spatial_reconciliation':diag['reconciliation'],'working_crs':'EPSG:3826',
  'numerical_policy':{'area_tolerance_m2':AREA_ATOL,'length_tolerance_m':LENGTH_ATOL,'source_geometries_repaired':False,'original_villages_changed':False,
   'ratios':'retain original floating results; no clipping to disguise errors; ratio tolerance from 0.1m² / original village area; road ratio tolerance 1e-10',
   'buffer_approximation':'Shapely buffer quad_segs=16, radii 300/500/800m; nested original polygons, no arbitrary snapping'},
  'population_linkage':'Tangbu accepted as same 456-village policy; provisional_match retained as evidence, not a reason for NA',
  'limitations':LIMITATIONS,'human_acceptance':'Codex assisted; DE handoff / DA acceptance / PM review pending'}

def export(ctx,frame,definitions,diag):
 validate_dataset(frame,ctx.base);contract=schema(ctx,frame,definitions,diag)
 payloads={f'data/processed/{STEM}.csv':frame.to_csv(index=False,lineterminator='\n',na_rep='__MISSING__',float_format='%.17g').encode('utf-8-sig'),
  f'data/processed/{STEM}_schema.json':(json.dumps(contract,ensure_ascii=False,indent=2)+'\n').encode('utf-8')}
 for rel,body in payloads.items():
  p=(ctx.root/rel).resolve();assert p.is_relative_to((ctx.root/'data/processed').resolve()) and rel not in ctx.bindings and rel not in ctx.handoff_bindings
  if p.exists():assert p.read_bytes()==body,('REFUSE DIFFERENT OUTPUT OVERWRITE',rel)
 for rel,body in payloads.items():
  p=ctx.root/rel
  if not p.exists():
   with p.open('xb') as stream:stream.write(body)
 saved_contract=json.loads((ctx.root/f'data/processed/{STEM}_schema.json').read_text(encoding='utf-8'))
 saved=read_csv(ctx.root/f'data/processed/{STEM}.csv',saved_contract);pd.testing.assert_frame_equal(frame,saved,check_exact=True);validate_dataset(saved,ctx.base)
 return {rel:{'path':rel,'bytes':(ctx.root/rel).stat().st_size,'sha256':sha(ctx.root/rel)} for rel in payloads}

def assert_protected_inputs(ctx):
 verify(ctx.root,ctx.bindings);verify(ctx.root,ctx.handoff_bindings)
 assert ctx.boundary.geometry.to_wkb().equals(ctx.bwkb)
 for family,h in ctx.original_geometry_hashes.items():assert geometry_digest(ctx.layers[family]['_source_original_geometry'])==h
 return True

def plots(ctx,frame,diag):
 import matplotlib.pyplot as plt
 from matplotlib import font_manager
 from matplotlib.patches import Patch
 font=Path('C:/Windows/Fonts/msjh.ttc')
 if font.is_file():
  font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=[font_manager.FontProperties(fname=str(font)).get_name(),'DejaVu Sans']
 plt.rcParams['axes.unicode_minus']=False;paths=[];bounds=ctx.city.bounds
 def finish(fig,name):
  fig.suptitle('Unit 2.6 交通設施資料處理與品質診斷；非正式Finding',fontsize=14)
  fig.tight_layout(rect=(0,.035,1,.95));fig.text(.01,.005,'0為本來源未觀測；灰色為缺失／無有效樣本，洋紅為處理失敗；不推定現實無設施。',fontsize=10)
  p=ctx.temp/name;fig.savefig(p,dpi=135,bbox_inches='tight');plt.show();paths.append(p.relative_to(ctx.root).as_posix())
 def boundary(ax):
  ctx.boundary.boundary.plot(ax=ax,color='grey',linewidth=.2)
  ax.set_xlim(bounds[0]-300,bounds[2]+300);ax.set_ylim(bounds[1]-300,bounds[3]+300);ax.set_axis_off()
 def map_col(ax,col,title,vmin=0,vmax=None,cmap='viridis'):
  g=ctx.boundary.copy();g[col]=frame[col].to_numpy(dtype=float,na_value=np.nan)
  g.plot(column=col,ax=ax,cmap=cmap,legend=True,vmin=vmin,vmax=vmax,linewidth=.12,edgecolor='grey',missing_kwds={'color':'lightgrey','label':'缺失／無有效樣本'})
  state=col+'_value_state'
  if state in frame:
   fail=frame[state].eq('spatial_processing_failed').to_numpy()
   if fail.any():g.loc[fail].plot(ax=ax,color='magenta',edgecolor='black')
  ax.set_title(title);ax.set_axis_off()
 fig,axs=plt.subplots(2,3,figsize=(16,12))
 for ax in axs.flat:boundary(ax)
 gpd.GeoSeries([ctx.road_union.intersection(ctx.city)],crs=3826).plot(ax=axs[0,0],color='grey',linewidth=.18)
 gpd.GeoSeries([ctx.major_union.intersection(ctx.city)],crs=3826).plot(ax=axs[0,0],color='crimson',linewidth=.32);axs[0,0].set_title('OSM線表示；紅為研究major六類')
 locations=ctx.signal_location_ledger
 for mask,color,label in [(locations.main_A,'royalblue','主要A位置'),(locations.geometry_B&~locations.main_A,'darkorange','僅幾何B位置')]:
  f=locations.loc[mask];x,y=ctx.to3826.transform(f.longitude.to_numpy(),f.latitude.to_numpy())
  axs[0,1].scatter(x,y,s=3,color=color,label=label)
 tests=ctx.layers['signals'].loc[ctx.layers['signals']._explicit_test&ctx.layers['signals']._coordinate_valid]
 axs[0,1].scatter(tests.geometry.x,tests.geometry.y,color='black',marker='x',s=13,label='排除機房測試');axs[0,1].legend(fontsize=7)
 axs[0,1].set_title('號誌唯一位置品質；非完整實體路口')
 gpd.GeoSeries([ctx.crossing_union.intersection(ctx.city)],crs=3826).plot(ax=axs[0,2],color='purple',linewidth=.4);axs[0,2].set_title('六層行穿標線面聯集，非設施數')
 gpd.GeoSeries(ctx.width_sample_geoms,crs=3826).plot(ax=axs[1,0],color='darkgreen',linewidth=.3);axs[1,0].set_title('計畫路寬尺寸標註；非縱向道路線')
 gpd.GeoSeries([ctx.mrt_buffers[500].intersection(ctx.city)],crs=3826).plot(ax=axs[1,1],color='lightblue',alpha=.8)
 mrt=ctx.layers['mrt'];near=mrt._coordinate_valid&mrt.geometry.intersects(ctx.city.buffer(800))
 mrt.loc[near].plot(ax=axs[1,1],color='navy',markersize=4);axs[1,1].set_title('2026入口與500m聯集，保留跨市來源')
 axs[1,2].set_axis_off();axs[1,2].text(.02,.88,'OSM：2025-01-01T21:21Z\n號誌：檔名2023，實際觀測日未認證\n行穿：2024封裝，非全年普查\n路寬：2023資源，計畫／地籍標註\nMRT：2026快照，非事故前環境\n混合標線型人行道：Blocked\n\n沒有兩套年度獨立設施觀測\n不提供交通暴露、VKT或因果識別',va='top',fontsize=13,transform=axs[1,2].transAxes)
 finish(fig,'source_layers_and_units.png')
 fig,axs=plt.subplots(2,2,figsize=(13,11))
 map_col(axs[0,0],'osm_road_density','指定OSM道路線密度（km/km²）')
 map_col(axs[0,1],'osm_major_road_ratio','研究major比例；非交通量占比',vmax=1)
 axs[1,0].hist(frame.osm_road_density.dropna().astype(float),bins=30);axs[1,0].set(title='456里道路密度；極端值保留',xlabel='km/km²',ylabel='行政里數')
 axs[1,1].hist(frame.osm_major_road_ratio.dropna().astype(float),bins=25);axs[1,1].set(title='六類major比例分布',xlabel='major / 全候選線長',ylabel='行政里數')
 finish(fig,'osm_density_and_major_ratio.png')
 fig,axs=plt.subplots(2,2,figsize=(13,11))
 map_col(axs[0,0],'observed_signal_location_density','主要A唯一位置密度（位置/km²）')
 difference=frame.signal_geometry_only_unique_location_count-frame.observed_unique_signal_location_count
 g=ctx.boundary.copy();g['_difference']=difference.to_numpy(dtype=float);g.plot(column='_difference',ax=axs[0,1],cmap='magma',legend=True,linewidth=.1,edgecolor='grey');axs[0,1].set_title('幾何B減保守A：來源區名品質影響');axs[0,1].set_axis_off()
 map_col(axs[1,0],'crosswalk_area_ratio','已觀測行穿標線面積比例，非設施完整性')
 signal=ctx.sources['signals'];axs[1,1].bar(['A','B','A無LCS-only','B無LCS-only'],[signal['main_A_locations'],signal['geometry_B_locations'],signal['main_A_without_LCS_locations'],signal['geometry_B_without_LCS_locations']])
 axs[1,1].set(title='號誌操作型口徑比較',ylabel='唯一座標位置數');axs[1,1].tick_params(axis='x',labelrotation=15)
 finish(fig,'signals_and_crosswalk_quality.png')
 fig,axs=plt.subplots(2,2,figsize=(13,11))
 map_col(axs[0,0],'annotated_road_width_sample_count','中點唯一歸里標註樣本數')
 map_col(axs[0,1],'median_annotated_road_width','計畫寬度標註中位數（m）；灰為無樣本')
 valid=frame.median_annotated_road_width.notna();axs[1,0].scatter(frame.loc[valid,'annotated_road_width_sample_count'].astype(float),frame.loc[valid,'median_annotated_road_width'].astype(float),s=12,alpha=.65)
 axs[1,0].set(title='標註樣本量與樣本中位數',xlabel='標註樣本數',ylabel='中位標註寬度m')
 axs[1,1].hist(frame.median_annotated_road_width.dropna().astype(float),bins=24);axs[1,1].set(title='有效標註里中位數分布；不補缺值',xlabel='m',ylabel='行政里數')
 finish(fig,'planned_width_samples_and_missingness.png')
 fig,axs=plt.subplots(2,3,figsize=(16,11))
 for ax,radius in zip(axs[0],RADII):map_col(ax,f'mrt_entrance_buffer_{radius}m_ratio',f'{radius}m直線聯集覆蓋；2026快照',vmax=1)
 map_col(axs[1,0],'mrt_entrance_density','已觀測入口密度，非站數／搭乘人次')
 g=ctx.boundary.copy();g['_radius_difference']=(frame.mrt_entrance_buffer_800m_ratio-frame.mrt_entrance_buffer_300m_ratio).to_numpy(dtype=float,na_value=np.nan)
 g.plot(column='_radius_difference',ax=axs[1,1],cmap='magma',legend=True,vmin=0,vmax=1,linewidth=.1,edgecolor='grey');axs[1,1].set_title('800m減300m覆蓋，非時間效果');axs[1,1].set_axis_off()
 axs[1,2].boxplot([frame[f'mrt_entrance_buffer_{r}m_ratio'].dropna().astype(float) for r in RADII],tick_labels=[str(r)+'m' for r in RADII]);axs[1,2].set(title='操作半徑敏感度；不等於步行可及性',ylabel='覆蓋比例')
 finish(fig,'mrt_entrances_and_radius_sensitivity.png')
 d=pd.DataFrame(diag['district_quality']);fig,axs=plt.subplots(2,3,figsize=(17,10))
 axs[0,0].barh(d.district,d.osm_road_density_area_weighted);axs[0,0].set(title='各區面積加權道路密度',xlabel='km/km²')
 positions=np.arange(len(d));area=d.fixed_area_sum_km2
 axs[0,1].barh(positions-.16,d.signal_main_locations/area,height=.3,label='保守A');axs[0,1].barh(positions+.16,d.signal_geometry_locations/area,height=.3,label='幾何B')
 axs[0,1].set_yticks(positions,d.district);axs[0,1].set(title='各區號誌位置密度口徑',xlabel='位置/km²');axs[0,1].legend(fontsize=8)
 axs[0,2].barh(d.district,d.width_missing_villages);axs[0,2].set(title='各區無路寬標註樣本里數',xlabel='行政里數')
 axs[1,0].barh(d.district,d.mrt500_ratio_area_weighted);axs[1,0].set(title='各區面積加權500m覆蓋',xlabel='比例',xlim=(0,1))
 stats=pd.DataFrame(diag['feature_statistics']).set_index('feature').loc[CORE]
 labels=['道路密度','major比例','號誌密度','行穿面積','標註路寬','MRT500m','入口密度'];ix=np.arange(len(labels))
 axs[1,1].barh(ix-.15,stats.zero_N,height=.3,label='觀測零');axs[1,1].barh(ix+.15,stats.missing_N,height=.3,label='NA')
 axs[1,1].set_yticks(ix,labels);axs[1,1].set(title='七候選零值與缺失分開',xlabel='行政里數');axs[1,1].legend(fontsize=8)
 axs[1,2].scatter(frame.fixed_village_area_km2.astype(float),frame.osm_road_density.astype(float),s=10,alpha=.6)
 for _,row in frame.nlargest(3,'osm_road_density').iterrows():axs[1,2].annotate(row.standard_village_name,(float(row.fixed_village_area_km2),float(row.osm_road_density)),fontsize=8)
 axs[1,2].set(title='小面積／極端密度品質檢查，未刪值',xlabel='原里面積km²',ylabel='道路km/km²')
 finish(fig,'district_source_quality_zero_missing_extremes.png')
 return paths
