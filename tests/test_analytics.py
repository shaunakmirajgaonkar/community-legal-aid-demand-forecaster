import pandas as pd
from analytics import demand_score, demand_level, normalize_columns, safe_positive_size

def test_levels():
    assert demand_level(10)=='Low'
    assert demand_level(30)=='Moderate'
    assert demand_level(60)=='High'
    assert demand_level(90)=='Critical'

def test_score_bounds():
    d=pd.DataFrame([{'zone':'X','case_volume_index':100,'housing_stress_index':100,'local_event_pressure':100,'unmet_service_index':100,'service_access_gap':100}])
    o=demand_score(d)
    assert 0 <= float(o.iloc[0].demand_score) <= 100

def test_normalize_and_sizes():
    d=normalize_columns(pd.DataFrame({'Zone Name':['A'],'Case Volume Index':[50]}))
    assert 'zone_name' in d.columns
    assert len(safe_positive_size([0,0,10]))==3
    assert all(v>0 for v in safe_positive_size([0,0,10]))
