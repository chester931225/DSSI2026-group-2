"""Unit 2.4: registered-population processing, with no accident engineering/GIS.

Sources are version-bound raw population, existing crosswalk and formal village
base. A/C files are used only for an optional key-only handoff validation.
"""
from pathlib import Path
import hashlib,io,json
import numpy as np
import pandas as pd
from IPython.display import display,Markdown

RAW='data/raw/112迄今各里人口數按年齡分.csv'
HELPER='data/code/unit24_population_support.py'
PRODUCER='data/code/prepare_taipei_dataset_b1.ipynb'
STEMS=['taipei_dataset_b1_annual','taipei_dataset_b1_pooled']
AGE=[f'{a}歲數量' for a in range(100)]+['100歲以上']
NUMERIC=['總計']+AGE
RAW_COLUMNS=['年份','月份','區域代碼','區域別','性別']+NUMERIC
AGE_GROUPS={'children':[f'{a}歲數量' for a in range(15)],
 'working_age':[f'{a}歲數量' for a in range(15,65)],
 'elderly':[f'{a}歲數量' for a in range(65,100)]+['100歲以上']}
COMPONENTS=['total','elderly','children']
FEATURES=['population_density','elderly_ratio','children_ratio']
CSV={'encoding':'utf-8-sig','line_terminator':'LF','missing_sentinel':'__MISSING__',
 'keep_default_na':False,'boolean_values':['True','False'],'original_empty_strings':'preserved'}
