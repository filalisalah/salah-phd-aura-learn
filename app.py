"""
AURA-Learn — Multimodal Learning Analytics & Adaptive Learning Environment Demonstrator
=========================================================================================

Proprietary Academic Research Prototype — All Rights Reserved.
Copyright (c) 2026 EL FILALI SALAH ADDINE.

License: proprietary. No redistribution, reuse, or commercial exploitation
without the prior written authorization of the rights holder.

⚠️ WARNING — 100% SYNTHETIC / NON-PRODUCTION
-----------------------------------------------------
All data handled by this application are hard-coded SYNTHETIC signals
(gaze, digital traces, latencies). No real capture, no camera, no
eye-tracker, no mandatory network call.
Academic demonstrator intended for the evaluation of a doctoral application
(PhD AI in Education — Hector Research Institute, University of Tübingen).

Three-layer architecture (demonstrator):

    Layer 1 — Bounded Multimodal Perception Swarm
        Three bounded agents (Attention_Gaze_Agent, Metacognitive_Trace_Agent,
        Pedagogical_Guardrail_Agent) produce bounded signals only.
        They NEVER decide.

    Layer 2 — Deterministic Pedagogical Arbitration Kernel
        Pure, deterministic Python engine, no LLM and no I/O: rules R1–R6
        evaluated in an explicit priority order. The only component allowed
        to "decide".

    Layer 3 — Glass-Box Educator Cockpit
        Human supervision (Accept / Overrule with mandatory justification)
        and an immutable append-only audit log, exportable to CSV in memory.

Execution:
    streamlit run app.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# `requests` is required for Live mode (optional). If absent, Live mode
# explicitly and silently falls back to the simulation.
try:  # pragma: no cover - depends on the runtime environment
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]


# =============================================================================
# 1. GLOBAL CONSTANTS — LEGAL NOTICE / IDENTIFIERS
# =============================================================================

# Top banner AND bottom footer — VERBATIM text (single line).
IP_NOTICE = "© 2026 EL FILALI SALAH ADDINE — Proprietary Academic Research Prototype (All Rights Reserved). Authorized exclusively for University of Tübingen for candidacy evaluation and doctoral supervision upon admission. Non-production synthetic demonstrator"

# -----------------------------------------------------------------------------
# 1b. DOCUMENT NAVIGATION — sub-pages fed by Learnsource/
# -----------------------------------------------------------------------------
# Resource folder actually present next to this script (READ ONLY).
LEARNSOURCE_DIR = Path(__file__).resolve().parent / "Learnsource"

# Session state key identifying the active document sub-page (or None).
DOC_VIEW_KEY = "active_document"

# Titles of the 4 document sub-pages (identical to the row-2 labels).
DOCUMENT_TITLES: Dict[str, str] = {
    "cover_letter": "✉️ Cover letter",
    "research_proposal": "🔬 Research Proposal",
    "architectural_blueprint": "🏗️ Architectural Blueprint",
    "technical_statement": "📝 Technical Statement",
}

# Button → expected substrings in the Learnsource/ file names.
# Substring order sets the priority (case-insensitive).
DOCUMENT_FILE_HINTS: Dict[str, List[str]] = {
    "cover_letter": ["cover"],
    "research_proposal": ["proposal", "research"],
    "architectural_blueprint": ["blueprint", "contribution", "roadmap"],
    "technical_statement": ["technical", "statement", "purpose"],
}

# Canonical identifiers of the bounded agents (Layer 1).
AGENT_ATTENTION = "Attention_Gaze_Agent"
AGENT_METACOGNITIVE = "Metacognitive_Trace_Agent"
AGENT_GUARDRAIL = "Pedagogical_Guardrail_Agent"
AGENT_ORDER: List[str] = [AGENT_ATTENTION, AGENT_METACOGNITIVE, AGENT_GUARDRAIL]

# Execution mode — exact required labels.
MODE_OFFLINE_LABEL = "Instant Offline Simulation"
MODE_LIVE_LABEL = "Live DeepSeek LLM"

# OpenAI-compatible endpoint (optional Live mode).
DEEPSEEK_ENDPOINT = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_TIMEOUT_S = 8

# Named thresholds of the R1–R6 deterministic kernel (no magic values in the code).
THRESHOLD_OFF_TASK_RATIO = 0.40          # R1: off-task saccade ratio
THRESHOLD_IDLE_TIME_S = 45.0             # R1: sustained idle pattern (seconds)
THRESHOLD_GAZE_DRIFT = 0.50              # R1: gaze drift score
THRESHOLD_TASK_COMPLEXITY = 0.70         # R2: task complexity
THRESHOLD_PROGRESS_STABILITY = 0.65      # R2: progress stability
THRESHOLD_MAX_DRIFT_DURATION_S = 8.0     # R2: brief diversion (seconds)
THRESHOLD_VETO_MIN_DRIFT_RATIO = 0.15    # R2: minimum drift for veto
THRESHOLD_ANSWER_REVISIONS = 4           # R4: answer revisions
THRESHOLD_SELF_CORRECTIONS = 3           # R4: self-correction events
THRESHOLD_LOW_LATENCY_S = 6.0            # R5: very low latency (seconds)
THRESHOLD_LOW_ACCURACY = 0.55            # R5: low accuracy
MIN_JUSTIFICATION_CHARS = 15             # Layer 3: minimum justification

# Human decisions exclusive to the cockpit (Layer 3).
DECISION_ACCEPT = "Accept Adaptive Action"
DECISION_OVERRULE = "Overrule & Suppress/Modify Intervention"


# =============================================================================
# 2. FROZEN SYNTHETIC SCENARIOS (hard-coded values → reproducibility)
# =============================================================================

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "1 - Mind Wandering & Gaze Drift Detection": {
        "id": "SCENARIO_MIND_WANDERING",
        "context": (
            "High off-task saccades and sustained idle pattern during a "
            "guided comprehension exercise."
        ),
        "supports_sensor_dropout": False,
        "signals": {
            # --- Synthetic eye-tracking (Layer 1, Attention agent) ---
            "sensor_online": True,
            "fixation_stability": 0.58,
            "off_task_saccade_ratio": 0.52,
            "gaze_drift_score": 0.71,
            "time_on_screen_s": 410.0,
            "drift_duration_s": 22.0,
            "task_complexity": 0.45,
            "progress_stability": 0.40,
            # --- Synthetic digital traces (Metacognitive agent) ---
            "idle_time_s": 96.0,
            "clicks_per_min": 9.0,
            "hint_requests": 1,
            "answer_revisions": 1,
            "self_correction_events": 0,
            "latency_per_item_s": 24.0,
            "accuracy": 0.62,
        },
    },
    "2 - Deep Flow Protection (Pedagogical Veto)": {
        "id": "SCENARIO_DEEP_FLOW",
        "context": (
            "Brief gaze diversion while solving a complex problem; "
            "stable progress to preserve."
        ),
        "supports_sensor_dropout": False,
        "signals": {
            "sensor_online": True,
            "fixation_stability": 0.88,
            "off_task_saccade_ratio": 0.16,
            # Brief but visible drift: the Attention agent flags it, without
            # reaching the R1 off-task saccade threshold.
            "gaze_drift_score": 0.62,
            "time_on_screen_s": 900.0,
            "drift_duration_s": 4.5,
            "task_complexity": 0.86,
            "progress_stability": 0.74,
            "idle_time_s": 12.0,
            "clicks_per_min": 4.5,
            "hint_requests": 0,
            "answer_revisions": 1,
            "self_correction_events": 1,
            "latency_per_item_s": 41.0,
            "accuracy": 0.81,
        },
    },
    "3 - Sensor Dropout / Graceful Degradation": {
        "id": "SCENARIO_SENSOR_DROPOUT",
        "context": (
            "Sensor instability: the eye-tracker / video stream may time out. "
            "The system must gracefully degrade to the digital trace."
        ),
        "supports_sensor_dropout": True,
        "signals": {
            # "Healthy" signals when the sensor is available (checkbox unchecked).
            "sensor_online": True,
            "fixation_stability": 0.82,
            "off_task_saccade_ratio": 0.10,
            "gaze_drift_score": 0.12,
            "time_on_screen_s": 600.0,
            "drift_duration_s": 2.0,
            "task_complexity": 0.40,
            "progress_stability": 0.60,
            "idle_time_s": 8.0,
            "clicks_per_min": 14.0,
            "hint_requests": 0,
            "answer_revisions": 1,
            "self_correction_events": 1,
            "latency_per_item_s": 30.0,
            "accuracy": 0.70,
        },
    },
}


# =============================================================================
# 3. LAYER 1 — BOUNDED AGENTS (synthetic signals only)
# =============================================================================

def attention_agent(signals: Dict[str, Any]) -> Dict[str, Any]:
    """Bounded visual-attention agent: proposes a status, does not decide."""
    online = bool(signals.get("sensor_online", True))
    off_task = float(signals.get("off_task_saccade_ratio", 0.0))
    drift = float(signals.get("gaze_drift_score", 0.0))
    fixation = float(signals.get("fixation_stability", 0.0))
    on_screen = float(signals.get("time_on_screen_s", 0.0))

    if not online:
        status = "SENSOR_OFFLINE"
        proposal = "No visual proposal: sensor offline."
        trace_step = "Eye-tracker stream unavailable: no visual verdict produced."
    elif off_task >= THRESHOLD_OFF_TASK_RATIO or drift >= THRESHOLD_GAZE_DRIFT:
        status = "DRIFT_SUSPECTED"
        proposal = (
            "Suggests the kernel evaluate gentle, non-intrusive scaffolding "
            "(no decision made here)."
        )
        trace_step = (
            f"off-task={off_task:.2f} ≥ {THRESHOLD_OFF_TASK_RATIO:.2f} "
            f"or drift={drift:.2f} ≥ {THRESHOLD_GAZE_DRIFT:.2f} → drift suspected."
        )
    else:
        status = "NORMAL"
        proposal = "No attentional intervention proposed."
        trace_step = (
            f"off-task={off_task:.2f} < {THRESHOLD_OFF_TASK_RATIO:.2f} and "
            f"drift={drift:.2f} < {THRESHOLD_GAZE_DRIFT:.2f} → attention stable."
        )

    return {
        "agent": AGENT_ATTENTION,
        "status": status,
        "proposal": proposal,
        "metrics": {
            "fixation_stability": fixation,
            "off_task_saccade_ratio": off_task,
            "gaze_drift_score": drift,
            "time_on_screen_s": on_screen,
        },
        "trace": trace_step,
    }


def metacognitive_agent(signals: Dict[str, Any]) -> Dict[str, Any]:
    """Bounded digital-trace agent: proposes a status, does not decide."""
    idle = float(signals.get("idle_time_s", 0.0))
    clicks = float(signals.get("clicks_per_min", 0.0))
    hints = int(signals.get("hint_requests", 0))
    revisions = int(signals.get("answer_revisions", 0))
    corrections = int(signals.get("self_correction_events", 0))

    if idle >= THRESHOLD_IDLE_TIME_S:
        status = "IDLE_PATTERN"
        proposal = (
            "Flags a sustained idle pattern: gentle scaffolding to be arbitrated "
            "by the deterministic kernel."
        )
        trace_step = (
            f"idle={idle:.0f}s ≥ {THRESHOLD_IDLE_TIME_S:.0f}s → idle pattern."
        )
    else:
        status = "ENGAGED"
        proposal = "No metacognitive intervention proposed."
        trace_step = (
            f"idle={idle:.0f}s < {THRESHOLD_IDLE_TIME_S:.0f}s, "
            f"{clicks:.1f} clicks/min → sustained engagement."
        )

    return {
        "agent": AGENT_METACOGNITIVE,
        "status": status,
        "proposal": proposal,
        "metrics": {
            "idle_time_s": idle,
            "clicks_per_min": clicks,
            "hint_requests": hints,
            "answer_revisions": revisions,
            "self_correction_events": corrections,
        },
        "trace": trace_step,
    }


def guardrail_precheck(signals: Dict[str, Any]) -> Dict[str, Any]:
    """Pedagogical guardrail agent: bounded pre-check, no final decision.

    The guardrail verdict is a PROPOSAL. The R1–R6 kernel remains the only
    component authorized to produce the final verdict.
    """
    online = bool(signals.get("sensor_online", True))
    off_task = float(signals.get("off_task_saccade_ratio", 0.0))
    complexity = float(signals.get("task_complexity", 0.0))
    progress = float(signals.get("progress_stability", 0.0))
    drift_duration = float(signals.get("drift_duration_s", 0.0))

    if not online:
        verdict = "DEGRADED"
        motive = "Sensor stream lost: degradation to the digital trace."
    elif (
        complexity >= THRESHOLD_TASK_COMPLEXITY
        and progress >= THRESHOLD_PROGRESS_STABILITY
        and drift_duration <= THRESHOLD_MAX_DRIFT_DURATION_S
        and off_task >= THRESHOLD_VETO_MIN_DRIFT_RATIO
    ):
        verdict = "VETO"
        motive = "Deep cognitive processing in progress: do not interrupt."
    elif off_task >= THRESHOLD_OFF_TASK_RATIO:
        verdict = "APPROVE"
        motive = "Sustained drift: gentle non-intrusive scaffolding acceptable."
    else:
        verdict = "APPROVE"
        motive = "No pedagogical risk detected on the bounded signals."

    return {
        "agent": AGENT_GUARDRAIL,
        "verdict": verdict,
        "motive": motive,
        "trace": f"Guardrail — {motive}",
    }


# =============================================================================
# 4. LAYER 2 — DETERMINISTIC ARBITRATION KERNEL R1–R6 (pure Python, zero LLM)
# =============================================================================

# Human-readable metadata for each rule (Layer 2 / matrix display).
RULES_META: List[Dict[str, str]] = [
    {
        "id": "R1",
        "verdict": "APPROVE_GENTLE_SCAFFOLD",
        "condition": "Gaze drift + sustained idle pattern",
        "thresholds": (
            f"off_task_ratio ≥ {THRESHOLD_OFF_TASK_RATIO:.2f}; "
            f"idle_time ≥ {THRESHOLD_IDLE_TIME_S:.0f}s; "
            f"gaze_drift ≥ {THRESHOLD_GAZE_DRIFT:.2f}"
        ),
    },
    {
        "id": "R2",
        "verdict": "HARD_VETO",
        "condition": "Deep flow detected + brief drift below the duration threshold",
        "thresholds": (
            f"task_complexity ≥ {THRESHOLD_TASK_COMPLEXITY:.2f}; "
            f"progress_stability ≥ {THRESHOLD_PROGRESS_STABILITY:.2f}; "
            f"drift_duration ≤ {THRESHOLD_MAX_DRIFT_DURATION_S:.0f}s; "
            f"off_task_ratio ≥ {THRESHOLD_VETO_MIN_DRIFT_RATIO:.2f}"
        ),
    },
    {
        "id": "R3",
        "verdict": "DEGRADE_TRACE_ONLY",
        "condition": "Loss of the eye-tracker / video stream",
        "thresholds": "sensor_online == False",
    },
    {
        "id": "R4",
        "verdict": "APPROVE_SUPPORT_HINT",
        "condition": "Cognitive load / distress (repeated error revisions)",
        "thresholds": (
            f"answer_revisions ≥ {THRESHOLD_ANSWER_REVISIONS}; "
            f"self_corrections ≥ {THRESHOLD_SELF_CORRECTIONS}"
        ),
    },
    {
        "id": "R5",
        "verdict": "APPROVE_REFLECTION_PROMPT",
        "condition": "Overconfidence / haste",
        "thresholds": (
            f"latency_per_item ≤ {THRESHOLD_LOW_LATENCY_S:.0f}s; "
            f"accuracy ≤ {THRESHOLD_LOW_ACCURACY:.2f}"
        ),
    },
    {
        "id": "R6",
        "verdict": "NO_ACTION",
        "condition": "Normal signal / no trigger",
        "thresholds": "no R1–R5 rule satisfied (abstention)",
    },
]

# Explicit priority order: first triggered rule = final verdict.
RULE_PRIORITY: List[str] = ["R3", "R2", "R1", "R4", "R5", "R6"]

VERDICT_LABELS: Dict[str, str] = {
    "APPROVE_GENTLE_SCAFFOLD": (
        "Propose gentle, non-intrusive scaffolding (discreet hint, guided pause)."
    ),
    "HARD_VETO": (
        "Pedagogical VETO: do not interrupt deep cognitive processing."
    ),
    "DEGRADE_TRACE_ONLY": (
        "Gracefully degrade to the digital trace only (TRACE_ONLY mode)."
    ),
    "APPROVE_SUPPORT_HINT": (
        "Propose a targeted support hint given the detected cognitive load."
    ),
    "APPROVE_REFLECTION_PROMPT": (
        "Propose a metacognitive reflection prompt before continuing."
    ),
    "NO_ACTION": "Status quo: no adaptive intervention (abstention).",
}


def evaluate_rules(signals: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates R1–R6 in pure Python and returns the deterministic verdict.

    Pure function: no I/O, no LLM, no randomness. The priority order is
    explicit (``RULE_PRIORITY``): the first triggered rule wins.
    """
    sensor_online = bool(signals.get("sensor_online", True))
    off_task = float(signals.get("off_task_saccade_ratio", 0.0))
    idle = float(signals.get("idle_time_s", 0.0))
    drift = float(signals.get("gaze_drift_score", 0.0))
    complexity = float(signals.get("task_complexity", 0.0))
    progress = float(signals.get("progress_stability", 0.0))
    drift_duration = float(signals.get("drift_duration_s", 0.0))
    revisions = int(signals.get("answer_revisions", 0))
    corrections = int(signals.get("self_correction_events", 0))
    latency = float(signals.get("latency_per_item_s", 99.0))
    accuracy = float(signals.get("accuracy", 1.0))

    # R1 — drift + sustained idle (requires an active sensor).
    r1 = (
        sensor_online
        and off_task >= THRESHOLD_OFF_TASK_RATIO
        and idle >= THRESHOLD_IDLE_TIME_S
        and drift >= THRESHOLD_GAZE_DRIFT
    )
    # R2 — deep flow + brief drift (requires an active sensor).
    r2 = (
        sensor_online
        and complexity >= THRESHOLD_TASK_COMPLEXITY
        and progress >= THRESHOLD_PROGRESS_STABILITY
        and drift_duration <= THRESHOLD_MAX_DRIFT_DURATION_S
        and off_task >= THRESHOLD_VETO_MIN_DRIFT_RATIO
    )
    # R3 — sensor stream loss.
    r3 = not sensor_online
    # R4 — cognitive load / distress.
    r4 = revisions >= THRESHOLD_ANSWER_REVISIONS and corrections >= THRESHOLD_SELF_CORRECTIONS
    # R5 — overconfidence / haste.
    r5 = latency <= THRESHOLD_LOW_LATENCY_S and accuracy <= THRESHOLD_LOW_ACCURACY
    # R6 — no trigger.
    r6 = not any([r1, r2, r3, r4, r5])

    triggered: Dict[str, bool] = {
        "R1": r1,
        "R2": r2,
        "R3": r3,
        "R4": r4,
        "R5": r5,
        "R6": r6,
    }

    # Builds the detailed evaluation for EACH rule (Layer 2 display).
    evaluations: List[Dict[str, Any]] = []
    for meta in RULES_META:
        rule_id = meta["id"]
        evaluations.append(
            {
                "Rule": rule_id,
                "Condition": meta["condition"],
                "Thresholds": meta["thresholds"],
                "State": "Triggered" if triggered[rule_id] else "Not triggered",
                "Proposed Verdict": meta["verdict"],
            }
        )

    # Selection by explicit priority.
    selected_id = next(rule_id for rule_id in RULE_PRIORITY if triggered[rule_id])
    selected_meta = next(m for m in RULES_META if m["id"] == selected_id)
    final_verdict = selected_meta["verdict"]

    # Step-by-step arbitration trace (sequence of strings).
    trace: List[str] = []
    for rule_id in RULE_PRIORITY:
        if rule_id == "R6":
            continue
        state = "TRIGGERED" if triggered[rule_id] else "not triggered"
        trace.append(f"Evaluation {rule_id} ({RULES_META[[m['id'] for m in RULES_META].index(rule_id)]['condition']}) → {state}.")
    trace.append(
        "Priority selection R3 > R2 > R1 > R4 > R5 > R6 → "
        f"selected rule: {selected_id}."
    )
    trace.append(
        f"Deterministic final verdict: {final_verdict} — {VERDICT_LABELS[final_verdict]}"
    )

    return {
        "rule_id": selected_id,
        "verdict": final_verdict,
        "reason": VERDICT_LABELS[final_verdict],
        "evaluations": evaluations,
        "trace": trace,
        "signals": dict(signals),
    }


