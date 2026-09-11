
from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd
import plotly.express as px
import streamlit as st
from analytics import normalize_columns,demand_score,priority_actions,safe_positive_size,scenario_score,zone_summary

st.set_page_config(page_title="Community Legal-Aid Demand Forecaster", page_icon="⚖️", layout="wide", initial_sidebar_state="expanded")
BASE=Path(__file__).parent; DATA=BASE/"data"

st.markdown("""
<style>
.stApp{background:linear-gradient(180deg,#fbfdff 0%,#f5f8fb 100%);color:#173b57}
.block-container{max-width:1480px;padding-top:1rem;padding-bottom:2rem}
section[data-testid="stSidebar"]{background:#fff;border-right:1px solid #dce6ee}
.hero{background:linear-gradient(135deg,#fff 0%,#eef8ff 52%,#fff8ee 100%);border:1px solid #dce7ef;border-radius:25px;padding:23px 26px;box-shadow:0 10px 30px rgba(24,57,84,.06);margin-bottom:18px}
.hero h1{margin:0;color:#153a56;font-size:2.18rem;letter-spacing:-.035em}.hero p{color:#61788b;margin:.45rem 0 0}.badges{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.badge{background:#fff;border:1px solid #dbe6ee;border-radius:999px;padding:7px 11px;color:#50687b;font-weight:750;font-size:.8rem}
.card{background:#fff;border:1px solid #dfe8ef;border-radius:18px;padding:17px;box-shadow:0 8px 22px rgba(34,66,91,.045)}
.kpi{background:#fff;border:1px solid #dbe6ee;border-radius:17px;padding:15px 16px;box-shadow:0 7px 18px rgba(34,66,91,.04)}.lab{color:#6f8291;font-size:.75rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em}.val{color:#153a56;font-size:1.72rem;font-weight:900;margin-top:4px}.sub{color:#7890a0;font-size:.8rem}
.section{font-size:1.08rem;font-weight:900;color:#19415e;margin-bottom:10px}.muted{color:#718595;font-size:.84rem}.side-title{font-size:1.24rem;font-weight:900;color:#153b57}.side-sub{font-size:.84rem;color:#708595;margin-bottom:12px}
div[data-testid="stMetricValue"]{color:#153a56}div[data-testid="stMetricLabel"]{color:#6b8090}
</style>
""", unsafe_allow_html=True)

def sample(n): return pd.read_csv(DATA/n)
def read_upload(u, fallback):
    if u is None:return fallback.copy()
    try:return pd.read_csv(u)
    except Exception as e:
        st.sidebar.error(f"Could not read {u.name}: {e}")
        return fallback.copy()

case_default=sample("sample_case_demand.csv")
event_default=sample("sample_local_events.csv")
service_default=sample("sample_service_history.csv")

st.sidebar.markdown('<div class="side-title">⚖️ JusticeDemand Local</div>',unsafe_allow_html=True)
st.sidebar.markdown('<div class="side-sub">Community Legal-Aid Demand Forecaster • 100% local</div>',unsafe_allow_html=True)
page=st.sidebar.radio("Workspace",["Overview","Demand Matrix","Case-Type Analysis","Housing & Access","Event Pressure","Service History","Scenario Lab","Reports & Export"])
st.sidebar.markdown("---")
st.sidebar.markdown("### 📂 Data sources")
case_up=st.sidebar.file_uploader("Case-demand records CSV",type=["csv"])
event_up=st.sidebar.file_uploader("Local events CSV",type=["csv"])
service_up=st.sidebar.file_uploader("Service history CSV",type=["csv"])
st.sidebar.caption("Local processing only • no external APIs • use authorized aggregate or de-identified records.")
if st.sidebar.button("↺ Restore sample data",use_container_width=True):st.rerun()

cases=normalize_columns(read_upload(case_up,case_default))
events=normalize_columns(read_upload(event_up,event_default))
service=normalize_columns(read_upload(service_up,service_default))
scored=demand_score(cases,events,service)
if scored.empty:
    st.error("No usable case-demand records found."); st.stop()

