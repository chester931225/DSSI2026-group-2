"""Analysis-only validation of five frozen Final artifacts; no upstream processing.

Run with the existing environment: python data/code/validate_taipei_analysis_ready.py
Use --root for an isolated project copy. Only reads files and prints JSON.
This does not verify original sources or establish Full Pipeline Reproduction.
Execution: Codex assisted; student DE/DA/PM acceptance remains pending.
"""
from pathlib import Path
import argparse
import hashlib
import json
from collections import Counter

import numpy as np
import pandas as pd

EXPECTED = {
    'data/processed/taipei_final_analytical_annual.csv': 'b2a6e14d945555b1fa3c4f01d7eadbe38cda4b537cd4327fb16e368fa29d74e6',
    'data/processed/taipei_final_analytical_pooled.csv': 'ce31390a3af8d941e93b0f150f377f01772b7d748aa75756ef66c8d55a4022e2',
    'data/processed/taipei_final_analytical_annual_schema.json': '06c3979a676d6124a4fa2db8d7e0cea8129ccec1211947d15750408ee952d8ca',
    'data/processed/taipei_final_analytical_pooled_schema.json': '471c04ca171adc5d49e2a2647460b9d3e896acb1a5088ccccb86bfe5ea95227e',
    'data/processed/taipei_feature_registry.json': '57c36e5572be721de86dabe992be2a0e0828893bab493c6ae104884cd062309c',
}
A1 = [x+'_ratio' for x in ['morning_peak', 'evening_peak', 'late_night', 'weekend',
                         'intersection', 'rear_end', 'side_collision', 'pedestrian_collision']]
A2 = A1 + ['multi_injury_ratio']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def project_root(start):
    for candidate in (Path(start).resolve(), *Path(start).resolve().parents):
        if (candidate/'AGENTS.md').is_file() and (candidate/'templates').is_dir():
            return candidate
    raise FileNotFoundError('Open within the student project (AGENTS.md and templates/)')


def read_csv(path, contract):
    """Use explicit nullable schema and exact sentinel; never infer CSV dtypes."""
    csv = contract['csv']
    require(csv['encoding'] == 'utf-8-sig' and csv['missing_sentinel'] == '__MISSING__'
            and csv['keep_default_na'] is False and csv['line_terminator'] == 'LF',
            'Unexpected CSV contract')
    require(csv['boolean_values'] == ['True', 'False'], 'Unexpected boolean vocabulary')
    frame = pd.read_csv(path, encoding=csv['encoding'], dtype='string',
                        keep_default_na=False, na_values=[csv['missing_sentinel']])
    require(list(frame) == [c['name'] for c in contract['columns']], 'Column order mismatch')
    missing_before = frame.isna()
    empty_before = frame.eq('').fillna(False)
    for field in contract['columns']:
        name, dtype = field['name'], field['dtype']
        values = frame[name]
        require(dtype in ['string', 'Int64', 'Float64', 'boolean'], 'Unsupported dtype '+dtype)
        if dtype == 'boolean':
            require(values.dropna().isin(csv['boolean_values']).all(), 'Invalid boolean '+name)
            frame[name] = values.map({'True': True, 'False': False}).astype('boolean')
        elif dtype == 'Int64':
            frame[name] = pd.to_numeric(values, errors='raise').astype('Int64')
        elif dtype == 'Float64':
            frame[name] = values.map(lambda v: pd.NA if pd.isna(v) else float(v)).astype('Float64')
            require(np.isfinite(frame[name].dropna().to_numpy(dtype=float)).all(), 'Nonfinite '+name)
        require(str(frame[name].dtype) == dtype, 'dtype mismatch '+name)
    require(frame.isna().equals(missing_before), 'Conversion altered missing values')
    for c in frame:
        if str(frame[c].dtype) == 'string':
            require(frame[c].eq('').fillna(False).equals(empty_before[c]), 'Empty string altered '+c)
    return frame


