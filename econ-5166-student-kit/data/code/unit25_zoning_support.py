"""Unit2.5 B2: fixed-snapshot zoning, Scheme B, explicit uncertainty.

The adopted linework candidates and method-sensitive union follow Unit1.6.
Buffer(0) is a comparison candidate only, never the adopted repair method.
Original villages, shapefiles, classification v1 and upstream data stay intact.
"""
from pathlib import Path
import hashlib,json,itertools
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely as s
from IPython.display import display,Markdown

HELPER='data/code/unit25_zoning_support.py';PRODUCER='data/code/prepare_taipei_dataset_b2.ipynb'
B2='taipei_dataset_b2';CW='urban_zoning_crosswalk_v2'
CORE=['residential','commercial','industrial','educational','park_green']
CLASSIFIED=sorted(CORE+['mixed_special_use','other_public_facilities','transportation','other_classified','agriculture_conservation','water'])
KEYS=['圖層','分區代碼','使用分區','分區說明','分區簡稱']
OUTKEY=['source_layer_code','original_zoning_code','original_zoning_name','original_zoning_description','original_zoning_abbreviation']
TARGETS={('25','IF','產業服務區','','產服'):('industrial',2,'IF產業服務不直接等同工業功能，沿Unit1.6指定研究修訂'),
 ('11','B','商業區','(供第二代展會中心使用)','商'):('commercial',1,'B明示第二代展會中心用途，沿Unit1.6指定研究修訂')}
