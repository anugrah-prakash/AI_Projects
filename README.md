# AI Strategy Copilot

A complete local Python web app for a WHU hackathon practice project. Python 3.10+; no third-party packages or build tools required. The browser interface uses plain HTML, CSS and JavaScript; all AI calls, configuration, validation and HTTP handling run in Python.

## Quick start

1. Extract the ZIP and open a terminal in `ai_strategy_copilot`.
2. Open the included `.env` file in a text editor. Set:
   ```dotenv
   OPENAI_API_KEY=your_actual_api_key
   OPENAI_MODEL=gpt-4o-mini
   PORT=8501
   ```
   Dotfiles can be hidden by your file manager. `.env.example` is an identical backup template. Do not add quotes unless needed; never share your real `.env`. An existing process environment variable overrides its `.env` value.
3. Run:
   ```bash
   python app.py
   ```
   Use `python3 app.py` on macOS/Linux if necessary, or `py app.py` on Windows.
4. Open http://127.0.0.1:8501 in your browser.
5. Edit the goal, budget, constraints and evidence. Click **Compare strategies**.

An OpenAI API key with access to the configured model is required for live analysis. API usage is separately billed. The model must support the Responses API and strict JSON-schema structured outputs. Change OPENAI_MODEL if your account does not have access to the default. Configuration is reread on requests; restart after changing PORT.

## Features

- Editable, prepopulated fictional Düsseldorf café brief, 18 customer comments, three competitors, goal and constraints.
- Automatic evidence IDs for each nonempty line: B1, F1, C1, U1, etc.
- Situation summary with fact/assumption/estimate labels and clickable source references.
- Exactly three options, with actions, pilot cost estimates, incremental staff effort, potential impact, evidence, risks and trade-offs.
- Transparent ranking: impact 40%, feasibility 35%, evidence 25%; each score is 1–5. Highest-scoring affordable option wins, with original order breaking ties.
- Recommendation, missing information, contradictory evidence and conditions that could change the decision.
- 30-day experiment with steps, owners, itemised spending, hypothesis, metric, baseline, measurable success threshold, measurement method and stop condition.
- Server checks output structure, finite numbers, unique option IDs, source IDs, citations for structured factual claims, recommendation/ranking consistency and budget arithmetic. Invalid reports are rejected, not silently patched.
- Last five runs retained in browser memory, input-change warning, previous-run viewing and comparison of changed inputs/budgets/recommendations.
- Downloadable JSON report with the exact input snapshot and source evidence. No API key in exports.
- Offline scripted sample mode for the original scenario and budget changes; no API calls. Arbitrary edits require live AI and are explicitly rejected in offline mode.
- API error messages for missing keys, rate limits, unavailable models, incomplete output and connection errors.

## Rehearsal

First enable offline sample mode and click Compare strategies. Try €2,000, €500 and €100. The €100 scenario switches to a no-cash discovery pilot. Offline reports are scripted illustrations, not analysis of your edits.

For live practice disable offline mode, set your API key, and compare the original example. Then reduce budget or add a constraint such as “No discounts or rewards allowed.” Inspect the recommendation and source evidence. The same strategy may remain best; compare its scope and explanation, not just its name.

## Validation and limits

Run automated checks from the project folder:
```bash
python -m unittest discover -s tests -v
```
Tests cover low/zero budgets, overbudget rejection, fabricated source IDs, uncited facts, invalid numbers, ranking consistency, a mocked API response, static-file serving, secret-file isolation, cross-origin rejection and the offline HTTP flow.

Live API calls were not executed during packaging because no user API key was supplied. The API integration follows the official structured-output contract: https://developers.openai.com/api/docs/guides/structured-outputs . Automated source-ID checks do not verify semantic support, and schema validity does not guarantee factual accuracy. Review each claim, score, forecast and operational constraint. Narrative text is prompted to remain grounded but is not semantically proven by the validator. Scores and financial impacts are estimates, not measured outcomes.

The included company and competitors are invented, and all numbers/comments are synthetic practice data. The prototype does not browse the web, independently validate market facts, perform accounting or execute recommended actions.

## Data and operation

Live mode sends your goal, budget and entered evidence to OpenAI. The request sets `store=false`; provider data handling still applies. Do not submit information you are not authorised to send. The app has no database and does not persist edits or reports automatically. Refreshing/closing the browser loses run history; export reports to preserve them. A failed request keeps the previous successful report visible with its original snapshot.

The `.env` file stays server-side, is excluded by `.gitignore`, and cannot be fetched by the app's fixed static routes. The server listens only on 127.0.0.1 and rejects cross-origin browser submissions. This is a local, single-user practice app, not a production multi-user deployment; keep it bound to localhost.

## Files

- `app.py`: Python web server and API routes.
- `core.py`: input processing, schemas, ranking checks and OpenAI client.
- `demo.py`: deterministic offline rehearsal report.
- `sample_data.json`: editable fictional defaults loaded at startup in the browser.
- `static/`: browser interface.
- `.env`: private API configuration, shipped with an empty key.
- `.env.example`: configuration template.
- `tests/test_app.py`: standard-library automated tests.
- `requirements.txt`: notes that no external dependencies are needed.

## Troubleshooting

- Port in use: change PORT in `.env` and restart.
- Missing key: fill OPENAI_API_KEY in `.env` beside app.py.
- 401: check the API key. 429: check API billing/quota or wait before retrying.
- 400/404: check model access and structured-output support.
- Report validation failed: retry; if persistent, try another supported model. No report is silently repaired.
- Edited input rejected in offline mode: reset the fictional example or disable offline mode.


## Ranking fix — 12 October 2026

The live workflow now makes two API calls. First, AI generates and scores three
options. Python validates them and selects the highest-scoring affordable option,
using original order for ties. Second, AI writes the recommendation and experiment
for that fixed winner. The model cannot change the winning ID or the option scores
in the second stage. Budget and citation checks remain enabled.

This resolves the previous model-versus-Python ranking mismatch. Two calls can
increase latency and API usage. A failed second call still leaves any previous
successful report intact. Tests use mocked API responses; no live API key was used.

To update an existing installation, replace core.py with this version and restart
python app.py. Keep your existing .env and API key. Replacing the whole app is also
possible, but back up .env first: the download deliberately contains an empty key.
