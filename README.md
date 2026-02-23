## What this project does

Rule-based baseline pipeline that converts ADI home-care visit dictations (Italian) into a structured JSON format.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m src.run_pipeline
python -m src.evaluate
## Tests

```bash
pytest -q
