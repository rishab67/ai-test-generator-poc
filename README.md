# 🤖 AI-Native QA Architect (Microsoft Build AI 2026)

> **Theme 06: Production Function (AI-Native CI/CD)** > Automatically generates runnable Pytest API test suites, executes semantic security fuzzing, and self-heals broken assertions using an agentic LLM architecture.

---

## 🎯 Hackathon Theme Alignment & The "Why"
API test authoring and maintenance is one of the highest-effort, lowest-creativity tasks in software engineering. Traditional CI/CD pipelines rely on static, hardcoded tests that break the moment a developer changes a JSON schema. 

This project directly addresses **Theme 06** by rewriting the software testing lifecycle into an AI-led delivery pipeline. It introduces:
1. **Automated Test Generation:** Dynamically fetches live Swagger/OpenAPI specs and translates them into runnable `pytest` code.
2. **Autonomous AppSec Fuzzing:** Replaces static negative testing by generating extreme, boundary-breaking payloads to test server resilience natively within the pipeline.
3. **Self-Adapting Quality Gates (Self-Healing):** Intercepts pipeline `AssertionErrors`, analyzes schema drift in live API responses, and dynamically outputs the exact Python patch required to fix the test.

---

## 🏗️ Architecture & Microsoft Open-Source Stack
To maintain a 100% free and open-source architecture while fulfilling the Microsoft Build AI requirements, this framework is designed around an agentic workflow:

* **Agent Orchestration (Microsoft AutoGen):** The system architecture is designed to be orchestrated by **Microsoft AutoGen** (MIT License). This enables a multi-agent routing topology: a "Developer Agent" generates the tests, a "Security Agent" fuzzes the endpoints, and an "SRE Agent" handles test self-healing.
* **LLM Backend (Google Gemini):** By connecting the Microsoft orchestration layer to **Gemini 2.5 Flash** via Google AI Studio, we ensure high-speed, cost-free reasoning that bypasses paid API limits.

```text
Swagger JSON (live) ──▶ AutoGen Orchestrator ──▶ Gemini 2.5 Flash
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
 Test Generation         Security Fuzzing        Self-Healing
 (pytest scripts)       (Boundary Payloads)     (Assertion Patches)


========================================================================
⚙️ Key Engineering Decisions1. Prompt Engineering as a Quality GateThe framework enforces hard SDET rules on the LLM output:Raw Python only — no markdown fences leaked into code.No fixture definitions inside generated files (avoids conftest.py conflicts).Dynamic path parameters use Python f-strings, not hardcoded values.Auth headers passed explicitly via headers={...}.2. Rate Limit Resilience (Circuit Breaking)A custom swap_model() fallback logic ensures the batch job runs unattended across all endpoints. If the primary Gemini model throttles, it silently switches to a lighter model (Flash-8B) and retries, ensuring CI/CD pipelines never crash due to LLM traffic.3. Session-scoped Playwright Fixturesconftest.py sets up one APIRequestContext for the entire test session. This avoids the massive overhead of spinning up a new browser context per test.💻 Tech StackLayerTechnologyAgent OrchestrationMicrosoft AutoGen (Architecture Design)LLM EngineGoogle Gemini 2.5 Flash / Flash-8B FallbacksTest FrameworkPython 3.12, Pytest, Requests, PlaywrightReporting / CIAllure, Pytest-HTML, GitHub PagesPerformanceLocust (SRE baselines)🚀 Setup & ExecutionPrerequisites: Python 3.11+, a free Google AI Studio API key.Bash# 1. Clone & Install
git clone [https://github.com/rishab67/ai-test-generator-poc.git](https://github.com/rishab67/ai-test-generator-poc.git)
cd ai-test-generator-poc
pip install -r requirements.txt


=========================================================
# 2. Set your API key
export GEMINI_API_KEY="your_key_here" # Linux/Mac
$env:GEMINI_API_KEY="your_key_here"   # Windows PowerShell

# 3. Execute the Autonomous Framework
python main.py                              # Generate test suites
pytest tests/test_ai_fuzzer.py -v -s        # Run Security Fuzzing
pytest tests/test_self_healing.py -v -s     # Run Self-Healing Demo

=====================================================================
📂 Enterprise Project StructurePlaintextai_test_generator_poc/
├── core/                  # AI Engine & Framework Logic
│   ├── ai_client.py
│   ├── fetch_swagger.py
│   └── openapi_ingestor.py
├── tests/                 # Execution Suite
│   ├── test_ai_fuzzer.py      (Phase 4: AppSec Fuzzer)
│   ├── test_self_healing.py   (Phase 5: Auto-Patching)
│   └── test_pet_api.py        (Dynamically Generated)
├── reports/               # CI/CD Artifacts
│   └── report.html
├── conftest.py            # Global Pytest fixtures
└── main.py                # Batch orchestrator

=============================================================
🛣️ Roadmap[ ] Implement full multi-agent AutoGen conversational loops for complex API flows.[ ] LLM output evaluation layer (structural scoring + semantic quality grading).[ ] Quarantine system — route low-quality outputs for human review.[ ] Support for OpenAPI v3 specs.Author: Birender Singh Sandhu | LinkedIn | GitHub
