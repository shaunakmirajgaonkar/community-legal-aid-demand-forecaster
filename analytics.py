
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from typing import Iterable

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    cols=[]
    for c in out.columns:
        s=str(c).strip().lower().replace(" ","_")
        s="".join(ch for ch in s if ch.isalnum() or ch=="_")
        cols.append(s or "column")
    out.columns=cols
    return out.loc[:,~out.columns.duplicated()]

def num(df,col,default=0.0):
    if col not in df.columns:
        return pd.Series(default,index=df.index,dtype=float)
    return pd.to_numeric(df[col],errors="coerce").fillna(default)

def demand_level(score):
    s=float(np.clip(score,0,100))
    if s<25:return "Low"
    if s<50:return "Moderate"
    if s<75:return "High"
    return "Critical"

def safe_positive_size(values: Iterable, minimum=12, maximum=60):
    s=pd.to_numeric(pd.Series(values),errors="coerce").fillna(0).abs()
    if s.empty:return []
    lo,hi=float(s.min()),float(s.max())
    if math.isclose(lo,hi):
        return [float((minimum+maximum)/2)]*len(s)
    return (minimum+(s-lo)/(hi-lo)*(maximum-minimum)).tolist()

def demand_score(cases: pd.DataFrame, events=None, service=None):
    d=normalize_columns(cases)
    if d.empty:return pd.DataFrame()
    case_pressure=(num(d,"case_volume_index")/100).clip(0,1)
    housing=(num(d,"housing_stress_index")/100).clip(0,1)
    event=(num(d,"local_event_pressure")/100).clip(0,1)
    unmet=(num(d,"unmet_service_index")/100).clip(0,1)
    access=(num(d,"service_access_gap")/100).clip(0,1)
    score=(case_pressure*.28+housing*.25+event*.15+unmet*.20+access*.12)*100
    if events is not None and not events.empty and "zone" in d.columns:
        e=normalize_columns(events)
        if "zone" in e.columns:
            e2=e.groupby("zone",as_index=False).agg(event_rows=("zone","size"))
            mapped=d["zone"].map(dict(zip(e2.zone,e2.event_rows))).fillna(0)
            score += (mapped.clip(0,10)/10)*2.5
    if service is not None and not service.empty and "zone" in d.columns:
        s=normalize_columns(service)
        if "zone" in s.columns and "service_requests" in s.columns:
            s2=s.groupby("zone",as_index=False)["service_requests"].mean()
            mapped=d["zone"].map(dict(zip(s2.zone,s2.service_requests))).fillna(0)
            score += (mapped/(mapped.max() or 1)).clip(0,1)*2.5
    out=d.copy()
    out["demand_score"]=score.clip(0,100).round(1)
    out["demand_level"]=out.demand_score.map(demand_level)
    out["review_priority"]=np.select([out.demand_score>=75,out.demand_score>=50,out.demand_score>=25],
                                      ["Immediate","Priority","Watch"],default="Routine")
    return out

def priority_actions(row):
    a=[]
    if float(row.get("housing_stress_index",0))>=70:a.append("Prepare housing-related legal-aid capacity for elevated demand.")
    if float(row.get("case_volume_index",0))>=70:a.append("Review intake capacity and triage coverage.")
    if float(row.get("unmet_service_index",0))>=70:a.append("Assess backlog and unmet-service pressure.")
    if float(row.get("local_event_pressure",0))>=70:a.append("Plan event-linked outreach and intake coverage.")
    if float(row.get("service_access_gap",0))>=70:a.append("Review local access barriers and referral pathways.")
    return a or ["Continue routine monitoring and refresh local service data."]

def scenario_score(row, changes):
    d=row.copy()
    for col,delta in changes.items():
        if col in d.index:
            d[col]=np.clip(float(d.get(col,0))+float(delta),0,100)
    return float(demand_score(pd.DataFrame([d])).iloc[0].demand_score)

def zone_summary(scored):
    if scored.empty or "zone" not in scored.columns:return pd.DataFrame()
    return scored.groupby("zone",as_index=False).agg(
        regions=("zone","count"), avg_demand=("demand_score","mean"),
        avg_housing_stress=("housing_stress_index","mean"),
        avg_case_pressure=("case_volume_index","mean")
    ).round(1)
