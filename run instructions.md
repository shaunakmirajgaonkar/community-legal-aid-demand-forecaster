# Run instructions
```bash
cd ~/Downloads/CommunityLegalAidDemandForecaster_Local
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python validate_project.py
python -m pytest tests -q
./run_project.sh
```