st.markdown("""
<div class="hero">
<h1>⚖️ Community Legal-Aid Demand Forecaster</h1>
<p>Local-first screening of potential legal-support service demand using case mix, housing stress, local events, access gaps, and service-history signals.</p>
<div class="badges"><span class="badge">100% Local</span><span class="badge">Privacy-conscious</span><span class="badge">Explainable score</span><span class="badge">CSV-first</span><span class="badge">No cloud inference</span></div>
</div>
""",unsafe_allow_html=True)

if page=="Overview":
    avg=float(scored.demand_score.mean()); crit=int((scored.demand_score>=75).sum()); high=int((scored.demand_score>=50).sum())
    housing=float(pd.to_numeric(scored.housing_stress_index,errors="coerce").mean()); access=float(pd.to_numeric(scored.service_access_gap,errors="coerce").mean())
    k=st.columns(5)
    vals=[("Regions screened",len(scored),"local planning units"),("Average demand",f"{avg:.1f}/100","screening signal"),("High/Critical",high,f"{crit} critical"),("Housing stress",f"{housing:.0f}/100","mean index"),("Access gap",f"{access:.0f}/100","mean index")]
    for c,(a,b,d) in zip(k,vals):c.markdown(f'<div class="kpi"><div class="lab">{a}</div><div class="val">{b}</div><div class="sub">{d}</div></div>',unsafe_allow_html=True)
    st.write("")
    l,r=st.columns([1.18,.82])
    with l:
        st.markdown('<div class="card"><div class="section">Demand landscape</div>',unsafe_allow_html=True)
        fig=px.scatter(scored,x="housing_stress_index",y="demand_score",color="demand_level",size=safe_positive_size(scored.case_volume_index),hover_name="zone",
                       hover_data=[c for c in ["case_volume_index","local_event_pressure","unmet_service_index","service_access_gap"] if c in scored],
                       template="simple_white",labels={"housing_stress_index":"Housing stress index","demand_score":"Demand score"})
        fig.update_layout(height=405,margin=dict(l=10,r=10,t=10,b=20),legend_title="")
        st.plotly_chart(fig,use_container_width=True); st.markdown('</div>',unsafe_allow_html=True)
    with r:
        st.markdown('<div class="card"><div class="section">Demand mix by level</div>',unsafe_allow_html=True)
        m=scored.demand_level.value_counts().reindex(["Low","Moderate","High","Critical"],fill_value=0).reset_index();m.columns=["level","count"]
        fig=px.bar(m,x="level",y="count",color="level",template="simple_white");fig.update_layout(height=405,margin=dict(l=10,r=10,t=10,b=20),showlegend=False)
        st.plotly_chart(fig,use_container_width=True);st.markdown('</div>',unsafe_allow_html=True)
    st.write("")
    a,b=st.columns([1.05,.95])
    with a:
        st.markdown('<div class="card"><div class="section">Priority service-review queue</div>',unsafe_allow_html=True)
        st.dataframe(scored.sort_values("demand_score",ascending=False)[["zone","demand_score","demand_level","review_priority","housing_stress_index","case_volume_index"]].head(8),use_container_width=True,hide_index=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with b:
        st.markdown('<div class="card"><div class="section">Local legal-aid visual</div>',unsafe_allow_html=True)
        st.image(str(BASE/"assets/legal_aid_hub.svg"),use_container_width=True)
        st.markdown('<div class="muted">Illustrative UI artwork; not legal advice, case evidence, or a map of service providers.</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

elif page=="Demand Matrix":
    st.markdown('<div class="card"><div class="section">Demand matrix</div>',unsafe_allow_html=True)
    c=st.columns(3); z=c[0].selectbox("Zone",["All"]+sorted(scored.zone.astype(str).unique().tolist())); th=c[1].slider("Minimum demand score",0,100,0); pri=c[2].checkbox("High/Critical only")
    v=scored[scored.demand_score>=th].copy()
    if z!="All":v=v[v.zone.astype(str)==z]
    if pri:v=v[v.demand_score>=50]
    st.dataframe(v.sort_values("demand_score",ascending=False),use_container_width=True,hide_index=True)
    st.markdown('</div>',unsafe_allow_html=True)
    st.write("")
    col1,col2=st.columns(2)
    with col1:
        st.markdown('<div class="card"><div class="section">Zone benchmark</div>',unsafe_allow_html=True)
        zs=zone_summary(scored)
        fig=px.bar(zs.sort_values("avg_demand",ascending=False),x="zone",y="avg_demand",template="simple_white",labels={"avg_demand":"Average demand"})
        fig.update_layout(height=350);st.plotly_chart(fig,use_container_width=True);st.markdown('</div>',unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="card"><div class="section">Selected zone guidance</div>',unsafe_allow_html=True)
        ch=st.selectbox("Select zone",sorted(scored.zone.astype(str).unique().tolist())); row=scored[scored.zone.astype(str)==ch].sort_values("demand_score",ascending=False).iloc[0]
        st.metric("Top demand score",f"{row.demand_score:.1f}/100",row.demand_level)
        for x in priority_actions(row):st.write("• "+x)
        st.markdown('</div>',unsafe_allow_html=True)

elif page=="Case-Type Analysis":
    st.markdown('<div class="card"><div class="section">Case-type demand signals</div>',unsafe_allow_html=True)
    if "case_type" in scored.columns:
        ct=scored.groupby("case_type",as_index=False).agg(avg_demand=("demand_score","mean"),avg_volume=("case_volume_index","mean"),regions=("zone","count")).sort_values("avg_demand",ascending=False)
        fig=px.bar(ct,x="case_type",y="avg_demand",color="avg_volume",template="simple_white",labels={"avg_demand":"Average demand","case_type":"Case type"})
        fig.update_layout(height=390);st.plotly_chart(fig,use_container_width=True)
    else:st.info("Upload data containing a case_type field.")
    st.dataframe(scored[["zone","case_type","case_volume_index","unmet_service_index","demand_score","demand_level"]].sort_values("demand_score",ascending=False) if "case_type" in scored else scored,use_container_width=True,hide_index=True)
    st.markdown('</div>',unsafe_allow_html=True)

elif page=="Housing & Access":
    st.markdown('<div class="card"><div class="section">Housing stress and service-access pressure</div>',unsafe_allow_html=True)
    fig=px.scatter(scored,x="housing_stress_index",y="service_access_gap",color="demand_level",size=safe_positive_size(scored.unmet_service_index),
                   hover_name="zone",template="simple_white",labels={"housing_stress_index":"Housing stress","service_access_gap":"Access gap"})
    fig.update_layout(height=410);st.plotly_chart(fig,use_container_width=True)
    st.dataframe(scored[["zone","housing_stress_index","service_access_gap","unmet_service_index","demand_score","demand_level"]].sort_values("housing_stress_index",ascending=False),use_container_width=True,hide_index=True)
    st.markdown('</div>',unsafe_allow_html=True)

elif page=="Event Pressure":
    st.markdown('<div class="card"><div class="section">Local-event pressure</div>',unsafe_allow_html=True)
    if not events.empty:
        ev=events.copy()
        if "event_date" in ev.columns:ev["event_date"]=pd.to_datetime(ev.event_date,errors="coerce")
        c=st.columns(3);c[0].metric("Event rows",len(ev));c[1].metric("Zones covered",ev.zone.nunique() if "zone" in ev else 0);c[2].metric("Event types",ev.event_type.nunique() if "event_type" in ev else 0)
        if "zone" in ev.columns:
            ed=ev.groupby("zone").size().reset_index(name="event_rows").sort_values("event_rows",ascending=False)
            fig=px.bar(ed,x="zone",y="event_rows",template="simple_white",labels={"event_rows":"Event records"})
            fig.update_layout(height=350);st.plotly_chart(fig,use_container_width=True)
        st.dataframe(ev,use_container_width=True,hide_index=True)
    else:st.info("No local event records loaded.")
    st.markdown('</div>',unsafe_allow_html=True)

elif page=="Service History":
    st.markdown('<div class="card"><div class="section">Service history and unmet demand</div>',unsafe_allow_html=True)
    if not service.empty:
        sv=service.copy()
        if "service_date" in sv.columns:sv["service_date"]=pd.to_datetime(sv.service_date,errors="coerce")
        if "zone" in sv.columns:
            g=sv.groupby("zone",as_index=False).agg(service_requests=("service_requests","sum") if "service_requests" in sv else ("zone","size"),
                                                    unmet_cases=("unmet_cases","sum") if "unmet_cases" in sv else ("zone","size"))
            fig=px.bar(g,x="zone",y=["service_requests","unmet_cases"],barmode="group",template="simple_white")
            fig.update_layout(height=380);st.plotly_chart(fig,use_container_width=True)
        st.dataframe(sv,use_container_width=True,hide_index=True)
    else:st.info("No service-history records loaded.")
    st.markdown('</div>',unsafe_allow_html=True)

elif page=="Scenario Lab":
    st.markdown('<div class="card"><div class="section">What-if demand scenario lab</div>',unsafe_allow_html=True)
    zone=st.selectbox("Base zone",sorted(scored.zone.astype(str).unique().tolist())); row=scored[scored.zone.astype(str)==zone].sort_values("demand_score",ascending=False).iloc[0]
    st.caption("Scenario changes alter screening inputs only; they are not legal forecasts or service guarantees.")
    c=st.columns(5)
    changes={
        "case_volume_index":c[0].slider("Case volume",-30,30,0),
        "housing_stress_index":c[1].slider("Housing stress",-30,30,0),
        "local_event_pressure":c[2].slider("Event pressure",-30,30,0),
        "unmet_service_index":c[3].slider("Unmet service",-30,30,0),
        "service_access_gap":c[4].slider("Access gap",-30,30,0),
    }
    before=float(row.demand_score);after=scenario_score(row,changes)
    x,y,z=st.columns(3);x.metric("Baseline",f"{before:.1f}",row.demand_level);y.metric("Scenario",f"{after:.1f}",f"{after-before:+.1f}");z.metric("Direction","Improves" if after<before else ("Worsens" if after>before else "Unchanged"))
    st.progress(float(np.clip(after/100,0,1)))
    st.markdown('</div>',unsafe_allow_html=True)

elif page=="Reports & Export":
    st.markdown('<div class="card"><div class="section">Reports & exports</div>',unsafe_allow_html=True)
    st.download_button("⬇ Download scored demand CSV",scored.to_csv(index=False).encode(),file_name="legal_aid_demand_scored.csv",mime="text/csv",use_container_width=True)
    top=scored.sort_values("demand_score",ascending=False).head(10)
    lines=["# Community Legal-Aid Demand Forecaster — Local Screening Report","",f"Regions screened: {len(scored)}",f"Average demand score: {scored.demand_score.mean():.1f}/100",f"High/Critical regions: {(scored.demand_score>=50).sum()}","",
           "## Priority regions"]
    lines += ["| Zone | Score | Level | Priority |","|---|---:|---|---|"] + [f"| {r.zone} | {r.demand_score:.1f} | {r.demand_level} | {r.review_priority} |" for _,r in top.iterrows()]
    lines += ["","## Responsible use","Screening signals are planning aids and do not constitute legal advice, case decisions, eligibility determinations, or predictions guaranteed to occur."]
    report="\n".join(lines)
    st.download_button("⬇ Download Markdown report",report.encode(),"legal_aid_demand_report.md","text/markdown",use_container_width=True)
    st.code(report,language="markdown")
    st.markdown('</div>',unsafe_allow_html=True)

st.markdown("---")
st.caption("Local-first service-demand screening • no external APIs • use qualified legal-aid and community-service professionals for decisions.")
