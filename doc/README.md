# Community Legal-Aid Demand Forecaster — JusticeDemand Local

100% local Streamlit decision-support dashboard for screening potential community legal-aid service demand using case mix, housing stress, local events, service access gaps, and service history.

## Features
- Explainable 0–100 demand score
- Low / Moderate / High / Critical classification
- Demand matrix and zone benchmarking
- Case-type demand analysis
- Housing stress and access-gap analysis
- Event pressure monitoring
- Service-history analysis
- What-if scenario lab
- CSV and Markdown exports
- Sidebar-only CSV uploads
- No external APIs or cloud inference

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python validate_project.py
python -m pytest tests -q
./run_project.sh
```

## Responsible use
This tool supports service planning; it is not legal advice, a case outcome predictor, eligibility adjudicator, or substitute for qualified legal-aid professionals and local governance.
