"""Unit 2.3 feature engineering from version-bound Unit 2.1/2.2 tables only.

No GIS, raw accident processing, imputation, feature scaling or model fitting.
Counts retain separate valid denominators; R20 sensitivity removes explicit True
only from casualty summaries, never from Dataset A or primary accident counts.
"""
from pathlib import Path
import hashlib
import io
import json
import numpy as np
import pandas as pd
from IPython.display import display, Markdown

FEATURES = {
 'morning_peak': ('morning_peak', '07:00≤時間<09:00'),
 'evening_peak': ('evening_peak', '17:00≤時間<19:00'),
 'late_night': ('late_night', '時間≥22:00或<06:00'),
 'weekend': ('weekend', '星期六或日，非全部國定假日'),
 'intersection': ('intersection', '位置代碼1–4，路口及附近／待轉／停等'),
 'rear_end': ('rear_end', '型態代碼13追撞'),
 'side_collision': ('side_collision', '型態代碼16側撞，非擦撞'),
 'pedestrian_collision': ('pedestrian_collision', '型態代碼1–9人與車代理，非所有行人涉入'),
 'multi_injury': ('multi_injury', '受傷人數≥2，不代表傷勢嚴重度'),
 'strict_intersection': ('intersection_strict', '位置代碼1，額外嚴格路口候選'),
}
MAIN_FEATURES = list(FEATURES)[:9]
CASUALTIES = {
 'injuries': ('injured_count', '受傷人數'),
 'fatalities_source': ('fatalities_source_count', '原死亡欄人數，時間窗未認證，不稱24h'),
 'fatalities_2_30d': ('fatalities_2_30d_count', '2–30日死亡欄，獨立保存、不與原死亡相加'),
}
SPECS = ['S0', 'S1', 'S2', 'S3']
THRESHOLDS = [5, 10, 20, 30, 50]
EXPECTED = {'S0': [21920,22292], 'S1': [22351,22732], 'S2': [21931,22302], 'S3': [22350,22730]}
STEMS = ['taipei_dataset_a_annual','taipei_dataset_a_pooled','taipei_dataset_c_annual','taipei_dataset_c_pooled']
PRODUCER = 'data/code/prepare_taipei_dataset_a_and_c.ipynb'
HELPER = 'data/code/unit23_feature_support.py'
CSV = {'encoding':'utf-8-sig','line_terminator':'LF','missing_sentinel':'__MISSING__',
       'keep_default_na':False,'boolean_values':['True','False'],'original_empty_strings':'preserved'}
LIMITATIONS = [
 'S0 primary; S1 required selection sensitivity; S2/S3 alternate geography, not independent samples',
 'all 456 villages retained; zero observations is not proof of no real accidents',
 'no final low-count threshold, imputation, smoothing, scaling, PCA, weighting or model selection',
 'registered population is not exposure; participants need not be local residents',
 'source accident datum unconfirmed; fixed geometry overlap/holes unchanged; history editions are snapshots',
 'source fatality time window and 2–30 day publication/follow-up semantics remain unconfirmed',
 'R20 denotes a conditional inconsistency, does not identify which field is wrong',
 'partial casualty sums describe known valid values only, not complete casualty totals',
 'density is spatial burden, not exposure-adjusted risk or probability',
 'A2 multi-injury and Dataset C injury burden are definitionally related, not independent validation',
 'annual 2024 training must fit future model preprocessing without using 2025 validation information',
 'Codex assisted execution; DE handoff, DA acceptance and PM review pending',
]

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()

def show(title, frame, block=20):
 display(Markdown('**'+title+'**'))
 if not len(frame): print('無符合紀錄')
 for start in range(0,len(frame),block): display(frame.iloc[start:start+block])

def read_csv(path, contract, selected=None):
 """Explicit schema parsing; float() preserves the writer's binary roundtrip."""
 defs=contract['columns']; names=[d['name'] for d in defs]
 header=pd.read_csv(path,encoding=contract['csv']['encoding'],nrows=0,keep_default_na=False)
 assert list(header)==names, ('column order',str(path))
 wanted=names if selected is None else list(selected)
 assert set(wanted)<=set(names)
 f=pd.read_csv(path,encoding=contract['csv']['encoding'],usecols=wanted,dtype='string',
               keep_default_na=False,na_values=[contract['csv']['missing_sentinel']])
 for d in defs:
  k=d['name']
  if k not in f:continue
  v=f[k];dtype=d['dtype']
  if dtype=='boolean':
   assert v.dropna().isin(['True','False']).all(), k
   f[k]=v.map({'True':True,'False':False}).astype('boolean')
  elif dtype=='Int64':f[k]=pd.to_numeric(v,errors='raise').astype('Int64')
  elif dtype=='Float64':f[k]=v.map(lambda x:pd.NA if pd.isna(x) else float(x)).astype('Float64')
  else:assert dtype=='string', (k,dtype)
 return f[wanted]

def divide(numerator, denominator):
 return (numerator.astype('Float64')/denominator.astype('Float64').where(denominator.gt(0))).astype('Float64')

def count_true(values):
 # Counting a predicate is different from replacing unknown source feature values.
 return values.eq(True).fillna(False).astype('Int64')

def common_keys(annual):return ['specification','village_id']+(['year'] if annual else [])

