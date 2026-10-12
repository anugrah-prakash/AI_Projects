# AI Strategy Copilot — Streamlit edition

Complete Python app for a fictional WHU hackathon practice case. Requires Python
3.10 or newer. Run this edition with Streamlit, not `python app.py`.

## Run in VS Code on Windows

1. Extract this ZIP into a new folder. Do not mix it with the previous HTTP-server edition.
2. In VS Code, open the folder containing app.py and requirements.txt.
3. Open Terminal → New Terminal and run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Open the included `.env` file, add your key and save:

```dotenv
OPENAI_API_KEY=your_actual_api_key
OPENAI_MODEL=gpt-4o-mini
```

5. Start the app:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open http://localhost:8501 if a browser does not open automatically. Using the
virtual environment's Python directly avoids PowerShell activation-policy issues.
If you already have an active Python environment, simply run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Edit `.env` as above. Stop the server with Ctrl+C.

## Streamlit Community Cloud

1. Put this folder's contents in a GitHub repository. Include app.py, core.py,
   demo.py, sample_data.json, requirements.txt and .streamlit/config.toml.
2. Do not commit `.env` or `.streamlit/secrets.toml` containing real credentials.
   The supplied .gitignore excludes both. Example files are safe templates.
3. On https://share.streamlit.io create an app, select the repository and branch,
   and set the main file path to `app.py` (or the relative path if nested).
4. Select Python 3.11 or newer in advanced settings when offered.
5. Paste the following TOML into the app's Secrets configuration:

```toml
OPENAI_API_KEY = "your_actual_api_key"
OPENAI_MODEL = "gpt-4o-mini"
APP_PASSWORD = "choose-a-long-private-password"
```

6. Deploy. Streamlit installs requirements.txt and runs app.py.

APP_PASSWORD is optional. If set, the sidebar requires this shared password before
showing the app or running analysis. This is a basic demo access gate, not a full
user-account system or rate limiter. Do not expose an unrestricted API-funded app
to the public. AI API usage remains separately billed from hosting.

Official deployment/secrets guidance:
https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management

## Configuration precedence

OpenAI key/model: Streamlit secrets → process environment → local `.env` → defaults.
For local Streamlit secrets, copy `.streamlit/secrets.toml.example` to
`.streamlit/secrets.toml` and fill in the key. Do not rename the example unless you
intend to use it: a placeholder secret would override a valid `.env` key.
APP_PASSWORD is read from Streamlit secrets or the process environment (not .env).
Restart after changing local configuration if necessary. No API key input widget
is exposed, and credentials are never included in report downloads.

## Included features

- Editable company brief, 18 customer comments, three fictional competitors,
  goal, cash budget and operational constraints.
- Compare strategies button and optional offline scripted rehearsal mode.
- Three scored options with cost/effort estimates, evidence, risks and trade-offs.
- Python selects the highest-scoring affordable option using impact 40%,
  feasibility 35% and evidence 25%. Ties follow original order.
- Two-stage live analysis: AI generates options; Python selects; AI writes the
  recommendation and experiment for that fixed winner.
- Facts, assumptions and estimates labelled; source expanders show exact inputs.
- Missing information, conflicting reports and decision-changing evidence.
- Itemised 30-day experiment, owner/day ranges, hypothesis, metric, baseline,
  success threshold, measurement method and stop condition.
- Budget arithmetic, score, source-ID and structured-output validation.
- Five-run session history, side-by-side input change inspection, stale-report
  warning, and JSON export with each run's complete evidence snapshot.
- Optional shared password and server-side secret configuration.

## Offline rehearsal

Check Offline sample mode, keep the original scenario, and click Compare strategies.
Try budgets of €2,000, €500 and €100. Offline mode is explicitly scripted and
supports budget changes only. Arbitrary goal/evidence/constraint edits require
live AI. Use Reset fictional example to restore the defaults. Resetting inputs
does not delete previous reports.

## Tests and verification

```bash
python -m unittest discover -s tests -v
```

Core tests cover the API contract using mock responses, missing keys, zero/low
budgets, invalid numbers, invalid citations, incorrect ranking, ties, overbudget
options and experiment spending. The optional Streamlit AppTest checks the offline
UI flow and stale-report warning; it skips when Streamlit is not installed.

Packaging checks: Python 3.10 and 3.11 grammar validation and the core tests passed.
Streamlit could not be installed in the packaging environment, so actual Streamlit
UI execution was not verified there. The AppTest is included for running after
installation. No live API requests were made: supply your own API key to test live.

## Limitations and data

All defaults are invented practice data. The app sends live-mode evidence to
OpenAI with store=false; provider data handling still applies. Source-ID validation
does not establish semantic correctness. Scores, costs and business effects are
estimates; inspect the evidence and feasibility before acting. The app does not
browse the web or carry out recommendations. There is no database. Closing or
refreshing the session may lose reports; use JSON export to preserve them.
A failed run leaves previous successful reports intact. Two sequential API calls
can take several minutes and each incurs API usage.

## Troubleshooting

- `No module named streamlit`: install requirements using the same Python you use to launch.
- `missing ScriptRunContext`: launch with `python -m streamlit run app.py`.
- Missing key: fill `.env` locally or Streamlit Secrets in the cloud.
- Unexpected key/model: check secret precedence; remove placeholder secrets.
- API 401/429: check credentials/billing/quota. API 400/404: check model access and
  support for Responses API structured outputs.
- Validation failure: retry and inspect inputs; invalid reports are not silently published.
- Password prompt: use the APP_PASSWORD configured by the app owner.

## Files

app.py — Streamlit UI and session state
core.py — evidence preparation, schemas, validation and API calls
demo.py — offline sample report
sample_data.json — editable fictional defaults
requirements.txt — Streamlit dependency
.env / .env.example — local API configuration
.streamlit/config.toml — theme
.streamlit/secrets.toml.example — cloud/local secrets template
tests/ — core regression tests and optional Streamlit UI test
