# Decoding the Amt — line-cited extraction update

## Run

Use Python 3.11+. Extract this project, open a terminal in its folder, and run:

```sh
python -m venv .venv
```

Activate on Windows: `.venv\Scripts\Activate.ps1`

Activate on macOS/Linux: `source .venv/bin/activate`

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Before launching, put your API key in `.env`. When updating an existing installation,
keep your existing private `.env`. Stop the old process with Ctrl+C before restarting.

## Current pipeline

1. Read a PDF's usable text layer, or transcribe images/scans using vision.
2. Let the reader compare and correct the text against the original.
3. Number source lines and extract all three answers together using `pipeline.py`.
4. Ask a second model request to correct the draft and add omitted explicit facts.
5. Build evidence quotes from the cited source lines locally. Reject invalid citations,
   unsupported numbers, and deadlines/amounts absent from the action's evidence.
6. Show concise answers, with source excerpts inside expandable panels.

This replaces the old Boolean-review/per-question pipeline. `core.py` retains legacy
helpers for regression tests, but the app now imports `pipeline.analyze`.
No answer for the supplied sample is hard-coded into the application. The sample
text and expected responses are used only in offline tests.

If one item fails evidence matching, other supported items remain, with a warning.
A wholly empty result is now an extraction error, never a claim that the letter has
no requirements. Malformed structured responses are discarded and retried once.
Scanned inputs normally use three model calls; PDFs with usable text use two.
Retries can double those calls. API usage is billed to your API account.

The app accepts a single PDF (1–6 pages), image or camera photo up to 20 MB.
For multi-page photos combine them into one PDF. Browser camera access requires
permission and localhost or HTTPS. Theme, SVG graphics and animations run locally.
Reduced-motion settings are respected.

## Limits and privacy

AI interpretation can still be wrong. Source citations and a corrective review do
not prove semantic accuracy. Verify the original before acting. This is a reading
aid, not a legal decision system. Relative dates are not calculated. The model must
not infer missing deadlines, amounts or penalties. Missing facts should prompt asking
the sender. No outside legal knowledge is injected into the interpretation.

Letter data is sent to OpenAI after consent. Requests use store=False; provider
retention rules still apply. The app keeps session data in memory without intentionally
writing letter files or logging their text. Clearing the app is not secure memory
erasure or deletion of provider records. Keep .env private. Public deployment requires
authentication, HTTPS, cost controls and a privacy/security review.

## Verification

```sh
python -m unittest discover -s tests -v
```

32 offline tests pass, including legacy regressions and the new line-cited pipeline.
Tests of model behavior use mocked responses: they do not establish live AI accuracy.
The supplied Finanzamt PDF's native text extraction was tested directly. Live API and
browser testing were not possible in the build environment.

For the supplied sample, expected content is: the office wants the 2025 tax return;
submit online via ELSTER by 31 October 2026; if you believe filing is unnecessary,
explain why in writing. Lateness may lead to a late fee, tax estimation and a threat
of a coercive fine. The original letter specifies no penalty amount.
