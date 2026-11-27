"""Unit2.7: version-bound saved-table integration; no raw processing/GIS/model.

All source columns have a reversible name/provenance map and exact value checks.
Only explicitly equivalent metadata/counts/areas are coalesced after validation.
"""
from pathlib import Path
from collections import Counter
import json,hashlib,platform,io
import pandas as pd
import numpy as np
from unit25_zoning_support import sha,read_csv,show,validate_b2
from unit23_feature_support import validate_bundle as validate_ac,EXPECTED,FEATURES,MAIN_FEATURES,THRESHOLDS
from unit24_population_support import validate_bundle as validate_b1
from unit26_transportation_support import validate_dataset as validate_b3

HELPER='data/code/unit27_integration_support.py'
PRODUCER='data/code/prepare_taipei_final_analytical_datasets.ipynb'
REGISTRY='data/processed/taipei_feature_registry.json'
STEMS={'base':'taipei_village_base',**{k+'_'+p:'taipei_dataset_'+k+'_'+p for k in ['a','b1','c'] for p in ['annual','pooled']},'b2':'taipei_dataset_b2','b3':'taipei_dataset_b3'}
FINAL={p:'taipei_final_analytical_'+p for p in ['annual','pooled']}
CSV={'encoding':'utf-8-sig','line_terminator':'LF','missing_sentinel':'__MISSING__','keep_default_na':False,'boolean_values':['True','False'],'original_empty_strings':'preserved','float_serialization':'17 significant digits, no analytical rounding'}
A1=[k+'_ratio' for k in MAIN_FEATURES if k!='multi_injury'];A2=A1+['multi_injury_ratio']
B1=['population_density','elderly_ratio','children_ratio']
B2=[k+'_observed_share' for k in ['residential','commercial','industrial','educational','park_green']]
B3_PRIORITY=['osm_road_density','osm_major_road_ratio']
B3_CONDITIONAL=['observed_signal_location_density','crosswalk_area_ratio','median_annotated_road_width']
B3_CURRENT=['mrt_entrance_buffer_500m_ratio','mrt_entrance_density']
B3_SENSITIVITY=['mrt_entrance_buffer_300m_ratio','mrt_entrance_buffer_800m_ratio','signal_geometry_only_location_density','signal_main_without_lcs_location_density','signal_geometry_without_lcs_location_density']
COMMON=set(['specification','village_id','year','period_start_year','period_end_year','period_years','period','district_name','standard_village_name','boundary_version','assignment_rule','observed_accident_count','has_observed_accident','boundary_code','population_code','population_village_name','boundary_village_name','verification_status','match_method','geometry_quality_flag','fixed_village_area_m2','fixed_village_area_km2']+['count_lt_'+str(t) for t in THRESHOLDS])
ALIASES={'village_area_m2':'fixed_village_area_m2','village_area_km2':'fixed_village_area_km2'}
PERSON_NOTE='2025-06龍福+1075、幸福-1066；既有官方搬遷與暫遷戶籍制度證據僅支持背景，與人口跳動直接關係未證實；保留原值及行政里，Chapter3/5按需求審查兩里敏感度，不把設籍人口當交通暴露。'
LIMITATIONS=[
 'D原版為主；S0 pooled為主要分群研究候選骨架，A1/A2尚未定案，S1必要穩健性、S2/S3地理配對敏感度，不是獨立樣本。',
 'A九比例不是總和必為1的組成向量；各自分母／NA／覆蓋率保留，沒有低樣本排除、比例平滑或完整案例刪里。',
 '2024/2025同里並非獨立實驗樣本；未來2024所有擬合／特徵選擇只可使用2024，不能以2025或pooled擬合Scaler／Imputer／PCA／分群中心。',
 'B1設籍人口非交通暴露或當事人住地；人口存量跳動的直接機制未證實。',
 'B2補充分區工作分類與條件式範圍，非完整分區或實際土地使用；B級工作CRS及Q/A、I/A保留，群間比較須同時報辨識與不確定比例。',
 'B3來源混合日期、完整性未認證；線表示非流量／VKT，號誌位置非完整路口，行穿面非完整設施，路寬為計畫尺寸標註。',
 'B2/B3只按village_id重複連接固定快照，不形成年度獨立觀測；MRT2026僅當期補充，不當2024/2025事前環境或主要分群特徵。',
 'C為事故負擔／分群後比較；原死亡時間窗及R20限制保留，非真正暴露校正事故風險，不支持因果結論。',
 '原固定幾何／孔洞／微重疊不改；固定與歷史面積用途分開，source_AREA_attribute不作正式分母。',
 '微量GIS比例超界依既有分子／分母與0.1m²容忍核對，原值及旗標保留；本輪不需要analysis_safe副本，未clip或變更上游。',
 'Codex協助；DE交付確認、DA驗收、PM審查及學生本人Git提交待完成；完成停止Unit2.7，不開始Chapter3。']
DEPENDENCE=[
 {'features':A1[:3],'note':'共同事故時間來源，定義依賴不是本輪相關性估計'},
 {'features':['rear_end_ratio','side_collision_ratio','pedestrian_collision_ratio'],'note':'共同原始碰撞型態欄，非獨立測量'},
 {'features':A2,'note':'九比例可重疊、分母各自有效，不是總和必為1的組成向量'},
 {'features':['multi_injury_ratio','mean_injuries_per_accident'],'note':'與C受傷負擔有定義關聯，不據此自動改權重或刪欄'},
 {'features':['population_density','osm_road_density','observed_signal_location_density','mrt_entrance_density'],'note':'共同固定面積分母可能形成結構依賴，不是實證相關性結果'},
 {'features':['osm_major_road_ratio','industrial_observed_share','mrt_entrance_density'],'note':'大量觀測零，不當缺失／現實不存在的自動證明'},
 {'features':['mrt_entrance_buffer_'+str(r)+'m_ratio' for r in [300,500,800]],'note':'巢狀半徑具結構相關，非三項獨立設施觀測'},
 {'features':[k+'_conditional_upper_bound' for k in ['residential','commercial','industrial','educational','park_green']],'note':'共用Q不確定聯集；各上界不可同時實現，不用中點補未知'}]

def verify(root,bindings):
 for rel,h in bindings.items():assert (root/rel).is_file() and sha(root/rel)==h,('INPUT HASH MISMATCH',rel)
