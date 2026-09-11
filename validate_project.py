from pathlib import Path
import pandas as pd
from analytics import demand_score
ROOT=Path(__file__).parent
cases=pd.read_csv(ROOT/'data/sample_case_demand.csv')
out=demand_score(cases)
assert len(out)==12
assert out.demand_score.between(0,100).all()
assert set(out.demand_level).issubset({'Low','Moderate','High','Critical'})
print('PASS: community legal-aid demand screening')
print(f'Regions: {len(out)}')
print(f'Demand range: {out.demand_score.min():.1f} - {out.demand_score.max():.1f}')
print(f'High/Critical: {(out.demand_score>=50).sum()}')
