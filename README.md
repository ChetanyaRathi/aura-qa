# AuraQA 🤖✨

> **A self-healing, AI-powered end-to-end test automation agent.** AuraQA writes tests from a URL, runs them inside a real browser, and automatically heals broken CSS selectors on the fly using AI and element intent.

---

## 🚀 Key Features

- **AI-Powered Test Generation**: Point AuraQA at any URL, and it will analyze the interactive elements on the page to write realistic E2E user flows.
- **Self-Healing Selectors**: When website changes break your selectors, the healer looks at the **intent** of the step (e.g., *"the green login button"*) and the new DOM layout to automatically discover the new selector and repair the test suite.
- **Sleek Web Dashboard**: A recruiter-facing React dashboard to trigger test runs, view real-time statistics (Passed, Healed, Failed), and see side-by-side diffs of repaired selectors.
- **Smart DOM Shrinking**: Compresses large web pages into small lists of visible, interactive elements to keep LLM context window costs low and accuracy high.
- **Nightly CI/CD Monitoring**: Out-of-the-box GitHub Actions workflow to run self-healing tests on a schedule.

---

## 🛠️ Tech Stack

- **Core Engine**: Python 3.10+, Playwright (browser automation)
- **AI Client**: Gemini (default) / Groq (backup)
- **Backend API**: FastAPI, Uvicorn, Pydantic v2
- **Frontend Dashboard**: React 18, Tailwind CSS, Babel (browser-compiled for zero-build-step demos)

---

## 📁 Repository Structure

```text
auraqa/
├── auraqa/                  # Core Python package (the brains)
│   ├── __init__.py
│   ├── llm.py               # AI client interface (Gemini / Groq)
│   ├── dom_utils.py         # DOM compressor (extracts interactive elements)
│   ├── models.py            # Data structures (TestCase, TestStep, StepResult)
│   ├── generator.py         # AI test flow generator
│   ├── runner.py            # Playwright test runner
│   ├── healer.py            # Self-healing selector resolver
│   └── reporter.py          # HTML/JSON reporter generator
│
├── tests_store/             # Saved test suites (JSON)
│   └── example_suite.json   # Sample SauceDemo test suite
│
├── reports/                 # Generated HTML and JSON test reports
│   └── report.html
│
├── frontend/                # Interactive dashboard
│   ├── index.html
│   └── dashboard.jsx        # Dashboard UI
│
├── .github/workflows/
│   └── ci.yml               # GitHub Actions workflow
│
├── cli.py                   # Command-line control
├── server.py                # FastAPI backend server
├── requirements.txt         # Project dependencies
└── .env.example             # Environment variable template
```

---

## ⚡ Quick Start

### 1. Install Dependencies
Ensure you have Python 3.10+ installed:
```bash
pip install -r requirements.txt
python -m playwright install --with-deps chromium
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and configure your API keys:
```bash
cp .env.example .env
```
Open `.env` and fill in either your `GEMINI_API_KEY` (free key from [AI Studio](https://aistudio.google.com/)) or your `GROQ_API_KEY`.

---

## 💻 CLI Usage

AuraQA provides a CLI tool (`cli.py`) to trigger tasks manually from the command line:

### Generate a Test Suite
Point the AI generator at any webpage:
```bash
python cli.py generate --url https://www.saucedemo.com/
```
*Saves the output suite JSON into `tests_store/`.*

### Run a Test Suite (Without Healing)
Run a suite to check if everything passes:
```bash
python cli.py run --suite tests_store/saucedemo_login_flows.json --headed
```

### Run a Test Suite with Self-Healing Enabled
If a page layout has changed and selectors are broken:
```bash
python cli.py heal --suite tests_store/saucedemo_login_flows.json --headed
```
*If a step fails, the healer will ask the LLM for the correct selector based on the element's intent, verify it works in the live browser, and write the corrected selector back to the JSON file.*

---

## 🖥️ Web Dashboard

Start the FastAPI backend to launch the interactive UI:
```bash
python -m uvicorn server:app --reload --port 8001
```

Open **`http://localhost:8001`** in your browser. From the dashboard, you can:
- Type in any website URL and generate a test suite on the fly.
- Select any saved suite from a dropdown and run it.
- View test progress, stats, and a breakdown of every selector healed by the AI.

---

## 🛡️ How the Self-Healing Works

Traditional E2E frameworks break when selectors change. AuraQA fixes this by using **Intent-Based Selection**:

1. **Test Defs Keep the Goal**: A test step doesn't just store `#login-button`, it stores `intent: "the green Login button"`.
2. **Interactive DOM Snapshot**: When `#login-button` fails to resolve, AuraQA runs a minified script to map visible, interactive elements on the screen.
3. **LLM Matches Intent**: AuraQA prompts the LLM with the list of candidate elements and the target intent.
4. **Verifying Before Trusting**: The runner tests the suggested selector in the browser session. If it resolves correctly, the step passes, and the JSON test suite is updated with the new selector permanently.