LIMITATIONS=[
 'registered population stocks, not necessarily actual residents or daytime/commuting/traffic exposure populations',
 'accident location need not be participant residence; area age structure is not participant or road-user age structure',
 'density is registered people per fixed km², not traffic flow, VKT or exposure-adjusted accident risk',
 'fixed 456-village geography is the adopted common research framework, not certified monthly historical boundaries',
 'monthly population reference day and precise age calculation conventions remain incompletely certified',
 'month-stock sums are computational person-month stocks, not distinct persons or annual population flows',
 'association with accident clusters is ecological and descriptive; no individual or causal inference',
 'B1 has no accident specification; do not create duplicate S0–S3 population observations',
 'annual training uses the corresponding year population; do not substitute pooled 2024–2025 for 2024 information',
 'Tangbu provisional_match is retained as evidence status, never an automatic exclusion or NA rule',
 'no imputation, outlier exclusion, winsorization, standardization, log transform or model fitting',
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
 for i in range(0,len(frame),block):display(frame.iloc[i:i+block])

def read_csv(path,contract,selected=None):
 names=[c['name'] for c in contract['columns']]
 header=pd.read_csv(path,encoding=contract['csv']['encoding'],nrows=0,keep_default_na=False)
 assert list(header)==names,('schema column order',str(path))
 columns=names if selected is None else list(selected)
 assert set(columns)<=set(names)
 f=pd.read_csv(path,encoding=contract['csv']['encoding'],usecols=columns,dtype='string',keep_default_na=False,na_values=[contract['csv']['missing_sentinel']])
 for c in contract['columns']:
  k=c['name'];dtype=c['dtype']
  if k not in f:continue
  if dtype=='boolean':
   assert f[k].dropna().isin(['True','False']).all(),k
   f[k]=f[k].map({'True':True,'False':False}).astype('boolean')
  elif dtype=='Int64':f[k]=pd.to_numeric(f[k],errors='raise').astype('Int64')
  elif dtype=='Float64':f[k]=f[k].map(lambda x:pd.NA if pd.isna(x) else float(x)).astype('Float64')
  else:assert dtype=='string',(k,dtype)
 return f[columns]

def verify(root,bindings):
 for path,expected in bindings.items():assert sha(root/path)==expected,('INPUT HASH MISMATCH',path)

def source_data(root,bindings):
 verify(root,bindings)
 raw=pd.read_csv(root/RAW,encoding='cp950',dtype='string',keep_default_na=False,na_filter=False)
 assert raw.shape==(64722,107) and list(raw)==RAW_COLUMNS
 assert raw['年份'].isin(['112','113','114','115']).all()
 assert raw['月份'].str.fullmatch(r'[0-9]{1,2}').all()
 dates=pd.to_numeric(raw['年份']).astype('Int64')*100+pd.to_numeric(raw['月份']).astype('Int64')
 assert int(dates.min())==11201 and int(dates.max())==11510
 scope=raw.loc[raw['年份'].isin(['113','114'])].copy()
 scope['source_roc_year_raw']=scope['年份'];scope['source_month_raw']=scope['月份']
 scope['year']=pd.to_numeric(scope['年份'],errors='raise').astype('Int64')+1911
 scope['month']=pd.to_numeric(scope['月份'],errors='raise').astype('Int64')
 assert scope['month'].between(1,12).all()
 scope['year_month']=scope['year'].astype('string')+'-'+scope['month'].astype('string').str.zfill(2)
 assert set(scope['year_month'])=={f'{y}-{m:02d}' for y in [2024,2025] for m in range(1,13)}
 assert not scope.duplicated(['year','month','區域代碼','性別']).any()
 assert scope['性別'].isin(['計','男','女']).all()
 assert scope.groupby(['year','month','區域代碼'])['性別'].nunique().eq(3).all()
 numeric=scope[NUMERIC].apply(pd.to_numeric,errors='coerce')
 invalid=numeric.isna()|numeric.lt(0)|numeric.mod(1).ne(0)|~np.isfinite(numeric.to_numpy(dtype=float))
 if invalid.to_numpy().any():
  rows,cols=np.where(invalid.to_numpy())
  preview=[dict(scope.iloc[int(r)][['year_month','區域代碼','區域別','性別']],field=NUMERIC[int(c)],value=scope.iloc[int(r)][NUMERIC[int(c)]]) for r,c in zip(rows[:15],cols[:15])]
  raise ValueError('Stop population outputs: invalid population cells '+str(preview))
 scope[NUMERIC]=numeric.astype('Int64')
 bad=scope[AGE].sum(axis=1,min_count=len(AGE)).ne(scope['總計'])
 assert not bad.any(),scope.loc[bad,['year_month','區域代碼','性別']].to_dict('records')
 wide=scope.pivot(index=['year','month','區域代碼'],columns='性別',values=NUMERIC)
 diff=wide.xs('男',level='性別',axis=1)+wide.xs('女',level='性別',axis=1)-wide.xs('計',level='性別',axis=1)
 assert not diff.isna().any().any() and diff.eq(0).all().all()
 villages=scope.loc[scope['區域代碼'].str.len().eq(11)].copy()
 assert len(villages)==32832
 coverage=villages.groupby(['year','month']).agg(rows=('區域代碼','size'),villages=('區域代碼','nunique'))
 assert len(coverage)==24 and coverage.rows.eq(1368).all() and coverage.villages.eq(456).all()
 total=villages.loc[villages['性別'].eq('計')].copy()
 assert len(total)==10944 and not total.duplicated(['year','month','區域代碼']).any()
 assert total.groupby('區域代碼').size().eq(24).all()
 cw=pd.read_csv(root/'data/processed/village_crosswalk.csv',encoding='utf-8-sig',dtype='string',keep_default_na=False,na_filter=False)
 assert len(cw)==456 and cw.village_id.is_unique and cw.population_code.is_unique
 schema=json.loads((root/'data/processed/taipei_village_base_schema.json').read_text(encoding='utf-8'))
 base=read_csv(root/'data/processed/taipei_village_base.csv',schema)
 assert base.shape==(456,41) and base.village_id.is_unique and base.district_name.nunique()==12
 assert base.village_area_km2.gt(0).all()
 assert set(total['區域代碼'])==set(cw.population_code)==set(base.population_code)
 district_rows=scope.loc[scope['區域代碼'].str.len().eq(8)&scope['區域代碼'].ne('63000000'),['區域代碼','區域別']].drop_duplicates()
 assert len(district_rows)==12 and district_rows['區域代碼'].is_unique and district_rows['區域別'].is_unique
 district_map=district_rows.set_index('區域代碼')['區域別']
 # Existing Unit1.3 population parent hierarchy only; never truncate to village_id.
 total['population_district_code']=total['區域代碼'].str[:8]
 total['raw_district_name']=total.population_district_code.map(district_map)
 joined=total.merge(cw,left_on='區域代碼',right_on='population_code',how='left',validate='many_to_one',indicator=True)
 assert len(joined)==10944 and joined['_merge'].eq('both').all()
 assert joined.raw_district_name.eq(joined.district_name).all()
 assert joined['區域別'].eq(joined.population_village_name).all()
 for col in ['population_code','boundary_code','district_name','population_village_name','boundary_village_name','standard_village_name','verification_status','match_method']:
  assert cw.set_index('village_id')[col].sort_index().equals(base.set_index('village_id')[col].sort_index()),col
 monthly=joined.drop(columns='_merge')
 monthly['total_population']=monthly['總計'].astype('Int64')
 for key,cols in AGE_GROUPS.items():monthly[key+'_population']=monthly[cols].sum(axis=1,min_count=len(cols)).astype('Int64')
 assert (monthly.elderly_population+monthly.children_population+monthly.working_age_population).eq(monthly.total_population).all()
 assert monthly.groupby(['village_id','year']).size().eq(12).all()
 assert not monthly.duplicated(['village_id','year_month']).any()
 facts={'raw_shape':[64722,107],'raw_encoding':'cp950 strict','raw_period':'2023-01 to 2026-10',
  'study_scope_rows_including_city_district':len(scope),'study_village_rows':len(villages),
  'monthly_total_rows':len(monthly),'months':24,'villages':456,'districts':12,
  'age_columns':101,'elderly_age_columns':len(AGE_GROUPS['elderly']),'children_age_columns':15,
  'negative_missing_nonnumeric_noninteger_cells':0,'age_total_mismatches':0,
  'male_female_total_mismatch_cells':int(diff.ne(0).to_numpy().sum()),
  'male_female_checked_cells':int(diff.size),'unmatched_population_codes':0,
  'name_or_district_mismatches':0,'raw_population_blank_cells_study':0,
  'population_source_hashes_verified':len(bindings),'geometries_read_or_recomputed':0}
 return monthly,base,cw,scope,facts

def reconcile(monthly,scope):
 keys=['year','month']
 raw_totals=scope.loc[scope['性別'].eq('計')]
 city=raw_totals.loc[raw_totals['區域代碼'].eq('63000000')].set_index(keys)[NUMERIC].sort_index()
 village=monthly.groupby(keys)[NUMERIC].sum(min_count=1).sort_index()
 pd.testing.assert_frame_equal(village,city,check_exact=True)
 district_raw=raw_totals.loc[raw_totals['區域代碼'].str.len().eq(8)&raw_totals['區域代碼'].ne('63000000')]
 district_raw=district_raw.rename(columns={'區域別':'district_name'}).set_index(keys+['district_name'])[NUMERIC].sort_index()
 district_village=monthly.groupby(keys+['district_name'])[NUMERIC].sum(min_count=1).sort_index()
 pd.testing.assert_frame_equal(district_village,district_raw,check_exact=True)
 assert city.shape==(24,102) and district_raw.shape==(288,102)
 return {'status':'passed','city_month_age_cells':int(city.size),'district_month_age_cells':int(district_raw.size),
  'city_and_12_districts_all_102_columns_exact':True,'zero_mismatches':True}

def aggregate_counts(monthly,base,annual):
 keys=['village_id']+(['year'] if annual else [])
 index=(pd.MultiIndex.from_product([base.village_id,[2024,2025]],names=keys) if annual else pd.Index(base.village_id,name='village_id'))
 group=monthly.groupby(keys,sort=True)
 out=pd.DataFrame(index=index)
 out['observed_month_count']=group.year_month.nunique().reindex(index,fill_value=0).astype('Int64')
 for key in COMPONENTS:
  source=key+'_population'
  out[key+'_population_month_sum']=group[source].sum(min_count=1).reindex(index).astype('Int64')
  out['valid_'+key+'_population_month_count']=group[source].count().reindex(index,fill_value=0).astype('Int64')
 return out.sort_index()

def derive_features(counts,expected,area):
 out={};records=counts.observed_month_count.eq(expected)
 out['monthly_records_complete']=records.astype('boolean')
 out['observed_month_coverage']=(counts.observed_month_count.astype('Float64')/expected).astype('Float64')
 for key in COMPONENTS:
  valid=counts['valid_'+key+'_population_month_count']
  complete=records&valid.eq(expected)
  out[key+'_population_complete']=complete.astype('boolean')
  out[key+'_population_month_coverage']=(valid.astype('Float64')/expected).astype('Float64')
  out['mean_monthly_'+key+'_population']=(counts[key+'_population_month_sum'].astype('Float64')/expected).where(complete).astype('Float64')
 total=counts.total_population_month_sum
 for key in ['elderly','children']:
  good=out[key+'_population_complete']&out['total_population_complete']&total.gt(0).fillna(False)
  out[key+'_ratio_numerator']=counts[key+'_population_month_sum'].where(good).astype('Int64')
  out[key+'_ratio_denominator']=total.where(good).astype('Int64')
  out[key+'_ratio']=(out[key+'_ratio_numerator'].astype('Float64')/out[key+'_ratio_denominator']).astype('Float64')
 out['population_density']=(out['mean_monthly_total_population']/area.astype('Float64')).astype('Float64')
 out['population_features_valid']=(out['population_density'].notna()&out['elderly_ratio'].notna()&out['children_ratio'].notna()).astype('boolean')
 return out

def make_dataset(counts,base,annual):
 data={};defs=[];n=len(counts);flat=counts.reset_index();ids=flat.village_id
 lookup=base.set_index('village_id')
 area=pd.Series(ids.map(lookup.village_area_km2).to_numpy(),index=counts.index,dtype='Float64')
 derived=derive_features(counts,12 if annual else 24,area)
 def add(name,values,dtype,meaning,unit='not applicable',source='Unit2.4 deterministic monthly aggregation',missing='依欄規則保留NA，不插補'):
  values=pd.Series([values]*n) if pd.api.types.is_scalar(values) else pd.Series(values).reset_index(drop=True)
  data[name]=values.astype(dtype)
  defs.append({'name':name,'dtype':dtype,'definition':meaning,'unit':unit,'source':source,'missing_rule':missing})
 add('village_id',ids,'string','共同固定10碼CPTVID，不由人口碼截碼產生','identifier','existing village_crosswalk','不可缺失、不轉數值')
 if annual:add('year',flat.year,'Int64','西元年，只由原民國113／114加1911一次','year','raw 年份','不可缺失')
 for col in ['district_name','standard_village_name','population_code','boundary_code','population_village_name','boundary_village_name','verification_status','match_method']:
  add(col,ids.map(lookup[col]),'string',{'verification_status':'原證據狀態保留；糖廍provisional不是排除／設NA規則','population_village_name':'人口原始里名保留，包括糖?里','boundary_village_name':'固定界原始里名保留，包括糖蔀里'}.get(col,'沿用既有crosswalk及正式里主表之'+col),'identifier' if 'code' in col else 'not applicable','Unit1.3 crosswalk / Unit2.2 base','不可缺失；原名稱不覆寫')
 # Parent codes are original population hierarchy, independent of fixed CPTVID.
 add('population_district_code',ids.map(lookup.population_code).str[:8],'string','既有已驗證人口碼之8碼行政區父碼，不作研究village_id','identifier','raw population hierarchy, Unit1.3 verified')
 add('population_sex_scope','計','string','正式計算只採計，男／女僅驗證不重複加總','category','raw 性別')
 rocyears=[json.dumps([str(int(y)-1911)],ensure_ascii=False) for y in flat.year] if annual else '["113", "114"]'
 add('source_roc_years_json',rocyears,'string','原始民國年字串JSON陣列，未改原值',source='raw 年份')
 add('period_start',flat.year.astype('string')+'-01' if annual else '2024-01','string','納入期間起始月份','year-month')
 add('period_end',flat.year.astype('string')+'-12' if annual else '2025-12','string','納入期間結束月份','year-month')
 add('period_years',1 if annual else 2,'Int64','計算期間年數','year')
 add('fixed_village_area_km2',area,'Float64','Unit2.2正式固定EPSG:3826幾何面積；不重新算面積、不用AREA或歷史面積','km²','Unit2.2 village_area_km2','正值不可缺失')
 expected=12 if annual else 24
 add('expected_month_count',expected,'Int64','完整年度12或兩年24個月','month')
 add('observed_month_count',counts.observed_month_count,'Int64','實際唯一計人口月紀錄數','month','raw year_month / sex 計','缺月以紀錄數反映，不補人口')
 if not annual:add('pooled_observed_month_count',counts.observed_month_count,'Int64','兩年實際唯一計月紀錄數，等同observed_month_count','month')
 add('missing_month_count',expected-counts.observed_month_count,'Int64','應有月份減實際月份數','month')
 for key in COMPONENTS:
  add('valid_'+key+'_population_month_count',counts['valid_'+key+'_population_month_count'],'Int64',key+'人口各自有效月份數','month')
  prefix='' if annual else 'pooled_'
  add(prefix+key+'_population_month_sum',counts[key+'_population_month_sum'],'Int64',key+'有效月人口存量加總，非期間不同個人總數','person-month stock',source='raw 總計' if key=='total' else 'raw age columns: '+json.dumps(AGE_GROUPS[key],ensure_ascii=False),missing='有部分月缺失僅已知月和；全部缺失NA，不能冒稱完整期間')
  add('mean_monthly_'+('population' if key=='total' else key+'_population'),derived['mean_monthly_'+key+'_population'],'Float64',key+f'人口月存量和／{expected}，須該欄完整月份才提供','person',missing='缺月或該人口欄不完整則NA；不改除以少數月份')
  covname='population_month_coverage' if key=='total' else key+'_population_month_coverage'
  add(covname,derived[key+'_population_month_coverage'],'Float64',key+'有效月數／應有月數','fraction')
  add(key+'_population_complete',derived[key+'_population_complete'],'boolean',key+'紀錄及有效月份均完整')
 for col in ['monthly_records_complete','observed_month_coverage','population_features_valid']:
  add(col,derived[col],'Float64' if col.endswith('coverage') else 'boolean','實際月份覆蓋率' if col.endswith('coverage') else ('三核心特徵均有有效值' if col=='population_features_valid' else '所有應有月份紀錄完整'),'fraction' if col.endswith('coverage') else 'logical flag')
 for key in ['elderly','children']:
  for part in ['numerator','denominator']:
   add(key+'_ratio_'+part,derived[key+'_ratio_'+part],'Int64',key+'比例之'+('人口月存量分子' if part=='numerator' else '總人口月存量有效分母'),'person-month stock',missing='相應月資料不完整或總人口和0則NA')
  add(key+'_ratio',derived[key+'_ratio'],'Float64',('65歲以上（含100歲以上）' if key=='elderly' else '0–14歲（含0與14歲）')+'人口月和／總人口月和，不平均月／年度比例','fraction',missing='相關月資料不完整或總人口分母0則NA')
 add('population_density',derived['population_density'],'Float64','完整期間平均月設籍人口／固定行政里面積，非交通暴露','registered person / km²',missing='總人口月資料不完整則NA')
 flag=pd.Series(np.where(derived['population_features_valid'].to_numpy(dtype=bool),'complete','incomplete_or_zero_denominator'),index=counts.index,dtype='string')
 add('population_quality_flag',flag,'string','完整性／零分母品質狀態；不是刪除條件')
 frame=pd.DataFrame(data)
 return frame,defs

def sum_col(component,annual):return ('' if annual else 'pooled_')+component+'_population_month_sum'

def validate_dataset(f,base,annual):
 keys=['village_id']+(['year'] if annual else [])
 assert len(f)==(912 if annual else 456) and not f.duplicated(keys).any()
 assert 'specification' not in f and f.village_id.nunique()==456 and f.district_name.nunique()==12
 assert set(f.village_id)==set(base.village_id) and f.village_id.str.fullmatch(r'\d{10}').all()
 assert f.population_code.str.fullmatch(r'\d{11}').all() and f.population_sex_scope.eq('計').all()
 if annual:assert f.groupby('year').village_id.nunique().to_dict()=={2024:456,2025:456}
 expected=12 if annual else 24
 assert f.expected_month_count.eq(expected).all() and f.observed_month_count.between(0,expected).all()
 assert f.missing_month_count.eq(expected-f.observed_month_count).all()
 assert f.period_years.eq(1 if annual else 2).all()
 assert f.fixed_village_area_km2.eq(f.village_id.map(base.set_index('village_id').village_area_km2)).all()
 assert f.fixed_village_area_km2.gt(0).all()
 counts=pd.DataFrame(index=f.index);counts['observed_month_count']=f.observed_month_count
 for key in COMPONENTS:
  counts[key+'_population_month_sum']=f[sum_col(key,annual)]
  counts['valid_'+key+'_population_month_count']=f['valid_'+key+'_population_month_count']
  assert f[sum_col(key,annual)].dropna().ge(0).all()
  assert f['valid_'+key+'_population_month_count'].between(0,expected).all()
 d=derive_features(counts,expected,f.fixed_village_area_km2)
 for key in COMPONENTS:
  formal='mean_monthly_'+('population' if key=='total' else key+'_population')
  pd.testing.assert_series_equal(f[formal],d['mean_monthly_'+key+'_population'],check_names=False,check_exact=True)
  coverage='population_month_coverage' if key=='total' else key+'_population_month_coverage'
  pd.testing.assert_series_equal(f[coverage],d[key+'_population_month_coverage'],check_names=False,check_exact=True)
  assert f[key+'_population_complete'].eq(d[key+'_population_complete']).all()
 for col in ['monthly_records_complete','observed_month_coverage','population_features_valid','population_density','elderly_ratio','children_ratio','elderly_ratio_numerator','elderly_ratio_denominator','children_ratio_numerator','children_ratio_denominator']:
  pd.testing.assert_series_equal(f[col],d[col],check_names=False,check_exact=True)
 assert f.population_density.dropna().ge(0).all()
 for col in ['elderly_ratio','children_ratio']:assert f[col].dropna().between(0,1).all()
 assert (f.elderly_ratio+f.children_ratio).dropna().le(1).all()
 for vid in ['6300700015','6301100044']:assert int(f.village_id.eq(vid).sum())==(2 if annual else 1)
 tang=f.loc[f.village_id.eq('6300700015')]
 assert tang.population_code.eq('63000070015').all() and tang.verification_status.eq('provisional_match').all()
 assert tang.standard_village_name.eq('糖廍里').all() and tang.population_village_name.eq('糖?里').all()
 return True

def validate_bundle(datasets,base):
 a=datasets[STEMS[0]];p=datasets[STEMS[1]].set_index('village_id').sort_index()
 validate_dataset(a,base,True);validate_dataset(datasets[STEMS[1]],base,False)
 group=a.groupby('village_id',sort=True)
 for key in COMPONENTS:
  pd.testing.assert_series_equal(group[sum_col(key,True)].sum(min_count=1),p[sum_col(key,False)],check_names=False,check_exact=True)
  col='valid_'+key+'_population_month_count'
  pd.testing.assert_series_equal(group[col].sum(),p[col],check_names=False,check_exact=True)
 pd.testing.assert_series_equal(group.observed_month_count.sum(),p.observed_month_count,check_names=False,check_exact=True)
 complete=a.groupby('village_id').total_population_complete.all()
 # Equal 12-month years imply this identity; formal calculation still uses sums/24.
 expected=group.mean_monthly_population.mean()
 assert np.allclose(expected.loc[complete].astype(float),p.loc[complete,'mean_monthly_population'].astype(float),rtol=0,atol=1e-10)
 return {'status':'passed','keys':'912 / 456 complete','annual_to_pooled_month_counts_and_sums':'exact','fixed_area':'exact Unit2.2 values'}

def build(root,bindings):
 monthly,base,cw,scope,facts=source_data(root,bindings)
 facts['city_district_reconciliation']=reconcile(monthly,scope)
 annual=aggregate_counts(monthly,base,True)
 pooled=annual.groupby(level='village_id',sort=True).sum(min_count=1).astype('Int64')
 direct=aggregate_counts(monthly,base,False)
 pd.testing.assert_frame_equal(pooled,direct,check_exact=True)
 datasets={};definitions={}
 for isannual,counts,stem in [(True,annual,STEMS[0]),(False,pooled,STEMS[1])]:
  f,d=make_dataset(counts,base,isannual);validate_dataset(f,base,isannual)
  datasets[stem]=f;definitions[stem]=d
 validate_bundle(datasets,base)
 # Actual inputs meet the previous full-completeness benchmark. No partial result is certified.
 for f in datasets.values():assert f.population_features_valid.all() and f.monthly_records_complete.all()
 facts.update({'direct_24_month_vs_annual_sums':'passed; exact values and nullable dtype',
  'formal_population_datasets':2,'accident_data_used_for_population_features':False,
  'human_acceptance':'Codex assisted; DE / DA / PM pending'})
 return datasets,definitions,monthly,base,facts

def handoff_check(root,datasets,bindings):
 verify(root,bindings);rows=[]
 for kind in ['a','c']:
  for period,expected in [('annual',3648),('pooled',1824)]:
   stem=f'taipei_dataset_{kind}_{period}'
   contract=json.loads((root/f'data/processed/{stem}_schema.json').read_text(encoding='utf-8'))
   keys=['village_id']+(['year'] if period=='annual' else [])
   a=read_csv(root/f'data/processed/{stem}.csv',contract,['specification']+keys)
   assert len(a)==expected and not a.duplicated(['specification']+keys).any()
   b=datasets[f'taipei_dataset_b1_{period}'][keys+FEATURES]
   merged=a.merge(b,on=keys,how='left',validate='many_to_one',indicator=True)
   assert len(merged)==len(a) and merged['_merge'].eq('both').all()
   assert merged[FEATURES].notna().all().all()
   rows.append({'dataset':stem,'rows_before':len(a),'rows_after':len(merged),'merge':'many_to_one','unmatched':0,'B1_rows':len(b),'accident_values_read':False})
 return rows

def edge_case_checks():
 # Artificial arithmetic tests only; never appended to the study population.
 c=pd.DataFrame({'observed_month_count':pd.array([12,11,12,0],dtype='Int64')})
 for key,value in [('total',120),('elderly',30),('children',20)]:
  c[key+'_population_month_sum']=pd.array([value,value,0,pd.NA],dtype='Int64')
  c['valid_'+key+'_population_month_count']=pd.array([12,11,12,0],dtype='Int64')
 d=derive_features(c,12,pd.Series([1,1,1,1],dtype='Float64'))
 assert d['population_density'].iloc[0]==10 and d['elderly_ratio'].iloc[0]==.25
 assert pd.isna(d['population_density'].iloc[1]) and pd.isna(d['elderly_ratio'].iloc[1])
 assert d['population_density'].iloc[2]==0 and pd.isna(d['elderly_ratio'].iloc[2])
 assert pd.isna(d['population_density'].iloc[3])
 c.loc[0,'valid_elderly_population_month_count']=11
 d=derive_features(c,12,pd.Series([1,1,1,1],dtype='Float64'))
 assert d['population_density'].iloc[0]==10 and pd.isna(d['elderly_ratio'].iloc[0])
 assert d['children_ratio'].iloc[0]==20/120
 return {'complete_months':'passed','incomplete_no_partial_mean':'passed','zero_denominator_NA':'passed','missing_component_independent':'passed','absent_record_no_imputation':'passed'}

def diagnostics(datasets,monthly):
 stats=[];city=[];district=[];extremes=[]
 for stem,f in datasets.items():
  annual=stem.endswith('annual');parts=[(str(y),g) for y,g in f.groupby('year')] if annual else [('2024–2025',f)]
  for period,g in parts:
   for col in FEATURES:
    v=g[col];stats.append({'period':period,'feature':col,'valid_N':int(v.count()),'missing_N':int(v.isna().sum()),'min':float(v.min()),'q25':float(v.quantile(.25)),'median':float(v.median()),'q75':float(v.quantile(.75)),'max':float(v.max()),'mean':float(v.mean()),'std_ddof1':float(v.std())})
    for tail,ordered in [('lowest',g.sort_values([col,'village_id'])),('highest',g.sort_values([col,'village_id'],ascending=[False,True]))]:
     for _,row in ordered.head(5).iterrows():extremes.append({'period':period,'feature':col,'tail':tail,'village_id':row.village_id,'district_name':row.district_name,'village_name':row.standard_village_name,'value':float(row[col]),'area_km2':float(row.fixed_village_area_km2),'mean_monthly_population':float(row.mean_monthly_population)})
   for name,h in [('臺北市',g)]+list(g.groupby('district_name')):
    sums={key:int(h[sum_col(key,annual)].sum()) for key in COMPONENTS}
    result={'period':period,'district':name,'villages':len(h),'total_population_month_sum':sums['total'],'elderly_population_month_sum':sums['elderly'],'children_population_month_sum':sums['children'],'mean_monthly_population':sums['total']/(12 if annual else 24),'elderly_ratio':sums['elderly']/sums['total'],'children_ratio':sums['children']/sums['total'],'all_monthly_records_complete':bool(h.monthly_records_complete.all())}
    (city if name=='臺北市' else district).append(result)
 a=datasets[STEMS[0]];first=a.loc[a.year.eq(2024)].set_index('village_id');second=a.loc[a.year.eq(2025)].set_index('village_id').reindex(first.index)
 changes=first[['district_name','standard_village_name']].copy()
 changes['mean_population_absolute_change']=second.mean_monthly_population-first.mean_monthly_population
 changes['mean_population_relative_change']=(second.mean_monthly_population-first.mean_monthly_population)/first.mean_monthly_population.where(first.mean_monthly_population.gt(0))
 changes['population_density_change']=second.population_density-first.population_density
 changes['elderly_ratio_percentage_point_change']=(second.elderly_ratio-first.elderly_ratio)*100
 changes['children_ratio_percentage_point_change']=(second.children_ratio-first.children_ratio)*100
 changes=changes.reset_index()
 change_summary=[]
 for col in changes.columns[3:]:
  v=changes[col];change_summary.append({'variable':col,'min':float(v.min()),'median':float(v.median()),'max':float(v.max()),'positive_villages':int(v.gt(0).sum()),'negative_villages':int(v.lt(0).sum()),'zero_villages':int(v.eq(0).sum())})
 month_coverage=monthly.groupby(['year','month','district_name']).agg(villages=('village_id','nunique'),records=('village_id','size')).reset_index()
 # December is a diagnostic only, never the formal population numerator.
 dec=monthly.loc[monthly.month.eq(12)].set_index(['village_id','year']).total_population
 annual=a.set_index(['village_id','year'])
 decdelta=(dec-annual.mean_monthly_population).rename('december_minus_annual_mean')
 return {'feature_summary':stats,'citywide_population':city,'district_population':district,'extreme_values':extremes,
  'cross_year_changes':json.loads(changes.to_json(orient='records',force_ascii=False,double_precision=15)),
  'cross_year_summary':change_summary,'monthly_district_coverage':month_coverage.to_dict('records'),
  'december_vs_annual_mean':{'different_village_years':int(decdelta.ne(0).sum()),'min_difference':float(decdelta.min()),'max_difference':float(decdelta.max())}}

def contract(stem,definitions,bindings,handoff_bindings):
 annual=stem.endswith('annual')
 return {'unit':'2.4','created_at':'2026-11-26','dataset_path':f'data/processed/{stem}.csv','producer':PRODUCER,'helper':HELPER,'documentation':f'data/processed/{stem}_documentation.ipynb','role':'external_environment_population',
  'observation_unit':'fixed research village'+(' × year' if annual else ' × pooled 2024–2025 period'),'expected_rows':912 if annual else 456,
  'primary_key':['village_id']+(['year'] if annual else []),'csv':CSV,'columns':definitions,'population_inputs':bindings,
  'handoff_only_inputs':handoff_bindings,'handoff_scope':'A/C only keys read, not population feature inputs; many-to-one checks, no integrated output',
  'raw_contract':{'encoding':'cp950 strict','shape':[64722,107],'columns':RAW_COLUMNS,'raw_NA':'no processed sentinel imposed; original empty strings retained and numeric cells checked explicitly'},
  'age_groups':AGE_GROUPS,'features':FEATURES,'period_months':12 if annual else 24,
  'complete_period_policy':'each feature requires its relevant expected 12/24 valid months; no partial-month mean or imputation; denominator 0 ratio NA',
  'pooling':'sum 24 original monthly population stocks; divide mean by 24; recompute age shares from population sums, never average yearly shares',
  'area':'fixed Unit2.2 village_area_km2 only; no geometry recomputation, AREA or historical area',
  'geography':'456 common fixed villages / 12 districts; no S0–S3 duplication','limitations':LIMITATIONS}

def export(root,datasets,definitions,bindings,handoff_bindings):
 planned={}
 for stem,f in datasets.items():
  planned[f'data/processed/{stem}.csv']=f.to_csv(index=False,na_rep='__MISSING__',lineterminator='\n',float_format='%.17g').encode('utf-8-sig')
  planned[f'data/processed/{stem}_schema.json']=(json.dumps(contract(stem,definitions[stem],bindings,handoff_bindings),ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 for rel,data in planned.items():
  path=(root/rel).resolve();assert path.is_relative_to((root/'data/processed').resolve())
  assert rel not in bindings and rel not in handoff_bindings
  if path.exists():assert path.read_bytes()==data,('REFUSE DIFFERENT OUTPUT OVERWRITE',rel)
 for rel,data in planned.items():
  path=root/rel
  if not path.exists():
   with path.open('xb') as stream:stream.write(data)
 outputs={}
 for stem,expected in datasets.items():
  schema=json.loads((root/f'data/processed/{stem}_schema.json').read_text(encoding='utf-8'))
  actual=read_csv(root/f'data/processed/{stem}.csv',schema)
  pd.testing.assert_frame_equal(actual,expected,check_exact=True)
  for suffix in ['.csv','_schema.json']:
   rel=f'data/processed/{stem}{suffix}';outputs[rel]={'path':rel,'bytes':(root/rel).stat().st_size,'sha256':sha(root/rel)}
 return outputs

def plots(datasets,diag,root):
 import matplotlib.pyplot as plt
 plt.rcParams.update({'font.family':'Microsoft JhengHei','axes.unicode_minus':False})
 folder=root/'data/temp/unit24_validation';folder.mkdir(parents=True,exist_ok=True);paths=[]
 def finish(fig,name):
  fig.suptitle('Unit 2.4 人口資料處理與品質診斷；非正式Finding',fontsize=13)
  fig.tight_layout(rect=(0,0,1,.95));p=folder/name;fig.savefig(p,dpi=140,bbox_inches='tight');plt.show();paths.append(p.relative_to(root).as_posix())
 a=datasets[STEMS[0]];p=datasets[STEMS[1]]
 fig,axes=plt.subplots(2,3,figsize=(15,8))
 for j,(col,title,unit) in enumerate([('population_density','設籍人口密度','人／固定km²'),('elderly_ratio','65歲以上比例','比例'),('children_ratio','0–14歲比例','比例')]):
  for year in [2024,2025]:axes[0,j].hist(a.loc[a.year.eq(year),col].astype(float),bins=28,histtype='step',label=str(year))
  axes[0,j].set(title=title+'（年度）',xlabel=unit,ylabel='行政里數');axes[0,j].legend()
  axes[1,j].hist(p[col].astype(float),bins=28,color='steelblue',alpha=.8)
  axes[1,j].set(title=title+'（2024–2025 pooled）',xlabel=unit,ylabel='行政里數')
 finish(fig,'population_feature_distributions.png')
 changes=pd.DataFrame(diag['cross_year_changes']);fig,axes=plt.subplots(1,3,figsize=(15,4.5))
 for ax,col,title,unit in [(axes[0],'mean_population_absolute_change','平均月人口變動','人；2025減2024'),(axes[1],'elderly_ratio_percentage_point_change','高齡比例變動','百分點；2025減2024'),(axes[2],'children_ratio_percentage_point_change','兒童比例變動','百分點；2025減2024')]:
  ax.hist(changes[col].astype(float),bins=30);ax.axvline(0,color='black',linewidth=.8);ax.set(title=title,xlabel=unit,ylabel='行政里數')
 finish(fig,'population_cross_year_changes.png')
 fig,axes=plt.subplots(1,2,figsize=(14,5))
 d=pd.DataFrame(diag['district_population']);years=d.loc[d.period.isin(['2024','2025'])]
 districts=sorted(years.district.unique())
 counts=years.pivot(index='district',columns='period',values='villages').reindex(districts)
 counts.plot.bar(ax=axes[0],rot=45);axes[0].set(title='各區完整12月人口之里數',ylabel='行政里數',xlabel='')
 axes[1].scatter(p.fixed_village_area_km2.astype(float),p.population_density.astype(float),s=12,alpha=.6)
 axes[1].set(title='固定面積與pooled密度品質檢查',xlabel='原固定里面積（km²）',ylabel='設籍人口／km²；極端值不排除')
 finish(fig,'district_coverage_and_area_density.png')
 return paths