def input_tables(root, bindings):
 for rel, expected in bindings.items():assert sha(root/rel)==expected, ('INPUT HASH MISMATCH',rel)
 def get(stem,selected=None):
  schema=json.loads((root/f'data/processed/{stem}_schema.json').read_text(encoding='utf-8'))
  assert schema['csv']['missing_sentinel']=='__MISSING__'
  return read_csv(root/f'data/processed/{stem}.csv',schema,selected),schema
 cols=['record_id','source_year','conditional_casualty_inconsistency_flag','r20_check_valid','injured_count_raw']
 for source,_ in FEATURES.values():cols += [source,source+'_valid']
 for source,_ in CASUALTIES.values():cols += [source,source+'_structural_valid']
 accidents,acc_schema=get('taipei_crashes_2024_2025_standardized',cols)
 spatial_cols=['record_id','source_year']+[k for s in SPECS for k in [f'eligible_{s.lower()}',f'village_id_{s.lower()}']]
 spatial,spatial_schema=get('taipei_crash_spatial_assignment_2024_2025',spatial_cols)
 base,base_schema=get('taipei_village_base')
 assert len(acc_schema['columns'])==191 and len(spatial_schema['columns'])==91 and base.shape==(456,41)
 assert len(accidents)==len(spatial)==45130
 for f in [accidents,spatial]:assert f.record_id.notna().all() and f.record_id.is_unique
 assert set(accidents.record_id)==set(spatial.record_id)
 merged=accidents.merge(spatial,on='record_id',how='outer',validate='one_to_one',suffixes=('','_spatial'),indicator=True)
 assert len(merged)==45130 and merged['_merge'].eq('both').all()
 assert merged.source_year.eq(merged.source_year_spatial).all()
 merged=merged.drop(columns=['source_year_spatial','_merge'])
 assert merged.source_year.value_counts().to_dict()=={2025:22762,2024:22368}
 assert base.village_id.is_unique and base.village_id.str.fullmatch(r'\d{10}').all()
 assert base.district_name.nunique()==12
 for source,_ in FEATURES.values():
  assert merged[source].notna().eq(merged[source+'_valid']).all(),source
 for source,_ in CASUALTIES.values():
  assert merged[source].notna().eq(merged[source+'_structural_valid']).all(),source
  assert merged[source].dropna().ge(0).all()
 assert merged.conditional_casualty_inconsistency_flag.notna().eq(merged.r20_check_valid).all()
 for year,expected in [(2024,(6,227)),(2025,(4,215))]:
  v=merged.loc[merged.source_year.eq(year),'conditional_casualty_inconsistency_flag']
  assert (int(v.sum()),int(v.isna().sum()))==expected
 for s in SPECS:
  eligible=merged[f'eligible_{s.lower()}'];vid=merged[f'village_id_{s.lower()}']
  assert eligible.notna().all() and eligible.eq(vid.notna()).all()
  assert vid.dropna().isin(base.village_id).all()
  assert [int((eligible&merged.source_year.eq(y)).sum()) for y in [2024,2025]]==EXPECTED[s]
 for small,large in [('s0','s1'),('s2','s3')]:
  mask=merged[f'eligible_{small}']
  assert merged.loc[mask,f'eligible_{large}'].all()
  assert merged.loc[mask,f'village_id_{small}'].eq(merged.loc[mask,f'village_id_{large}']).all()
 tang=base.loc[base.standard_village_name.eq('糖廍里')]
 assert len(tang)==1 and tang.village_id.iloc[0]=='6300700015' and tang.verification_status.iloc[0]=='provisional_match'
 facts={'accidents':45130,'accident_schema_columns':191,'assignment_schema_columns':91,
        'base_shape':list(base.shape),'merge':'one_to_one; all 45130 retained',
        'raw_injury_empty_strings':int(merged.injured_count_raw.eq('').sum()),
        'raw_injury_sentinel_NA':int(merged.injured_count_raw.isna().sum()),
        'source_hashes_verified':len(bindings),'no_spatial_join':True}
 return merged,base,facts

def membership(merged):
 parts=[]
 source_cols=['record_id','source_year','conditional_casualty_inconsistency_flag']
 source_cols += [v[0] for v in FEATURES.values()]+[v[0] for v in CASUALTIES.values()]
 for s in SPECS:
  mask=merged[f'eligible_{s.lower()}']
  p=merged.loc[mask,source_cols].copy()
  p['specification']=s
  p['village_id']=merged.loc[mask,f'village_id_{s.lower()}']
  p=p.rename(columns={'source_year':'year'})
  parts.append(p)
 out=pd.concat(parts,ignore_index=True)
 out['specification']=out.specification.astype('string')
 assert not out.duplicated(['specification','record_id']).any()
 return out

def skeleton(base, annual):
 idx=pd.MultiIndex.from_product([SPECS,base.village_id.tolist()]+([[2024,2025]] if annual else []),names=common_keys(annual))
 return idx

def aggregate_counts(members,base,annual):
 keys=common_keys(annual);idx=skeleton(base,annual)
 group=members.groupby(keys,observed=True,sort=True,dropna=False)
 counts=pd.DataFrame(index=idx)
 counts['observed_accident_count']=group.size().reindex(idx,fill_value=0).astype('Int64')
 for feature,(source,_) in FEATURES.items():
  num=count_true(members[source]).groupby([members[k] for k in keys],sort=True).sum()
  den=members[source].notna().astype('Int64').groupby([members[k] for k in keys],sort=True).sum()
  counts[feature+'_numerator']=num.reindex(idx,fill_value=0).astype('Int64')
  counts[feature+'_denominator']=den.reindex(idx,fill_value=0).astype('Int64')
  counts[feature+'_false_count']=counts[feature+'_denominator']-counts[feature+'_numerator']
  counts[feature+'_missing_count']=counts.observed_accident_count-counts[feature+'_denominator']
 r=members.conditional_casualty_inconsistency_flag
 for name,mask in [('true',r.eq(True).fillna(False)),('false',r.eq(False).fillna(False)),('unknown',r.isna())]:
  counts['r20_'+name+'_count']=mask.astype('Int64').groupby([members[k] for k in keys]).sum().reindex(idx,fill_value=0).astype('Int64')
 counts['r20_excluded_accident_count']=counts.r20_true_count
 counts['r20_retained_accident_count']=counts.observed_accident_count-counts.r20_true_count
 for sensitivity in [False,True]:
  prefix='r20_excluded_' if sensitivity else ''
  pool=members.loc[~r.eq(True).fillna(False)] if sensitivity else members
  n=counts.r20_retained_accident_count if sensitivity else counts.observed_accident_count
  for stem,(source,_) in CASUALTIES.items():
   g=pool.groupby(keys,observed=True,sort=True)[source]
   valid=g.count().reindex(idx,fill_value=0).astype('Int64')
   summed=g.sum(min_count=1).reindex(idx).astype('Int64')
   # Empty collection=0; observed accidents with all values unknown=NA.
   summed=summed.mask(n.eq(0),0).mask(n.gt(0)&valid.eq(0),pd.NA)
   positive=pool[source].gt(0).fillna(False).astype('Int64').groupby([pool[k] for k in keys]).sum().reindex(idx,fill_value=0).astype('Int64')
   counts[prefix+stem+'_observed_sum']=summed
   counts[prefix+stem+'_valid_accident_count']=valid
   counts[prefix+stem+'_missing_accident_count']=n-valid
   counts[prefix+stem+'_positive_accident_count']=positive
 return counts.sort_index()

