### ⚠️ Academic Disclaimer & Proprietary Intellectual Property Notice — PhD AI in Education (University of Tübingen)

> **AURA-Learn is a proprietary, source-available, NON-PRODUCTION research prototype.**
>
> - **Synthetic by construction:** the demonstrator is built with **100% synthetic** data — simulated eye-tracking signals, simulated video stream status and simulated digital interaction traces. There is **no real data, no human subject, no consent requirement and no data collection** of any kind.
> - **Restricted academic use only:** execution and inspection are strictly limited to **academic evaluation by the selection committee and the supervisors (Prof. Dr. Babette Bühler, Prof. Dr. Ulrich Trautwein)** of the Hector Research Institute of Education Sciences and Psychology (University of Tübingen), in the context of the "PhD AI in Education" application, and to official doctoral supervision in the event of admission.
> - **No endorsement:** no official affiliation with, approval by or partnership with the University of Tübingen or the Hector Research Institute is expressed or implied.
> - **License:** see [`LICENSE`](LICENSE) — proprietary & source-available, **not open source**.
> - **© 2026 EL FILALI SALAH ADDINE — All Rights Reserved.**

---

# AURA-Learn: Multimodal Learning Analytics & Adaptive Learning Environment Demonstrator

AURA-Learn is a **Glass-Box** demonstrator for multimodal Learning Analytics: a bounded perception swarm, a fully deterministic pedagogical arbitration kernel, and a human-in-the-loop educator cockpit. It is an academic demonstration artefact showing how learning signals can be *proposed* by bounded agents, *decided* by an auditable rule kernel, and *supervised* by a human educator whose decisions are recorded in an immutable audit log. Every scenario is deterministic, offline by default, and synthetic.

---

## Table of contents