def path(stem,suffix='.csv'):return 'data/processed/'+stem+suffix
def key(period):return ['specification','village_id']+(['year'] if period=='annual' else [])
def same(a,b):pd.testing.assert_series_equal(a.reset_index(drop=True),b.reset_index(drop=True),check_names=False,check_exact=True)
def encoded(frame):return frame.to_csv(index=False,lineterminator='\n',na_rep='__MISSING__',float_format='%.17g').encode('utf-8-sig')
def jbytes(value):return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
def details(body):return {'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}

class Context:
 def __init__(self,root,bindings,project_context=None):
  self.root=Path(root).resolve();self.bindings=bindings;verify(self.root,bindings);self.project_context=project_context
  self.temp=self.root/'data/temp/unit27_integration';self.temp.mkdir(parents=True,exist_ok=True)
  self.frames={};self.contracts={};self.manifest=[];self.contract_audit=[]
  expected={'base':(456,41),'a_annual':(3648,128),'a_pooled':(1824,127),'b1_annual':(912,46),'b1_pooled':(456,46),'b2':(456,127),'b3':(456,113),'c_annual':(3648,80),'c_pooled':(1824,79)}
  for name,stem in STEMS.items():
   rel=path(stem);scpath=path(stem,'_schema.json');sc=json.loads((self.root/scpath).read_text(encoding='utf-8'))
   f=read_csv(self.root/rel,sc);assert f.shape==expected[name]
   assert len(f.columns)==len(set(f.columns));assert [str(f[c].dtype) for c in f]==[x['dtype'] for x in sc['columns']]
   raw=(self.root/rel).read_bytes();assert raw.startswith(b'\xef\xbb\xbf') and b'\r\n' not in raw
   assert sc['csv']['missing_sentinel']=='__MISSING__' and sc['csv']['keep_default_na'] is False
   keys=sc.get('primary_key',['village_id']);assert not f.duplicated(keys).any() and f[keys].notna().all().all()
   self.frames[name]=f;self.contracts[name]=sc
   self.manifest.append({'dataset_family':name,'dataset_version':str(sc.get('unit','Unit2.2'))+' frozen saved file','path':rel,'rows':len(f),'columns':len(f.columns),**details(raw),'schema_path':scpath,'schema_sha256':bindings[scpath],'documentation':path(stem,'_documentation.ipynb'),'documentation_sha256':bindings[path(stem,'_documentation.ipynb')],'primary_key':keys,'observation_unit':sc['observation_unit'],'temporal_reference':temporal(name,sc),'producer':sc['producer'],'limitations':sc.get('limitations',[])})
   self.contract_audit.append({'dataset':name,'encoding':sc['csv']['encoding'],'LF':True,'missing_sentinel':sc['csv']['missing_sentinel'],'NA_inference':False,'empty_strings_preserved':True,'shape':list(f.shape),'dtype_counts':dict(Counter(map(str,f.dtypes))),'NA_cells':int(f.isna().sum().sum()),'empty_string_cells':int(sum(f[c].eq('').sum() for c in f if str(f[c].dtype)=='string'))})
  base=self.frames['base'];assert base.village_id.nunique()==456 and base.district_name.nunique()==12
  assert base.village_id.str.fullmatch(r'\d{10}').all() and base.village_area_m2.gt(0).all()
  lookup=base.set_index('village_id')
  for name,f in self.frames.items():
   assert set(f.village_id)==set(base.village_id)
   for col in ['district_name','standard_village_name','boundary_code','population_code','boundary_village_name','population_village_name','verification_status','match_method','geometry_quality_flag']:
    if col in f:same(f[col],f.village_id.map(lookup[col]))
   for col in ['fixed_village_area_km2','fixed_village_area_m2']:
    if col in f:same(f[col],f.village_id.map(lookup[col.replace('fixed_','')]))
  self.upstream_checks={'AC':validate_ac({STEMS[k]:self.frames[k] for k in ['a_annual','a_pooled','c_annual','c_pooled']},base),
   'B1':validate_b1({STEMS[k]:self.frames[k] for k in ['b1_annual','b1_pooled']},base),'B2':validate_b2(self.frames['b2'],base),'B3':validate_b3(self.frames['b3'],base)}
  self.versions={'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__}
  self.definitions={k:{x['name']:x for x in sc['columns']} for k,sc in self.contracts.items()}

def temporal(name,sc):
 if name=='base':return 'fixed research geography; separate historical 2024/2025 snapshots; not proof of monthly boundaries'
 if name=='b2':return 'static planning snapshot: content label 2025-01, resource2026-04-09, DBF/legal dates separately retained; not annual observations'
 if name=='b3':return 'mixed static transport snapshots: OSM2025, signal filename2023/date uncertified, crossings2024 packaging, planned width2023 resource, MRT2026'
 return ('2024/2025 separately; 12 months for B1' if name.endswith('annual') else 'pooled2024–2025; 24 population months, never mean annual ratios')

def source_maps(ctx,period):
 names=['a_'+period,'c_'+period,'b1_'+period,'b2','b3','base'];counts=Counter()
 for name in names:counts.update(ALIASES.get(c,c) if name=='base' else c for c in ctx.frames[name])
 maps={}
 for name in names:
  family=name.split('_')[0];maps[name]={}
  for c in ctx.frames[name]:
   target=ALIASES.get(c,c) if name=='base' else c
   if counts[target]>1 and target not in COMMON:target=family+'_'+target
   maps[name][c]=target
  assert len(set(maps[name].values()))==len(maps[name])
 return names,maps

def integrate(ctx,period):
 names,maps=source_maps(ctx,period);first=names[0];frame=ctx.frames[first].rename(columns=maps[first]).copy();lineage={}
 logs=[];K=key(period)
 def origin(name,col):
  return {'source_dataset':path(STEMS[name]),'source_family':name,'source_column':col,'source_sha256':ctx.bindings[path(STEMS[name])],
   'source_schema_sha256':ctx.bindings[path(STEMS[name],'_schema.json')],'source_primary_key':ctx.contracts[name].get('primary_key',['village_id']),
   'definition':ctx.definitions[name][col]['definition'],'unit':ctx.definitions[name][col]['unit'],'dtype':ctx.definitions[name][col]['dtype'],
   'missing_rule':ctx.definitions[name][col].get('missing_rule',ctx.definitions[name][col].get('missing','source NA preserved')),
   'transformation':'exact alias '+col+' -> '+maps[name][col]+'; no numeric transform' if col!=maps[name][col] else 'identity; no numeric transform'}
 for col in ctx.frames[first]:lineage[maps[first][col]]=[origin(first,col)]
 logs.append({'period':period,'step':'A skeleton','left_rows_before':len(frame),'rows_after':len(frame),'duplicate_keys':0,'left_unmatched':0,'right_unused_keys':0,'new_columns':len(frame.columns),'shared_columns_verified':list(K),'cardinality':'complete skeleton'})
 for name in names[1:]:
  raw=ctx.frames[name];right=raw.rename(columns=maps[name]);join=K if name.startswith('c_') else (['village_id','year'] if name=='b1_annual' else ['village_id'])
  assert not right.duplicated(join).any()
  overlap=[c for c in right if c in frame and c not in join];assert all(c in COMMON for c in overlap),(name,overlap)
  checked=right.rename(columns={c:'__verify_'+c for c in overlap})
  before=len(frame);ncol=len(frame.columns);card='one_to_one' if name.startswith('c_') else 'many_to_one'
  merged=frame.merge(checked,on=join,how='left',validate=card,indicator='__match',sort=False)
  unmatched=int(merged.__match.ne('both').sum());assert unmatched==0 and len(merged)==before
  used=frame[join].drop_duplicates().merge(right[join],on=join,how='right',indicator=True,validate='one_to_one');unused=int(used._merge.eq('right_only').sum());assert unused==0
  for col in overlap:same(merged[col],merged['__verify_'+col])
  merged=merged.drop(columns=['__match']+['__verify_'+c for c in overlap])
  assert not merged.columns.str.endswith(('_x','_y')).any()
  frame=merged
  for col in raw:lineage.setdefault(maps[name][col],[]).append(origin(name,col))
  logs.append({'period':period,'step':name,'left_rows_before':before,'rows_after':len(frame),'duplicate_keys':int(frame.duplicated(K).sum()),'left_unmatched':unmatched,'right_unused_keys':unused,'new_columns':len(frame.columns)-ncol,'shared_columns_verified':overlap+join,'cardinality':card})
 # New flags describe source definitions; they never change underlying values or eligibility.
 derived={
 'population_geographic_comparability_flag':(frame.standard_village_name.isin(['龍福里','幸福里'])&frame.district_name.eq('中正區'),'boolean','兩個既有2025-06人口存量跳動里；不是排除規則','quality_indicator'),
 'population_geographic_comparability_note':(pd.Series([PERSON_NOTE if v else 'no specifically documented 2025-06 two-village event flag; not certification of geographic comparability' for v in frame.standard_village_name.isin(['龍福里','幸福里'])&frame.district_name.eq('中正區')],dtype='string'),'string','既有事件證據界線與後續敏感度註記','metadata'),
 'b2_static_snapshot_repeated':(pd.Series(True,index=frame.index),'boolean','B2按village_id重複連接固定快照，不代表年度變動','quality_indicator'),
 'b3_static_snapshot_repeated':(pd.Series(True,index=frame.index),'boolean','B3按village_id重複連接混合來源固定快照，不代表年度變動','quality_indicator'),
 'environment_snapshot_not_verified_pre_accident':(pd.Series(True,index=frame.index),'boolean','B2/B3不自動視為事前環境；尤其MRT2026','quality_indicator')}
 for name,(values,dtype,definition,role) in derived.items():
  frame[name]=values.astype(dtype);lineage[name]=[{'source_dataset':'derived in Unit2.7','source_family':'integration','source_column':'district_name + standard_village_name' if name.startswith('population_') else 'upstream B2/B3 snapshot metadata','source_primary_key':K,'definition':definition,'unit':'not applicable','dtype':dtype,'missing_rule':'not missing; derived documented flag/note, not imputation','transformation':'deterministic quality annotation; original values unchanged','derived_role':role}]
 frame=frame.sort_values(K,kind='stable').reset_index(drop=True)
 fidelity=check_fidelity(ctx,frame,maps)
 return frame,lineage,maps,logs,fidelity

def check_fidelity(ctx,frame,maps):
 records=[]
 for name,mapping in maps.items():
  source=ctx.frames[name];keys=ctx.contracts[name].get('primary_key',['village_id']);K=[mapping[k] for k in keys]
  expected=source.rename(columns=mapping).set_index(K)
  aligned=expected.reindex(pd.MultiIndex.from_frame(frame[K]) if len(K)>1 else pd.Index(frame[K[0]]))
  for target in mapping.values():
   if target in K:continue
   same(frame[target],aligned[target])
  records.append({'source':name,'columns_checked':len(mapping),'final_rows_checked':len(frame),'all_values_dtypes_NA_exact':True})
 return records

def numerical_audit(ctx):
 records=[]
 for family in ['b2','b3']:
  f=ctx.frames[family];area=f.fixed_village_area_m2
  for item in ctx.contracts[family]['columns']:
   col=item['name']
   if item['unit']!='fraction':continue
   v=f[col];bad=(v.lt(0)|v.gt(1)).fillna(False);excess=np.maximum(-v, v-1).clip(lower=0)*area
   if family=='b2':
    if col.endswith('_coverage_share'):num=col.replace('_coverage_share','_area_m2')
    elif col=='uncertain_union_share':num='uncertain_union_area_m2'
    elif col=='uncovered_share':num='uncovered_area_m2'
    elif col=='non_zoning_boundary_share':num='non_zoning_boundary_area_m2'
    elif col.endswith('_observed_share'):num=col.replace('_observed_share','_identified_area_m2')
    elif col.endswith('_share'):num=col[:-6]+'_area_m2'
    else:num=None
   else:
    num={'crosswalk_area_ratio':'observed_crosswalk_area_m2',**{'mrt_entrance_buffer_'+str(r)+'m_ratio':'mrt_entrance_buffer_'+str(r)+'m_area_m2' for r in [300,500,800]}}.get(col)
   if num in f:
    same(v,f[num]/area);direct_excess=np.maximum(-f[num],f[num]-area).clip(lower=0)
    assert direct_excess.max()<=.1 and excess.max()<=.1
   else:
    direct_excess=pd.Series(0.,index=f.index)
    assert ((v>=-1e-10)&(v<=1+1e-10)|v.isna()).all()
   records.append({'family':family,'column':col,'valid_N':int(v.notna().sum()),'outside_strict_0_1':int(bad.sum()),'max_ratio_excess':float(np.maximum(-v,v-1).clip(lower=0).max()),'max_equivalent_area_excess_m2':float(excess.max()),'numerator':num if num in f else 'not an area ratio / strict fraction check','denominator':'fixed_village_area_m2' if num in f else 'source definition','source_numerator_reconciliation':num in f,'area_tolerance_m2':.1,'analysis_safe_created':False,'raw_values_changed':False})
 return records

def classification(column,origins,ctx):
 src=origins[0];family=src['source_family'].split('_')[0];name=src['source_column'];dtype=src['dtype']
 identifier=name in {'village_id','specification','year','district_name','standard_village_name','boundary_code','population_code','population_district_code','district_code_source'} or name.startswith(('historical_boundary_code','historical_district_code'))
 role='metadata';use='retain provenance; do not automatically model';main=False;external=False;sensitivity=None
 readiness='Ready with explicit assumptions'
 if identifier:role='identifier'
 elif family=='integration':role=src['derived_role'];use='source quality annotation, never exclusion'
 elif column in A2:role='clustering_candidate';main=True;use='A1/A2 candidate only; S0 pooled main research skeleton; final feature/sample policy pending'
 elif column=='strict_intersection_ratio':role='sensitivity';sensitivity='strict_intersection';use='alternative intersection definition, not automatically an additional main feature'
 elif column in B1:role='core_external';external=True;use='core population comparison after accident clustering; registered population is not exposure'
 elif column in B2:role='supplementary_external';external=True;readiness='Partially ready';use='supplementary zoning comparison with I/A and Q/A; no final quality threshold'
 elif column in B3_PRIORITY:role='priority_external';external=True;use='priority external transport comparison after accident clustering'
 elif column in B3_CONDITIONAL:role='supplementary_external';external=True;use='conditional / supplementary transport comparison, retain source definition limits'
 elif column in B3_CURRENT:role='supplementary_external';external=True;use='2026 current-environment supplement only; never pre-accident covariate'
 elif column in B3_SENSITIVITY:role='sensitivity';external=True;sensitivity='MRT radius' if column.startswith('mrt_') else 'signal A/B/LCS';use='alternative radius or source-quality definition, not independent measurements'
 elif column=='observed_accident_count':role='burden_outcome';external=True;use='post-clustering burden and denominator; never automatically cluster on count'
 elif family=='c' and (name.startswith('r20_') or name.endswith('_r20_difference') or '_removed_by_r20' in name):role='sensitivity';sensitivity='R20 casualty definition';external=name.endswith('_observed_sum') or 'mean_injuries' in name or 'fatality_ratio' in name;use='post-clustering casualty sensitivity; explicit R20=True only excluded'
 elif family=='c' and (name.endswith('_observed_sum') or name.startswith(('mean_injuries','source_positive_fatality','observed_accidents_per','mean_annual_observed','historical_mean_annual'))):role='burden_outcome';external=True;use='post-clustering burden comparison; not exposure-adjusted risk or clustering feature'
 elif name=='source_AREA_attribute':role='metadata';use='uninterpreted original AREA attribute retained for provenance; never a formal area denominator'
 elif dtype=='boolean' or any(t in name for t in ['quality','coverage','readiness','value_state','interpretation','failure','residual','roundoff','processing_status','missing','conflict','no_valid_samples','count_lt_','denominator_lt_']):role='quality_indicator';use='quality / missingness / candidate threshold; no automatic row deletion or clustering'
 elif dtype in ['Int64','Float64']:role='numerator_denominator';use='preserve counts / areas / samples / denominators; no automatic clustering'
 if family=='b2':readiness='Partially ready'
 if family=='b3':
  specs={x['feature']:x for x in ctx.contracts['b3']['feature_readiness']}
  if column in specs:readiness=specs[column]['readiness_status']
  elif name.startswith(('signal_','observed_signal','crosswalk_','observed_crosswalk','annotated_road','median_annotated')):readiness='Partially ready'
 if family=='a' and name.startswith('strict_intersection'):sensitivity='strict_intersection'
 leakage='No fitted preprocessing in Unit2.7. Fit future 2024 feature selection/scaler/smoothing/PCA/centres with 2024 only; never 2025 or pooled.'
 if family in ['b2','b3']:leakage+=' Static snapshots are not independent annual measurements or verified pre-accident environment; MRT2026 excluded from pre-accident use.'
 zero='Observed zero remains zero; never equate NA / False / empty string with zero. Source coverage may be incomplete.'
 if 'width' in name:zero+=' No annotation sample: count0 and median/quartiles NA, not zero width.'
 if family=='b2':zero+=' Observed zoning0 does not certify true absence, especially I=0; Q/A and I/A mandatory context.'
 if name.endswith('_ratio') and family=='a':zero+=' Positive valid denominator with numerator0 => ratio0; denominator0 => NA.'
 return {'analytical_role':role,'readiness':readiness,'recommended_use':use,'allowed_for_main_clustering':main,'allowed_for_external_comparison':external,'sensitivity_group':sensitivity,'leakage_warning':leakage,'zero_policy':zero}

def feature_sets(ctx):
 c=ctx.frames['c_annual']
 burden=[x for x in c if x=='observed_accident_count' or x.endswith('_observed_sum') or x.startswith(('mean_injuries','source_positive_fatality','observed_accidents_per','mean_annual_observed','historical_mean_annual'))]
 return {'A1':A1,'A2':A2,'strict_intersection_alternative':['strict_intersection_ratio'],'B1_core_external':B1,'B2_supplementary_observed':B2,'B3_priority_external':B3_PRIORITY,'B3_conditional_supplementary':B3_CONDITIONAL,'B3_2026_current_supplementary':B3_CURRENT,'B3_sensitivity':B3_SENSITIVITY,'C_burden_and_sensitivity':burden,'C_R20_sensitivity':[x for x in c if x.startswith('r20_') or x.endswith('_r20_difference') or '_removed_by_r20' in x]}

def definitions_for(ctx,frame,lineage,period):
 result=[]
 for col in frame:
  origins=lineage[col];d=origins[0];classif=classification(col,origins,ctx)
  result.append({'name':col,'column_name':col,'dtype':str(frame[col].dtype),'definition':d['definition'],'unit':d['unit'],'missing_rule':d['missing_rule'],'missing_policy':d['missing_rule']+'; preserve exact nullable source values, no imputation',
   'source_dataset':list(dict.fromkeys(x['source_dataset'] for x in origins)),'source_column':[x['source_column'] for x in origins],
   'source':origins,'transformation':'identity / checked shared-field coalescence / explicit alias; deterministic quality flags only',
   'temporal_reference':{x['source_family']:temporal(x['source_family'],{}) if x['source_family']!='integration' else 'documented 2025-06 event / fixed environment snapshots' for x in origins},
   'geographic_reference':'fixed456 CPTVID string; fixed area remains canonical; S2/S3 historical area-time separate; no geometry in Final CSV',
   'interpretation_limitations':LIMITATIONS,'formal_analysis_selected':False,**classif})
 return result

def annual_pooled_checks(ctx,annual,pooled,maps):
 # Original saved-table validators above already recompute ratio definitions;
 # this additionally checks that every final source alias remains faithful.
 check_fidelity(ctx,annual,maps['annual']);check_fidelity(ctx,pooled,maps['pooled'])
 a=annual.set_index(key('annual'));p=pooled.set_index(key('pooled')).sort_index();g=annual.groupby(key('pooled'),sort=True)
 additive=[]
 for family in ['a','c']:
  for col in ctx.frames[family+'_annual']:
   if col.endswith(('_count','_numerator','_denominator')) and str(ctx.frames[family+'_annual'][col].dtype)=='Int64':
    if col in additive:continue
    same(g[col].sum(min_count=1),p[col]);additive.append(col)
 b1=ctx.frames['b1_annual'].groupby('village_id',sort=True);bp=ctx.frames['b1_pooled'].set_index('village_id').sort_index()
 for kind in ['total','elderly','children']:
  same(b1[kind+'_population_month_sum'].sum(min_count=1),bp['pooled_'+kind+'_population_month_sum'])
  same(b1['valid_'+kind+'_population_month_count'].sum(),bp['valid_'+kind+'_population_month_count'])
 for family in ['b2','b3']:
   for rawcol,col in maps['annual'][family].items():
    if rawcol=='village_id':continue
   src=ctx.frames[family].set_index('village_id')[rawcol]
   same(annual[col],annual.village_id.map(src));same(pooled[maps['pooled'][family][rawcol]],pooled.village_id.map(src))
 return {'status':'passed','additive_AC_columns':len(additive),'B1_month_stocks_and_counts':'exact12+12=24','B2_B3_static_values':'exact across years/specs/pooled, not independent annual observations','pooling':'upstream ratios retained from pooled numerator/denominator, never annual ratio means','historical_density':'retained original area-time denominators, validated by Unit2.3 saved-table assertions'}

def validate_final(ctx,frame,period,maps):
 K=key(period);assert len(frame)==(3648 if period=='annual' else 1824) and not frame.duplicated(K).any()
 assert frame[K].notna().all().all() and frame.village_id.str.fullmatch(r'\d{10}').all()
 assert frame.groupby(['specification']+(['year'] if period=='annual' else [])).size().eq(456).all()
 assert frame.loc[frame.specification.eq('S0')].shape[0]==(912 if period=='annual' else 456)
 for spec,nums in EXPECTED.items():
  f=frame.loc[frame.specification.eq(spec)]
  if period=='annual':assert [int(f.loc[f.year.eq(y),'observed_accident_count'].sum()) for y in [2024,2025]]==nums
  else:assert int(f.observed_accident_count.sum())==sum(nums)
 assert frame.district_name.nunique()==12 and set(frame.village_id)==set(ctx.frames['base'].village_id)
 same(frame.fixed_village_area_km2,frame.village_id.map(ctx.frames['base'].set_index('village_id').village_area_km2))
 missing=frame.annotated_road_width_sample_count.eq(0)
 assert frame.loc[missing,['median_annotated_road_width','annotated_road_width_q1','annotated_road_width_q3']].isna().all().all()
 assert set(frame.loc[missing,'village_id'])=={'6301100048','6301200040','6301200042'}
 sugar=frame.loc[frame.village_id.eq('6300700015')];assert sugar.verification_status.eq('provisional_match').all() and sugar.population_density.notna().all()
 if period=='annual':
  zero=frame.loc[frame.village_id.eq('6301100044')&frame.year.eq(2025)];assert len(zero)==4
  assert zero.observed_accident_count.eq(0).all() and zero.observed_accidents_per_fixed_km2.eq(0).all()
  assert zero[A2+['strict_intersection_ratio','mean_injuries_per_accident','source_positive_fatality_ratio']].isna().all().all()
  assert zero[B1+B2+B3_PRIORITY].notna().all().all()
 assert frame.population_geographic_comparability_flag.sum()==(16 if period=='annual' else 8)
 assert not frame.columns.str.endswith(('_x','_y')).any() and not {'geometry','WKT','geometry_wkt'}&set(frame)
 return check_fidelity(ctx,frame,maps)

def quality_report(ctx,frames):
 rows=[];missing=[];low=[]
 for period,frame in frames.items():
  cols=['specification']+(['year'] if period=='annual' else [])
  for values,g in frame.groupby(cols,sort=True):
   values=values if isinstance(values,tuple) else (values,);info=dict(zip(cols,map(lambda v:int(v) if isinstance(v,(np.integer,int)) else v,values)))
   rows.append({'dataset':period,**info,'rows':len(g),'columns':len(g.columns),'duplicate_keys':int(g.duplicated(key(period)).sum()),'unique_villages':g.village_id.nunique(),'observed_accidents':int(g.observed_accident_count.sum()),'zero_accident_villages':int(g.observed_accident_count.eq(0).sum()),'B1_complete':int(g.population_features_valid.sum()),'B2_I_zero_villages':int(g.identified_zoning_area_m2.eq(0).sum()),'B2_uncertain_positive_villages':int(g.uncertain_union_area_m2.gt(0).sum()),'B3_width_NA_villages':int(g.median_annotated_road_width.isna().sum()),'B3_any_failure':int(g.any_spatial_processing_failed.sum()),'B2_roundoff_villages':int(g.quality_share_roundoff_flag.sum()),'B3_roundoff_villages':int(g.coverage_ratio_roundoff_flag.sum()),'geography':str(g.boundary_version.iloc[0]),'B2_B3_static_repeated':True})
   for col in A2+['strict_intersection_ratio']+B1+B2+B3_PRIORITY+B3_CONDITIONAL+B3_CURRENT+['mean_injuries_per_accident','source_positive_fatality_ratio']:
    x=g[col];missing.append({'dataset':period,**info,'feature':col,'valid_N':int(x.notna().sum()),'NA_N':int(x.isna().sum()),'zero_N':int(x.eq(0).sum())})
   for t in THRESHOLDS:
    low.append({'dataset':period,**info,'threshold_candidate':t,'accident_count_below':int(g['count_lt_'+str(t)].sum()),**{k+'_denominator_below':int(g[k+'_denominator_lt_'+str(t)].sum()) for k in FEATURES},'final_exclusion_selected':False})
 b2=ctx.frames['b2'];area=b2.fixed_village_area_m2
 return {'group_quality':rows,'feature_missing_zero':missing,'low_count_candidates':low,'B2':{'area_weighted_I_A':float(b2.identified_zoning_area_m2.sum()/area.sum()),'village_mean_I_A':float(b2.identified_zoning_coverage_share.mean()),'village_median_I_A':float(b2.identified_zoning_coverage_share.median()),'uncertain_positive_villages':int(b2.uncertain_union_area_m2.gt(0).sum()),'I_zero_villages':b2.loc[b2.identified_zoning_area_m2.eq(0),['village_id','district_name','standard_village_name']].to_dict('records'),'industrial_observed_zero_villages':int(b2.industrial_observed_share.eq(0).sum()),'five_core_valid':b2[B2].notna().sum().to_dict()},'numerical_boundary_audit':numerical_audit(ctx),'B3_readiness':ctx.contracts['b3']['feature_readiness'],'B3_blocked':ctx.contracts['b3']['blocked_features'],'population_note':PERSON_NOTE,'analysis_safe_columns_created':[]}

def chapter2_inventory(ctx):
 records=[]
 stems=[('village_crosswalk','support_crosswalk'),('urban_zoning_crosswalk','support_classification_v1'),('urban_zoning_crosswalk_v2','support_classification_v2'),('taipei_crashes_2024_2025_standardized','accident_level_source'),('taipei_village_base','geographic_base'),('taipei_crash_spatial_assignment_2024_2025','accident_assignment_source')]+[(s,'formal_upstream_feature') for k,s in STEMS.items() if k!='base']
 for stem,role in stems:
  rel=path(stem);sp=path(stem,'_schema.json');doc=path(stem,'_documentation.ipynb');raw=(ctx.root/rel).read_bytes()
  if (ctx.root/sp).is_file():
   sc=json.loads((ctx.root/sp).read_text(encoding='utf-8'));one=sc['columns'][0]['name'];f=read_csv(ctx.root/rel,sc,[one]);rows=len(f);cols=len(sc['columns']);producer=sc.get('producer','not available');obs=sc.get('observation_unit','source-defined');schema_hash=ctx.bindings.get(sp,sha(ctx.root/sp))
  else:
   f=pd.read_csv(ctx.root/rel,encoding='utf-8-sig',dtype='string',keep_default_na=False);rows,cols=f.shape
   producer='data/code/taipei_population_validation.ipynb' if stem=='village_crosswalk' else 'data/code/taipei_urban_planning_geometry_validation.ipynb';obs='one crosswalk key';schema_hash=None
  records.append({'dataset':stem,'role':role,'path':rel,'rows':rows,'columns':cols,**details(raw),'schema_path':sp if (ctx.root/sp).is_file() else None,'schema_sha256':schema_hash,'producer':producer,'documentation':doc,'observation_unit':obs,'version':'frozen existing file, no upstream rerun','quality_status':'local technical validation; original limitations retained, human acceptance pending'})
 return records

def make_registry(ctx,frames,defs,maps,quality):
 byname={}
 for period in ['annual','pooled']:
  for d in defs[period]:
   name=d['name']
   if name not in byname:
    byname[name]={k:v for k,v in d.items() if k not in ['name','source']};byname[name]['dataset_variants']={}
   entry=byname[name];assert entry['dtype']==d['dtype'] and entry['analytical_role']==d['analytical_role']
   entry['dataset_variants'][period]={'source':d['source'],'definition':d['definition'],'unit':d['unit'],'missing_rule':d['missing_rule'],'temporal_reference':d['temporal_reference']}
   entry['source_dataset']=list(dict.fromkeys(entry['source_dataset']+d['source_dataset']));entry['source_column']=list(dict.fromkeys(entry['source_column']+d['source_column']))
 body={p:encoded(f) for p,f in frames.items()};inventory=chapter2_inventory(ctx)
 for p,f in frames.items():inventory.append({'dataset':FINAL[p],'role':'final_analysis','path':path(FINAL[p]),'rows':len(f),'columns':len(f.columns),**details(body[p]),'schema_path':path(FINAL[p],'_schema.json'),'producer':PRODUCER,'documentation':path(FINAL[p],'_documentation.ipynb'),'observation_unit':'specification × fixed village'+(' × year' if p=='annual' else ' × pooled2024–2025'),'quality_status':'source-faithful complete skeleton; no formal sample/feature selection; human review pending'})
 inventory.append({'dataset':'taipei_feature_registry','role':'metadata_feature_use_contract','path':REGISTRY,'entries':len(byname),'producer':PRODUCER,'documentation':'data/processed/taipei_feature_registry_documentation.ipynb','self_hash_policy':'own bytes/hash are verified by independent documentation and PROJECT; not embedded recursively'})
 return {'unit':'2.7','created_at':'2026-11-27','registry_version':'unit27_v1','role':'metadata_feature_use_contract','producer':PRODUCER,'helper':HELPER,'documentation':'data/processed/taipei_feature_registry_documentation.ipynb','source_inputs':ctx.bindings,'input_manifest':ctx.manifest,'processing_environment':ctx.versions,'reviewed_project_context':ctx.project_context,
  'datasets':{p:{'path':path(FINAL[p]),'schema_path':path(FINAL[p],'_schema.json'),'documentation':path(FINAL[p],'_documentation.ipynb'),'rows':len(f),'columns':list(f),'primary_key':key(p),**details(body[p])} for p,f in frames.items()},
  'features':list(byname.values()),'role_counts':dict(Counter(x['analytical_role'] for x in byname.values())),
  'candidate_feature_sets':feature_sets(ctx),'main_research_skeleton':{'specification':'S0','period':'pooled','rows':456,'final_analysis_sample_selected':False,'final_A1_or_A2_selected':False},
  'specifications':{'S0':'primary fixed conservative','S1':'required selection sensitivity fixed geometric unique','S2':'historical conservative geography sensitivity','S3':'historical geometric unique geography sensitivity'},
  'structural_dependence_notes':DEPENDENCE,'blocked_features':ctx.contracts['b3']['blocked_features'],'source_readiness':{'B3':ctx.contracts['b3']['feature_readiness'],'B3_recommended_tiers':{'priority':B3_PRIORITY,'conditional_or_supplementary':B3_CONDITIONAL,'current_2026_supplementary':B3_CURRENT},'B2':'supplementary, report I/A and Q/A alongside comparisons; no final threshold','B1':'core external; source population stock event note retained'},
  'population_geographic_comparability_note':PERSON_NOTE,'B2_uncertainty_audit':quality['B2'],'numerical_boundary_audit':quality['numerical_boundary_audit'],'analysis_safe_policy':'none created: no downstream operation currently requires strict0–1. Original values/flags retained; do not globally clip. Future derivatives require justified source-based tolerance and separate names.',
  'temporal_isolation':{'2024_fit_only':'all future feature choice, low-count/smoothing fitted parameters, scaler, imputer, PCA and cluster centres must fit2024 alone; apply frozen transforms to2025','pooled_for_cross_year_fit':False,'static_B2_B3_are_annual_measurements':False,'MRT2026_is_pre_accident':False,'models_fitted_in_unit27':False,'same_village_years_independent':False},
  'low_count_policy':'candidate5/10/20/30/50 flags retained; final exclusion/smoothing/sample policy pending Chapter3; no complete-case deletion',
  'chapter2_inventory':inventory,'limitations':LIMITATIONS,'human_acceptance':'Codex assisted; DE handoff / DA acceptance / PM review pending','chapter3_started':False}

def validate_registry(registry,frames,defs):
 required=['column_name','source_dataset','source_column','definition','dtype','unit','analytical_role','temporal_reference','geographic_reference','missing_policy','zero_policy','readiness','recommended_use','allowed_for_main_clustering','allowed_for_external_comparison','sensitivity_group','leakage_warning','interpretation_limitations']
 entries={x['column_name']:x for x in registry['features']};assert len(entries)==len(registry['features'])
 assert set(entries)==set.union(*(set(f) for f in frames.values()))
 assert {x['column_name'] for x in registry['features'] if x['allowed_for_main_clustering']}==set(A2)
 assert registry['candidate_feature_sets']['A1']==A1 and registry['candidate_feature_sets']['A2']==A2
 for name,e in entries.items():
  assert all(k in e for k in required)
  assert e['analytical_role'] in ['identifier','clustering_candidate','core_external','priority_external','supplementary_external','burden_outcome','numerator_denominator','quality_indicator','sensitivity','metadata']
  for p,variant in e['dataset_variants'].items():
   assert name in frames[p] and e['dtype']==str(frames[p][name].dtype)
   source=next(x for x in defs[p] if x['name']==name);assert variant['source']==source['source']
 for p,f in frames.items():
  assert registry['datasets'][p]['columns']==list(f) and registry['datasets'][p]['primary_key']==key(p)
 for e in registry['blocked_features']:assert e['feature'] not in entries and e['formal_numeric_column_created'] is False
 return True

def schema(ctx,period,frame,defs,registry_hash,logs):
 return {'unit':'2.7','created_at':'2026-11-27','dataset_path':path(FINAL[period]),'producer':PRODUCER,'helper':HELPER,'documentation':path(FINAL[period],'_documentation.ipynb'),'role':'final_analysis_'+period,'primary_key':key(period),'expected_rows':len(frame),'observation_unit':'specification × fixed research village'+(' × year' if period=='annual' else ' × pooled2024–2025'),'csv':CSV,'columns':defs,'source_inputs':ctx.bindings,'input_manifest':ctx.manifest,'feature_registry':{'path':REGISTRY,'sha256':registry_hash},'processing_environment':ctx.versions,'merge_cardinality_log':logs,'geography':'original fixed456 CPTVID; original fixed area; historical area-time separate S2/S3','temporal_alignment':'B1 matching annual/pooled12/24months; B2/B3 repeated static snapshot, no independent annual observations','numerical_policy':'source raw ratios retained; 0.1m² upstream area tolerance, source numerator/denominator checked; no analysis_safe or universal clip','limitations':LIMITATIONS,'human_acceptance':'Codex assisted; DE handoff / DA acceptance / PM review pending'}

def export(ctx,frames,defs,maps,logs,registry):
 assert validate_registry(registry,frames,defs)
 for p,f in frames.items():validate_final(ctx,f,p,maps[p])
 regbody=jbytes(registry);reghash=details(regbody)['sha256'];payload={REGISTRY:regbody}
 for p,f in frames.items():payload[path(FINAL[p])]=encoded(f);payload[path(FINAL[p],'_schema.json')]=jbytes(schema(ctx,p,f,defs[p],reghash,logs[p]))
 for rel,body in payload.items():
  target=(ctx.root/rel).resolve();assert target.is_relative_to((ctx.root/'data/processed').resolve()) and rel not in ctx.bindings
  if target.exists():assert target.read_bytes()==body,('REFUSE DIFFERENT OUTPUT OVERWRITE',rel)
 for rel,body in payload.items():
  target=ctx.root/rel
  if not target.exists():
   with target.open('xb') as stream:stream.write(body)
 savedreg=json.loads((ctx.root/REGISTRY).read_text(encoding='utf-8'));assert savedreg==registry
 for p,f in frames.items():
  sc=json.loads((ctx.root/path(FINAL[p],'_schema.json')).read_text(encoding='utf-8'));saved=read_csv(ctx.root/path(FINAL[p]),sc)
  pd.testing.assert_frame_equal(saved,f,check_exact=True);assert sc['columns']==defs[p] and sc['feature_registry']['sha256']==reghash
  validate_final(ctx,saved,p,maps[p])
 verify(ctx.root,ctx.bindings)
 return {rel:{'path':rel,**details((ctx.root/rel).read_bytes())} for rel in payload}

def validate_documented(root,frame,contract,registry,period):
 """Independent saved Final checks; no integration, GIS or upstream processing."""
 root=Path(root);K=key(period)
 assert contract['dataset_path']==path(FINAL[period]) and contract['primary_key']==K
 assert len(frame)==(3648 if period=='annual' else 1824) and not frame.duplicated(K).any()
 assert list(frame)==[x['name'] for x in contract['columns']]==registry['datasets'][period]['columns']
 assert [str(frame[c].dtype) for c in frame]==[x['dtype'] for x in contract['columns']]
 assert frame[K].notna().all().all() and frame.groupby(['specification']+(['year'] if period=='annual' else [])).size().eq(456).all()
 assert frame.district_name.nunique()==12 and frame.village_id.nunique()==456
 bc=json.loads((root/path(STEMS['base'],'_schema.json')).read_text(encoding='utf-8'));base=read_csv(root/path(STEMS['base']),bc).set_index('village_id')
 assert set(frame.village_id)==set(base.index)
 same(frame.fixed_village_area_m2,frame.village_id.map(base.village_area_m2));same(frame.fixed_village_area_km2,frame.village_id.map(base.village_area_km2))
 for spec,nums in EXPECTED.items():
  f=frame.loc[frame.specification.eq(spec)]
  if period=='annual':assert [int(f.loc[f.year.eq(y),'observed_accident_count'].sum()) for y in [2024,2025]]==nums
  else:assert int(f.observed_accident_count.sum())==sum(nums)
 entries={e['column_name']:e for e in registry['features']}
 for d in contract['columns']:
  e=entries[d['name']];assert e['dtype']==d['dtype'] and e['analytical_role']==d['analytical_role']
  variant=e['dataset_variants'][period];assert variant['source']==d['source'] and variant['definition']==d['definition'] and variant['unit']==d['unit']
 assert {e['column_name'] for e in registry['features'] if e['allowed_for_main_clustering']}==set(A2)
 assert frame.observed_month_count.eq(12 if period=='annual' else 24).all() and frame.population_features_valid.all()
 width=frame.annotated_road_width_no_valid_samples
 assert set(frame.loc[width,'village_id'])=={'6301100048','6301200040','6301200042'}
 assert frame.loc[width,['median_annotated_road_width','annotated_road_width_q1','annotated_road_width_q3']].isna().all().all()
 assert frame.loc[frame.village_id.eq('6300700015'),'verification_status'].eq('provisional_match').all()
 assert frame.loc[frame.village_id.eq('6300700015'),'population_density'].notna().all()
 if period=='annual':
  zero=frame.loc[frame.village_id.eq('6301100044')&frame.year.eq(2025)];assert len(zero)==4 and zero.observed_accident_count.eq(0).all()
  assert zero.observed_accidents_per_fixed_km2.eq(0).all() and zero[A2+['mean_injuries_per_accident','source_positive_fatality_ratio']].isna().all().all()
 assert frame.b2_static_snapshot_repeated.all() and frame.b3_static_snapshot_repeated.all()
 assert frame.environment_snapshot_not_verified_pre_accident.all()
 for e in registry['blocked_features']:assert e['feature'] not in frame
 assert contract['feature_registry']['sha256']==sha(root/REGISTRY)
 return {'status':'passed','independent_saved_file_read':True,'dataset':period,'rows':len(frame),'columns':len(frame.columns),'source_contract_and_registry_consistent':True,'no_integration_or_GIS_rerun':True,'human_acceptance':'DE handoff / DA acceptance / PM review pending'}

def plots(ctx,frames,quality):
 import matplotlib.pyplot as plt
 from matplotlib import font_manager
 font=Path('C:/Windows/Fonts/msjh.ttc')
 if font.is_file():font_manager.fontManager.addfont(str(font));plt.rcParams['font.family']=[font_manager.FontProperties(fname=str(font)).get_name(),'DejaVu Sans']
 plt.rcParams['axes.unicode_minus']=False
 g=pd.DataFrame(quality['group_quality']);fig,axes=plt.subplots(1,3,figsize=(17,5))
 labels=g.specification+' / '+g.apply(lambda r:str(int(r.year)) if pd.notna(r.get('year')) else 'pooled',axis=1)
 axes[0].barh(labels,g.rows);axes[0].set(title='各規格完整456里骨架',xlabel='列數')
 f=frames['pooled'].loc[frames['pooled'].specification.eq('S0')];features=A2+B1+B2+B3_PRIORITY+B3_CONDITIONAL+B3_CURRENT
 na=[int(f[c].isna().sum()) for c in features];zero=[int(f[c].eq(0).sum()) for c in features];pos=np.arange(len(features))
 axes[1].barh(pos-.15,zero,height=.3,label='觀測0');axes[1].barh(pos+.15,na,height=.3,label='NA');axes[1].set_yticks(pos,features,fontsize=7);axes[1].set(title='S0 pooled候選零／缺失，未刪里',xlabel='里數');axes[1].legend()
 low=pd.DataFrame(quality['low_count_candidates']);v=low.loc[low.dataset.eq('pooled')&low.specification.eq('S0')];axes[2].bar(v.threshold_candidate.astype(str),v.accident_count_below);axes[2].set(title='低事故數候選門檻，未選正式政策',xlabel='候選門檻',ylabel='低於門檻里數')
 fig.suptitle('Unit2.7資料整合完整性與品質診斷；非正式EDA／Finding',fontsize=14);fig.tight_layout();p=ctx.temp/'integration_quality.png';fig.savefig(p,dpi=125,bbox_inches='tight');plt.show()
 return [p.relative_to(ctx.root).as_posix()]