def pool_annual_counts(annual):
 pooled=annual.groupby(level=['specification','village_id'],sort=True).sum(min_count=1).astype('Int64')
 for prefix,ncol in [('', 'observed_accident_count'),('r20_excluded_','r20_retained_accident_count')]:
  for stem in CASUALTIES:
   valid=pooled[prefix+stem+'_valid_accident_count'];n=pooled[ncol]
   col=prefix+stem+'_observed_sum'
   pooled[col]=pooled[col].mask(n.eq(0),0).mask(n.gt(0)&valid.eq(0),pd.NA)
 return pooled

def definition(name,dtype,meaning,unit,source,missing):
 return {'name':name,'dtype':dtype,'definition':meaning,'unit':unit,'source':source,'missing_rule':missing}

def make_dataset(counts,base,annual,kind):
 data={};defs=[]
 def add(name,values,dtype,meaning,unit='not applicable',source='Unit2.3 deterministic aggregation',missing='不補值；依欄定義保留NA'):
  v=values if isinstance(values,pd.Series) else pd.Series(values,index=counts.index)
  if pd.api.types.is_scalar(values):v=pd.Series([values]*len(counts),index=counts.index)
  data[name]=v.reset_index(drop=True).astype(dtype)
  defs.append(definition(name,dtype,meaning,unit,source,missing))
 flat=counts.reset_index();ids=flat.village_id
 lookup=base.set_index('village_id')
 add('specification',flat.specification,'string','S0主分析；S1必要保守程度敏感度；S2歷史界；S3共同敏感度')
 add('village_id',ids,'string','固定CPTVID共同10碼研究ID','identifier','Unit2.2 village_id','不可缺失，不轉數值')
 if annual:add('year',flat.year,'Int64','事故年度','year','Unit2.1 source_year','不可缺失')
 add('period_start_year',flat.year if annual else 2024,'Int64','本列觀測期間起年','year')
 add('period_end_year',flat.year if annual else 2025,'Int64','本列觀測期間迄年','year')
 add('period_years',1 if annual else 2,'Int64','觀測期間年數','year')
 add('period',flat.year.astype('string') if annual else '2024–2025','string','年度或兩年合併期間標示')
 for col,meaning in [('district_name','固定研究行政區'),('standard_village_name','標準里名，糖廍里已接受')]:
  add(col,ids.map(lookup[col]),'string',meaning,source='Unit2.2 village base',missing='不可缺失')
 add('boundary_version',flat.specification.map({'S0':'fixed','S1':'fixed','S2':'source_year_history','S3':'source_year_history'}),'string','空間配對採固定或對應年歷史界')
 add('assignment_rule',flat.specification.map({'S0':'conservative','S1':'geometry_unique','S2':'conservative','S3':'geometry_unique'}),'string','沿用Unit2.2，不重新歸里')
 add('observed_accident_count',counts.observed_accident_count,'Int64','成功歸里之觀測事故數，非完整真實事故總數','accident','Unit2.2 eligible and village_id','無觀測配對事故為0')
 add('has_observed_accident',counts.observed_accident_count.gt(0),'boolean','是否至少一筆觀測配對事故')
 for t in THRESHOLDS:add(f'count_lt_{t}',counts.observed_accident_count.lt(t),'boolean',f'觀測事故數<{t}候選品質旗標；不排除任何里')
 n=counts.observed_accident_count
 if kind=='a':
  for feature,(source,meaning) in FEATURES.items():
   prefix=feature+'_';den=counts[prefix+'denominator'];num=counts[prefix+'numerator']
   for suffix,explanation in [('numerator','有效且符合條件'),('denominator','該特徵有效'),('false_count','有效且不符合'),('missing_count','該特徵缺失或無效')]:
    add(prefix+suffix,counts[prefix+suffix],'Int64',meaning+'；'+explanation+'事故數','accident','Unit2.1 '+source+' / '+source+'_valid','計數可為0；不把來源NA當False')
   add(prefix+'coverage',divide(den,n),'Float64',meaning+'；有效數／觀測數','fraction','各自denominator / observed_accident_count','觀測事故數0則NA')
   add(prefix+'ratio',divide(num,den),'Float64',meaning+'；符合數／各自有效數','fraction','各自numerator / denominator','有效分母0則NA')
   for t in THRESHOLDS:add(prefix+f'denominator_lt_{t}',den.lt(t),'boolean',f'{meaning}有效分母<{t}候選旗標，不作正式排除')
 else:
  for col in ['r20_true_count','r20_false_count','r20_unknown_count','r20_excluded_accident_count','r20_retained_accident_count']:
   meaning={'r20_true_count':'明確R20=True數','r20_false_count':'明確R20=False數，未知不混入','r20_unknown_count':'R20=NA數','r20_excluded_accident_count':'敏感度僅排除明確True數，不改主事故數','r20_retained_accident_count':'敏感度保留False及未知之事故數'}[col]
   add(col,counts[col],'Int64',meaning,'accident','Unit2.1 conditional_casualty_inconsistency_flag','三態分開計數')
  for sensitivity in [False,True]:
   prefix='r20_excluded_' if sensitivity else ''
   ns=counts.r20_retained_accident_count if sensitivity else n
   for stem,(source,meaning) in CASUALTIES.items():
    key=prefix+stem;valid=counts[key+'_valid_accident_count'];missing=counts[key+'_missing_accident_count']
    label=('排除明確R20=True後；' if sensitivity else '主要原有效值口徑；')+meaning
    add(key+'_observed_sum',counts[key+'_observed_sum'],'Int64',label+'；已知有效值加總，部分缺失非完整總數','person','Unit2.1 '+source,'無觀測事故=0（空集合）；有事故但全缺失=NA')
    for suffix,desc in [('valid_accident_count','獨立有效事故數'),('missing_accident_count','獨立缺失事故數'),('positive_accident_count','有效且人數>0事故數')]:
     add(key+'_'+suffix,counts[key+'_'+suffix],'Int64',label+'；'+desc,'accident','Unit2.1 '+source+' / '+source+'_structural_valid','0為計數，不補原傷亡值')
    add(key+'_coverage',divide(valid,ns),'Float64',label+'；有效事故數／本口徑保留事故數','fraction',missing='本口徑保留事故數0則NA')
    add(key+'_all_missing_flag',ns.gt(0)&valid.eq(0),'boolean',label+'；有觀測事故但本欄全缺失')
    add(key+'_partial_missing_flag',valid.gt(0)&missing.gt(0),'boolean',label+'；本欄部分缺失，總量僅已知部分')
   add(prefix+'mean_injuries_per_accident',divide(counts[prefix+'injuries_observed_sum'],counts[prefix+'injuries_valid_accident_count']),'Float64','有效受傷人數和／受傷欄有效事故數','person / valid accident',missing='受傷欄有效分母0則NA')
   add(prefix+'source_positive_fatality_ratio',divide(counts[prefix+'fatalities_source_positive_accident_count'],counts[prefix+'fatalities_source_valid_accident_count']),'Float64','原死亡欄有效且>0事故數／原死亡欄有效事故數，非已認證死亡事故率','fraction',missing='原死亡欄有效分母0則NA')
  for stem in CASUALTIES:
   add(stem+'_sum_removed_by_r20',counts[stem+'_observed_sum']-counts['r20_excluded_'+stem+'_observed_sum'],'Int64','主要已知人數和減R20敏感度已知人數和；任一未知則NA','person')
  add('mean_injuries_r20_difference',data['mean_injuries_per_accident']-data['r20_excluded_mean_injuries_per_accident'],'Float64','主要平均受傷減R20敏感度平均受傷；分母各自重算','person / valid accident')
  add('source_fatality_ratio_r20_difference',data['source_positive_fatality_ratio']-data['r20_excluded_source_positive_fatality_ratio'],'Float64','主要原死亡正值比例減R20敏感度比例','fraction difference')
  area=ids.map(lookup.village_area_km2).astype('Float64')
  historical=flat.specification.isin(['S2','S3'])
  if annual:
   histarea=pd.Series([lookup.loc[v,f'historical_area_km2_{int(y)}'] for v,y in zip(ids,flat.year)],dtype='Float64')
  else:histarea=ids.map(lookup.historical_area_km2_2024+lookup.historical_area_km2_2025).astype('Float64')
  histarea=histarea.where(historical)
  add('fixed_village_area_km2',area,'Float64','原固定EPSG:3826幾何面積，共同分母，不使用AREA','km²','Unit2.2 village_area_km2','正值不可缺失')
  add('historical_density_applicable',historical,'boolean','僅S2/S3適用歷史地理密度')
  add('historical_area_time_km2_year',histarea,'Float64','年度為該年歷史面積×1年；pooled為兩年歷史面積和','km² year','Unit2.2 historical_area_km2_2024/2025','S0/S1不適用為NA')
  add('observed_accidents_per_fixed_km2',divide(n.reset_index(drop=True),area),'Float64','觀測事故數／固定面積；年度為當年、pooled為兩年累計','accident / km² / observation period')
  add('mean_annual_observed_accidents_per_fixed_km2',divide(n.reset_index(drop=True),area*(1 if annual else 2)),'Float64','觀測事故數／（固定面積×期間年數），pooled平均每年','accident / km² / year')
  add('historical_mean_annual_accidents_per_km2',divide(n.reset_index(drop=True),histarea),'Float64','觀測事故數／歷史面積年總和；pooled為面積年加權平均年度密度，不是累計密度','accident / km² / year',missing='S0/S1不適用為NA')
 frame=pd.DataFrame(data)
 assert list(frame)==[d['name'] for d in defs]
 return frame,defs