- [Academic context](#academic-context)
- [Three-tier architecture](#three-tier-architecture)
  - [Tier 1 — Bounded Multimodal Perception Swarm](#tier-1--bounded-multimodal-perception-swarm)
  - [Tier 2 — Deterministic Pedagogical Arbitration Kernel (R1–R6)](#tier-2--deterministic-pedagogical-arbitration-kernel-r1r6)
  - [Tier 3 — Glass-Box Educator Cockpit](#tier-3--glass-box-educator-cockpit)
- [The 3 synthetic scenarios](#the-3-synthetic-scenarios)
- [Execution modes](#execution-modes)
- [Installation and running](#installation-and-running)
- [User interface (reference heritage)](#user-interface-reference-heritage)
- [Verbatim banner and footer](#verbatim-banner-and-footer)
- [Limitations and non-goals](#limitations-and-non-goals)
- [Research roadmap](#research-roadmap)
- [License and citation](#license-and-citation)
- [Contact / author](#contact--author)

---

## Academic context

AURA-Learn accompanies the author's application to the doctoral position **"PhD position in AI in Education (m/w/d), E13 TV-L 75 %"** at the **Hector Research Institute of Education Sciences and Psychology, University of Tübingen**.

Offer reference (evaluation context only, no affiliation implied):

`https://uni-tuebingen.de/en/university/careers/newsfullview-job-advertisements/article/phd-position-in-ai-in-education-m-w-d-e13-tv-l-75/`

This URL is cited solely to document the academic evaluation context of the demonstrator. It does not establish, and must not be read as establishing, any official relationship, endorsement or partnership with the University of Tübingen or the Hector Research Institute.

---

## Three-tier architecture

```
+----------------------------------------------------------------------------------+
|                                 AURA-Learn                                       |
+----------------------------------------------------------------------------------+
|                                                                                  |
|  TIER 1 — Bounded Multimodal Perception Swarm          (proposes, never decides) |
|  +--------------------+ +---------------------------+ +------------------------+  |
|  | Attention_Gaze_    | | Metacognitive_Trace_      | | Pedagogical_Guardrail_ |  |
|  | Agent              | | Agent                     | | Agent [VETO POWER]     |  |
|  | status / metrics   | | status / metrics          | | APPROVE|VETO|DEGRADED  |  |
|  +--------------------+ +---------------------------+ +------------------------+  |
|                 |                    |                        |                  |
|                 +--------------------+------------------------+                  |
|                                      v                                           |
|  TIER 2 — Deterministic Pedagogical Arbitration Kernel                           |
|           pure Python · no LLM · no I/O · evaluate_rules(signals)                |
|           RULE_PRIORITY = [R3, R2, R1, R4, R5, R6]                               |
|                                      |                                           |
|                                      v                                           |
|                              Final verdict proposal                              |
|                                      |                                           |
|  TIER 3 — Glass-Box Educator Cockpit                                             |
|           Accept  |  Overrule & justify (>= 15 chars)                            |
|           Immutable append-only audit log  ·  in-memory CSV export               |
|                                                                                  |
+----------------------------------------------------------------------------------+
```

Flow of one arbitration:

```text
Signals (synthetic) -> Tier 1 Agents -> Tier 2 R1-R6 -> Proposal -> Tier 3 Human Oversight -> Immutable Audit Log
```

### Tier 1 — Bounded Multimodal Perception Swarm

Three **bounded** agents consume the synthetic signal dictionary. "Bounded" means: each agent only transforms a narrow subset of signals into a bounded status plus a step-level trace; **no agent has decision authority**, and no agent can emit an adaptive action on its own. All decisions are delegated to Tier 2.

| Agent | Family of signals | Outputs (exact keys consumed / produced) |
|---|---|---|
| `Attention_Gaze_Agent` | Synthetic eye-tracking: fixation stability, off-task saccade ratio, gaze drift score, time on screen | `status` ∈ {`NORMAL`, `DRIFT_SUSPECTED`, `SENSOR_OFFLINE`}; metrics `fixation_stability`, `off_task_saccade_ratio`, `gaze_drift_score`, `time_on_screen_s` |
| `Metacognitive_Trace_Agent` | Synthetic digital traces: idle time, clicks/min, hint requests, answer revisions, self-corrections | `status` ∈ {`ENGAGED`, `IDLE_PATTERN`}; metrics `idle_time_s`, `clicks_per_min`, `hint_requests`, `answer_revisions`, `self_correction_events` |
| `Pedagogical_Guardrail_Agent` | Complexity, progress stability, drift duration, off-task ratio, sensor state | Badge **VETO POWER**; `verdict` ∈ {`APPROVE`, `VETO`, `DEGRADED`} — a *proposal*, never the final verdict |

Each agent returns a `proposal` (natural-language hint to the kernel) and a `trace` (mini glass-box explanation displayed in the UI).

### Tier 2 — Deterministic Pedagogical Arbitration Kernel (R1–R6)

A **pure Python** kernel: no LLM, no network, no file I/O, no randomness. Its single entry point is `evaluate_rules(signals)`, which returns the triggered rule, the final verdict, a per-rule evaluation matrix and a step-by-step arbitration trace.

The priority order is explicit and hard-coded:

```python
RULE_PRIORITY = ["R3", "R2", "R1", "R4", "R5", "R6"]  # first trigger wins
```

| Rule | Condition | Thresholds (exact constants) | Verdict |
|---|---|---|---|
| R1 | Gaze drift + sustained idle pattern | `off_task_ratio >= 0.40`, `idle >= 45 s`, `gaze_drift >= 0.50` | `APPROVE_GENTLE_SCAFFOLD` |
| R2 | Deep flow + brief drift | `complexity >= 0.70`, `progress >= 0.65`, `drift_duration <= 8 s`, `off_task >= 0.15` | `HARD_VETO` |
| R3 | Sensor loss (eye-tracker / video) | `sensor_online == False` | `DEGRADE_TRACE_ONLY` |
| R4 | Cognitive load / distress | `answer_revisions >= 4`, `self_corrections >= 3` | `APPROVE_SUPPORT_HINT` |
| R5 | Haste / over-confidence | `latency <= 6 s`, `accuracy <= 0.55` | `APPROVE_REFLECTION_PROMPT` |
| R6 | No trigger | abstention | `NO_ACTION` |

Threshold constants are named in the code (`THRESHOLD_OFF_TASK_RATIO`, `THRESHOLD_IDLE_TIME_S`, `THRESHOLD_GAZE_DRIFT`, `THRESHOLD_TASK_COMPLEXITY`, `THRESHOLD_PROGRESS_STABILITY`, `THRESHOLD_MAX_DRIFT_DURATION_S`, `THRESHOLD_VETO_MIN_DRIFT_RATIO`, `THRESHOLD_ANSWER_REVISIONS`, `THRESHOLD_SELF_CORRECTIONS`, `THRESHOLD_LOW_LATENCY_S`, `THRESHOLD_LOW_ACCURACY`) — no magic numbers in the decision path.

### Tier 3 — Glass-Box Educator Cockpit

The human educator supervises the machine proposal inside a form with two exclusive decisions:

- `Accept Adaptive Action` — the kernel proposal is endorsed;
- `Overrule & Suppress/Modify Intervention` — the proposal is overridden, **mandatory pedagogical justification of at least 15 characters** (`MIN_JUSTIFICATION_CHARS = 15`). If the justification is shorter, the entry is **not recorded** and a blocking error is displayed.

Committed decisions are appended to an **immutable, append-only audit log** stored in `st.session_state["audit_log"]`. Each entry is a plain dictionary with the following keys:

| Key | Content |
|---|---|
| `entry_id` | Sequential identifier, rendered as `#n` |
| `timestamp_utc` | ISO-8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`) |
| `scenario` | Scenario label used for the run |
| `mode` | Execution mode label |
| `rule_id` | Triggered kernel rule (`R1`–`R6`) |
| `machine_verdict` | Deterministic verdict produced by Tier 2 |
| `human_decision` | `Accept Adaptive Action` or `Overrule & Suppress/Modify Intervention` |
| `justification` | Pedagogical rationale (or `—` when accepted without comment) |

The log is displayed read-only (no deletion or editing control is exposed), mirrored as raw JSON in an expander, and exportable as CSV **entirely in memory** via `st.download_button` (`aura_learn_audit_log.csv`, UTF-8 with BOM). **Nothing is ever written to disk.**

---

## The 3 synthetic scenarios

All scenario signals are frozen, hard-coded dictionaries — the same inputs always produce the same verdict.

| Scenario | Agent reaction | Rule | Verdict |
|---|---|---|---|
| `1 - Mind Wandering & Gaze Drift Detection` | Attention → `DRIFT_SUSPECTED`; Metacognitive → `IDLE_PATTERN`; Guardrail → `APPROVE` | **R1** | `APPROVE_GENTLE_SCAFFOLD` |
| `2 - Deep Flow Protection (Pedagogical Veto)` | Attention → `DRIFT_SUSPECTED`; Metacognitive → `ENGAGED`; Guardrail → **`VETO`** | **R2** | `HARD_VETO` |
| `3 - Sensor Dropout / Graceful Degradation` | Checkbox *"Simulate Eye-Tracker / Video stream timeout"* ticked → attention stream unavailable, Guardrail → `DEGRADED` | **R3** | `DEGRADE_TRACE_ONLY` |

For scenario 3, when the checkbox is **left unchecked**, the synthetic sensor signals are healthy and no rule triggers: the kernel falls back to **R6** → `NO_ACTION`. The checkbox is disabled for scenarios 1 and 2, where sensor dropout is not supported.

Scenario 2 is the pedagogical heart of the demonstrator: a *brief* gaze drift during deep, stable work is intentionally **not** interrupted — the guardrail raises `VETO`, and the kernel returns `HARD_VETO`, protecting flow over reactivity.

---

## Execution modes

Two modes are exposed in the sidebar, with `Instant Offline Simulation` selected by default.

| Mode | Behaviour |
|---|---|
| `Instant Offline Simulation` (default) | 100% deterministic; frozen synthetic signals; **no network call at all** |
| `Live DeepSeek LLM` (optional) | Adds an optional natural-language narrative generated by an external LLM |

Live mode details:

- API key is optional, typed as a password field, held **only** in `st.session_state["deepseek_api_key"]` — never written to disk, never logged, never included in the audit log;
- endpoint `https://api.deepseek.com/chat/completions`, model `deepseek-chat`, timeout `8 s`, `temperature 0.0`, `max_tokens 220`;
- the LLM is instructed to be a *bounded pedagogical explainer*: it explains the verdict in three sentences and **must not alter or contest it**.

**The API key never influences the R1–R6 kernel.** The deterministic verdict is computed before, and independently of, any LLM call. Any failure (missing key, absent `requests` module, network error, timeout, parsing error) results in an explicit fallback to the deterministic narrative — never in an altered verdict.

---

## Installation and running

Requires **Python ≥ 3.10** (the code uses modern type annotations with `from __future__ import annotations`).

Dependencies ([`requirements.txt`](requirements.txt)):

```text
streamlit>=1.36.0
pandas>=2.1.0
requests>=2.31.0
```

Setup:

```bash
python -m venv .venv
```

Activation on Windows:

```bat
.venv\Scripts\activate
```

Activation on Unix / macOS:

```bash
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

No API key, no sensor, no camera and no network connection are required for the default offline mode. The entry point is [`app.py`](app.py).

### Run and Debug in VS Code (F5 → server + Microsoft Edge)

A ready-to-use configuration is provided in [`.vscode/`](.vscode):

1. Open the **Run and Debug** panel (`Ctrl+Shift+D`).
2. Select the default configuration **`Streamlit + Edge`** (first entry).
3. Press **F5** → Streamlit starts under `debugpy` in the integrated terminal; in parallel, the non-blocking pre-launch task **`Streamlit: open Edge (detached)`** spawns [`.vscode/open-edge.ps1`](.vscode/open-edge.ps1) in the background. The script polls `http://localhost:8501` (500 ms interval, 60 s timeout) and then opens **Microsoft Edge** on that URL in a regular tab.

No browser debugger is attached: the browser launch does not depend on js-debug, and the Python debug session starts immediately because the pre-launch task returns at once (it only starts a detached background process). The script is idempotent, logs to `.vscode/open-edge.log`, exits with code 0 on success and with code 1 (opening nothing) when the URL does not answer.

A fallback configuration **`Streamlit: server only`** starts the server under `debugpy` without opening any browser. An optional task **`Streamlit: kill port 8501`** frees a port held by a stray Streamlit process.

> **Troubleshooting — `Unable to attach to the browser`.** The previous `serverReadyAction` + `debugWithEdge` setup attached the JavaScript debugger (js-debug 1.93.0 bundled with the editor) to Edge 158 (Chromium 158): the CDP handshake is closed right after `Target.attachToBrowserTarget`, and the session fails with `Unable to launch browser: "Unable to attach to the browser"`. This is a protocol/version incompatibility, not a configuration mistake — the profile, enterprise policy and extension checks all passed. The browser attach was therefore removed and replaced by the script above.

Full details (port, stopping the server, required extensions, known limits) are in [`README-dev.md`](README-dev.md).

---

## User interface (reference heritage)

The UI deliberately mirrors the author's **AURA-Grid** reference demonstrator, so that both artefacts share one visual and interaction language:

- top header with **8 buttons** arranged in two rows of four (`🏛️ Diploma`, `📄 Resume`, `💼 LinkedIn Profile`, `🎓 E-learning Portfolio`, `✉️ Cover letter`, `🔬 Research Proposal`, `🏗️ Architectural Blueprint`, `📝 Technical Statement`) — row 1 links out to external pages, row 2 opens internal document sub-pages;
- **pink palette** `#c2185b` (with `#880e4f` / `#ad1457` variants) and **green palette** `#1b8a3a`;
- **blinking indicators** (`@keyframes scenario-label-blink`, `@keyframes dl-arrow-blink`) for the active Scenario — Execution Mode: enlarged, non-blinking by design;
- the three **Layers** displayed in reading order: perception cards, arbitration kernel, educator cockpit;
- the launch button is labelled **`Run Multimodal Arbitration`**.

The verdict card is colour-coded by severity (`HARD_VETO` → error, `DEGRADE_TRACE_ONLY` → warning, approving verdicts → success, `NO_ACTION` → info) and the full rule matrix is available in an expander.

### Header navigation and document sub-pages

- Row 1 (`🏛️ Diploma`, `📄 Resume`, `💼 LinkedIn Profile`, `🎓 E-learning Portfolio`) opens the same external URLs as AURA-Grid in a **new tab** via `st.link_button`.
- Row 2 (`✉️ Cover letter`, `🔬 Research Proposal`, `🏗️ Architectural Blueprint`, `📝 Technical Statement`) routes to four internal document sub-pages, mirroring AURA-Grid's Ressources pattern (`st.session_state` + `?doc=` query parameter, with a `← Back to AURA-Learn` back button).
- The sub-pages render the matching PDF read **read-only** from [`Learnsource/`](Learnsource/), selected by case-insensitive filename matching; if a document is missing, the page shows a clear `st.warning` (expected filename + folder) instead of failing.

---

## Verbatim banner and footer

The exact legal notice displayed at the top of the page, in the sidebar and in the footer is:

```text
© 2026 EL FILALI SALAH ADDINE — Proprietary Academic Research Prototype (All Rights Reserved). Authorized exclusively for University of Tübingen for candidacy evaluation and doctoral supervision upon admission. Non-production synthetic demonstrator
```

---

## Limitations and non-goals

- **Non-production artefact.** This is a research and demonstration prototype, not a deployable product.
- **Synthetic data only.** All eye-tracking, video and trace signals are generated/hard-coded; there is no data ingestion path.
- **No empirical validation.** No study, no user testing and no statistical validation are claimed.
- **No personal data processing.** By construction there is no processing of personal data, therefore the GDPR is not applicable to this artefact.
- **No public deployment.** The application is not intended for public hosting or institutional rollout.
- **No clinical or pedagogical claims.** No therapeutic, diagnostic, medical or validated instructional effect is asserted.
- **Not a substitute for educators.** The kernel proposes adaptive actions; only a human decides and signs them.

---

## Research roadmap

The following directions are **not implemented** in this prototype and are listed purely as research perspectives:

- Real multimodal perception (calibrated eye-tracking, screen capture, interaction logs) under an approved ethics protocol.
- Empirical calibration and sensitivity analysis of the R1–R6 thresholds with domain experts.
- Controlled studies comparing deterministic arbitration against baseline heuristics in authentic learning tasks.
- Richer explainability surfaces (counterfactual rule traces, per-agent uncertainty reporting).
- Formal verification of kernel invariants (priority ordering, abstention completeness).
- Multi-learner and multi-session extensions with privacy-preserving aggregate analytics.

---

## License and citation

AURA-Learn is distributed under a **proprietary, source-available academic research license**. Read [`LICENSE`](LICENSE) before any use.

- **This is NOT open-source software.** Source availability is granted solely for academic evaluation and doctoral supervision; no public, community or permissive licensing scheme applies.
- Copying, redistribution, modification, sublicensing, commercial exploitation, external reuse and use as training data are prohibited without prior written consent of the author.
- Any breach terminates all rights immediately and requires destruction of every copy.

Suggested citation:

```bibtex
@misc{elfilalisalahaddine2026auralean,
  author       = {EL FILALI SALAH ADDINE},
  title        = {AURA-Learn: Multimodal Learning Analytics \& Adaptive Learning Environment Demonstrator},
  year         = {2026},
  note         = {Proprietary source-available academic research prototype; synthetic data only; non-production demonstrator. Prepared for the PhD AI in Education application (Hector Research Institute of Education Sciences and Psychology, University of Tübingen)},
  howpublished = {Source-available research artefact, not open source}
}
```

---

## Contact / author

**EL FILALI SALAH ADDINE** — author, sole copyright holder and licensor of AURA-Learn.
All licensing, permission and collaboration requests must be made in writing (see Section 10 of [`LICENSE`](LICENSE)).

---

© 2026 EL FILALI SALAH ADDINE — All Rights Reserved. Proprietary & source-available academic research prototype.