THRESHOLDS=[50,70,80,90,95,99]
AREA_ATOL=0.1;CITY_AREA_ATOL=0.1;CITY_DERIVED_OVERLAP_ATOL=0.01;REPAIR_ATOL=1e-6;OVERLAY_GRID=1e-4
CSV={'encoding':'utf-8-sig','line_terminator':'LF','missing_sentinel':'__MISSING__','keep_default_na':False,'boolean_values':['True','False'],'original_empty_strings':'preserved'}
LIMITATIONS=[
 'B2 supplementary external environment only, not Dataset A clustering input; no coverage-based deletion of other datasets',
 'urban planning CRS EPSG:3826 is grade-B working convention only; raw has no PRJ and is not grade-A certified',
 'fixed planning snapshot; 2025-01 description, 2026-04-09 resource and DBF dates are different metadata, not legal effective dates',
 'not two independent annual zoning observations, not guaranteed pre-accident exposure, no causal or leakage-free prediction claim',
 'observed identified zoning shares, not complete zoning or actual land use; five core shares are not renormalized',
 'conditional bounds assume identified classifications and method-sensitive spatial envelope are adequate; not confidence intervals or certified legal/land-use truth',
 'upper bounds cannot all be jointly attained; midpoint is not a best estimate; no full-share imputation',
 '38 sensitive features use union of linework/structure/buffer0 polygon candidates as uncertainty, not a guaranteed true-error boundary',
 '105 algorithmically consistent linework repairs are research working geometries, not official or human certification',
 'fixed village overlap and holes preserved; village sums differ from city union; original AREA is not denominator',
 'Yangmingshan park feature remains unclassified; no classification from landscape, location or similar names',
 'observed zero is not confirmed absence; failed overlay retains village and NA, not zero',
 'no final coverage exclusion threshold, feature transformation, model fitting or inference',
 'Codex assisted execution; DE handoff / DA acceptance / PM review pending',
]

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for b in iter(lambda:stream.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()

def show(title,frame,block=18):
 display(Markdown('**'+title+'**'))
 if not len(frame):print('無符合紀錄')
 with pd.option_context('display.max_columns',None,'display.max_colwidth',None):
  for i in range(0,len(frame),block):display(frame.iloc[i:i+block])

def verify(root,bindings):
 for rel,h in bindings.items():assert sha(root/rel)==h,('INPUT HASH MISMATCH',rel)

def read_csv(path,contract,selected=None):
 names=[c['name'] for c in contract['columns']]
 assert list(pd.read_csv(path,encoding=contract['csv']['encoding'],nrows=0,keep_default_na=False))==names
 wanted=names if selected is None else list(selected)
 f=pd.read_csv(path,encoding=contract['csv']['encoding'],usecols=wanted,dtype='string',keep_default_na=False,na_values=[contract['csv']['missing_sentinel']])
 for c in contract['columns']:
  col=c['name'];dtype=c['dtype']
  if col not in f:continue
  if dtype=='boolean':
   assert f[col].dropna().isin(['True','False']).all()
   f[col]=f[col].map({'True':True,'False':False}).astype('boolean')
  elif dtype=='Int64':f[col]=pd.to_numeric(f[col],errors='raise').astype('Int64')
  elif dtype=='Float64':f[col]=f[col].map(lambda x:pd.NA if pd.isna(x) else float(x)).astype('Float64')
  else:assert dtype=='string',(col,dtype)
 return f[wanted]

def parts(g):
 if g.is_empty:return [],[]
 if g.geom_type=='Polygon':return [g],[]
 if hasattr(g,'geoms'):
  polys=[];other=[]
  for p in g.geoms:
   a,b=parts(p);polys+=a;other+=b
  return polys,other
 return [],[g]

def poly(g):
 p,_=parts(g);return s.union_all(p) if p else s.Polygon()

class Context:
 def __init__(self,root,bindings,handoff_bindings):
  self.root=Path(root);self.bindings=bindings;self.handoff_bindings=handoff_bindings
  verify(self.root,bindings);verify(self.root,handoff_bindings)
  self.raw=gpd.read_file(self.root/'data/raw/細計-面.shp',encoding='cp950',engine='pyogrio')
  assert len(self.raw)==15518 and self.raw.crs is None
  assert self.raw.geom_type.value_counts().to_dict()=={'Polygon':15508,'MultiPolygon':10}
  self.raw_wkb=self.raw.geometry.to_wkb().copy()
  self.work=self.raw.copy().set_crs(epsg=3826)
  self.ug=np.asarray(self.raw.geometry.array,dtype=object)
  self.original_valid=s.is_valid(self.ug);self.bad=np.flatnonzero(~self.original_valid)
  assert len(self.bad)==143 and np.isfinite(self.raw.total_bounds).all()
  b=gpd.read_file(self.root/'data/raw/G97_A_CAVLGE_P.shp',encoding='utf-8',engine='pyogrio')
  contract=json.loads((self.root/'data/processed/taipei_village_base_schema.json').read_text(encoding='utf-8'))
  self.base=read_csv(self.root/'data/processed/taipei_village_base.csv',contract).sort_values('village_id').reset_index(drop=True)
  assert self.base.shape==(456,41) and self.base.village_id.is_unique
  assert len(b)==456 and b.crs.to_epsg()==3826 and b.CPTVID.is_unique
  self.boundary=b.set_index('CPTVID').loc[self.base.village_id].reset_index()
  self.bg=np.asarray(self.boundary.geometry.array,dtype=object)
  self.bwkb=self.boundary.geometry.to_wkb().copy()
  assert s.is_valid(self.bg).all() and (s.area(self.bg)>0).all()
  np.testing.assert_allclose(s.area(self.bg),self.base.village_area_m2.astype(float),rtol=0,atol=1e-6)
  self.city=s.union_all(self.bg)
  self.districts={d:s.union_all(self.bg[self.base.district_name.eq(d).to_numpy()]) for d in sorted(self.base.district_name.unique())}
  self.oldcw=pd.read_csv(self.root/'data/processed/urban_zoning_crosswalk.csv',encoding='utf-8-sig',dtype='string',keep_default_na=False)
  assert self.oldcw.shape==(296,12) and not self.oldcw.duplicated(OUTKEY).any()
  rawkeys=self.raw[KEYS].fillna('').rename(columns=dict(zip(KEYS,OUTKEY)))
  self.join=rawkeys.merge(self.oldcw,on=OUTKEY,how='left',validate='many_to_one',indicator=True)
  assert len(self.join)==15518 and self.join['_merge'].eq('both').all()
  self.oldcat=self.join.research_zoning_category.to_numpy()
  assert int((self.oldcat=='non_zoning_boundary').sum())==3 and int((self.oldcat=='unclassified').sum())==1
  self.rawids=np.array([bindings['data/raw/細計-面.shp'][:12]+':'+str(i+1).zfill(5) for i in range(15518)])
  self.categories=sorted(set(self.oldcat)-{'non_zoning_boundary','unclassified'})
  assert self.categories==CLASSIFIED
  self.area_cache={};self.district_area_cache={};self.source_union_cache={};self.source_cross_cache={};self.diagnostics={};self.failures={}
  self.facts={'raw_records':15518,'raw_types':self.raw.geom_type.value_counts().to_dict(),'raw_invalid':143,
    'shapely_version':s.__version__,'GEOS_version':s.geos_version_string,'zoning_overlay_precision_grid_m':OVERLAY_GRID,
    'raw_crs':None,'working_crs':'EPSG:3826','crs_evidence':'B; working convention, not official grade A',
    'raw_bounds':[float(x) for x in self.raw.total_bounds],'fixed_villages':456,'districts':12,
    'city_original_union_km2':float(self.city.area/1e6),'village_area_sum_km2':float(self.base.village_area_km2.sum()),
    'city_partition_aggregate_tolerance_m2':CITY_AREA_ATOL,
    'old_crosswalk_shape':[296,12],'all_raw_compound_keys_matched':True,'area_tolerance_m2':AREA_ATOL,
   'repair_agreement_tolerance_m2':REPAIR_ATOL,'positive_overlap_rule':'strict source area > 0; no threshold dropping',
   'derived_city_overlap_tolerance_m2':CITY_DERIVED_OVERLAP_ATOL,
    'human_acceptance':'Codex assisted; DE / DA / PM pending'}
  print('Input identity, 15518 features, 296 keys and original 456 villages verified',flush=True)

 def repair(self):
  trials={'linework':s.make_valid(self.ug[self.bad],method='linework',keep_collapsed=True),
   'structure':s.make_valid(self.ug[self.bad],method='structure',keep_collapsed=True),'buffer0':s.buffer(self.ug[self.bad],0)}
  polys={k:np.asarray([poly(g) for g in gs],dtype=object) for k,gs in trials.items()}
  self.reference=self.ug.copy();self.reference[self.bad]=polys['linework']
  rows=[];sensitive=[];envelopes=[]
  for j,i in enumerate(self.bad):
   l,st,bf=[polys[k][j] for k in ['linework','structure','buffer0']]
   d1=l.symmetric_difference(st).area;d2=l.symmetric_difference(bf).area
   pp,rem=parts(trials['linework'][j])
   consistent=not(st.is_empty or bf.is_empty) and l.is_valid and l.area>0 and max(d1,d2)<=REPAIR_ATOL
   if not consistent:sensitive.append(int(i));envelopes.append(s.union_all([l,st,bf]))
   rows.append({'source_record_id':self.rawids[i],'source_row_1based':int(i+1),'original_number':str(self.raw.iloc[i]['編號']),
    'original_layer':str(self.raw.iloc[i]['圖層']),'original_zoning_code':str(self.raw.iloc[i]['分區代碼']),
    'original_zoning_name':str(self.raw.iloc[i]['使用分區']),'original_category':self.oldcat[i],
    'original_reason':s.is_valid_reason(self.ug[i]),'original_area_diagnostic_m2':self.ug[i].area,
    'linework_area_m2':l.area,'structure_area_m2':st.area,'buffer0_comparison_area_m2':bf.area,
    'linework_structure_symdiff_m2':d1,'linework_buffer0_symdiff_m2':d2,
    'nonpolygon_count':len(rem),'nonpolygon_types':','.join(sorted({x.geom_type for x in rem})),
    'nonpolygon_length_m':sum(x.length for x in rem),'polygon_components':len(parts(l)[0]),
    'fragments_below_1m2':sum(x.area<1 for x in parts(l)[0]),
    'status':'adopted_linework_algorithmic_candidate' if consistent else 'withheld_method_sensitive',
    'human_or_official_certified':False})
  self.repair_ledger=pd.DataFrame(rows)
  self.sensitive=np.zeros(15518,dtype=bool);self.sensitive[sensitive]=True
  self.sensitive_union=s.union_all(envelopes)
  self.sensitive_candidate_geoms=envelopes
  assert len(sensitive)==38 and len(self.bad)-len(sensitive)==105
  assert s.is_valid(self.reference).all() and (s.area(self.reference)>0).all()
  assert all(bytes(self.reference[i].wkb)==bytes(self.ug[i].wkb) for i in np.flatnonzero(self.original_valid))
  groups={}
  for i,g in enumerate(self.ug):groups.setdefault(bytes(g.wkb),[]).append(i)
  self.duplicate_groups=[v for v in groups.values() if len(v)>1]
  assert len(self.duplicate_groups)==5 and sum(map(len,self.duplicate_groups))==11
  self.duplicate_ledger=pd.DataFrame([{'duplicate_group':j+1,'source_record_id':self.rawids[i],'source_row_1based':i+1,'category':self.oldcat[i],**self.raw.iloc[i][KEYS].fillna('').to_dict()} for j,ids in enumerate(self.duplicate_groups) for i in ids])
  self.facts.update({'adopted_invalid_linework_candidates':105,'withheld_method_sensitive':38,
   'linework_nonpolygon_records':int(self.repair_ledger.nonpolygon_count.gt(0).sum()),
   'linework_nonpolygon_parts':int(self.repair_ledger.nonpolygon_count.sum()),
   'sensitive_candidate_union_city_km2':self.sensitive_union.intersection(self.city).area/1e6,
   'exact_WKB_duplicate_groups':5,'exact_WKB_duplicate_records':11})
  print('143 invalid features: 105 linework candidates / 38 sensitive unions; original valid features untouched',flush=True)

 def revise_classification(self):
  cw=self.oldcw.copy();cw['original_record_count']=pd.to_numeric(cw.original_record_count).astype('Int64')
  cw['original_research_zoning_category']=cw.research_zoning_category
  cw['classification_revision_applied']=pd.Series(False,index=cw.index,dtype='boolean')
  cw['classification_revision_reason']=pd.Series('',index=cw.index,dtype='string')
  cw['revision_evidence']=pd.Series('',index=cw.index,dtype='string')
  cw['revision_evidence_status']=pd.Series('unchanged_original_evidence',index=cw.index,dtype='string')
  cw['classification_version']=pd.Series('v2_unit25',index=cw.index,dtype='string')
  cw['affected_record_ids_json']=pd.Series('[]',index=cw.index,dtype='string')
  cw['revision_affected_record_count']=pd.Series(0,index=cw.index,dtype='Int64')
  cw['revision_reference_union_area_m2']=pd.Series(0.,index=cw.index,dtype='Float64')
  self.revised_records=np.zeros(15518,dtype=bool)
  revisions=[]
  for key,(oldcategory,expected,reason) in TARGETS.items():
   mask=np.ones(len(cw),dtype=bool);rawmask=np.ones(15518,dtype=bool)
   for col,val in zip(OUTKEY,key):mask&=cw[col].eq(val).to_numpy();rawmask&=self.join[col].eq(val).to_numpy()
   assert mask.sum()==1 and rawmask.sum()==expected and cw.loc[mask,'research_zoning_category'].iloc[0]==oldcategory
   assert int(cw.loc[mask,'original_record_count'].iloc[0])==expected
   area=s.union_all(self.reference[rawmask]).area
   cw.loc[mask,'research_zoning_category']='mixed_special_use'
   cw.loc[mask,'classification_revision_applied']=True
   cw.loc[mask,'classification_revision_reason']=reason
   cw.loc[mask,'revision_evidence']='data/code/taipei_data_integration_readiness.ipynb#section-5; Unit2.5 explicit instruction; original five-field compound key'
   cw.loc[mask,'revision_evidence_status']='research_revision_adopted_unit25_not_legal_change'
   cw.loc[mask,'affected_record_ids_json']=json.dumps(self.rawids[rawmask].tolist(),ensure_ascii=False)
   cw.loc[mask,'revision_affected_record_count']=expected
   cw.loc[mask,'revision_reference_union_area_m2']=area
   self.revised_records|=rawmask
   revisions.append({'compound_key':list(key),'old_category':oldcategory,'new_category':'mixed_special_use','records':expected,'reference_union_m2':area})
  assert int(cw.classification_revision_applied.sum())==2 and self.revised_records.sum()==3
  assert abs(s.union_all(self.reference[self.revised_records]).area-72611.009)<1
  unchanged=~cw.classification_revision_applied
  for col in self.oldcw:
   if col=='original_record_count':assert cw.loc[unchanged,col].astype('string').eq(self.oldcw.loc[unchanged,col]).all()
   else:assert cw.loc[unchanged,col].eq(self.oldcw.loc[unchanged,col]).all()
  newjoin=self.join[OUTKEY].merge(cw[OUTKEY+['research_zoning_category']],on=OUTKEY,validate='many_to_one')
  self.newcat=newjoin.research_zoning_category.to_numpy()
  assert int((self.newcat!=self.oldcat).sum())==3
  self.v2=cw;self.revisions=pd.DataFrame(revisions)
  self.facts['classification_revision']={'keys':2,'records':3,'reference_union_m2':s.union_all(self.reference[self.revised_records]).area,'research_only':True}

 def source_union(self,mask,grid):
  key=(np.flatnonzero(mask).tobytes(),grid)
  if key not in self.source_union_cache:self.source_union_cache[key]=s.union_all(self.reference[mask],grid_size=grid)
  return self.source_union_cache[key]

 def scenario(self,categories,classification_pending=False,label='v2',legacy_double=False):
  grid=None if legacy_double else OVERLAY_GRID
  nonpolygon_audit=[]
  def polygon_only(g,operation):
   pp,rem=parts(g)
   if rem:nonpolygon_audit.append({'scenario':label,'operation':operation,'nonpolygon_parts':len(rem),'types':','.join(sorted({r.geom_type for r in rem})),'length_m':sum(r.length for r in rem)})
   return s.union_all(pp,grid_size=grid) if pp else s.Polygon()
  def union(gs,operation):return polygon_only(s.union_all(gs,grid_size=grid),operation)
  def intersection(a,b):return s.intersection(a,b,grid_size=grid)
  def difference(a,b,operation):return polygon_only(s.difference(a,b,grid_size=grid),operation)
  double_unions={c:self.source_union(categories==c,None) for c in self.categories}
  unions={c:polygon_only(self.source_union(categories==c,grid),'class_union_'+c) for c in self.categories}
  classified=union(list(unions.values()),'classified_union');unknown=union(self.reference[categories=='unclassified'],'unclassified_union')
  candidate=union([classified,unknown],'candidate_union');cross=[];contacts=[]
  print('Scenario',label,'class unions ready; precision grid',grid,flush=True)
  for a,b in itertools.combinations(self.categories,2):
   pairkey=(sha_bytes(unions[a].wkb),sha_bytes(unions[b].wkb),grid)
   if pairkey not in self.source_cross_cache:self.source_cross_cache[pairkey]=intersection(unions[a],unions[b])
   x=self.source_cross_cache[pairkey];p,other=parts(x)
   if p:cross.append(union(p,'cross_'+a+'_'+b))
   contacts.append({'scenario':label,'category_a':a,'category_b':b,'positive_area_m2':x.area,'nonarea_parts':len(other),'nonarea_length_m':sum(g.length for g in other)})
  print('Scenario',label,'55 class-pair intersections ready',flush=True)
  cross_union=union(cross,'cross_union');raw_cu=intersection(classified,unknown);cu=polygon_only(raw_cu,'classified_unknown_intersection')
  _,unknown_contacts=parts(raw_cu)
  contacts.append({'scenario':label,'category_a':'classified','category_b':'unclassified','positive_area_m2':raw_cu.area,'nonarea_parts':len(unknown_contacts),'nonarea_length_m':sum(g.length for g in unknown_contacts)})
  review=union(self.reference[self.revised_records],'pending_classification_union') if classification_pending else s.Polygon()
  withheld=union([cross_union,cu,self.sensitive_union,review],'withheld_union')
  effective={c:difference(g,withheld,'effective_'+c) for c,g in unions.items()}
  identified=difference(classified,withheld,'identified_union')
  print('Scenario',label,'reliable class differences ready',flush=True)
  # Original city/village boundaries are never put onto the overlay grid.
  # Their actual original geometries still define the final study-domain clip.
  uncovered=self.city.difference(candidate)
  # Keep the original study-domain edge off the zoning precision grid.
  # Only zoning-derived uncertainty is gridded, then combine the untouched
  # original-city uncovered geometry in double precision.
  zoning_uncertain=union([unknown,cross_union,cu,self.sensitive_union,review],'zoning_uncertainty_union')
  uncertainty=poly(s.union_all([zoning_uncertain.intersection(self.city),uncovered]))
  partition_error=identified.intersection(self.city).area+uncertainty.area-self.city.area
  iq_polygon=poly(identified.intersection(uncertainty))
  iq_overlap=iq_polygon.area
  print('City partition error m2',partition_error,'I/Q overlap m2',iq_overlap,flush=True)
  if abs(partition_error)>CITY_AREA_ATOL or iq_overlap>CITY_AREA_ATOL:
   debug=self.root/'data/temp/unit25_validation/partition_debug';debug.mkdir(parents=True,exist_ok=True)
   for name,g in {'classified':classified,'candidate':candidate,'identified':identified,'uncertainty':uncertainty,'zoning_uncertain':zoning_uncertain,'uncovered':uncovered,'withheld':withheld,'city':self.city}.items():(debug/(name+'.wkb')).write_bytes(g.wkb)
  # City identities aggregate complex seams across 456 original geometries.
  # A separate 0.1m² city budget (<4e-10 of city area) does not relax the
  # 0.1m² checks on each village; derived class-pair overlap is stricter,
  # checked separately at 0.01m².
  assert abs(partition_error)<=CITY_AREA_ATOL,('CITY_PARTITION',label,partition_error)
  assert iq_overlap<=CITY_AREA_ATOL,('CITY_IQ_OVERLAP',label,iq_overlap)
  residual_audit=[]
  check_pairs=itertools.combinations(self.categories,2) if not legacy_double else [('agriculture_conservation','park_green'),('other_public_facilities','park_green')]
  for a,b in check_pairs:
   post=poly(intersection(effective[a],effective[b]))
   inside=post.intersection(self.city).area if post.area>0 else 0.
   raw_pair=self.source_cross_cache[(sha_bytes(unions[a].wkb),sha_bytes(unions[b].wkb),grid)]
   source_supported=post.intersection(poly(raw_pair)).intersection(self.city).area if inside>0 else 0.
   residual_audit.append({'scenario':label,'category_a':a,'category_b':b,'derived_global_overlap_m2':post.area,'derived_city_overlap_m2':inside,'source_supported_residual_m2':source_supported})
   if not legacy_double and (inside>CITY_DERIVED_OVERLAP_ATOL or source_supported>AREA_ATOL):
    debug=self.root/'data/temp/unit25_validation/overlay_debug';debug.mkdir(parents=True,exist_ok=True)
    for name,g in {'class_a':unions[a],'class_b':unions[b],'effective_a':effective[a],'effective_b':effective[b],'withheld':withheld,'post_overlap':post,'city':self.city}.items():(debug/(name+'.wkb')).write_bytes(g.wkb)
    detail={'scenario':label,'category_a':a,'category_b':b,'residual_overlap_m2':post.area,'residual_inside_city_m2':post.intersection(self.city).area,'a_valid':effective[a].is_valid,'b_valid':effective[b].is_valid}
    (debug/'details.json').write_text(json.dumps(detail,ensure_ascii=False,indent=2),encoding='utf-8')
    raise AssertionError('Post-Scheme-B derived class overlap: '+str(detail))
  sets={'candidate_zoning':candidate,'classified_candidate':classified,'identified_zoning':identified,'uncertain_union':uncertainty,
   'unclassified':unknown,'cross_class_overlap':cross_union,'classified_unclassified_overlap':cu,
   'geometry_sensitive':self.sensitive_union,'uncovered':uncovered,
   'non_zoning_boundary':union(self.reference[categories=='non_zoning_boundary'],'nonzoning_union'),
   'classification_pending':review}
  stats=pd.DataFrame([{'scenario':label,'category':c,'raw_original_area_diagnostic_m2':float(s.area(self.ug[categories==c]).sum()),
    'linework_reference_area_sum_m2':float(s.area(self.reference[categories==c]).sum()),'same_class_union_m2':unions[c].area,
    'same_class_duplicate_removed_m2':float(s.area(self.reference[categories==c]).sum()-double_unions[c].area),
    'overlay_precision_area_change_m2':unions[c].area-double_unions[c].area,
    'identified_city_union_m2':effective[c].intersection(self.city).area,'source_records':int((categories==c).sum())} for c in self.categories])
  print('Scenario',label,'identified city km²',identified.intersection(self.city).area/1e6,'uncertain km²',uncertainty.area/1e6,flush=True)
  return {'label':label,'class_unions':unions,'effective':effective,'sets':sets,'contact_audit':pd.DataFrame(contacts),'post_overlay_residual_audit':pd.DataFrame(residual_audit),'derived_nonpolygon_audit':pd.DataFrame(nonpolygon_audit),'union_stats':stats,'overlay_grid_m':grid,'city_partition_residual_m2':partition_error,'city_I_Q_overlap_m2':iq_overlap,'I_Q_polygon_overlap':iq_polygon}

 def village_areas(self,g):
  key=sha_bytes(g.wkb)
  if key in self.area_cache:return self.area_cache[key].copy()
  values=np.zeros(456,dtype=float)
  for district,dshape in self.districts.items():
   ids=np.flatnonzero(self.base.district_name.eq(district).to_numpy())
   try:
    clipped=g.intersection(dshape)
    self.district_area_cache[(key,district)]=clipped.area
    values[ids]=s.area(s.intersection(self.bg[ids],clipped))
   except s.errors.GEOSException:
    for i in ids:
     try:values[i]=self.bg[i].intersection(g).area
     except s.errors.GEOSException as error:
      self.failures.setdefault(int(i),[]).append(str(error));values[i]=np.nan
  check=np.array([0,100,200,300,455])
  np.testing.assert_allclose(values[check],s.area(s.intersection(self.bg[check],g)),rtol=1e-10,atol=.001)
  self.area_cache[key]=values.copy();return values

def sha_bytes(value):return hashlib.sha256(value).hexdigest()

def count_positive_intersections(villages,geometries):
 if not len(geometries):return np.zeros(len(villages),dtype=np.int64)
 shapes=np.asarray(geometries,dtype=object);pairs=s.STRtree(shapes).query(villages,predicate='intersects')
 values=np.zeros(len(villages),dtype=np.int64)
 for start in range(0,pairs.shape[1],5000):
  left,right=pairs[:,start:start+5000]
  positive=s.area(s.intersection(villages[left],shapes[right]))>0
  np.add.at(values,left[positive],1)
 return values

def make_b2(ctx,scenario):
 data={};definitions=[];n=456
 def add(name,values,dtype,meaning,unit='not applicable',source='Unit2.5 Scheme B derived geometry',missing='處理失敗保留NA，不補零'):
  assert name not in data,('DUPLICATE_DERIVED_COLUMN',name)
  values=pd.Series([values]*n) if pd.api.types.is_scalar(values) else pd.Series(values).reset_index(drop=True)
  data[name]=values.astype(dtype)
  definitions.append({'name':name,'dtype':dtype,'definition':meaning,'unit':unit,'source':source,'missing_rule':missing})
 for col in ['village_id','boundary_code','district_name','standard_village_name','verification_status','geometry_quality_flag']:
  add(col,ctx.base[col],'string','Unit2.2固定里主表之'+col,source='Unit2.2 village base',missing='不可缺失，糖廍正常納入')
 add('fixed_village_area_m2',ctx.base.village_area_m2,'Float64','完整原固定里幾何面積，所有比例的共同分母','m²','Unit2.2 village_area_m2','正值不可缺失')
 add('fixed_village_area_km2',ctx.base.village_area_km2,'Float64','原固定里面積，無修補／填洞／去重疊','km²','Unit2.2 village_area_km2','正值不可缺失')
 for col,val,meaning in [
  ('crosswalk_version','v2_unit25','指定兩鍵修訂，非法定分區變更'),('working_crs','EPSG:3826','記憶體工作CRS，不補原PRJ'),
  ('crs_evidence_grade','B','strongly supported工作假設，非A級官方認證'),
  ('snapshot_source_description','2025-01','沿Unit1.4官方頁內容時間，非個案生效日'),
  ('snapshot_resource_version','2026-04-09','Unit1.4已逐bytes核對官方資源版本，非生效日'),
  ('analysis_role','supplementary_external_zoning','補充環境，不直接入A或排除其他資料集')]:
  add(col,val,'string',meaning,source='Unit1.4–1.6 evidence / Unit2.5 working specification',missing='原時間語義限制保留')
 with (ctx.root/'data/raw/細計-面.dbf').open('rb') as stream:header=stream.read(4)
 add('source_dbf_header_date',f'{1900+header[1]:04d}-{header[2]:02d}-{header[3]:02d}','string','DBF標頭記錄日期，與資源／網頁／法定生效日不同',source='raw DBF header bytes')
 add('legal_snapshot_effective_date',pd.NA,'string','所有個案分區共同法定生效日尚未取得',missing='未知為NA，不能宣稱事故前環境')
 add('year_specific_observation',False,'boolean','單一固定快照，無獨立2024／2025分區觀測')
 area=ctx.base.village_area_m2.astype('Float64')
 quality_names={
  'candidate_zoning':'candidate_zoning_coverage_share','classified_candidate':'classified_candidate_coverage_share',
  'identified_zoning':'identified_zoning_coverage_share','uncertain_union':'uncertain_union_share',
  'unclassified':'unclassified_coverage_share','cross_class_overlap':'cross_class_overlap_share',
  'classified_unclassified_overlap':'classified_unclassified_overlap_share','geometry_sensitive':'geometry_sensitive_coverage_share',
  'uncovered':'uncovered_share','non_zoning_boundary':'non_zoning_boundary_share'}
 for name,share in quality_names.items():
  print('Village intersections:',name,flush=True)
  values=ctx.village_areas(scenario['sets'][name])
  add(name+'_area_m2',values,'Float64',name+'幾何與原里實際交集面積；來源集合可能相互重疊','m²')
  add(name+'_area_km2',values/1e6,'Float64',name+'交集面積','km²')
  add(share,data[name+'_area_m2']/area,'Float64',name+'交集／完整里面積，非各來源可相加的互斥分類','fraction')
 quality_arrays=np.asarray([data[c].to_numpy(dtype=float,na_value=np.nan) for c in quality_names.values()])
 quality_excess=np.nanmax(np.vstack([np.zeros(n)]+[data[name+'_area_m2'].to_numpy(dtype=float,na_value=np.nan)-area.to_numpy(dtype=float) for name in quality_names]),axis=0)
 add('quality_share_roundoff_flag',np.any((quality_arrays<0)|(quality_arrays>1),axis=0),'boolean','品質覆蓋比例因浮點交集略超0–1；不clip數值，超額須在每里0.1m²內')
 add('quality_share_roundoff_max_excess_m2',quality_excess,'Float64','十個品質來源中超過完整里面積之最大正超額，零代表無超額；只作數值稽核','m²')
 category_values={}
 for category in ctx.categories:
  print('Village class intersections:',category,flush=True)
  values=ctx.village_areas(scenario['effective'][category]);category_values[category]=values
  add(category+'_identified_area_m2',values,'Float64',category+'經同類union及方案B扣除不確定範圍後已辨識面積','m²')
  add(category+'_identified_area_km2',values/1e6,'Float64',category+'可靠工作分類面積，不等同實際土地使用','km²')
  name=category+'_observed_share' if category in CORE else category+'_identified_share'
  add(name,data[category+'_identified_area_m2']/area,'Float64',category+'已辨識面積／完整里面積，不以已辨識總面積為分母','fraction')
 main=sum((data[c+'_identified_area_m2'] for c in CORE),start=pd.Series(0.,index=range(n),dtype='Float64'))
 other=sum((data[c+'_identified_area_m2'] for c in ctx.categories if c not in CORE),start=pd.Series(0.,index=range(n),dtype='Float64'))
 for name,v,meaning in [('core_five_identified',main,'五核心已辨識面積，不重新正規化'),('other_noncore_identified',other,'其餘六個已分類類別合計，與other_classified單一類別分開；混合特殊是已知類別，不當未知')]:
  add(name+'_area_m2',v,'Float64',meaning,'m²');add(name+'_share',v/area,'Float64',meaning+'／完整里面積','fraction')
 uncertain=data['uncertain_union_share']
 for category in CORE:
  observed=data[category+'_observed_share'];upper=np.minimum(1,observed+uncertain).astype('Float64')
  add(category+'_conditional_lower_bound',observed,'Float64','條件式L等於已辨識覆蓋；假定既有工作分類及包絡足夠，不是信賴區間','fraction')
  add(category+'_conditional_upper_bound',upper,'Float64','條件式U=min(1,L+不確定聯集比例)，非官方真值認證且各類上界不能同時實現','fraction')
  add(category+'_conditional_bound_width',upper-observed,'Float64','U−L；不以中點補成最佳估計','fraction')
  add(category+'_observed_zero_flag',data[category+'_identified_area_m2'].eq(0),'boolean','已辨識面積為0，不等於已證實該分區不存在')
  state=['processing_failure' if pd.isna(l) or pd.isna(q) else ('observed_zero_not_confirmed_absent' if l==0 and q>0 else 'observed_positive_with_uncertainty' if q>0 else 'complete_working_coverage_under_assumptions') for l,q in zip(observed,uncertain)]
  add(category+'_interpretation_state',state,'string','區分已觀測零／部分覆蓋／處理失敗，不宣稱實際分區確定零')
 residual=data['identified_zoning_area_m2']+data['uncertain_union_area_m2']-area
 add('area_partition_residual_m2',residual,'Float64','I＋Q−A，只供浮點稽核；不clip數值掩蓋差異','m²')
 add('classified_sum_residual_m2',main+other-data['identified_zoning_area_m2'],'Float64','各類已辨識面積和−已辨識聯集I','m²')
 add('candidate_uncovered_residual_m2',data['candidate_zoning_area_m2']+data['uncovered_area_m2']-area,'Float64','候選覆蓋＋未覆蓋−完整里面積','m²')
 add('identified_uncertain_overlap_m2',ctx.village_areas(scenario['I_Q_polygon_overlap']),'Float64','I與Q實際交集之面積部分；線／點不算面積，只容許已明示浮點誤差','m²')
 for t in THRESHOLDS:add(f'coverage_ge_{t}',data['identified_zoning_coverage_share'].ge(t/100),'boolean',f'可靠辨識覆蓋≥{t}%候選旗標，不是正式排除政策')
 for name,geoms,meaning in [
  ('invalid_source_reference_intersection_count',ctx.reference[ctx.bad],'原無效143筆linework面參考與里正面積相交數'),
  ('adopted_repair_intersection_count',ctx.reference[np.flatnonzero(~ctx.original_valid&~ctx.sensitive)],'105算法一致linework候選與里正面積相交數'),
  ('method_sensitive_intersection_count',ctx.sensitive_candidate_geoms,'38方法敏感的三候選面聯集與里正面積相交數')]:
  add(name,count_positive_intersections(ctx.bg,geoms),'Int64',meaning+'；不是官方認證修復','source feature count')
 failed=pd.Series([i in ctx.failures for i in range(n)],dtype='boolean')
 add('overlay_failed_flag',failed,'boolean','幾何交集實際失敗，保留ID與NA；不將失敗當0')
 add('processing_status',pd.Series(np.where(failed,'failed_overlay','success_retained_uncertainty'),dtype='string'),'string','成功呈現可靠資訊與不確定性，不代表完整分區已知')
 add('processing_failure_reason',[json.dumps(ctx.failures.get(i,[]),ensure_ascii=False) for i in range(n)],'string','交集失敗訊息JSON；[]表示本輪未失敗')
 # In the unlikely event of a local GEOS failure, all derived numeric/quality
 # values for that village remain unknown; never replace them with zero.
 if failed.any():
  metadata=set(ctx.base.columns)|{'fixed_village_area_m2','fixed_village_area_km2','year_specific_observation'}
  for d in definitions:
   col=d['name']
   if d['dtype'] in ['Float64','Int64','boolean'] and col not in metadata and col!='overlay_failed_flag':data[col]=data[col].mask(failed,pd.NA)
  for category in CORE:data[category+'_interpretation_state']=data[category+'_interpretation_state'].mask(failed,'processing_failure')
 frame=pd.DataFrame(data)
 assert list(frame)==[d['name'] for d in definitions] and len(frame.columns)==len(set(frame.columns))
 try:validate_b2(frame,ctx.base)
 except Exception:
  debug=ctx.root/'data/temp/unit25_validation';debug.mkdir(parents=True,exist_ok=True)
  frame.to_pickle(debug/'failed_numeric_validation.pkl')
  raise
 return frame,definitions

def validate_b2(f,base):
 assert len(f)==456 and f.village_id.is_unique and f.village_id.notna().all()
 assert set(f.village_id)==set(base.village_id) and f.district_name.nunique()==12
 assert 'year' not in f and 'specification' not in f
 assert f.village_id.str.fullmatch(r'\d{10}').all()
 lookup=base.set_index('village_id')
 for col in ['district_name','standard_village_name','boundary_code','verification_status']:assert f[col].eq(f.village_id.map(lookup[col])).all()
 assert f.fixed_village_area_m2.eq(f.village_id.map(lookup.village_area_m2)).all()
 assert f.fixed_village_area_km2.eq(f.village_id.map(lookup.village_area_km2)).all()
 good=~f.overlay_failed_flag
 for col in f:
  if col.endswith(('_area_m2','_area_km2')):
   assert f.loc[good,col].notna().all() and f.loc[good,col].ge(0).all(),col
  if col.endswith(('_share','_conditional_lower_bound','_conditional_upper_bound','_conditional_bound_width')):
   quality_columns=['candidate_zoning_coverage_share','classified_candidate_coverage_share','identified_zoning_coverage_share','uncertain_union_share','unclassified_coverage_share','cross_class_overlap_share','classified_unclassified_overlap_share','geometry_sensitive_coverage_share','uncovered_share','non_zoning_boundary_share']
   tolerance=AREA_ATOL/f.loc[good,'fixed_village_area_m2'] if col in quality_columns else 0.
   assert f.loc[good,col].notna().all() and ((f.loc[good,col]>=-tolerance)&(f.loc[good,col]<=1+tolerance)).all(),(col,float(f.loc[good,col].min()),float(f.loc[good,col].max()))
 assert f.loc[good,'quality_share_roundoff_max_excess_m2'].le(AREA_ATOL).all()
 expected_roundoff=((f[quality_columns]<0)|(f[quality_columns]>1)).any(axis=1)
 assert f.loc[good,'quality_share_roundoff_flag'].eq(expected_roundoff.loc[good]).all()
 for col in ['area_partition_residual_m2','classified_sum_residual_m2','candidate_uncovered_residual_m2','identified_uncertain_overlap_m2']:
  assert f.loc[good,col].abs().le(AREA_ATOL).all(),(col,float(f.loc[good,col].abs().max()))
 np.testing.assert_allclose((f.identified_zoning_area_m2+f.uncertain_union_area_m2).loc[good].astype(float),f.fixed_village_area_m2.loc[good].astype(float),rtol=0,atol=AREA_ATOL)
 category_columns=[c+'_identified_area_m2' for c in CLASSIFIED]
 np.testing.assert_allclose(f.loc[good,category_columns].sum(axis=1).astype(float),f.loc[good,'identified_zoning_area_m2'].astype(float),rtol=0,atol=AREA_ATOL)
 np.testing.assert_allclose((f.candidate_zoning_area_m2+f.uncovered_area_m2).loc[good].astype(float),f.fixed_village_area_m2.loc[good].astype(float),rtol=0,atol=AREA_ATOL)
 for category in CORE:
  l=f[category+'_observed_share'];q=f.uncertain_union_share
  pd.testing.assert_series_equal(f[category+'_conditional_lower_bound'],l,check_names=False,check_exact=True)
  expected=np.minimum(1,l+q).astype('Float64')
  pd.testing.assert_series_equal(f[category+'_conditional_upper_bound'],expected,check_names=False,check_exact=True)
  pd.testing.assert_series_equal(f[category+'_conditional_bound_width'],expected-l,check_names=False,check_exact=True)
  assert (expected[good]>=l[good]).all()
  assert f[category+'_observed_zero_flag'].loc[good].eq(f.loc[good,category+'_identified_area_m2'].eq(0)).all()
 for t in THRESHOLDS:assert f.loc[good,f'coverage_ge_{t}'].eq(f.loc[good,'identified_zoning_coverage_share'].ge(t/100)).all()
 assert f.core_five_identified_share.loc[good].le(f.identified_zoning_coverage_share.loc[good]+AREA_ATOL/f.loc[good,'fixed_village_area_m2']).all()
 for vid in ['6300700015','6301100044']:assert int(f.village_id.eq(vid).sum())==1
 return True

def crosswalk_definitions(cw):
 meanings={
 'research_zoning_category':'v2研究工作分類；僅指定2鍵3筆由industrial／commercial改mixed_special_use',
 'original_research_zoning_category':'v1原研究分類，完整保留供版本比較',
 'classification_revision_applied':'本次指定研究分類修訂旗標，不是法定分區變更',
 'classification_revision_reason':'依Unit1.6及Unit2.5指定修訂原因；未修訂為原空字串',
 'revision_evidence':'既有Notebook與學生指示證據，不冒稱新增官方個案核定',
 'revision_evidence_status':'本次研究採用或原證據維持；與原verification_status分開',
 'classification_version':'v2_unit25，保留v1原檔',
 'affected_record_ids_json':'受指定修訂的來源穩定ID JSON陣列，未修訂為[]',
 'revision_affected_record_count':'此鍵指定修訂圖徵數；未修訂為0',
 'revision_reference_union_area_m2':'受修訂圖徵linework參考聯集面積；非真實／法定面積認證',
 'original_record_count':'原鍵對應圖徵數，沿v1保留',
 'verification_status':'原official_supported／research_classification／ambiguous／excluded狀態保留，不提升為官方認證'}
 return [{'name':col,'dtype':str(cw[col].dtype),'definition':meanings.get(col,'v1原欄位保留：'+col),
  'unit':'m²' if col.endswith('_m2') else 'source feature count' if col.endswith('_count') else 'not applicable',
  'source':'v1 five-field compound key / Unit1.6 / Unit2.5 adopted research revision',
  'missing_rule':'原空字串保留；未修訂原因空字串、IDs為[]；__MISSING__僅真正NA'} for col in cw]

def handoff_check(root,b2,bindings):
 verify(root,bindings);results=[]
 for kind in ['a','b1','c']:
  for period in ['annual','pooled']:
   stem=f'taipei_dataset_{kind}_{period}'
   schema=json.loads((root/f'data/processed/{stem}_schema.json').read_text(encoding='utf-8'))
   assert schema['csv']['missing_sentinel']=='__MISSING__'
   keys=['village_id']+(['year'] if period=='annual' else [])+(['specification'] if kind!='b1' else [])
   left=read_csv(root/f'data/processed/{stem}.csv',schema,keys)
   right=b2[['village_id','processing_status','identified_zoning_coverage_share']]
   merged=left.merge(right,on='village_id',how='left',validate='many_to_one',indicator=True)
   assert len(merged)==len(left) and merged['_merge'].eq('both').all()
   results.append({'dataset':stem,'rows_before':len(left),'rows_after':len(merged),'unmatched':0,
    'merge':'many_to_one','B2_rows':456,'B2_NA_rows_retained':int(merged.identified_zoning_coverage_share.isna().sum()),
    'feature_values_used_as_B2_input':False,'missing_sentinel':schema['csv']['missing_sentinel']})
 return results

def diagnostics(ctx,new,old,prior,b2):
 city=[]
 for sc in [new,old,prior]:
  for name,g in sc['sets'].items():city.append({'scenario':sc['label'],'set':name,'city_union_area_km2':g.intersection(ctx.city).area/1e6,'city_union_share':g.intersection(ctx.city).area/ctx.city.area})
 stats=[]
 for category in CORE:
  for suffix in ['_observed_share','_conditional_lower_bound','_conditional_upper_bound','_conditional_bound_width']:
   col=category+suffix;v=b2[col]
   stats.append({'feature':col,'valid_N':int(v.count()),'NA_N':int(v.isna().sum()),'zero_N':int(v.eq(0).sum()),
    'min':float(v.min()),'q25':float(v.quantile(.25)),'median':float(v.median()),'q75':float(v.quantile(.75)),
    'max':float(v.max()),'mean':float(v.mean()),'std_ddof1':float(v.std())})
 thresholds=[{'coverage_threshold_percent':t,'villages':int(b2[f'coverage_ge_{t}'].sum()),'unknown_processing_flags':int(b2[f'coverage_ge_{t}'].isna().sum())} for t in THRESHOLDS]
 district=[]
 for d,ids in b2.groupby('district_name').groups.items():
  f=b2.loc[ids];dshape=ctx.districts[d];area=f.fixed_village_area_m2.sum()
  row={'district':d,'villages':len(f),'district_union_area_km2':dshape.area/1e6,'village_area_sum_km2':float(area/1e6),
   'identified_share_village_area_weighted':float(f.identified_zoning_area_m2.sum()/area),
   'identified_share_village_mean':float(f.identified_zoning_coverage_share.mean()),
   'identified_share_village_median':float(f.identified_zoning_coverage_share.median()),
   'coverage_ge_90_villages':int(f.coverage_ge_90.sum())}
  for name in ['candidate_zoning','identified_zoning','uncertain_union','unclassified','cross_class_overlap','geometry_sensitive','uncovered']:
   key=sha_bytes(new['sets'][name].wkb)
   unionarea=ctx.district_area_cache.get((key,d))
   if unionarea is None:unionarea=new['sets'][name].intersection(dshape).area
   row[name+'_district_union_km2']=unionarea/1e6
   row[name+'_village_sum_km2']=float(f[name+'_area_m2'].sum()/1e6)
  for category in ctx.categories:row[category+'_identified_village_sum_km2']=float(f[category+'_identified_area_m2'].sum()/1e6)
  district.append(row)
 old_i=ctx.village_areas(old['sets']['identified_zoning']);old_q=ctx.village_areas(old['sets']['uncertain_union'])
 revised_footprint=ctx.village_areas(s.union_all(ctx.reference[ctx.revised_records]))
 impact=b2[['village_id','district_name','standard_village_name']].copy()
 impact['revised_source_intersection_m2']=revised_footprint
 impact['identified_area_change_m2']=b2.identified_zoning_area_m2-old_i
 impact['uncertain_union_area_change_m2']=b2.uncertain_union_area_m2-old_q
 for category in CORE:
  before=ctx.village_areas(old['effective'][category])
  impact[category+'_area_change_m2']=b2[category+'_identified_area_m2']-before
  impact[category+'_share_change']=impact[category+'_area_change_m2']/b2.fixed_village_area_m2
 class_impact=[{'category':c,'old_city_identified_m2':old['effective'][c].intersection(ctx.city).area,
  'new_city_identified_m2':new['effective'][c].intersection(ctx.city).area,
  'city_change_m2':new['effective'][c].intersection(ctx.city).area-old['effective'][c].intersection(ctx.city).area} for c in ctx.categories]
 benchmark=[]
 review=poly(s.union_all(ctx.reference[ctx.revised_records],grid_size=OVERLAY_GRID))
 grid_pending={'identified_zoning':poly(s.difference(old['sets']['identified_zoning'],review,grid_size=OVERLAY_GRID)),
  'uncertain_union':poly(s.union_all([old['sets']['uncertain_union'],review],grid_size=OVERLAY_GRID)).intersection(ctx.city)}
 for setname,expected in [('uncertain_union',93.695150),('identified_zoning',174.854933)]:
  old16=prior['sets'][setname].intersection(ctx.city).area/1e6;actual=new['sets'][setname].intersection(ctx.city).area/1e6
  pending_grid=grid_pending[setname].intersection(ctx.city).area/1e6
  no_pending_grid=old['sets'][setname].intersection(ctx.city).area/1e6
  benchmark.append({'set':setname,'prior_recorded_rounded_km2':expected,'same_input_unit16_reconstruction_km2':old16,
   'reconstruction_minus_recorded_km2':old16-expected,'formal_v2_km2':actual,'v2_minus_unit16_km2':actual-old16,
   'numeric_overlay_grid_effect_km2':pending_grid-old16,
   'release_of_three_pending_features_effect_km2':no_pending_grid-pending_grid,
   'pure_v1_to_v2_classification_effect_km2':actual-no_pending_grid})
 footprint=impact.loc[impact.revised_source_intersection_m2.gt(0)]
 affected=impact.loc[impact.filter(like='_area_change_m2').abs().gt(AREA_ATOL).any(axis=1)]
 totals={'city_union_identified_share':new['sets']['identified_zoning'].intersection(ctx.city).area/ctx.city.area,
  'village_area_weighted_identified_share':float(b2.identified_zoning_area_m2.sum()/b2.fixed_village_area_m2.sum()),
  'village_identified_share_mean':float(b2.identified_zoning_coverage_share.mean()),
  'village_identified_share_median':float(b2.identified_zoning_coverage_share.median()),
  'city_union_uncertain_km2':new['sets']['uncertain_union'].area/1e6,
  'village_sum_uncertain_km2':float(b2.uncertain_union_area_m2.sum()/1e6),
  'revision_source_footprint_villages':len(footprint),'revision_material_area_change_villages':len(affected),
  'overlay_failure_villages':int(b2.overlay_failed_flag.sum()),
  'quality_share_roundoff_villages':int(b2.quality_share_roundoff_flag.sum()),'quality_share_roundoff_max_excess_m2':float(b2.quality_share_roundoff_max_excess_m2.max()),
  'city_partition_residual_m2':new['city_partition_residual_m2'],'city_I_Q_overlap_m2':new['city_I_Q_overlap_m2'],
  'area_partition_max_abs_m2':float(b2.area_partition_residual_m2.abs().max()),
  'class_sum_max_abs_m2':float(b2.classified_sum_residual_m2.abs().max()),
  'I_Q_overlap_max_m2':float(b2.identified_uncertain_overlap_m2.max())}
 totals['derived_city_class_pair_overlap_max_m2']=float(new['post_overlay_residual_audit'].derived_city_overlap_m2.max())
 totals['source_supported_post_overlap_max_m2']=float(new['post_overlay_residual_audit'].source_supported_residual_m2.max())
 return {'city_sets':city,'feature_summary':stats,'thresholds':thresholds,'district_quality':district,
  'same_class_union_audit':new['union_stats'].to_dict('records'),'derived_nonpolygon_audit':pd.concat([sc['derived_nonpolygon_audit'] for sc in [new,old,prior]],ignore_index=True).to_dict('records'),
  'classification_revision_city_impact':class_impact,'classification_revision_village_impact':json.loads(impact.to_json(orient='records',force_ascii=False,double_precision=15)),
  'revision_footprint_villages':json.loads(footprint.to_json(orient='records',force_ascii=False,double_precision=15)),
  'benchmark_comparison':benchmark,'post_overlay_residual_audit':pd.concat([sc['post_overlay_residual_audit'] for sc in [new,old,prior]],ignore_index=True).to_dict('records'),'totals':totals}

def contract(stem,definitions,ctx):
 support=stem==CW
 return {'unit':'2.5','created_at':'2026-11-27','dataset_path':f'data/processed/{stem}.csv',
  'producer':PRODUCER,'helper':HELPER,'documentation':f'data/processed/{stem}_documentation.ipynb',
  'role':'processing_support_zoning_classification' if support else 'supplementary_external_zoning',
  'observation_unit':'five-field source compound classification key' if support else 'one fixed research village; one snapshot, no year/specification duplication',
  'expected_rows':296 if support else 456,'primary_key':OUTKEY if support else ['village_id'],
  'csv':CSV,'columns':definitions,'source_inputs':ctx.bindings,'handoff_only_inputs':ctx.handoff_bindings,
  'classification_version':'v2_unit25','classification_targets':ctx.revisions.to_dict('records'),
  'classification_evidence':'original verification_status retained; two keys / three features revised under research instruction, not legal zoning change',
  'working_crs':{'raw_urban_crs':None,'memory_working':'EPSG:3826','grade':'B','fixed_village_source':'EPSG:3826','raw_PRJ_written':False},
  'geometry_policy':{'original_valid_unchanged':True,'invalid':143,'adopted_linework_algorithmic_candidates':105,'withheld_method_sensitive':38,
   'repair_agreement_symdiff_m2':REPAIR_ATOL,'sensitive_geometry':'union of polygon parts of linework / structure / buffer0 candidates, not bbox; buffer0 only for comparison',
   'nonpolygon_parts':'recorded separately; never counted as area','overlap':'strict positive area >0; zero-area contacts separately recorded',
   'area_partition_tolerance_m2':AREA_ATOL,'city_partition_aggregate_tolerance_m2':CITY_AREA_ATOL,'derived_city_overlap_tolerance_m2':CITY_DERIVED_OVERLAP_ATOL,
   'overlay_precision_grid_m':OVERLAY_GRID,
   'overlay_precision_scope':'consistent precision for derived zoning union/intersection/difference only; no set_precision or coordinate change on raw source or fixed villages; final village intersections use original geometry',
   'derived_overlay_roundoff':'source positive overlaps all included; derived class-pair overlap must satisfy 0.01m², per-village and city area identities 0.1m²; legacy Unit1.6 double-precision reconstruction is diagnostic only',
   'no_ratio_clipping':'no clip to hide geometry error; min(1,L+Q/A) is only the defined conditional upper bound'},
  'fraction_roundoff':'core observed and all conditional bounds are strictly [0,1]; ten quality-source shares may exceed [0,1] only within 0.1m² / original village area, with explicit roundoff flag and maximum excess in m²; raw ratios retained without clipping',
  'scheme_B':'same-class union; remove cross-class positive overlap, classified-unclassified overlap and sensitive union from all reliable classes; no category priority',
  'uncertainty':'geometric union of cross-class overlap, unknown coverage, classified-unknown overlap, sensitive union and uncovered; source sets may overlap, never directly sum them',
  'conditional_bounds':'L=identified class/full original village area; U=min(1,L+uncertain union/full village area); width=U-L; assumptions conditional, not confidence intervals or certified legal truth',
  'zero_NA_policy':'observed 0 is not confirmed absence; processing failure => retained village ID + NA and failure reason',
  'limitations':LIMITATIONS}

def export(ctx,b2,definitions):
 datasets={B2:b2,CW:ctx.v2};defs={B2:definitions,CW:crosswalk_definitions(ctx.v2)}
 planned={}
 for stem,f in datasets.items():
  planned[f'data/processed/{stem}.csv']=f.to_csv(index=False,lineterminator='\n',na_rep='__MISSING__',float_format='%.17g').encode('utf-8-sig')
  planned[f'data/processed/{stem}_schema.json']=(json.dumps(contract(stem,defs[stem],ctx),ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 for rel,payload in planned.items():
  path=(ctx.root/rel).resolve();assert path.is_relative_to((ctx.root/'data/processed').resolve())
  assert rel not in ctx.bindings and rel not in ctx.handoff_bindings
  if path.exists():assert path.read_bytes()==payload,('REFUSE DIFFERENT OUTPUT OVERWRITE',rel)
 for rel,payload in planned.items():
  path=ctx.root/rel
  if not path.exists():
   with path.open('xb') as stream:stream.write(payload)
 outputs={}
 for stem,expected in datasets.items():
  sc=json.loads((ctx.root/f'data/processed/{stem}_schema.json').read_text(encoding='utf-8'))
  actual=read_csv(ctx.root/f'data/processed/{stem}.csv',sc)
  pd.testing.assert_frame_equal(actual,expected,check_exact=True)
  for suffix in ['.csv','_schema.json']:
   rel=f'data/processed/{stem}{suffix}';outputs[rel]={'path':rel,'bytes':(ctx.root/rel).stat().st_size,'sha256':sha(ctx.root/rel)}
 return outputs

def validate_crosswalk(cw,old):
 assert len(cw)==296 and not cw.duplicated(OUTKEY).any()
 assert cw.classification_revision_applied.sum()==2 and cw.revision_affected_record_count.sum()==3
 assert cw.original_record_count.sum()==15518
 for key,(category,count,reason) in TARGETS.items():
  mask=pd.Series(True,index=cw.index)
  for col,value in zip(OUTKEY,key):mask&=cw[col].eq(value)
  assert mask.sum()==1 and cw.loc[mask,'research_zoning_category'].eq('mixed_special_use').all()
  assert cw.loc[mask,'original_research_zoning_category'].eq(category).all()
  assert int(cw.loc[mask,'revision_affected_record_count'].iloc[0])==count
 untouched=~cw.classification_revision_applied
 for col in old:
  a=cw.loc[untouched,col].astype('string');b=old.loc[untouched,col].astype('string')
  pd.testing.assert_series_equal(a,b,check_names=False,check_exact=True)
 assert cw.loc[cw.original_zoning_name.eq('陽明山公園'),'research_zoning_category'].eq('unclassified').all()
 return True

def assert_originals_unchanged(ctx):
 verify(ctx.root,ctx.bindings);verify(ctx.root,ctx.handoff_bindings)
 assert ctx.raw.crs is None and ctx.raw.geometry.to_wkb().equals(ctx.raw_wkb)
 assert ctx.boundary.geometry.to_wkb().equals(ctx.bwkb)
 return True

def plots(ctx,new,b2,diag):
 import matplotlib.pyplot as plt
 from matplotlib import font_manager
 font=Path('C:/Windows/Fonts/msjh.ttc')
 if font.is_file():font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=[font_manager.FontProperties(fname=str(font)).get_name(),'DejaVu Sans']
 plt.rcParams['axes.unicode_minus']=False
 folder=ctx.root/'data/temp/unit25_validation';folder.mkdir(parents=True,exist_ok=True);paths=[]
 def finish(fig,name):
  fig.suptitle('Unit 2.5 都市計畫資料處理與品質診斷；非正式Finding',fontsize=13)
  fig.tight_layout(rect=(0,0,1,.95));p=folder/name;fig.savefig(p,dpi=140,bbox_inches='tight');plt.show();paths.append(p.relative_to(ctx.root).as_posix())
 def map_column(ax,col,title,vmin=0,vmax=1,cmap='viridis'):
  g=ctx.boundary.copy();g[col]=b2[col].to_numpy(dtype=float,na_value=np.nan)
  g.plot(column=col,ax=ax,vmin=vmin,vmax=vmax,cmap=cmap,legend=True,linewidth=.1,edgecolor='grey',missing_kwds={'color':'magenta','label':'處理失敗NA'})
  ax.set_title(title);ax.set_axis_off()
 fig,axs=plt.subplots(1,3,figsize=(15,6))
 for ax,col,title in zip(axs,['candidate_zoning_coverage_share','identified_zoning_coverage_share','uncertain_union_share'],['原始候選覆蓋（含未分類）','可靠工作分類覆蓋','不確定聯集（非觀測零值）']):map_column(ax,col,title)
 finish(fig,'candidate_identified_uncertainty_maps.png')
 fig,axs=plt.subplots(1,3,figsize=(15,6))
 for ax,col,title in zip(axs,['unclassified_coverage_share','geometry_sensitive_coverage_share','cross_class_overlap_share'],['未分類覆蓋（陽明山公園）','38方法敏感範圍','跨類正面積重疊']):
  maximum=float(b2[col].max());map_column(ax,col,title,vmax=maximum if maximum>0 else 1,cmap='magma')
 finish(fig,'uncertainty_source_maps.png')
 fig,axs=plt.subplots(2,3,figsize=(15,10))
 for ax,category in zip(axs.flat,CORE):map_column(ax,category+'_observed_share',category+'已辨識／完整里面積')
 axs.flat[-1].text(.05,.6,'五類不加總正規化至1\n未分類不直接歸公園\n0代表已辨識零，不代表確定不存在\nNA處理失敗以紫色區別',fontsize=13);axs.flat[-1].set_axis_off()
 finish(fig,'five_core_observed_share_maps.png')
 fig,axs=plt.subplots(1,3,figsize=(16,5))
 axs[0].hist(b2.identified_zoning_coverage_share.dropna().astype(float),bins=24);axs[0].set(title='456里可靠辨識覆蓋',xlabel='覆蓋比例',ylabel='行政里數')
 axs[1].boxplot([b2[c+'_conditional_bound_width'].dropna().astype(float) for c in CORE],tick_labels=['住宅','商業','工業','文教','公園綠地'],showfliers=True);axs[1].set(title='條件式區間寬度；非信賴區間',ylabel='U-L')
 d=pd.DataFrame(diag['district_quality']).sort_values('identified_share_village_area_weighted')
 axs[2].barh(d.district,d.identified_share_village_area_weighted);axs[2].set(title='各區逐里面積加權辨識覆蓋',xlabel='覆蓋比例',xlim=(0,1))
 finish(fig,'coverage_bounds_district_quality.png')
 fig,axs=plt.subplots(1,2,figsize=(13,5))
 changes=pd.DataFrame(diag['classification_revision_city_impact']);changes=changes.loc[changes.city_change_m2.abs().gt(.01)]
 axs[0].barh(changes.category,changes.city_change_m2/1e6);axs[0].axvline(0,color='black',linewidth=.8);axs[0].set(title='v2減v1：同幾何／方案B分類影響',xlabel='可靠分類面積變化（km²）')
 revised=s.union_all(ctx.reference[ctx.revised_records]);ctx.boundary.boundary.plot(ax=axs[1],color='grey',linewidth=.25)
 gpd.GeoSeries([revised],crs=3826).plot(ax=axs[1],color='red',label='指定2鍵3圖徵')
 axs[1].set_title('指定修訂來源範圍，非里界變動');axs[1].set_axis_off()
 finish(fig,'classification_revision_impact.png')
 return paths