def validate_dataset(frame,kind,annual):
 keys=common_keys(annual)
 assert len(frame)==(3648 if annual else 1824) and not frame.duplicated(keys).any()
 assert frame.specification.value_counts().to_dict()=={s:912 if annual else 456 for s in SPECS}
 assert frame.groupby('specification').village_id.nunique().eq(456).all()
 assert frame.village_id.str.fullmatch(r'\d{10}').all()
 assert frame.period_years.eq(1 if annual else 2).all()
 if annual:
  assert set(frame.year)=={2024,2025}
  assert frame.groupby(['specification','year']).size().eq(456).all()
 n=frame.observed_accident_count
 assert n.notna().all() and n.ge(0).all() and frame.has_observed_accident.eq(n.gt(0)).all()
 for s in SPECS:
  f=frame.loc[frame.specification.eq(s)]
  if annual:
   assert [int(f.loc[f.year.eq(y),'observed_accident_count'].sum()) for y in [2024,2025]]==EXPECTED[s]
  else:assert int(f.observed_accident_count.sum())==sum(EXPECTED[s])
 for t in THRESHOLDS:assert frame[f'count_lt_{t}'].eq(n.lt(t)).all()
 if kind=='a':
  for feature in FEATURES:
   num=frame[feature+'_numerator'];den=frame[feature+'_denominator'];false=frame[feature+'_false_count'];missing=frame[feature+'_missing_count']
   assert (num+false).eq(den).all() and (den+missing).eq(n).all()
   assert num.ge(0).all() and num.le(den).all() and den.le(n).all()
   pd.testing.assert_series_equal(frame[feature+'_ratio'],divide(num,den),check_names=False)
   pd.testing.assert_series_equal(frame[feature+'_coverage'],divide(den,n),check_names=False)
   for t in THRESHOLDS:assert frame[f'{feature}_denominator_lt_{t}'].eq(den.lt(t)).all()
  assert frame.strict_intersection_numerator.le(frame.intersection_numerator).all()
  assert frame.strict_intersection_denominator.eq(frame.intersection_denominator).all()
 else:
  assert (frame.r20_true_count+frame.r20_false_count+frame.r20_unknown_count).eq(n).all()
  assert frame.r20_retained_accident_count.eq(n-frame.r20_true_count).all()
  for prefix,ns in [('',n),('r20_excluded_',frame.r20_retained_accident_count)]:
   for stem in CASUALTIES:
    key=prefix+stem;v=frame[key+'_valid_accident_count'];m=frame[key+'_missing_accident_count'];total=frame[key+'_observed_sum']
    assert (v+m).eq(ns).all() and v.ge(0).all() and m.ge(0).all()
    assert total.isna().eq(ns.gt(0)&v.eq(0)).all()
    assert total.loc[ns.eq(0)].eq(0).all()
    assert frame[key+'_positive_accident_count'].le(v).all()
    pd.testing.assert_series_equal(frame[key+'_coverage'],divide(v,ns),check_names=False)
    assert frame[key+'_all_missing_flag'].eq(ns.gt(0)&v.eq(0)).all()
    assert frame[key+'_partial_missing_flag'].eq(v.gt(0)&m.gt(0)).all()
   pd.testing.assert_series_equal(frame[prefix+'mean_injuries_per_accident'],divide(frame[prefix+'injuries_observed_sum'],frame[prefix+'injuries_valid_accident_count']),check_names=False)
   pd.testing.assert_series_equal(frame[prefix+'source_positive_fatality_ratio'],divide(frame[prefix+'fatalities_source_positive_accident_count'],frame[prefix+'fatalities_source_valid_accident_count']),check_names=False)
  assert frame.fixed_village_area_km2.gt(0).all()
  applies=frame.specification.isin(['S2','S3'])
  assert frame.historical_density_applicable.eq(applies).all()
  assert frame.historical_area_time_km2_year.isna().eq(~applies).all()
  pd.testing.assert_series_equal(frame.observed_accidents_per_fixed_km2,divide(n,frame.fixed_village_area_km2),check_names=False)
  pd.testing.assert_series_equal(frame.mean_annual_observed_accidents_per_fixed_km2,divide(n,frame.fixed_village_area_km2*frame.period_years),check_names=False)
  pd.testing.assert_series_equal(frame.historical_mean_annual_accidents_per_km2,divide(n,frame.historical_area_time_km2_year),check_names=False)
 for col in frame:
  if col.endswith(('_ratio','_coverage')) and not col.endswith('_difference'):
   assert frame[col].dropna().between(0,1).all(),col
 assert len(frame.loc[frame.standard_village_name.eq('糖廍里')])==(8 if annual else 4)
 if annual:
  zero=frame.loc[frame.village_id.eq('6301100044')&frame.year.eq(2025)]
  assert len(zero)==4 and zero.observed_accident_count.eq(0).all()
  if kind=='a':
   for feature in FEATURES:
    assert zero[feature+'_denominator'].eq(0).all() and zero[feature+'_ratio'].isna().all() and zero[feature+'_coverage'].isna().all()
  else:
   assert zero.observed_accidents_per_fixed_km2.eq(0).all()
   assert zero.mean_injuries_per_accident.isna().all() and zero.source_positive_fatality_ratio.isna().all()
 return True