# =============================================================================
# 5. OPTIONAL LIVE MODE — DeepSeek (never used by the R1–R6 kernel)
# =============================================================================

def request_live_narrative(
    api_key: str, scenario_label: str, verdict: Dict[str, Any]
) -> Dict[str, Any]:
    """Attempts a DeepSeek narrative. NEVER alters the deterministic verdict.

    Returns ``{"ok": bool, "text": str, "error": str}``. Any error is caught
    and surfaced to the UI ("fallback to deterministic simulation").
    The API key is never logged nor written to disk.
    """
    if not api_key.strip():
        return {"ok": False, "text": "", "error": "API key missing."}
    if requests is None:
        return {
            "ok": False,
            "text": "",
            "error": "Module 'requests' unavailable in this environment.",
        }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a bounded pedagogical explainer. You must not "
                    "alter or contest the deterministic verdict. Explain in "
                    "3 sentences, in English, why the given verdict is "
                    "pedagogically defensible for a synthetic learning scenario."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Scenario: {scenario_label}\n"
                    f"Triggered rule: {verdict['rule_id']}\n"
                    f"Final verdict: {verdict['verdict']}\n"
                    f"Kernel rationale: {verdict['reason']}"
                ),
            },
        ],
        "temperature": 0.0,
        "max_tokens": 220,
    }

    try:
        response = requests.post(
            DEEPSEEK_ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=DEEPSEEK_TIMEOUT_S,
        )
        response.raise_for_status()
        data = response.json()
        text = str(data["choices"][0]["message"]["content"]).strip()
        return {"ok": True, "text": text, "error": ""}
    except Exception as exc:  # network error / timeout / parsing → explicit fallback
        return {
            "ok": False,
            "text": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


# =============================================================================
# 6. UTILITIES & SESSION STATE
# =============================================================================

def utc_now_iso() -> str:
    """Returns the ISO-8601 UTC timestamp, e.g. 2026-11-24T20:44:00Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def init_session_state() -> None:
    """Idempotent session-state initialization (no state outside the session)."""
    defaults: Dict[str, Any] = {
        "audit_log": [],            # immutable append-only audit log
        "last_verdict": None,       # latest kernel verdict
        "last_run_key": None,       # configuration key of the last run
        "live_notice": "",          # Live mode fallback message
        "live_narrative": "",       # LLM narrative (never decisive)
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_scenario_signals(scenario_key: str, sensor_dropout: bool) -> Dict[str, Any]:
    """Returns a frozen copy of the scenario's synthetic signals."""
    signals = dict(SCENARIOS[scenario_key]["signals"])
    if scenario_key.startswith("3") and sensor_dropout:
        # Simulation of the eye-tracker / video stream loss.
        signals["sensor_online"] = False
    return signals


def append_audit_entry(
    scenario_label: str,
    mode_label: str,
    rule_id: str,
    machine_verdict: str,
    human_decision: str,
    justification: str,
) -> Dict[str, Any]:
    """Appends an immutable, timestamped entry to the audit log (append-only)."""
    log: List[Dict[str, Any]] = st.session_state.setdefault("audit_log", [])
    entry = {
        "entry_id": len(log) + 1,
        "timestamp_utc": utc_now_iso(),
        "scenario": scenario_label,
        "mode": mode_label,
        "rule_id": rule_id,
        "machine_verdict": machine_verdict,
        "human_decision": human_decision,
        "justification": justification,
    }
    log.append(entry)
    return entry


def audit_log_dataframe(entries: List[Dict[str, Any]]) -> pd.DataFrame:
    """Builds the display DataFrame for the log (read-only index)."""
    rows = [
        {
            "Entry": f"#{entry['entry_id']}",
            "Timestamp (UTC)": entry["timestamp_utc"],
            "Scenario": entry["scenario"],
            "Execution Mode": entry["mode"],
            "Rule": entry["rule_id"],
            "Machine Verdict": entry["machine_verdict"],
            "Human Decision": entry["human_decision"],
            "Justification": entry["justification"],
        }
        for entry in entries
    ]
    return pd.DataFrame(rows)


# =============================================================================
# 7. UI SHELL — CSS SHARED WITH THE AURA-GRID REFERENCE
# =============================================================================

def inject_global_css() -> None:
    """Injects the palette, spacing and blinking animations."""
    st.markdown(
        """
        <style>
        /* AURA-Grid reference palette */
        :root {
            --aura-pink: #c2185b;
            --aura-pink-dark: #880e4f;
            --aura-pink-darker: #ad1457;
            --aura-green: #1b8a3a;
            --aura-green-bright: #00e676;
            --aura-red: #c62828;
            --aura-grey: #6b7280;
        }

        /* Main container: reduces the empty band at the top */
        .block-container,
        [data-testid="stMainBlockContainer"] {
            padding-top: 2.25rem !important;
            padding-bottom: 0 !important;
        }

        header[data-testid="stHeader"] {
            height: 2rem;
            min-height: 2rem;
            background: transparent;
        }

        [data-testid="stAppViewContainer"] > .main {
            padding-top: 0 !important;
        }

        /* Hides the Streamlit Cloud actions (deploy / share) */
        [data-testid="stToolbarActions"],
        [data-testid="stAppDeployButton"],
        [data-testid="stStatusWidget"] {
            display: none !important;
        }

        /* --- Download buttons: dark pink + blinking green arrow */
        [data-testid="stDownloadButton"] button {
            background-color: #c2185b !important;
            border: 1px solid #c2185b !important;
            color: #ffffff !important;
            box-shadow: 0 2px 10px rgba(194, 24, 91, 0.35);
        }

        [data-testid="stDownloadButton"] button:hover {
            background-color: #ad1457 !important;
            border-color: #ad1457 !important;
            color: #ffffff !important;
            box-shadow: 0 3px 14px rgba(173, 20, 87, 0.5);
        }

        [data-testid="stDownloadButton"] button p {
            color: #ffffff !important;
        }

        [data-testid="stDownloadButton"] button p::before {
            content: "\\2193";
            display: inline-block;
            margin-right: 0.5rem;
            color: #00e676;
            font-size: 1.2em;
            font-weight: 900;
            line-height: 1;
            text-shadow: 0 0 6px rgba(0, 230, 118, 0.9);
            animation: dl-arrow-blink 1s ease-in-out infinite;
        }

        @keyframes dl-arrow-blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.1; }
        }

        /* --- "Execution Mode" label: enlarged, WITHOUT blinking -----------
           Scope deliberately narrowed to the radio widget label ONLY
           (`[data-testid="stWidgetLabel"]`). The former selector
           `.st-key-execution_mode label p` descended inside the
           `radiogroup` and therefore made both options
           "Instant Offline Simulation" and "Live DeepSeek LLM" blink.
           The AURA-Grid reference blinks NEITHER this title NOR its
           options: only the typographic styling is kept. */
        .st-key-execution_mode [data-testid="stWidgetLabel"] p {
            font-size: 1.4rem !important;
            font-weight: 800 !important;
            line-height: 1.2 !important;
        }

        /* Explicit guardrail (robust across Streamlit versions): no
           animation / variable opacity may reach the `radiogroup` content
           (option labels + their `p`), including via a broad
           `.stRadio label` selector. */
        [data-testid="stSidebar"] .st-key-execution_mode [role="radiogroup"],
        [data-testid="stSidebar"] .st-key-execution_mode [role="radiogroup"] label,
        [data-testid="stSidebar"] .st-key-execution_mode [role="radiogroup"] p,
        [data-testid="stSidebar"] .st-key-execution_mode .stRadio label p {
            animation: none !important;
            opacity: 1 !important;
        }

        /* --- "Choose a Scenario" label: enlarged + blinking --------------- */
        .st-key-scenario_select [data-testid="stWidgetLabel"] p,
        .st-key-scenario_select label p {
            font-size: 1.4rem !important;
            font-weight: 800 !important;
            line-height: 1.2 !important;
            animation: scenario-label-blink 1.1s ease-in-out infinite;
        }

        @keyframes scenario-label-blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.15; }
        }

        /* VETO POWER badge of the guardrail agent */
        .aura-veto-badge {
            display: inline-block;
            background: #c62828;
            color: #ffffff;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.4px;
        }

        @media (prefers-reduced-motion: reduce) {
            [data-testid="stDownloadButton"] button p::before,
            .st-key-scenario_select [data-testid="stWidgetLabel"] p,
            .st-key-scenario_select label p {
                animation: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# 8. UI — HEADER (8 BUTTONS), DOCUMENT SUB-PAGES, FOOTER
# =============================================================================

# 8 header buttons, two rows of four — labels, layout, targets and
# mechanism IDENTICAL to the AURA-Grid reference.
# Each entry: (key, label, type, target)
#   type == "external" -> absolute link opened in a NEW TAB
#   type == "document" -> internal sub-page (target = document key)
HEADER_ROWS: List[List[tuple]] = [
    [
        ("diploma", "🏛️ Diploma", "external", "https://e-learning-labo.web.app/diplome"),
        ("resume", "📄 Resume", "external", "https://e-learning-labo.web.app/cv"),
        (
            "linkedin",
            "💼 LinkedIn Profile",
            "external",
            "https://www.linkedin.com/in/filali-salah",
        ),
        (
            "elearning",
            "🎓 E-learning Portfolio",
            "external",
            "https://e-learning-labo.web.app/",
        ),
    ],
    [
        ("cover_letter", "✉️ Cover letter", "document", "cover_letter"),
        (
            "research_proposal",
            "🔬 Research Proposal",
            "document",
            "research_proposal",
        ),
        (
            "architectural_blueprint",
            "🏗️ Architectural Blueprint",
            "document",
            "architectural_blueprint",
        ),
        (
            "technical_statement",
            "📝 Technical Statement",
            "document",
            "technical_statement",
        ),
    ],
]


def _list_learnsource_files() -> List[Path]:
    """Deterministically lists the files in Learnsource/ (read only)."""
    if not LEARNSOURCE_DIR.is_dir():
        return []
    try:
        return sorted(
            (p for p in LEARNSOURCE_DIR.iterdir() if p.is_file()),
            key=lambda p: p.name.lower(),
        )
    except OSError:  # pragma: no cover - defensive, never blocking for the UI
        return []


def resolve_document_file(doc_key: str) -> Optional[Path]:
    """Resolves the actual file for a button in Learnsource/ (case-insensitive).

    Matching by substrings in the order of ``DOCUMENT_FILE_HINTS``: the first
    file whose (lowercased) name contains an expected substring is kept.
    Returns ``None`` when nothing matches, which triggers the graceful
    fallback of the sub-page (no exception raised).
    """
    hints = DOCUMENT_FILE_HINTS.get(doc_key, [])
    if not hints:
        return None
    files = _list_learnsource_files()
    for hint in hints:
        for path in files:
            if hint in path.name.lower():
                return path
    return None


def _open_document(doc_key: str) -> None:
    """Callback: opens a document sub-page (session state + ?doc=)."""
    st.session_state[DOC_VIEW_KEY] = doc_key
    st.query_params["doc"] = doc_key


def _close_document() -> None:
    """Callback: back to the AURA-Learn home page."""
    st.session_state[DOC_VIEW_KEY] = None
    st.query_params.pop("doc", None)


def render_header_links() -> None:
    """Renders the 8 header buttons as two rows of four columns.

    Row 1: ``st.link_button`` -> same external URLs as the reference,
    opened natively in a NEW TAB (default behavior).
    Row 2: ``st.button`` with a routing callback to the sub-page.
    """
    for row in HEADER_ROWS:
        columns = st.columns(len(row))
        for column, (key, label, kind, target) in zip(columns, row):
            with column:
                if kind == "external":
                    st.link_button(label, target, use_container_width=True)
                else:
                    st.button(
                        label,
                        key=f"header_btn_{key}",
                        on_click=_open_document,
                        args=(target,),
                        use_container_width=True,
                    )


def render_document_page(doc_key: str) -> None:
    """Displays a document sub-page (same structure as the reference).

    Order: back button, title, embedded document (``st.pdf``) or explicit
    warning if the file is missing.
    """
    title = DOCUMENT_TITLES.get(doc_key, "Document")
    hints = DOCUMENT_FILE_HINTS.get(doc_key, [])

    st.button(
        "← Back to AURA-Learn",
        on_click=_close_document,
        key=f"back_doc_{doc_key}",
    )
    st.title(title)

    file_path = resolve_document_file(doc_key)
    if file_path is None:
        # Graceful fallback: document missing -> warning, no crash.
        expected = " / ".join(f'"{h}"' for h in hints) or "—"
        st.warning(
            "Document unavailable: no matching file "
            f"({expected}) was found in the "
            f"aura-learn/Learnsource/ folder ({LEARNSOURCE_DIR})."
        )
        return

    filename = file_path.name
    try:
        pdf_bytes = file_path.read_bytes()
    except OSError as exc:
        st.warning(f'Unable to read the document "{filename}": {exc}')
        return

    # Primary action: native download (identical to the reference).
    st.download_button(
        f"Download {filename}",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        use_container_width=True,
        key=f"download_doc_{doc_key}",
    )

    # Embedded preview through ``st.pdf`` only. A data-URI iframe
    # ("data:application/pdf;base64,...") must never be reintroduced here:
    # Chromium/Edge block PDFs embedded that way ("page blocked").
    pdf_viewer = getattr(st, "pdf", None)
    if pdf_viewer is None:
        st.warning(
            "Inline PDF preview is unavailable: this Streamlit build has no "
            "`st.pdf` (provided by `streamlit-pdf`). Install "
            "`streamlit[pdf]>=1.67` (see aura-learn/requirements.txt) to "
            "enable it. The download button above still works."
        )
        return

    try:
        pdf_viewer(pdf_bytes, height=900, alt=f"Preview of {filename}")
    except Exception as exc:
        st.warning(
            f"Unable to render the PDF preview ({type(exc).__name__}): {exc}"
        )


def render_top_notice() -> None:
    """Verbatim legal notice at the top of the page (rendered via ``st.caption``)."""
    st.caption(IP_NOTICE)


def render_footer() -> None:
    """Footer: separator + verbatim legal notice (like the reference)."""
    st.divider()
    st.caption(IP_NOTICE)


# =============================================================================
# 9. UI — SIDEBAR (Execution Mode, Scenario, launch)
# =============================================================================

def render_sidebar() -> Dict[str, Any]:
    """Renders the sidebar controls and returns the active configuration."""
    # --- Execution Mode (first, above the scenario group) ------------------
    mode_label = st.sidebar.radio(
        "Execution Mode",
        options=[MODE_OFFLINE_LABEL, MODE_LIVE_LABEL],
        index=0,  # Instant Offline Simulation selected BY DEFAULT
        key="execution_mode",
        help=(
            "Offline: frozen synthetic signals and deterministic kernel "
            "(reproducible). Live: optional DeepSeek narrative, with no effect "
            "on the R1–R6 verdict."
        ),
    )

    run_clicked = st.sidebar.button(
        "Run Multimodal Arbitration",
        type="primary",
        use_container_width=True,
        key="run_arbitration_button",
        help=(
            "Triggers the full chain: bounded perception → deterministic "
            "R1–R6 kernel → adaptive proposal → educator cockpit."
        ),
    )

    api_key = ""
    if mode_label == MODE_LIVE_LABEL:
        api_key = st.sidebar.text_input(
            "DeepSeek API key",
            type="password",
            key="deepseek_api_key",
            help=(
                "Used only in session memory. Never written to disk, never "
                "logged, never included in the audit log."
            ),
        )

    st.sidebar.markdown("---")

    # --- Scenario (below the execution mode) ---------------------------------
    scenario_key = st.sidebar.selectbox(
        "Choose a Scenario",
        options=list(SCENARIOS.keys()),
        index=0,
        key="scenario_select",
    )
    scenario = SCENARIOS[scenario_key]
    st.sidebar.caption(f"Context: {scenario['context']}")

    sensor_dropout = False
    if scenario["supports_sensor_dropout"]:
        sensor_dropout = st.sidebar.checkbox(
            "Simulate Eye-Tracker / Video stream timeout",
            value=False,
            key="sensor_dropout_active",
            help=(
                "Forces the loss of the sensor stream to demonstrate graceful "
                "degradation to the digital trace (DEGRADE_TRACE_ONLY verdict)."
            ),
        )
    else:
        st.sidebar.checkbox(
            "Simulate Eye-Tracker / Video stream timeout",
            value=False,
            key="sensor_dropout_disabled",
            disabled=True,
            help="Available only for scenario 3.",
        )

    st.sidebar.divider()
    st.sidebar.caption(IP_NOTICE)

    return {
        "mode_label": mode_label,
        "scenario_key": scenario_key,
        "sensor_dropout": sensor_dropout,
        "api_key": api_key,
        "run": run_clicked,
    }


# =============================================================================
# 10. UI — LAYER 1: AGENT CARDS
# =============================================================================

STATUS_COLOR: Dict[str, str] = {
    "NORMAL": "#1b8a3a",
    "DRIFT_SUSPECTED": "#c62828",
    "SENSOR_OFFLINE": "#6b7280",
    "ENGAGED": "#1b8a3a",
    "IDLE_PATTERN": "#c2185b",
    "APPROVE": "#1b8a3a",
    "VETO": "#c62828",
    "DEGRADED": "#c2185b",
}


def render_attention_card(result: Dict[str, Any]) -> None:
    """Attention_Gaze_Agent card."""
    st.markdown(f"#### {AGENT_ATTENTION}")
    color = STATUS_COLOR.get(result["status"], "#6b7280")
    st.markdown(
        f"<span style='color:{color};font-weight:700;font-size:1.05rem;'>"
        f"{result['status']}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("**Proposal**")
    st.write(result["proposal"])
    metrics = result["metrics"]
    st.metric("Fixation stability", f"{metrics['fixation_stability']:.2f}")
    st.metric("Off-task saccade ratio", f"{metrics['off_task_saccade_ratio']:.2f}")
    st.metric("Gaze drift score", f"{metrics['gaze_drift_score']:.2f}")
    st.metric("Time on screen", f"{metrics['time_on_screen_s']:.0f} s")
    with st.expander("Mini-trace"):
        st.write(result["trace"])


def render_metacognitive_card(result: Dict[str, Any]) -> None:
    """Metacognitive_Trace_Agent card."""
    st.markdown(f"#### {AGENT_METACOGNITIVE}")
    color = STATUS_COLOR.get(result["status"], "#6b7280")
    st.markdown(
        f"<span style='color:{color};font-weight:700;font-size:1.05rem;'>"
        f"{result['status']}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("**Proposal**")
    st.write(result["proposal"])
    metrics = result["metrics"]
    st.metric("Idle time", f"{metrics['idle_time_s']:.0f} s")
    st.metric("Clicks / min", f"{metrics['clicks_per_min']:.1f}")
    st.metric("Hint requests", str(metrics["hint_requests"]))
    st.metric("Answer revisions", str(metrics["answer_revisions"]))
    st.metric("Self-corrections", str(metrics["self_correction_events"]))
    with st.expander("Mini-trace"):
        st.write(result["trace"])


def render_guardrail_card(result: Dict[str, Any]) -> None:
    """Pedagogical_Guardrail_Agent card (VETO POWER badge)."""
    st.markdown(f"#### {AGENT_GUARDRAIL}")
    st.markdown(
        "<span class='aura-veto-badge'>VETO POWER</span>",
        unsafe_allow_html=True,
    )
    color = STATUS_COLOR.get(result["verdict"], "#6b7280")
    st.markdown(
        f"<span style='color:{color};font-weight:700;font-size:1.05rem;'>"
        f"{result['verdict']}</span>",
        unsafe_allow_html=True,
    )
    st.caption("Bounded proposal — the R1–R6 kernel remains the decision-maker.")
    st.markdown("**Motive**")
    st.write(result["motive"])
    with st.expander("Mini-trace"):
        st.write(result["trace"])


def render_layer1(
    attention: Dict[str, Any],
    metacognitive: Dict[str, Any],
    guardrail: Dict[str, Any],
) -> None:
    """Layer 1 — three columns of bounded agents."""
    st.subheader("Layer 1 — Bounded Multimodal Perception Swarm")
    columns = st.columns(3)
    with columns[0]:
        render_attention_card(attention)
    with columns[1]:
        render_metacognitive_card(metacognitive)
    with columns[2]:
        render_guardrail_card(guardrail)


# =============================================================================
# 11. UI — LAYER 2: R1–R6 KERNEL (matrix + trace)
# =============================================================================

RULE_BADGE: Dict[str, str] = {
    "Triggered": "✅ Triggered",
    "Not triggered": "— Not triggered",
}


def render_layer2(verdict: Dict[str, Any]) -> None:
    """Layer 2 — rule matrix, selected rule and arbitration trace."""
    st.subheader("Layer 2 — Deterministic Pedagogical Arbitration Kernel (R1–R6)")

    evaluations = [dict(row) for row in verdict["evaluations"]]
    for row in evaluations:
        row["State"] = RULE_BADGE.get(row["State"], row["State"])
    st.dataframe(
        pd.DataFrame(evaluations),
        use_container_width=True,
        hide_index=True,
    )

    selected_rule = verdict["rule_id"]
    severity = {
        "HARD_VETO": "error",
        "DEGRADE_TRACE_ONLY": "warning",
        "APPROVE_GENTLE_SCAFFOLD": "success",
        "APPROVE_SUPPORT_HINT": "success",
        "APPROVE_REFLECTION_PROMPT": "success",
        "NO_ACTION": "info",
    }.get(verdict["verdict"], "info")

    message = (
        f"**Triggered rule: `{selected_rule}`**  \n"
        f"**Final verdict: `{verdict['verdict']}`**  \n"
        f"**Proposed action:** {verdict['reason']}"
    )
    if severity == "error":
        st.error(message)
    elif severity == "warning":
        st.warning(message)
    elif severity == "success":
        st.success(message)
    else:
        st.info(message)

    st.markdown("**Arbitration trace (glass-box)**")
    for step in verdict["trace"]:
        st.write(f"- {step}")

    with st.expander("Rule Matrix R1–R6"):
        st.dataframe(
            pd.DataFrame(RULES_META).rename(
                columns={
                    "id": "Rule ID",
                    "condition": "Condition",
                    "thresholds": "Thresholds",
                    "verdict": "Verdict",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )


# =============================================================================
# 12. UI — LAYER 3: GLASS-BOX COCKPIT + AUDIT LOG
# =============================================================================

def render_layer3(verdict: Dict[str, Any], scenario_label: str, mode_label: str) -> None:
    """Layer 3 — human supervision and immutable append-only audit log."""
    st.subheader("Layer 3 — Glass-Box Educator Cockpit")

    st.markdown("**Adaptive action proposed by the kernel**")
    st.info(
        f"Rule `{verdict['rule_id']}` → `{verdict['verdict']}`: {verdict['reason']}"
    )

    with st.form("glass_box_cockpit_form", clear_on_submit=False):
        decision = st.radio(
            "Supervision decision",
            options=[DECISION_ACCEPT, DECISION_OVERRULE],
            index=0,
            key="cockpit_decision",
        )
        justification = st.text_area(
            "Pedagogical justification "
            f"(mandatory when overruling — min. {MIN_JUSTIFICATION_CHARS} characters)",
            placeholder="Explain the pedagogical rationale for your decision...",
            key="cockpit_justification",
        )
        submitted = st.form_submit_button(
            "Commit Decision to Immutable Audit Log",
            type="primary",
        )

    if submitted:
        stripped = justification.strip()
        if decision == DECISION_OVERRULE and len(stripped) < MIN_JUSTIFICATION_CHARS:
            # Blocking validation: no recording until the pedagogical
            # justification is sufficient.
            st.error(
                "A pedagogical justification of at least "
                f"{MIN_JUSTIFICATION_CHARS} characters is mandatory when "
                "overruling the machine verdict. Entry NOT recorded."
            )
        else:
            entry = append_audit_entry(
                scenario_label=scenario_label,
                mode_label=mode_label,
                rule_id=verdict["rule_id"],
                machine_verdict=verdict["verdict"],
                human_decision=decision,
                justification=stripped if stripped else "—",
            )
            st.success(
                f"Decision committed to the immutable audit log as entry "
                f"#{entry['entry_id']}."
            )

    render_audit_log()


def render_audit_log() -> None:
    """Displays the full log (read only) and the in-memory CSV export."""
    st.markdown("#### Immutable Audit Log (append-only)")
    log: List[Dict[str, Any]] = st.session_state.get("audit_log", [])
    if not log:
        st.info("No audit entries yet. Run an arbitration and commit a decision.")
        return

    # Displays the most recent entry first (unchanged storage).
    display_entries = list(reversed(log))
    st.dataframe(
        audit_log_dataframe(display_entries),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Entry index is read-only: no deletion or editing control is exposed."
    )

    csv_bytes = audit_log_dataframe(log).to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Download audit log (CSV)",
        data=csv_bytes,
        file_name="aura_learn_audit_log.csv",
        mime="text/csv",
        key="audit_csv_download",
    )

    with st.expander("Raw JSON audit log"):
        st.json(log)


# =============================================================================
# 13. MAIN ORCHESTRATION
# =============================================================================

def main() -> None:
    # MUST be the first Streamlit call in the script.
    st.set_page_config(
        page_title=(
            "AURA-Learn — Multimodal Learning Analytics & Adaptive Learning "
            "Environment Demonstrator"
        ),
        page_icon="🧠",
        layout="wide",
    )

    inject_global_css()
    init_session_state()

    # --- Top verbatim notice (st.caption rendering, like AURA-Grid) --------
    # No colored box: the header is aligned with the reference.
    render_top_notice()

    # --- Document sub-page routing -----------------------------------------
    # Session state is synchronized with ?doc=... (shareable links,
    # back/forward navigation), exactly like the AURA-Grid reference.
    requested_document = st.query_params.get("doc")
    if (
        not isinstance(requested_document, str)
        or requested_document not in DOCUMENT_TITLES
    ):
        requested_document = None
    if DOC_VIEW_KEY not in st.session_state:
        st.session_state[DOC_VIEW_KEY] = requested_document
    elif st.session_state[DOC_VIEW_KEY] != requested_document:
        st.session_state[DOC_VIEW_KEY] = requested_document

    active_document = st.session_state.get(DOC_VIEW_KEY)
    if active_document:
        # Short-circuit: the home page (and the R1–R6 kernel) is not executed;
        # the in-session audit log is preserved.
        render_document_page(active_document)
        render_footer()
        return

    # --- 8 header buttons (2 rows of 4) ------------------------------------
    render_header_links()

    # --- Title and subtitle -------------------------------------------------
    st.subheader("🧠 AURA-Learn — Multimodal Learning Analytics & Adaptive Learning Environment Demonstrator")
    st.caption(
        "Bounded Perception Swarm → Deterministic Pedagogical Arbitration "
        "Kernel → Glass-Box Educator Cockpit — 100% synthetic, non-production."
    )

    # --- Sidebar ------------------------------------------------------------
    config = render_sidebar()
    mode_label = config["mode_label"]
    scenario_key = config["scenario_key"]
    sensor_dropout = config["sensor_dropout"]
    api_key = config["api_key"]
    scenario = SCENARIOS[scenario_key]

    # A run is triggered by the button or by a configuration change
    # (same reactive behavior as the AURA-Grid reference).
    run_key = (mode_label, scenario_key, sensor_dropout)
    should_run = config["run"] or st.session_state["last_run_key"] != run_key

    if should_run:
        signals = get_scenario_signals(scenario_key, sensor_dropout)

        # Layer 1 — bounded perception (proposals only).
        attention = attention_agent(signals)
        metacognitive = metacognitive_agent(signals)
        guardrail = guardrail_precheck(signals)

        # Layer 2 — deterministic kernel: sole decision authority.
        verdict = evaluate_rules(signals)
        st.session_state["last_verdict"] = verdict
        st.session_state["last_run_key"] = run_key

        # Optional Live mode: LLM narrative, never decisive.
        st.session_state["live_narrative"] = ""
        st.session_state["live_notice"] = ""
        if mode_label == MODE_LIVE_LABEL:
            live_result = request_live_narrative(api_key, scenario_key, verdict)
            if live_result["ok"]:
                st.session_state["live_narrative"] = live_result["text"]
            else:
                st.session_state["live_notice"] = (
                    "Live DeepSeek LLM unavailable ("
                    f"{live_result['error']}) — fallback to deterministic "
                    "simulation. The R1–R6 kernel verdict is unchanged."
                )

    verdict: Optional[Dict[str, Any]] = st.session_state.get("last_verdict")

    if verdict is None:
        st.info(
            "Select a scenario (offline mode needs no API key) and click "
            "**Run Multimodal Arbitration** to begin."
        )
        render_audit_log()
        render_footer()
        return

    # Non-blocking Live mode fallback banner.
    if st.session_state.get("live_notice"):
        st.warning(st.session_state["live_notice"])

    signals = verdict["signals"]
    attention = attention_agent(signals)
    metacognitive = metacognitive_agent(signals)
    guardrail = guardrail_precheck(signals)

    # --- Layer 1 ------------------------------------------------------------
    render_layer1(attention, metacognitive, guardrail)
    st.markdown("---")

    # --- Layer 2 ------------------------------------------------------------
    render_layer2(verdict)

    # Optional Live mode narrative (pedagogical, non-decisive).
    if st.session_state.get("live_narrative"):
        with st.expander("Live DeepSeek narrative (non-authoritative)"):
            st.write(st.session_state["live_narrative"])
    st.markdown("---")

    # --- Layer 3 ------------------------------------------------------------
    render_layer3(verdict, scenario_key, mode_label)

    render_footer()


if __name__ == "__main__":
    main()