def check_fraction(actual, numerator, denominator, label):
    expected = (numerator/denominator).where(denominator.gt(0))
    require(actual.isna().equals(expected.isna()), 'Missingness rule mismatch '+label)
    valid = expected.notna()
    require(np.allclose(actual[valid].to_numpy(dtype=float), expected[valid].to_numpy(dtype=float),
                        rtol=1e-12, atol=1e-14), 'Fraction mismatch '+label)


def validate(root):
    root = Path(root).resolve()
    require((root/'AGENTS.md').is_file() and (root/'templates').is_dir(), 'Invalid project root')
    for relative, expected in EXPECTED.items():
        p = (root/relative).resolve()
        require(p.is_relative_to(root), 'Path escapes isolated project')
        require(p.is_file(), 'Missing analysis artifact '+relative)
        require(sha(p) == expected, 'HASH MISMATCH '+relative)
    registry = json.loads((root/'data/processed/taipei_feature_registry.json').read_text('utf8'))
    entries = {e['column_name']: e for e in registry['features']}
    require(len(entries) == len(registry['features']) == 494, 'Registry union must contain 494 fields')
    sets = registry['candidate_feature_sets']
    require(sets['A1'] == A1 and sets['A2'] == A2, 'A1/A2 candidate mismatch')
    require({n for n,e in entries.items() if e['allowed_for_main_clustering']} == set(A2), 'Role mismatch')
    require(dict(Counter(e['analytical_role'] for e in entries.values())) == registry['role_counts'], 'Role counts')
    frames, schemas, results = {}, {}, {}
    required_metadata = ['source_dataset','source_column','definition','unit','dtype','analytical_role',
                         'missing_policy','zero_policy','readiness','recommended_use',
                         'temporal_reference','geographic_reference','leakage_warning','interpretation_limitations']
    for entry in entries.values():
        require(all(k in entry for k in required_metadata), 'Incomplete registry metadata '+entry['column_name'])
    for period, rows in [('annual',3648), ('pooled',1824)]:
        base = 'data/processed/taipei_final_analytical_'+period
        sc = json.loads((root/(base+'_schema.json')).read_text('utf8'))
        require(sc['dataset_path'] == base+'.csv', 'Schema path mismatch')
        require(sc['feature_registry']['sha256'] == EXPECTED['data/processed/taipei_feature_registry.json'], 'Registry binding')
        frame = read_csv(root/(base+'.csv'), sc)
        key = ['specification','village_id'] + (['year'] if period == 'annual' else [])
        require(frame.shape == (rows,490) and sc['expected_rows'] == rows, 'Unexpected shape '+period)
        require(sc['primary_key'] == key and not frame.duplicated(key).any()
                and frame[key].notna().all().all(), 'Primary key failure '+period)
        require(set(frame.specification) == {'S0','S1','S2','S3'}, 'Specification set')
        require(frame.village_id.str.fullmatch(r'\d{10}').all() and frame.village_id.nunique() == 456, 'Village IDs')
        require(frame.district_name.nunique() == 12, 'District count')
        groups = ['specification'] + (['year'] if period == 'annual' else [])
        require(frame.groupby(groups).size().eq(456).all(), 'Incomplete specification skeleton')
        s0 = frame.loc[frame.specification.eq('S0')]
        if period == 'annual':
            require(set(frame.year) == {2024,2025}, 'Annual years')
            require(s0.groupby('year').village_id.nunique().to_dict() == {2024:456,2025:456}, 'S0 annual')
        else:
            require(len(s0) == s0.village_id.nunique() == 456, 'S0 pooled')
        require(registry['datasets'][period]['columns'] == list(frame)
                and registry['datasets'][period]['primary_key'] == key, 'Registry dataset contract')
        for field in sc['columns']:
            name = field['name'];entry = entries[name];variant = entry['dataset_variants'][period]
            require(entry['dtype'] == field['dtype'] == str(frame[name].dtype), 'Registry dtype '+name)
            require(entry['analytical_role'] == field['analytical_role'], 'Registry role '+name)
            require(all(variant[k] == field[k] for k in ['source','definition','unit']), 'Registry lineage '+name)
        candidate_contract = {}
        for ratio in A2 + sets['strict_intersection_alternative']:
            stem = ratio.removesuffix('_ratio')
            n,d,f,m,c = [stem+s for s in ['_numerator','_denominator','_false_count','_missing_count','_coverage']]
            require(frame[[n,d,f,m]].notna().all().all(), 'Missing candidate counts '+stem)
            require(frame[[n,d,f,m]].ge(0).all().all(), 'Negative candidate counts '+stem)
            require((frame[n]+frame[f]).equals(frame[d]), 'Valid denominator '+stem)
            require((frame[d]+frame[m]).equals(frame.observed_accident_count), 'Observation count '+stem)
            check_fraction(frame[ratio],frame[n],frame[d],ratio)
            check_fraction(frame[c],frame[d],frame.observed_accident_count,c)
            quality = [m,c]
            for threshold in [5,10,20,30,50]:
                flag = stem+'_denominator_lt_'+str(threshold)
                require(frame[flag].equals(frame[d].lt(threshold)), 'Low denominator flag '+flag)
                quality.append(flag)
            candidate_contract[ratio] = {'numerator':n,'denominator':d,'false_count':f,'quality_columns':quality}
        readable = {}
        for name, cols in sets.items():
            # Some C fields are period-specific; the exact variants are in the registry.
            active = [c for c in cols if period in entries[c]['dataset_variants']]
            require(all(c in frame for c in active), 'Unreadable candidate set '+name)
            readable[name] = {'columns':active, 'valid_cells':int(frame[active].notna().sum().sum()),
                              'missing_cells':int(frame[active].isna().sum().sum())}
        tang = frame.loc[frame.village_id.eq('6300700015')]
        require(tang.verification_status.eq('provisional_match').all()
                and tang.population_density.notna().all(), 'Accepted Tangbu inclusion changed')
        widths = frame.annotated_road_width_no_valid_samples
        require(set(frame.loc[widths,'village_id']) == {'6301100048','6301200040','6301200042'}, 'Width quality IDs')
        require(frame.loc[widths,['median_annotated_road_width','annotated_road_width_q1','annotated_road_width_q3']].isna().all().all(), 'Width NA contract')
        if period == 'annual':
            zero = frame.loc[frame.year.eq(2025)&frame.village_id.eq('6301100044')]
            require(len(zero)==4 and zero.observed_accident_count.eq(0).all()
                    and zero[A2].isna().all().all(), 'Zero accident proportions must stay NA')
        for item in registry['blocked_features']:
            require(item['feature'] not in frame and item['formal_numeric_column_created'] is False, 'Blocked feature')
        results[period] = {'shape':list(frame.shape),'primary_key':key,'s0_rows':len(s0),
                           'nullable_dtypes':frame.dtypes.astype(str).value_counts().to_dict(),
                           'missing_cells':int(frame.isna().sum().sum()),
                           'candidate_contract':candidate_contract,'readable_feature_sets':readable}
        frames[period]=frame;schemas[period]=sc
    require(set(entries) == set(frames['annual']) | set(frames['pooled']), 'Registry field union')
    require(set(frames['annual'].village_id) == set(frames['pooled'].village_id), 'Village universe mismatch')
    return {'status':'passed','mode':'Analysis-only validation','five_output_hashes':EXPECTED,
            'registry_union_fields':494,'A1_count':8,'A2_count':9,'datasets':results,
            'upstream_sources_verified':False,'full_pipeline_reproduction_verified':False,
            'scope_notice':'Only five saved analysis outputs validated. Full original source dependencies, including the exact evidence ZIP, remain mandatory for Mode B and were NOT verified by this tool.',
            'human_acceptance':'DE handoff / DA acceptance / PM review pending'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,help='Exact isolated student project root')
    args = parser.parse_args()
    root = args.root.resolve() if args.root is not None else project_root(Path.cwd())
    print(json.dumps(validate(root),ensure_ascii=False,indent=2))