def build(root,bindings):
 merged,base,facts=input_tables(root,bindings)
 members=membership(merged)
 annual=aggregate_counts(members,base,True)
 pooled=pool_annual_counts(annual)
 direct=aggregate_counts(members,base,False)
 pd.testing.assert_frame_equal(pooled,direct,check_exact=True)
 datasets={};definitions={}
 for kind in ['a','c']:
  for isannual,counts in [(True,annual),(False,pooled)]:
   name=f'taipei_dataset_{kind}_'+('annual' if isannual else 'pooled')
   f,d=make_dataset(counts,base,isannual,kind)
   validate_dataset(f,kind,isannual)
   datasets[name]=f;definitions[name]=d
 for period in ['annual','pooled']:
  a=datasets[f'taipei_dataset_a_{period}'];c=datasets[f'taipei_dataset_c_{period}']
  pd.testing.assert_frame_equal(a[common_keys(period=='annual')+['observed_accident_count']],c[common_keys(period=='annual')+['observed_accident_count']])
 facts.update({'pooled_direct_vs_annual_counts':'passed; exact counts and NA',
               'formal_datasets':4,'human_review':'Codex assisted; DE / DA / PM acceptance pending'})
 facts['membership_comparisons']=[]
 for year in [2024,2025]:
  primary=set(members.loc[members.year.eq(year)&members.specification.eq('S0'),'record_id'])
  for spec in ['S1','S2','S3']:
   other=set(members.loc[members.year.eq(year)&members.specification.eq(spec),'record_id'])
   facts['membership_comparisons'].append({'year':year,'comparison':spec+' versus S0',
      'S0_only':len(primary-other),'other_only':len(other-primary),'both':len(primary&other)})
 validate_bundle(datasets,base)
 return datasets,definitions,members,base,facts

def validate_bundle(datasets,base):
 """Independent saved-table handoff checks; no accident processing or GIS."""
 for kind in ['a','c']:
  a=datasets[f'taipei_dataset_{kind}_annual'];p=datasets[f'taipei_dataset_{kind}_pooled']
  validate_dataset(a,kind,True);validate_dataset(p,kind,False)
  key=['specification','village_id'];q=p.set_index(key).sort_index()
  g=a.groupby(key,sort=True)
  countcols=[col for col in a if col.endswith(('_count','_numerator','_denominator'))]
  # observed casualty sums require explicit all-missing handling below.
  summed=g[countcols].sum(min_count=1)
  pd.testing.assert_frame_equal(summed,q[countcols],check_exact=True)
  if kind=='c':
   for prefix,ncol in [('', 'observed_accident_count'),('r20_excluded_','r20_retained_accident_count')]:
    for stem in CASUALTIES:
     col=prefix+stem+'_observed_sum';total=g[col].sum(min_count=1)
     expected=total.mask(q[ncol].eq(0),0).mask(q[ncol].gt(0)&q[prefix+stem+'_valid_accident_count'].eq(0),pd.NA)
     pd.testing.assert_series_equal(expected,q[col],check_exact=True)
 for period in ['annual','pooled']:
  a=datasets[f'taipei_dataset_a_{period}'];c=datasets[f'taipei_dataset_c_{period}']
  keys=common_keys(period=='annual')+['observed_accident_count']
  pd.testing.assert_frame_equal(a[keys],c[keys])
  lookup=base.set_index('village_id')
  assert c.fixed_village_area_km2.eq(c.village_id.map(lookup.village_area_km2)).all()
  for s in SPECS:assert set(c.loc[c.specification.eq(s),'village_id'])==set(base.village_id)
  applies=c.historical_density_applicable
  if period=='annual':
   expected=pd.Series([lookup.loc[v,f'historical_area_km2_{int(y)}'] for v,y in zip(c.village_id,c.year)],dtype='Float64')
  else:expected=c.village_id.map(lookup.historical_area_km2_2024+lookup.historical_area_km2_2025).astype('Float64')
  pd.testing.assert_series_equal(c.historical_area_time_km2_year,expected.where(applies),check_names=False,check_exact=True)
 return {'status':'passed','A_C_keys_counts':'exact','pooled_counts_and_nullable_sums':'exact','area_denominators':'match Unit2.2 base'}

def edge_case_checks():
 """Small synthetic checks of dangerous nullable pooling, not research data."""
 index=pd.MultiIndex.from_product([['S0'],['0000000001'],[2024,2025]],names=['specification','village_id','year'])
 for n,v,s,expected in [([0,2],[0,0],[0,pd.NA],pd.NA),([0,2],[0,2],[0,3],3),([2,3],[0,0],[pd.NA,pd.NA],pd.NA),([1,1],[0,1],[pd.NA,2],2)]:
  a=pd.DataFrame(index=index)
  a['observed_accident_count']=pd.array(n,dtype='Int64');a['r20_retained_accident_count']=a.observed_accident_count
  for prefix in ['', 'r20_excluded_']:
   for stem in CASUALTIES:
    a[prefix+stem+'_valid_accident_count']=pd.array(v,dtype='Int64')
    a[prefix+stem+'_observed_sum']=pd.array(s,dtype='Int64')
  actual=pool_annual_counts(a).injuries_observed_sum.iloc[0]
  assert pd.isna(actual) if pd.isna(expected) else actual==expected
 zero=pd.Series([0,1],dtype='Int64');den=pd.Series([0,2],dtype='Int64')
 assert pd.isna(divide(zero,den).iloc[0]) and divide(zero,den).iloc[1]==0.5
 r=pd.Series([True,False,pd.NA],dtype='boolean')
 assert list((~r.eq(True).fillna(False)))==[False,True,True]
 return {'nullable_pooling_edge_cases':4,'zero_denominator':'passed','R20_unknown_retained':'passed'}

def contract(stem,definitions,bindings):
 annual=stem.endswith('annual');kind=stem.split('_')[2]
 return {'unit':'2.3','created_at':'2026-11-26','dataset_path':f'data/processed/{stem}.csv',
  'producer':PRODUCER,'helper':HELPER,'documentation':f'data/processed/{stem}_documentation.ipynb',
  'role':'accident_composition_candidates' if kind=='a' else 'external_accident_burden',
  'observation_unit':'specification × fixed research village'+(' × year' if annual else ' × pooled 2024–2025 period'),
  'expected_rows':3648 if annual else 1824,'primary_key':common_keys(annual),
  'csv':CSV,'columns':definitions,'source_inputs':bindings,
  'specifications':{'S0':'PRIMARY fixed conservative','S1':'REQUIRED selection sensitivity, fixed geometry only','S2':'historical conservative sensitivity','S3':'historical geometry-only sensitivity'},
  'feature_sets':{'A1':[f+'_ratio' for f in MAIN_FEATURES if f!='multi_injury'], 'A2':[f+'_ratio' for f in MAIN_FEATURES], 'strict_candidate':'strict_intersection_ratio'},
  'pooling':'sum raw numerators, valid denominators, false and missing counts; recompute ratios/coverage, never average yearly fractions',
  'casualty_missing':'empty observed set sum=0; observed accidents but zero valid values sum=NA; partially missing sum covers known values only',
  'r20':'primary unchanged; sensitivity removes explicit True only, retains unknown separately, recomputes each casualty valid denominator',
  'density':'fixed period cumulative N/area; mean annual N/(period_years*fixed area); S2/S3 historical N/sum(yearly history area), area-year weighted; S0/S1 historical NA',
  'low_count':'5/10/20/30/50 candidate flags, no exclusion threshold adopted','limitations':LIMITATIONS}

def export(root,datasets,definitions,bindings):
 # Preflight all destinations before any write; reruns may only reproduce bytes.
 planned={}
 for stem,f in datasets.items():
  csv=f.to_csv(index=False,na_rep='__MISSING__',lineterminator='\n',float_format='%.17g').encode('utf-8-sig')
  schema=contract(stem,definitions[stem],bindings)
  js=(json.dumps(schema,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
  planned[f'data/processed/{stem}.csv']=csv
  planned[f'data/processed/{stem}_schema.json']=js
 for rel,data in planned.items():
  p=(root/rel).resolve()
  assert p.is_relative_to((root/'data/processed').resolve())
  assert rel not in bindings
  if p.exists():assert p.read_bytes()==data,('REFUSE DIFFERENT OUTPUT OVERWRITE',rel)
 for rel,data in planned.items():
  p=root/rel
  if not p.exists():
   with p.open('xb') as stream:stream.write(data)
 outputs={}
 for stem,expected in datasets.items():
  rel=f'data/processed/{stem}.csv';schemarel=f'data/processed/{stem}_schema.json'
  schema=json.loads((root/schemarel).read_text(encoding='utf-8'))
  actual=read_csv(root/rel,schema)
  pd.testing.assert_frame_equal(actual,expected,check_exact=True)
  validate_dataset(actual,stem.split('_')[2],stem.endswith('annual'))
  for path in [rel,schemarel]:outputs[path]={'path':path,'bytes':(root/path).stat().st_size,'sha256':sha(root/path)}
 return outputs

def diagnostics(datasets):
 features=[];burden=[];low=[];distributions=[]
 for period in ['annual','pooled']:
  a=datasets[f'taipei_dataset_a_{period}'];c=datasets[f'taipei_dataset_c_{period}']
  groups=['specification']+(['year'] if period=='annual' else [])
  for key,g in a.groupby(groups,sort=True):
   vals=key if isinstance(key,tuple) else (key,);info=dict(zip(groups,[int(v) if k=='year' else str(v) for k,v in zip(groups,vals)]));info['period']=period
   n=int(g.observed_accident_count.sum())
   for feature in FEATURES:
    den=int(g[feature+'_denominator'].sum());num=int(g[feature+'_numerator'].sum());missing=int(g[feature+'_missing_count'].sum())
    features.append(dict(info,feature=feature,observed_N=n,numerator=num,denominator=den,false_count=den-num,missing_count=missing,coverage=den/n if n else None,ratio=num/den if den else None))
    for t in THRESHOLDS:
     low.append(dict(info,variable=feature+'_denominator',threshold=t,villages_below=int(g[feature+'_denominator'].lt(t).sum()),zero=int(g[feature+'_denominator'].eq(0).sum())))
   for t in THRESHOLDS:low.append(dict(info,variable='observed_accident_count',threshold=t,villages_below=int(g.observed_accident_count.lt(t).sum()),zero=int(g.observed_accident_count.eq(0).sum())))
   distributions.append(dict(info,min=int(g.observed_accident_count.min()),median=float(g.observed_accident_count.median()),max=int(g.observed_accident_count.max()),zero_villages=int(g.observed_accident_count.eq(0).sum())))
  for key,g in c.groupby(groups,sort=True):
   vals=key if isinstance(key,tuple) else (key,);info=dict(zip(groups,[int(v) if k=='year' else str(v) for k,v in zip(groups,vals)]));info['period']=period
   row=dict(info,observed_N=int(g.observed_accident_count.sum()))
   for col in ['r20_true_count','r20_false_count','r20_unknown_count','r20_retained_accident_count']:row[col]=int(g[col].sum())
   for prefix in ['', 'r20_excluded_']:
    for stem in CASUALTIES:
     for suffix in ['observed_sum','valid_accident_count','missing_accident_count','positive_accident_count']:
      v=g[prefix+stem+'_'+suffix].sum(min_count=1);row[prefix+stem+'_'+suffix]=None if pd.isna(v) else int(v)
   burden.append(row)
 cross=[]
 for period in ['annual','pooled']:
  for kind in ['a','c']:
   f=datasets[f'taipei_dataset_{kind}_{period}'];keys=['village_id']+(['year'] if period=='annual' else [])
   measures=(['observed_accident_count']+[feature+suffix for feature in MAIN_FEATURES for suffix in ['_ratio','_denominator','_missing_count','_coverage']] if kind=='a' else ['injuries_observed_sum','fatalities_source_observed_sum','fatalities_2_30d_observed_sum','mean_injuries_per_accident','source_positive_fatality_ratio','observed_accidents_per_fixed_km2'])
   primary=f.loc[f.specification.eq('S0')].set_index(keys)
   for spec in ['S1','S2','S3']:
    other=f.loc[f.specification.eq(spec)].set_index(keys).reindex(primary.index)
    for col in measures:
     x=primary[col];y=other[col];both=x.notna()&y.notna();delta=(y[both]-x[both]).astype('Float64')
     cross.append({'period':period,'dataset':kind,'comparison':spec+'−S0','variable':col,
                   'both_valid':int(both.sum()),'only_S0_missing':int((x.isna()&y.notna()).sum()),
                   'only_other_missing':int((x.notna()&y.isna()).sum()),'both_missing':int((x.isna()&y.isna()).sum()),
                   'changed_valid':int(delta.ne(0).sum()),'mean_difference':float(delta.mean()) if len(delta) else None,
                   'median_abs_difference':float(delta.abs().median()) if len(delta) else None,
                   'max_abs_difference':float(delta.abs().max()) if len(delta) else None})
 return {'feature_totals':features,'casualty_totals':burden,'low_count_diagnostics':low,
         'count_distribution':distributions,'cross_specification':cross,
         'feature_dependence':'three time features share time; collision features share type; multi-injury linked to C; no normalization, feature deletion or correlation-based selection'}

def plots(datasets,diag,root):
 import matplotlib
 import matplotlib.pyplot as plt
 plt.rcParams.update({'font.family':'Microsoft JhengHei','axes.unicode_minus':False})
 out=root/'data/temp/unit23_validation';out.mkdir(parents=True,exist_ok=True)
 paths=[]
 def finish(fig,name):
  fig.suptitle('Unit 2.3 資料處理與品質診斷；非正式Finding',fontsize=13)
  fig.tight_layout(rect=(0,0,1,.95));path=out/name;fig.savefig(path,dpi=140,bbox_inches='tight');plt.show();paths.append(path.relative_to(root).as_posix())
 fig,axes=plt.subplots(1,3,figsize=(15,4.6))
 for ax,label,period,year in [(axes[0],'2024','annual',2024),(axes[1],'2025','annual',2025),(axes[2],'2024–2025合併','pooled',None)]:
  f=datasets['taipei_dataset_a_'+period];f=f.loc[f.year.eq(year)] if year else f
  ax.boxplot([f.loc[f.specification.eq(s),'observed_accident_count'].astype(float) for s in SPECS],tick_labels=SPECS,showfliers=True)
  ax.set(title=label,ylabel='每里觀測事故數（完整456里）')
 finish(fig,'counts_by_specification.png')
 totals=pd.DataFrame(diag['feature_totals']);low=pd.DataFrame(diag['low_count_diagnostics'])
 fig,axes=plt.subplots(1,3,figsize=(17,5))
 for ax,metric,title in [(axes[0],'denominator','九特徵有效事故分母'),(axes[1],'coverage','九特徵有效覆蓋率')]:
  t=totals.loc[totals.period.eq('pooled')&totals.feature.isin(MAIN_FEATURES)].pivot(index='feature',columns='specification',values=metric).reindex(MAIN_FEATURES)
  image=ax.imshow(t.to_numpy(float),aspect='auto',vmin=.995 if metric=='coverage' else None,vmax=1 if metric=='coverage' else None)
  ax.set_xticks(range(4),SPECS);ax.set_yticks(range(9),MAIN_FEATURES);ax.set_title(title+'（兩年合併）');fig.colorbar(image,ax=ax,shrink=.8)
 z=low.loc[low.period.eq('pooled')&low.variable.eq('observed_accident_count')].pivot(index='threshold',columns='specification',values='villages_below')
 for s in SPECS:axes[2].plot(z.index,z[s],marker='o',label=s)
 axes[2].set(title='兩年合併低事故數候選門檻',xlabel='事故數小於門檻',ylabel='行政里數');axes[2].legend()
 finish(fig,'denominators_coverage_low_counts.png')
 fig,axes=plt.subplots(1,3,figsize=(17,5))
 f=datasets['taipei_dataset_a_pooled'];p=f.loc[f.specification.eq('S0')].set_index('village_id')
 for ax,feature in [(axes[0],'rear_end'),(axes[1],'multi_injury')]:
  for s in ['S1','S2','S3']:
   q=f.loc[f.specification.eq(s)].set_index('village_id').reindex(p.index)
   delta=q[feature+'_ratio']-p[feature+'_ratio'];ax.hist(delta.dropna().astype(float),bins=28,histtype='step',label=s+' - S0')
  ax.set(title=feature+'比例差（共同有效里）',xlabel='比例差',ylabel='行政里數');ax.legend()
 c=datasets['taipei_dataset_c_pooled']
 for s in SPECS:axes[2].hist(c.loc[c.specification.eq(s),'mean_annual_observed_accidents_per_fixed_km2'].astype(float),bins=30,histtype='step',label=s)
 axes[2].set(title='固定分母平均年度空間密度',xlabel='事故／km²／年；非暴露校正率',ylabel='行政里數');axes[2].legend()
 finish(fig,'cross_specification_and_density.png')
 fig,axes=plt.subplots(1,2,figsize=(13,4.7))
 c=datasets['taipei_dataset_c_pooled'];coverage=c.groupby('specification')[[k+'_coverage' for k in CASUALTIES]].min()
 coverage.plot.bar(ax=axes[0],ylim=(.95,1.001),rot=0);axes[0].set(title='各里傷亡欄覆蓋率最小值（兩年）',ylabel='最小有效覆蓋率')
 totals=pd.DataFrame(diag['casualty_totals']);r=totals.loc[totals.period.eq('annual')].copy();labels=r.specification+' / '+r.year.astype('Int64').astype('string')
 axes[1].bar(labels,r.r20_unknown_count,label='R20未知');axes[1].bar(labels,r.r20_true_count,bottom=r.r20_unknown_count,label='明確R20=True')
 axes[1].tick_params(axis='x',rotation=45);axes[1].set(title='R20未知與明確疑點分開保留',ylabel='事故數');axes[1].legend()
 finish(fig,'casualty_coverage_r20.png')
 return paths
