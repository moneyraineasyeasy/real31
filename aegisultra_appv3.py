# aegisultra_app.py
#
# AEGIS ULTRA V3 Streamlit Command Center
#
# Compatible with:
# - aegisultra_enginev2.py
# - aegisultra_enginev3.py
#
# Important:
# CORRECT_SCORE is not an engine input market. Correct-score
# references are generated automatically from the FT model.

from __future__ import annotations

import hashlib
import html
import importlib
import json
import math
import os
import traceback
import urllib.error
import urllib.request
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

os.environ["ARROW_DEFAULT_MEMORY_POOL"] = "system"

import pandas as pd
import streamlit as st

import aegisultra_enginev2 as aegis_v2
import aegisultra_enginev3 as aegis


# ============================================================
# 1. Reload engine modules
# ============================================================

importlib.invalidate_caches()

aegis_v2 = importlib.reload(
    aegis_v2
)

aegis = importlib.reload(
    aegis
)


APP_NAME = "AEGIS ULTRA"
APP_VERSION = "3.1.0"

ENGINE_NAME = getattr(
    aegis,
    "ENGINE_NAME",
    "Aegis Ultra Engine",
)

ENGINE_VERSION = getattr(
    aegis,
    "ENGINE_VERSION",
    "Unknown",
)

DEFAULT_API_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbz7fltyng10Ulm2fjfgWWl3740GRFbHcvUci2lSvAv8nhkduIOnyfG_Q0IPwxKYoddd6g/"
    "exec"
)

PERIOD_ORDER = {
    "FT": 0,
    "HT": 1,
}

SUPPORTED_INPUT_MARKETS = {
    "1X2",
    "AH",
    "OU",
    "HHAD",
    "TEAM_OU",
}


# ============================================================
# 2. Page configuration
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 3. Styling
# ============================================================

st.markdown(
    """
    <style>
    :root {
        --bg: #080a11;
        --surface: rgba(255,255,255,0.045);
        --border: rgba(255,255,255,0.09);
        --green: #32d9a1;
        --blue: #7388ff;
        --purple: #ae72ff;
        --amber: #ffbd59;
        --red: #ff6577;
    }

    .stApp {
        background:
            radial-gradient(
                circle at 10% 5%,
                rgba(81,102,255,0.15),
                transparent 29%
            ),
            radial-gradient(
                circle at 90% 2%,
                rgba(172,81,255,0.12),
                transparent 26%
            ),
            linear-gradient(
                180deg,
                #090b13 0%,
                #0d1019 48%,
                #080a11 100%
            );
    }

    .block-container {
        max-width: 1540px;
        padding-top: 1.25rem;
        padding-bottom: 4rem;
    }

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                rgba(16,19,31,0.99),
                rgba(8,10,17,0.99)
            );
        border-right: 1px solid var(--border);
    }

    .hero {
        position: relative;
        overflow: hidden;
        padding: 2rem 2.15rem;
        margin-bottom: 1.25rem;
        border-radius: 24px;
        background:
            linear-gradient(
                120deg,
                rgba(76,95,255,0.23),
                rgba(150,68,255,0.16),
                rgba(0,214,170,0.09)
            );
        border: 1px solid rgba(255,255,255,0.12);
        box-shadow: 0 18px 60px rgba(0,0,0,0.36);
    }

    .hero-badge {
        display: inline-block;
        padding: 0.38rem 0.75rem;
        margin-bottom: 0.9rem;
        border-radius: 999px;
        color: #c6ffee;
        background: rgba(0,214,163,0.12);
        border: 1px solid rgba(0,214,163,0.27);
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.08em;
    }

    .hero-title {
        margin: 0;
        color: white;
        font-size: 3rem;
        font-weight: 850;
        letter-spacing: -0.055em;
    }

    .hero-text {
        max-width: 1050px;
        margin-top: 0.72rem;
        color: rgba(255,255,255,0.70);
        line-height: 1.65;
    }

    .summary-card {
        min-height: 125px;
        padding: 1.05rem 1.15rem;
        border-radius: 17px;
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(255,255,255,0.085);
        box-shadow: 0 10px 32px rgba(0,0,0,0.20);
    }

    .summary-label {
        color: rgba(255,255,255,0.50);
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .summary-value {
        margin-top: 0.42rem;
        color: white;
        font-size: 1.55rem;
        font-weight: 850;
    }

    .summary-note {
        margin-top: 0.35rem;
        color: rgba(255,255,255,0.48);
        font-size: 0.8rem;
    }

    .status-pass {
        color: var(--green);
    }

    .status-caution {
        color: var(--amber);
    }

    .status-fail {
        color: var(--red);
    }

    .recommendation-card {
        padding: 1.25rem 1.35rem;
        margin-bottom: 0.9rem;
        border-radius: 18px;
        background:
            linear-gradient(
                120deg,
                rgba(0,214,163,0.10),
                rgba(255,255,255,0.035)
            );
        border: 1px solid rgba(0,214,163,0.22);
        box-shadow: 0 12px 34px rgba(0,0,0,0.23);
    }

    .recommendation-rank {
        color: #7fffd3;
        font-size: 0.77rem;
        font-weight: 850;
        letter-spacing: 0.1em;
    }

    .recommendation-name {
        margin-top: 0.32rem;
        color: white;
        font-size: 1.35rem;
        font-weight: 850;
    }

    .recommendation-stats {
        margin-top: 0.55rem;
        color: rgba(255,255,255,0.66);
        font-size: 0.91rem;
        line-height: 1.65;
    }

    .period-badge {
        display: inline-block;
        padding: 0.26rem 0.62rem;
        margin-bottom: 0.4rem;
        border-radius: 999px;
        color: #bae6fd;
        background: rgba(56,189,248,0.11);
        border: 1px solid rgba(56,189,248,0.24);
        font-size: 0.72rem;
        font-weight: 850;
    }

    .score-card {
        text-align: center;
        min-height: 140px;
        padding: 1.25rem 0.85rem;
        border-radius: 18px;
        background:
            linear-gradient(
                145deg,
                rgba(130,91,255,0.16),
                rgba(255,255,255,0.035)
            );
        border: 1px solid rgba(151,120,255,0.22);
    }

    .score-value {
        color: white;
        font-size: 2rem;
        font-weight: 850;
    }

    .score-note {
        margin-top: 0.35rem;
        color: #d7ceff;
        font-size: 0.9rem;
    }

    textarea {
        font-family:
            "SFMono-Regular",
            Consolas,
            monospace !important;
        font-size: 0.86rem !important;
        line-height: 1.5 !important;
    }

    [data-testid="stMetric"] {
        padding: 0.9rem 1rem;
        border-radius: 15px;
        background: rgba(255,255,255,0.042);
        border: 1px solid rgba(255,255,255,0.075);
    }

    [data-testid="stDataFrame"] {
        overflow: hidden;
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.075);
    }

    div[data-testid="stExpander"] {
        border-radius: 15px;
        background: rgba(255,255,255,0.018);
    }

    /* ==========================================================
       Model Health Diagnostic Panel
       ========================================================== */

    .health-panel {
        position: relative;
        overflow: hidden;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.1rem;
        border-radius: 22px;
        background:
            radial-gradient(
                circle at 88% 8%,
                rgba(56,189,248,0.13),
                transparent 34%
            ),
            linear-gradient(
                120deg,
                rgba(20,28,52,0.72),
                rgba(11,16,32,0.86)
            );
        border: 1px solid rgba(255,255,255,0.10);
        box-shadow: 0 16px 48px rgba(0,0,0,0.28);
    }

    .health-panel-robust {
        border-color: rgba(50,217,161,0.32);
        box-shadow:
            0 0 0 1px rgba(50,217,161,0.12),
            0 16px 48px rgba(0,0,0,0.28);
    }

    .health-panel-acceptable {
        border-color: rgba(255,189,89,0.32);
        box-shadow:
            0 0 0 1px rgba(255,189,89,0.12),
            0 16px 48px rgba(0,0,0,0.28);
    }

    .health-panel-fragile {
        border-color: rgba(255,101,119,0.34);
        box-shadow:
            0 0 0 1px rgba(255,101,119,0.14),
            0 16px 48px rgba(0,0,0,0.28);
    }

    .health-panel-header {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        margin-bottom: 1.15rem;
    }

    .health-panel-kicker {
        color: rgba(255,255,255,0.46);
        font-size: 0.72rem;
        font-weight: 950;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }

    .health-grid {
        display: grid;
        grid-template-columns: 210px 1fr;
        gap: 2rem;
        align-items: center;
    }

    @media (max-width: 820px) {
        .health-grid {
            grid-template-columns: 1fr;
            gap: 1.2rem;
        }
    }

    .health-gauge-wrap {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }

    .health-gauge {
        position: relative;
        width: 178px;
        height: 178px;
    }

    .health-gauge svg {
        transform: rotate(-90deg);
        width: 100%;
        height: 100%;
    }

    .health-gauge-track {
        fill: none;
        stroke: rgba(255,255,255,0.08);
        stroke-width: 12;
    }

    .health-gauge-arc {
        fill: none;
        stroke-width: 12;
        stroke-linecap: round;
        transition: stroke-dasharray 0.6s ease;
    }

    .health-gauge-score {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .health-gauge-score-value {
        color: #fff;
        font-size: 2.55rem;
        font-weight: 850;
        line-height: 1;
    }

    .health-gauge-score-unit {
        color: rgba(255,255,255,0.42);
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        margin-top: 0.15rem;
    }

    .health-grade {
        margin-top: 0.85rem;
        display: inline-block;
        padding: 0.4rem 0.95rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 950;
        letter-spacing: 0.12em;
    }

    .health-grade-robust {
        color: #8fffd1;
        background: rgba(50,217,161,0.13);
        border: 1px solid rgba(50,217,161,0.34);
    }

    .health-grade-acceptable {
        color: #ffe0a8;
        background: rgba(255,189,89,0.13);
        border: 1px solid rgba(255,189,89,0.34);
    }

    .health-grade-fragile {
        color: #ffb3bd;
        background: rgba(255,101,119,0.14);
        border: 1px solid rgba(255,101,119,0.36);
    }

    .health-dimensions {
        display: flex;
        flex-direction: column;
        gap: 0.62rem;
    }

    .health-dimension {
        display: grid;
        grid-template-columns: 132px 1fr 78px;
        align-items: center;
        gap: 0.85rem;
    }

    .health-dim-label {
        color: rgba(255,255,255,0.58);
        font-size: 0.81rem;
        font-weight: 800;
        letter-spacing: 0.02em;
    }

    .health-bar {
        position: relative;
        height: 8px;
        border-radius: 999px;
        background: rgba(255,255,255,0.08);
        overflow: hidden;
    }

    .health-bar-fill {
        position: absolute;
        inset: 0;
        border-radius: 999px;
    }

    .health-dim-value {
        text-align: right;
        font-size: 0.79rem;
        font-weight: 850;
        letter-spacing: 0.02em;
    }

    .health-issues {
        margin-top: 1.15rem;
        padding: 0.9rem 1rem;
        border-radius: 13px;
        background: rgba(255,101,119,0.075);
        border: 1px solid rgba(255,101,119,0.20);
    }

    .health-issues-title {
        color: #ffb3bd;
        font-size: 0.75rem;
        font-weight: 950;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    .health-issue {
        color: rgba(255,255,255,0.72);
        font-size: 0.83rem;
        line-height: 1.6;
        padding-left: 1rem;
        position: relative;
    }

    .health-issue::before {
        content: "⚠";
        position: absolute;
        left: 0;
        color: #ffbd59;
        font-size: 0.72rem;
    }

    .health-notes {
        margin-top: 1rem;
        color: rgba(255,255,255,0.40);
        font-size: 0.76rem;
        line-height: 1.6;
    }

    @media (max-width: 700px) {
        .hero-title {
            font-size: 2.15rem;
        }

        .hero {
            padding: 1.4rem 1.3rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 4. Generic helpers
# ============================================================

def optional_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def safe_float(
    value: Any,
    default: Optional[float] = None,
) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(number):
        return default

    return number


def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    number = safe_float(value)

    if number is None:
        return default

    return int(number)


def html_escape(value: Any) -> str:
    return html.escape(
        str(value if value is not None else "—")
    )


def json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()

    if hasattr(value, "tolist"):
        return value.tolist()

    if isinstance(value, set):
        return list(value)

    return str(value)


def json_text(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        default=json_default,
    )


def format_probability(
    value: Any,
    digits: int = 1,
) -> str:
    number = safe_float(value)

    if number is None:
        return "—"

    if 1.0 < number <= 100.0:
        number /= 100.0

    return f"{number * 100:.{digits}f}%"


def format_odds(
    value: Any,
    digits: int = 3,
) -> str:
    number = safe_float(value)

    if number is None:
        return "—"

    return f"{number:.{digits}f}"


def format_ev(
    value: Any,
    digits: int = 2,
) -> str:
    number = safe_float(value)

    if number is None:
        return "—"

    return f"{number * 100:+.{digits}f}%"


def _fmt_market_change(value: Any) -> str:
    """把市場變動值格式化為帶正負號的 pp 字串，None 時回傳 —。"""
    number = safe_float(value)

    if number is None:
        return "—"

    return f"{number:+.2f}pp"


def probability_value(
    record: Dict[str, Any],
    metric: str,
    statistic: str = "minimum",
) -> Any:
    probability = record.get(
        "probability",
        {},
    )

    if not isinstance(probability, dict):
        return None

    metric_record = probability.get(
        metric,
        {},
    )

    if not isinstance(metric_record, dict):
        return None

    return metric_record.get(
        statistic
    )


def summary_value(
    record: Dict[str, Any],
    field: str,
    statistic: str = "minimum",
) -> Any:
    section = record.get(
        field,
        {},
    )

    if isinstance(section, dict):
        return section.get(
            statistic
        )

    return section


def status_chinese(status: Any) -> str:
    translations = {
        "PASS": "通過",
        "CAUTION": "注意",
        "FAIL": "失敗",
        "COMPLETED": "已完成",
        "NOT_AVAILABLE": "不適用",
        "NOT_PROVIDED": "未提供",
        "NOT_TESTABLE": "無法測試",
        "DISABLED": "已停用",
        "ROBUST": "穩健",
        "FRAGILE": "脆弱",
        "OFFICIAL": "正式推薦",
        "REFERENCE_ONLY": "僅供參考",
        "FAIR_OR_BETTER": "價格合理或更佳",
        "MIXED_PRICE": "價格訊號混合",
        "SLIGHTLY_UNDERPAID": "輕微回報不足",
        "POOR_PRICE": "價格偏差",
        "SEVERELY_UNDERPAID": "嚴重回報不足",
        "SUPPORTED": "支持",
        "CONFLICTED": "衝突",
        "NEUTRAL": "中性",
        "STRONG": "強",
        "MODERATE": "中等",
        "WEAK": "弱",
        "NONE": "沒有",
        "UNKNOWN": "未知",
    }

    text = optional_text(
        status
    ).upper() or "UNKNOWN"

    return translations.get(
        text,
        text.replace("_", " "),
    )


def status_css_class(status: Any) -> str:
    value = optional_text(
        status
    ).upper()

    if value in {
        "PASS",
        "COMPLETED",
        "SUPPORTED",
        "ROBUST",
        "OFFICIAL",
        "FAIR_OR_BETTER",
    }:
        return "status-pass"

    if value in {
        "CAUTION",
        "NEUTRAL",
        "NOT_AVAILABLE",
        "NOT_PROVIDED",
        "NOT_TESTABLE",
        "DISABLED",
        "FRAGILE",
        "MIXED_PRICE",
    }:
        return "status-caution"

    return "status-fail"


def result_summary_card(
    label: str,
    value: str,
    note: str,
    css_class: str = "",
) -> None:
    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-label">
                {html_escape(label)}
            </div>
            <div class="summary-value {css_class}">
                {html_escape(value)}
            </div>
            <div class="summary-note">
                {html_escape(note)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def download_name(prefix: str) -> str:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return f"{prefix}_{timestamp}.json"


# ============================================================
# 5a. Model health diagnostic
# ============================================================
#
# A weighted-rule health engine. It reads the telemetry that the
# AEGIS Ultra engine already exposes on the result object and
# condenses it into a single grade (ROBUST / ACCEPTABLE / FRAGILE)
# plus a per-dimension score sheet and a list of concrete issues.
#
# Dimensions and default weights (sum = 1.00):
#   odds_movement    0.20  - consensus among monitored books
#   family_out       0.18  - one-family removal stability
#   stress           0.17  - hit prob. under light/medium stress
#   ht_ft_coherence  0.15  - HT transport consistency
#   model_quality    0.14  - grid / projection quality
#   coverage         0.16  - how much telemetry we actually have
#
# Each dimension returns a 0..1 score. The weighted mean is mapped
# to a grade at thresholds 0.75 (ROBUST) and 0.55 (ACCEPTABLE).
#
# Weights and thresholds are intentionally exposed as constants so
# they can be tuned without touching the grading code.

HEALTH_WEIGHTS: Dict[str, float] = {
    "odds_movement": 0.20,
    "family_out": 0.18,
    "stress": 0.17,
    "ht_ft_coherence": 0.15,
    "model_quality": 0.14,
    "coverage": 0.16,
}

HEALTH_THRESHOLD_ROBUST = 0.75
HEALTH_THRESHOLD_ACCEPTABLE = 0.55

# A status value that, by itself, drags the grade down to FRAGILE
# regardless of the weighted mean. Set to None to disable.
HEALTH_HARD_FAIL_STATUSES = {
    "POOR_PRICE",
    "SEVERELY_UNDERPAID",
    "FAIL",
}


def _score_from_status(
    status: Any,
    mapping: Optional[Dict[str, float]] = None,
) -> Optional[float]:
    """Turn a textual status into a 0..1 score using ``mapping``."""

    text = optional_text(status).upper()

    if not text or text == "UNKNOWN":
        return None

    if mapping:
        if text in mapping:
            return mapping[text]

        return mapping.get(
            "DEFAULT",
            0.5,
        )

    return None


def _score_coverage(
    result: Dict[str, Any],
    candidates: List[Dict[str, Any]],
) -> float:
    """
    How much of the V3 telemetry is actually present? A model with
    no movement series, no stress audit and no family-out audit is
    technically not unhealthy -- it is just unaudited, which is a
    different (and weaker) statement.
    """

    checks = 0
    present = 0

    # odds movement
    checks += 1

    if result.get(
        "odds_movement_analysis"
    ) or result.get(
        "odds_shift_analysis"
    ):
        present += 1

    elif any(
        bool(candidate.get("odds_movement"))
        for candidate in candidates
    ):
        present += 1

    # family-out + stress
    checks += 1

    if any(
        candidate.get("family_out_audit")
        for candidate in candidates
    ):
        present += 0.5

    if any(
        candidate.get("stress_audit")
        for candidate in candidates
    ):
        present += 0.5

    # HT-FT coherence
    checks += 1

    if result.get(
        "ht_ft_coherence"
    ):
        present += 1

    # model quality / projection diagnostics
    checks += 1

    if result.get(
        "model_quality"
    ) or result.get(
        "diagnostics"
    ):
        present += 1

    # at least one candidate has a probability distribution
    checks += 1

    if any(
        candidate.get("probability")
        for candidate in candidates
    ):
        present += 1

    return present / checks if checks else 0.0


def _score_odds_movement(
    result: Dict[str, Any],
    candidates: List[Dict[str, Any]],
) -> Optional[float]:
    """
    Prefer an explicit agreement ratio when the engine supplies it;
    fall back to a coarse status mapping.
    """

    for container_name in (
        "odds_movement_analysis",
        "odds_shift_analysis",
    ):
        container = result.get(
            container_name
        )

        if isinstance(
            container,
            dict,
        ):
            ratio = safe_float(
                container.get(
                    "agreement_ratio"
                )
            )

            if ratio is not None:
                return max(
                    0.0,
                    min(
                        1.0,
                        ratio,
                    ),
                )

            return _score_from_status(
                container.get("status"),
                {
                    "PASS": 0.9,
                    "SUPPORTED": 0.85,
                    "FAIR_OR_BETTER": 0.8,
                    "MIXED_PRICE": 0.55,
                    "CAUTION": 0.5,
                    "CONFLICTED": 0.35,
                    "SLIGHTLY_UNDERPAID": 0.35,
                    "POOR_PRICE": 0.15,
                    "SEVERELY_UNDERPAID": 0.05,
                    "NOT_AVAILABLE": 0.45,
                    "NOT_PROVIDED": 0.45,
                    "NOT_TESTABLE": 0.5,
                    "DEFAULT": 0.5,
                },
            )

    return None


def _score_family_out(
    candidates: List[Dict[str, Any]],
) -> Optional[float]:
    """Average family-out score across candidates that have it."""

    scores = []

    for candidate in candidates:
        audit = candidate.get(
            "family_out_audit"
        )

        if not isinstance(
            audit,
            dict,
        ):
            continue

        explicit = safe_float(
            audit.get("score")
        )

        if explicit is not None:
            scores.append(
                max(
                    0.0,
                    min(
                        1.0,
                        explicit,
                    ),
                )
            )

            continue

        scores.append(
            _score_from_status(
                audit.get("status"),
                {
                    "PASS": 0.9,
                    "ROBUST": 0.88,
                    "SUPPORTED": 0.8,
                    "CAUTION": 0.5,
                    "FRAGILE": 0.3,
                    "FAIL": 0.1,
                    "DEFAULT": 0.5,
                },
            )
            or 0.5
        )

    if not scores:
        return None

    return sum(scores) / len(scores)


def _score_stress(
    candidates: List[Dict[str, Any]],
) -> Optional[float]:
    """
    Light stress is the most realistic scenario, so we weight it
    heaviest inside this dimension; medium is a tie-breaker.
    """

    scores = []

    for candidate in candidates:
        stress = candidate.get(
            "stress_audit"
        )

        if not isinstance(
            stress,
            dict,
        ):
            continue

        light = safe_float(
            stress.get("light"),
            stress.get(
                "light_hit_probability"
            ),
        )

        if light is None:
            light = safe_float(
                stress.get("light", {}).get(
                    "hit_probability"
                )
            )

        medium = safe_float(
            stress.get("medium"),
            stress.get(
                "medium_hit_probability"
            ),
        )

        if medium is None:
            medium = safe_float(
                stress.get("medium", {}).get(
                    "hit_probability"
                )
            )

        candidate_scores = [
            s
            for s in (light, medium)
            if s is not None
        ]

        if candidate_scores:
            # 70% light / 30% medium
            weighted = (
                (light or 0.0) * 0.7
                + (medium or 0.0) * 0.3
            ) / (
                0.7 + (0.3 if medium is not None else 0.0)
                or 1.0
            )

            scores.append(
                max(
                    0.0,
                    min(
                        1.0,
                        weighted,
                    ),
                )
            )

    if not scores:
        return None

    return sum(scores) / len(scores)


def _score_ht_ft_coherence(
    result: Dict[str, Any],
) -> Optional[float]:
    coherence = result.get(
        "ht_ft_coherence"
    )

    if not isinstance(
        coherence,
        dict,
    ):
        return None

    return _score_from_status(
        coherence.get("status"),
        {
            "PASS": 0.92,
            "COMPLETED": 0.85,
            "SUPPORTED": 0.8,
            "CAUTION": 0.5,
            "FRAGILE": 0.3,
            "FAIL": 0.1,
            "NOT_AVAILABLE": 0.6,
            "NOT_TESTABLE": 0.55,
            "DEFAULT": 0.5,
        },
    )


def _score_model_quality(
    result: Dict[str, Any],
) -> Optional[float]:
    quality = result.get(
        "model_quality"
    )

    if isinstance(
        quality,
        dict,
    ):
        explicit = safe_float(
            quality.get("score")
        )

        if explicit is not None:
            return max(
                0.0,
                min(
                    1.0,
                    explicit,
                ),
            )

        return _score_from_status(
            quality.get("status"),
            {
                "PASS": 0.92,
                "COMPLETED": 0.85,
                "ROBUST": 0.88,
                "SUPPORTED": 0.78,
                "CAUTION": 0.5,
                "FRAGILE": 0.3,
                "FAIL": 0.1,
                "DEFAULT": 0.5,
            },
        )

    return None


def evaluate_model_health(
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run the full diagnostic. Always returns a complete dict even
    when the engine output is missing or malformed, so the UI can
    render a graceful "insufficient data" state instead of erroring.
    """

    if not isinstance(
        result,
        dict,
    ):
        return _empty_health(
            "INSUFFICIENT_DATA",
            ["引擎未回傳有效結果，無法進行健康評估。"],
        )

    candidates = result.get(
        "candidate_markets",
        [],
    )

    if not isinstance(
        candidates,
        list,
    ):
        candidates = []

    scorers = {
        "odds_movement": lambda: _score_odds_movement(
            result,
            candidates,
        ),
        "family_out": lambda: _score_family_out(
            candidates,
        ),
        "stress": lambda: _score_stress(
            candidates,
        ),
        "ht_ft_coherence": lambda: _score_ht_ft_coherence(
            result,
        ),
        "model_quality": lambda: _score_model_quality(
            result,
        ),
        "coverage": lambda: _score_coverage(
            result,
            candidates,
        ),
    }

    dimensions: Dict[str, Dict[str, Any]] = {}
    weighted_sum = 0.0
    weight_used = 0.0

    for name, scorer in scorers.items():
        weight = HEALTH_WEIGHTS.get(
            name,
            0.0,
        )

        score = scorer()

        dimensions[name] = {
            "score": score,
            "weight": weight,
            "available": score is not None,
        }

        if score is not None:
            weighted_sum += score * weight
            weight_used += weight

    composite = (
        weighted_sum / weight_used
        if weight_used > 0
        else 0.0
    )

    # hard-fail: any key status in the denylist drags the grade
    # down to FRAGILE and records a concrete issue.
    hard_fail_reasons = _collect_hard_fail_reasons(
        result,
        candidates,
    )

    grade = _grade_from_score(
        composite,
        hard_fail_reasons,
    )

    return {
        "grade": grade,
        "composite": round(
            composite,
            4,
        ),
        "score_0_100": round(
            composite * 100,
        ),
        "dimensions": dimensions,
        "weight_used_ratio": round(
            weight_used,
            4,
        ),
        "hard_fail_reasons": hard_fail_reasons,
        "issues": _collect_issues(
            dimensions,
            hard_fail_reasons,
        ),
    }


def _grade_from_score(
    composite: float,
    hard_fail_reasons: List[str],
) -> str:
    if hard_fail_reasons:
        return "FRAGILE"

    if composite >= HEALTH_THRESHOLD_ROBUST:
        return "ROBUST"

    if composite >= HEALTH_THRESHOLD_ACCEPTABLE:
        return "ACCEPTABLE"

    return "FRAGILE"


def _collect_hard_fail_reasons(
    result: Dict[str, Any],
    candidates: List[Dict[str, Any]],
) -> List[str]:
    reasons: List[str] = []

    def check(
        status: Any,
        source: str,
    ) -> None:
        text = optional_text(status).upper()

        if text in HEALTH_HARD_FAIL_STATUSES:
            reasons.append(
                f"{source} 狀態為「{status_chinese(text)}」，"
                f"嚴重削弱結論可信度"
            )

    check(
        result.get(
            "model_quality",
            {},
        ).get("status")
        if isinstance(
            result.get("model_quality"),
            dict,
        )
        else None,
        "模型品質",
    )

    for candidate in candidates:
        check(
            candidate.get("price_status"),
            f"{optional_text(candidate.get('label')) or '候選盤'} 價格",
        )

    return reasons


def _collect_issues(
    dimensions: Dict[str, Dict[str, Any]],
    hard_fail_reasons: List[str],
) -> List[str]:
    issues: List[str] = list(
        hard_fail_reasons
    )

    for name, info in dimensions.items():
        if info.get(
            "available"
        ):
            continue

        label = HEALTH_DIMENSION_LABELS.get(
            name,
            name,
        )

        issues.append(
            f"{label}：缺少評估資料"
        )

    # flag the lowest non-coverage dimension that is actually
    # available, so the analyst knows the main weak spot.
    available = {
        name: info
        for name, info in dimensions.items()
        if info.get("available")
        and name != "coverage"
        and info.get("score") is not None
    }

    if available:
        weakest_name, weakest = min(
            available.items(),
            key=lambda item: item[1]["score"],
        )

        if weakest["score"] < 0.45:
            label = HEALTH_DIMENSION_LABELS.get(
                weakest_name,
                weakest_name,
            )

            issues.append(
                f"最弱環節 — {label}："
                f"{round(weakest['score'] * 100)} 分"
            )

    # de-duplicate while preserving order
    seen = set()
    deduped: List[str] = []

    for issue in issues:
        if issue in seen:
            continue

        seen.add(issue)
        deduped.append(issue)

    return deduped


def _empty_health(
    grade: str,
    issues: List[str],
) -> Dict[str, Any]:
    return {
        "grade": grade,
        "composite": 0.0,
        "score_0_100": 0,
        "dimensions": {
            name: {
                "score": None,
                "weight": weight,
                "available": False,
            }
            for name, weight in HEALTH_WEIGHTS.items()
        },
        "weight_used_ratio": 0.0,
        "hard_fail_reasons": [],
        "issues": issues,
    }


HEALTH_DIMENSION_LABELS: Dict[str, str] = {
    "odds_movement": "盤口走勢",
    "family_out": "Family-out",
    "stress": "壓力測試",
    "ht_ft_coherence": "HT–FT 一致性",
    "model_quality": "模型品質",
    "coverage": "資料覆蓋",
}

HEALTH_DIMENSION_DESCRIPTIONS: Dict[str, str] = {
    "odds_movement": "多家莊家盤口與機率方向是否一致",
    "family_out": "抽走單一家族莊家後結論是否保持穩定",
    "stress": "輕度 / 中度偏離情境下的命中率",
    "ht_ft_coherence": "上半場與全場機率是否自洽",
    "model_quality": "網格與機率投影的收斂品質",
    "coverage": "本次分析實際覆蓋的審計項目比例",
}


def health_grade_label(grade: str) -> str:
    return {
        "ROBUST": "穩健",
        "ACCEPTABLE": "可接受",
        "FRAGILE": "脆弱",
    }.get(
        optional_text(
            grade
        ).upper(),
        "待評估",
    )


def health_grade_css_class(grade: str) -> str:
    return {
        "ROBUST": "health-grade-robust",
        "ACCEPTABLE": "health-grade-acceptable",
        "FRAGILE": "health-grade-fragile",
    }.get(
        optional_text(
            grade
        ).upper(),
        "health-grade-acceptable",
    )


def health_panel_css_class(grade: str) -> str:
    return {
        "ROBUST": "health-panel-robust",
        "ACCEPTABLE": "health-panel-acceptable",
        "FRAGILE": "health-panel-fragile",
    }.get(
        optional_text(
            grade
        ).upper(),
        "",
    )


def health_arc_color(grade: str) -> str:
    return {
        "ROBUST": "#32d9a1",
        "ACCEPTABLE": "#ffbd59",
        "FRAGILE": "#ff6577",
    }.get(
        optional_text(
            grade
        ).upper(),
        "#7388ff",
    )


def _dimension_color(score: Optional[float]) -> str:
    if score is None:
        return "rgba(255,255,255,0.18)"

    if score >= 0.75:
        return "#32d9a1"

    if score >= 0.55:
        return "#ffbd59"

    return "#ff6577"


def _dimension_value_text(
    info: Dict[str, Any],
) -> str:
    score = info.get("score")

    if score is None:
        return "無資料"

    return f"{round(score * 100)} 分"


def render_health_panel(
    result: Dict[str, Any],
) -> None:
    """
    Hero 正下方（summary cards 之後、結果 tabs 之前）的模型
    健康診斷面板。純展示，不修改 session_state。
    """

    health = evaluate_model_health(
        result
    )

    grade = health.get(
        "grade",
        "ACCEPTABLE",
    )

    score = health.get(
        "score_0_100",
        0,
    )

    dimensions = health.get(
        "dimensions",
        {},
    )

    issues = health.get(
        "issues",
        [],
    )

    # ring geometry: circumference for r=74, stroke=12
    circumference = 2 * math.pi * 74
    clamped = max(
        0.0,
        min(
            1.0,
            health.get(
                "composite",
                0.0,
            ),
        ),
    )
    dash_offset = circumference * (
        1 - clamped
    )

    color = health_arc_color(
        grade
    )

    dimension_rows = "\n".join(
        _dimension_row(
            name,
            info,
        )
        for name, info in dimensions.items()
    )

    issues_html = ""

    if issues:
        issue_items = "".join(
            f'<div class="health-issue">{html_escape(item)}'
            f'</div>'
            for item in issues[:6]
        )

        issues_html = f"""
        <div class="health-issues">
            <div class="health-issues-title">
                需注意項目（{len(issues)}）
            </div>
            {issue_items}
        </div>
        """

    coverage_pct = round(
        health.get(
            "weight_used_ratio",
            0.0,
        )
        * 100,
    )

    st.markdown(
        f"""
        <div class="health-panel {health_panel_css_class(grade)}">
            <div class="health-panel-header">
                <div class="health-panel-kicker">
                    模型健康診斷 · Model Health
                </div>
            </div>

            <div class="health-grid">
                <div class="health-gauge-wrap">
                    <div class="health-gauge">
                        <svg viewBox="0 0 168 168">
                            <circle
                                class="health-gauge-track"
                                cx="84" cy="84" r="74"
                            />
                            <circle
                                class="health-gauge-arc"
                                cx="84" cy="84" r="74"
                                stroke="{color}"
                                stroke-dasharray="{circumference}"
                                stroke-dashoffset="{dash_offset}"
                            />
                        </svg>
                        <div class="health-gauge-score">
                            <div class="health-gauge-score-value">
                                {score}
                            </div>
                            <div class="health-gauge-score-unit">
                                / 100
                            </div>
                        </div>
                    </div>
                    <span class="health-grade {health_grade_css_class(grade)}">
                        {html_escape(health_grade_label(grade))}
                    </span>
                </div>

                <div class="health-dimensions">
                    {dimension_rows}
                </div>
            </div>

            {issues_html}

            <div class="health-notes">
                評分為綜合評估（非命中率預測）：盤口走勢 20% ／
                Family-out 18% ／ 壓力測試 17% ／ HT–FT 一致性 15% ／
                模型品質 14% ／ 資料覆蓋 16%。
                本次有效評估覆蓋 {coverage_pct}%。
                指標僅供風險參考，不構成投注保證。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _dimension_row(
    name: str,
    info: Dict[str, Any],
) -> str:
    label = HEALTH_DIMENSION_LABELS.get(
        name,
        name,
    )

    description = HEALTH_DIMENSION_DESCRIPTIONS.get(
        name,
        "",
    )

    score = info.get("score")
    available = info.get(
        "available",
        score is not None,
    )

    if available and score is not None:
        pct = max(
            2.0,
            min(
                100.0,
                score * 100,
            ),
        )

        color = _dimension_color(
            score
        )

        value_text = (
            f"{round(score * 100)} 分"
        )

        fill_style = (
            f"width:{pct:.1f}%;"
            f"background:linear-gradient("
            f"90deg, {color}, {color}cc);"
        )

    else:
        pct = 6.0
        color = "rgba(255,255,255,0.22)"

        value_text = (
            '<span style="color:rgba(255,255,255,0.32)">'
            '無資料</span>'
        )

        fill_style = (
            f"width:{pct:.1f}%;"
            f"background:{color};"
        )

    return f"""
        <div class="health-dimension">
            <div>
                <div class="health-dim-label">{html_escape(label)}</div>
                <div style="
                    color:rgba(255,255,255,0.30);
                    font-size:0.7rem;
                    margin-top:0.12rem;
                ">{html_escape(description)}</div>
            </div>
            <div class="health-bar">
                <div class="health-bar-fill" style="{fill_style}"></div>
            </div>
            <div class="health-dim-value" style="color:{color}">
                {value_text}
            </div>
        </div>
    """

def example_json_input() -> Dict[str, Any]:
    return {
        "match": {
            "name": "主隊 vs 客隊",
            "home": "主隊",
            "away": "客隊",
            "competition": "示例賽事",
            "kickoff": "",
            "snapshot_time": (
                datetime.now()
                .astimezone()
                .isoformat(
                    timespec="minutes"
                )
            ),
        },
        "sharp_books": [
            {
                "key": "pinnacle",
                "title": "Pinnacle",
                "markets": {
                    "FT": {
                        "1X2": {
                            "home": 2.12,
                            "draw": 3.35,
                            "away": 3.55,
                        },
                        "AH": [
                            {
                                "line": -0.25,
                                "home": 1.95,
                                "away": 1.95,
                            }
                        ],
                        "OU": [
                            {
                                "line": 2.25,
                                "over": 1.92,
                                "under": 1.98,
                            }
                        ],
                        "HHAD": [],
                        "TEAM_OU": [],
                    },
                    "HT": {
                        "1X2": {
                            "home": 2.75,
                            "draw": 2.10,
                            "away": 4.10,
                        },
                        "AH": [
                            {
                                "line": 0.0,
                                "home": 1.62,
                                "away": 2.28,
                            }
                        ],
                        "OU": [
                            {
                                "line": 1.0,
                                "over": 1.92,
                                "under": 1.98,
                            }
                        ],
                        "HHAD": [],
                        "TEAM_OU": [],
                    },
                },
            }
        ],
        "hkjc_markets": [
            {
                "id": "M001",
                "period": "FT",
                "market": "AH",
                "selection": "HOME",
                "line": -0.25,
                "odds": 1.95,
                "label": "主隊 全場 AH -0.25",
            },
            {
                "id": "M002",
                "period": "FT",
                "market": "OU",
                "selection": "UNDER",
                "line": 2.25,
                "odds": 1.88,
                "label": "全場入球細 2.25",
            },
            {
                "id": "M003",
                "period": "HT",
                "market": "OU",
                "selection": "UNDER",
                "line": 1.0,
                "odds": 1.90,
                "label": "半場入球細 1.0",
            },
        ],
        "odds_movements": [],
        "settings": {
            "minimum_odds": 1.50,
            "maximum_odds": None,
            "max_recommendations": 3,
            "minimum_official_hit_probability": 0.50,
            "correct_score_count": 2,
            "devig_methods": [
                "MULTIPLICATIVE",
                "POWER",
                "SHIN",
            ],
            "primary_source": "pinnacle",
            "ev_rejection_floor": None,
            "features": {
                "quality_gate": True,
                "stress_audit": True,
                "family_out_audit": True,
                "adaptive_grids": True,
                "ht_ft_coherence": True,
                "prior_comparison": True,
                "odds_shift_analysis": True,
            },
            "movement": {
                "neutral_threshold_pp": 0.50,
                "strong_threshold_pp": 2.00,
                "minimum_external_books": 2,
                "minimum_agreement": 0.60,
                "strong_agreement": 0.75,
                "adjacent_line_tolerance": 0.50,
            },
        },
    }


# ============================================================
# 6. Input compatibility validation
# ============================================================

def reject_unsupported_correct_score_inputs(
    input_data: Dict[str, Any],
) -> None:
    """
    Engine V3 generates correct-score references from the FT
    score distribution. It does not accept CORRECT_SCORE as a
    sharp constraint or HKJC candidate market.
    """

    for book in input_data.get(
        "sharp_books",
        [],
    ):
        if not isinstance(book, dict):
            continue

        markets = book.get(
            "markets",
            {},
        )

        if not isinstance(markets, dict):
            continue

        for period in [
            "FT",
            "HT",
        ]:
            block = markets.get(
                period,
                {},
            )

            if (
                isinstance(block, dict)
                and block.get(
                    "CORRECT_SCORE"
                )
            ):
                raise ValueError(
                    "Engine V3 不接受 CORRECT_SCORE 作為"
                    "尖銳市場約束。請移除 sharp_books 內的 "
                    "CORRECT_SCORE。波膽參考會由 FT 模型"
                    "自動產生。"
                )

    for candidate in input_data.get(
        "hkjc_markets",
        [],
    ):
        if not isinstance(candidate, dict):
            continue

        market = optional_text(
            candidate.get("market")
        ).upper()

        if market in {
            "CORRECT_SCORE",
            "EXACT_SCORE",
            "CS",
        }:
            raise ValueError(
                "Engine V3 不接受 CORRECT_SCORE 作為 "
                "HKJC 候選盤。請移除此候選盤。"
                "波膽參考會由 FT 模型自動產生。"
            )


def normalize_v3_input(
    input_data: Dict[str, Any],
) -> Dict[str, Any]:
    if not isinstance(input_data, dict):
        raise ValueError(
            "輸入 JSON 最外層必須是 object。"
        )

    data = deepcopy(
        input_data
    )

    reject_unsupported_correct_score_inputs(
        data
    )

    settings = data.setdefault(
        "settings",
        {},
    )

    if not isinstance(settings, dict):
        raise ValueError(
            "settings 必須是 object。"
        )

    settings.setdefault(
        "devig_methods",
        [
            "MULTIPLICATIVE",
            "POWER",
            "SHIN",
        ],
    )

    features = settings.setdefault(
        "features",
        {},
    )

    if not isinstance(features, dict):
        features = {}
        settings["features"] = features

    features.setdefault(
        "quality_gate",
        True,
    )

    features.setdefault(
        "stress_audit",
        True,
    )

    features.setdefault(
        "family_out_audit",
        True,
    )

    features.setdefault(
        "adaptive_grids",
        True,
    )

    features.setdefault(
        "ht_ft_coherence",
        True,
    )

    features.setdefault(
        "prior_comparison",
        True,
    )

    features.setdefault(
        "odds_shift_analysis",
        True,
    )

    movement = settings.setdefault(
        "movement",
        {},
    )

    if not isinstance(movement, dict):
        movement = {}
        settings["movement"] = movement

    movement.setdefault(
        "neutral_threshold_pp",
        0.50,
    )

    movement.setdefault(
        "strong_threshold_pp",
        2.00,
    )

    movement.setdefault(
        "minimum_external_books",
        2,
    )

    movement.setdefault(
        "minimum_agreement",
        0.60,
    )

    movement.setdefault(
        "strong_agreement",
        0.75,
    )

    movement.setdefault(
        "adjacent_line_tolerance",
        0.50,
    )

    data.setdefault(
        "odds_movements",
        [],
    )

    return data


# ============================================================
# 7. Cached engine execution
# ============================================================

@st.cache_data(
    show_spinner=False,
    max_entries=24,
)
def cached_engine_run(
    canonical_json: str,
    engine_fingerprint: str,
) -> Dict[str, Any]:
    del engine_fingerprint

    return aegis.run_engine(
        json.loads(
            canonical_json
        )
    )


def engine_fingerprint() -> str:
    content = b""

    modules = [
        aegis_v2,
        aegis,
    ]

    seen_paths = set()

    for module in modules:
        path = getattr(
            module,
            "__file__",
            None,
        )

        if (
            not path
            or path in seen_paths
        ):
            continue

        seen_paths.add(
            path
        )

        try:
            with open(
                path,
                "rb",
            ) as file:
                content += file.read()

        except OSError:
            content += optional_text(
                path
            ).encode("utf-8")

    return hashlib.sha256(
        content
    ).hexdigest()


def execute_engine(
    input_data: Dict[str, Any],
) -> Dict[str, Any]:
    normalized = normalize_v3_input(
        input_data
    )

    canonical = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=json_default,
    )

    fingerprint = engine_fingerprint()

    analysis_hash = hashlib.sha256(
        (
            canonical
            + fingerprint
        ).encode("utf-8")
    ).hexdigest()

    if (
        st.session_state.get(
            "analysis_hash"
        )
        == analysis_hash
        and st.session_state.get(
            "result"
        )
        is not None
    ):
        return st.session_state[
            "result"
        ]

    result = cached_engine_run(
        canonical,
        fingerprint,
    )

    st.session_state[
        "analysis_hash"
    ] = analysis_hash

    st.session_state[
        "result"
    ] = result

    st.session_state[
        "input_snapshot"
    ] = result.get(
        "input_snapshot",
        normalized,
    )

    return result


# ============================================================
# 8. Result renderers
# ============================================================

def recommendation_card(
    recommendation: Dict[str, Any],
) -> None:
    rank = recommendation.get(
        "rank",
        recommendation.get(
            "official_rank",
            "—",
        ),
    )

    hit_min = probability_value(
        recommendation,
        "hit",
        "minimum",
    )

    hit_median = probability_value(
        recommendation,
        "hit",
        "median",
    )

    nonloss = probability_value(
        recommendation,
        "nonloss",
        "minimum",
    )

    full_loss = probability_value(
        recommendation,
        "full_loss",
        "maximum",
    )

    ev_min = summary_value(
        recommendation,
        "expected_return",
        "minimum",
    )

    shift = recommendation.get(
        "odds_shift",
        {},
    )

    shift_text = ""

    if isinstance(shift, dict):
        verdict = shift.get(
            "verdict"
        )

        strength = shift.get(
            "strength"
        )

        if verdict:
            shift_text = (
                "<br>市場走勢："
                f"<b>{html_escape(status_chinese(verdict))}</b>"
                "｜強度："
                f"<b>{html_escape(status_chinese(strength))}</b>"
            )

    st.markdown(
        f"""
        <div class="recommendation-card">
            <div class="period-badge">
                {html_escape(recommendation.get("period", "FT"))}
            </div>
            <div class="recommendation-rank">
                OFFICIAL PICK #{html_escape(rank)}
            </div>
            <div class="recommendation-name">
                {html_escape(recommendation.get("label", "—"))}
            </div>
            <div class="recommendation-stats">
                HKJC 賠率：
                <b>{format_odds(recommendation.get("hkjc_odds"))}</b>
                ｜保守命中率：
                <b>{format_probability(hit_min)}</b>
                ｜中位命中率：
                <b>{format_probability(hit_median)}</b>
                ｜保守不輸率：
                <b>{format_probability(nonloss)}</b>
                <br>
                最大全輸率：
                <b>{format_probability(full_loss)}</b>
                ｜保守 EV：
                <b>{format_ev(ev_min)}</b>
                ｜價格：
                <b>{html_escape(
                    status_chinese(
                        recommendation.get("price_status")
                    )
                )}</b>
                {shift_text}
            </div>
            <div class="recommendation-stats" style="margin-top:4px;padding-top:4px;border-top:1px dashed rgba(255,255,255,0.15);">
                <b>市場共識：</b>
                {
                    f'{safe_float(recommendation.get("consensus_pct"), 0.0) * 100:.0f}%'
                    if recommendation.get("consensus_pct") is not None
                    else '—'
                }
                ｜<b>Pinnacle 對齊：</b>
                {
                    '✅ 是'
                    if recommendation.get("pinnacle_alignment") is True
                    else (
                        '❌ 否'
                        if recommendation.get("pinnacle_alignment") is False
                        else '—'
                    )
                }
                ｜<b>平均偏差：</b>
                {
                    f'{safe_float(recommendation.get("mean_deviation_pp"), 0.0):.1f}pp'
                    if recommendation.get("mean_deviation_pp") is not None
                    else '—'
                }
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def candidate_dataframe(
    candidates: List[Dict[str, Any]],
) -> pd.DataFrame:
    rows = []

    for candidate in candidates:
        shift = candidate.get(
            "odds_shift",
            {},
        )

        if not isinstance(shift, dict):
            shift = {}

        prior_comparison = candidate.get(
            "pre_projection_prior_comparison",
            {},
        )

        disparity = (
            prior_comparison.get(
                "disparity",
                {},
            )
            if isinstance(
                prior_comparison,
                dict,
            )
            else {}
        )

        reasons = []

        for key in [
            "exclusion_reasons",
            "official_exclusion_reasons",
        ]:
            values = candidate.get(
                key,
                [],
            )

            if isinstance(values, list):
                reasons.extend(
                    optional_text(value)
                    .replace("_", " ")
                    for value in values
                )

        rows.append({
            "正式": (
                "✅"
                if candidate.get("official")
                else ""
            ),
            "排名": candidate.get(
                "official_rank"
            ),
            "ID": candidate.get("id"),
            "候選盤": candidate.get(
                "label"
            ),
            "時段": candidate.get(
                "period"
            ),
            "市場": candidate.get(
                "market"
            ),
            "HKJC 賠率": candidate.get(
                "hkjc_odds"
            ),
            "保守命中率": format_probability(
                probability_value(
                    candidate,
                    "hit",
                    "minimum",
                )
            ),
            "中位命中率": format_probability(
                probability_value(
                    candidate,
                    "hit",
                    "median",
                )
            ),
            "保守不輸率": format_probability(
                probability_value(
                    candidate,
                    "nonloss",
                    "minimum",
                )
            ),
            "保守 EV": format_ev(
                summary_value(
                    candidate,
                    "expected_return",
                    "minimum",
                )
            ),
            "價格": status_chinese(
                candidate.get(
                    "price_status"
                )
            ),
            "Prior 差距": format_probability(
                disparity.get(
                    "median_hit_range"
                ),
                2,
            ),
            "走勢": status_chinese(
                shift.get(
                    "verdict",
                    "NOT_AVAILABLE",
                )
            ),
            "走勢強度": status_chinese(
                shift.get(
                    "strength",
                    "NONE",
                )
            ),
            "市場變動": (
                _fmt_market_change(
                    shift.get(
                        "market_implied_probability_change_pp"
                    )
                )
            ),
            "排除原因": "；".join(
                reasons
            ),
            "共識度": (
                f"{safe_float(candidate.get('consensus_pct'), 0.0) * 100:.0f}%"
                if candidate.get("consensus_pct") is not None
                else "—"
            ),
            "Pinnacle 對齊": (
                "✅ 是"
                if candidate.get("pinnacle_alignment")
                else (
                    "❌ 否"
                    if candidate.get("pinnacle_alignment") is False
                    else "—"
                )
            ),
            "平均偏差(pp)": (
                f"{safe_float(candidate.get('mean_deviation_pp'), 0.0):.1f}"
                if candidate.get("mean_deviation_pp") is not None
                else "—"
            ),
        })

    return pd.DataFrame(
        rows
    )


def consensus_dataframe(
    records: List[Dict[str, Any]],
) -> pd.DataFrame:
    """把 market consensus 檢查結果整理成顯示用的 dataframe。"""
    if not records:
        return pd.DataFrame()

    rows = []

    for record in records:
        rows.append({
            "市場": record.get("market"),
            "時段": record.get("period"),
            "選項": record.get("selection"),
            "線位": (
                f'{safe_float(record.get("line"), 0.0):.2f}'
                if record.get("line") is not None
                else "—"
            ),
            "Pinnacle 機率": format_probability(
                record.get("pinnacle_probability"),
            ),
            "共識度": (
                f'{safe_float(record.get("consensus_pct"), 0.0) * 100:.0f}%'
                if record.get("consensus_pct") is not None
                else "—"
            ),
            "Pinnacle 對齊": (
                "✅ 是"
                if record.get("pinnacle_alignment")
                else (
                    "❌ 否"
                    if record.get("pinnacle_alignment") is False
                    else "—"
                )
            ),
            "平均偏差(pp)": (
                f'{safe_float(record.get("mean_deviation_pp"), 0.0):.2f}'
                if record.get("mean_deviation_pp") is not None
                else "—"
            ),
            "最大偏差(pp)": (
                f'{safe_float(record.get("max_deviation_pp"), 0.0):.2f}'
                if record.get("max_deviation_pp") is not None
                else "—"
            ),
            "莊家數": record.get("n_books"),
        })

    return pd.DataFrame(
        rows
    )


def prior_dataframe(
    candidate: Dict[str, Any],
) -> pd.DataFrame:
    comparison = candidate.get(
        "pre_projection_prior_comparison",
        {},
    )

    priors = (
        comparison.get(
            "priors",
            {},
        )
        if isinstance(
            comparison,
            dict,
        )
        else {}
    )

    rows = []

    for prior_name in [
        "DIXON_COLES",
        "INDEPENDENT_POISSON",
        "COM_POISSON",
    ]:
        record = priors.get(
            prior_name,
            {},
        )

        if not record.get(
            "available"
        ):
            rows.append({
                "Prior": prior_name,
                "可用": "否",
                "情境數": 0,
                "最低命中率": "—",
                "中位命中率": "—",
                "最高命中率": "—",
                "中位 EV": "—",
                "中位公平賠率": "—",
            })
            continue

        hit = (
            record.get(
                "probability",
                {},
            ).get(
                "hit",
                {},
            )
        )

        expected_return = record.get(
            "expected_return",
            {},
        )

        fair_odds = record.get(
            "fair_odds",
            {},
        )

        rows.append({
            "Prior": prior_name,
            "可用": "是",
            "情境數": record.get(
                "scenario_count"
            ),
            "最低命中率": format_probability(
                hit.get("minimum"),
                2,
            ),
            "中位命中率": format_probability(
                hit.get("median"),
                2,
            ),
            "最高命中率": format_probability(
                hit.get("maximum"),
                2,
            ),
            "中位 EV": format_ev(
                expected_return.get(
                    "median"
                )
            ),
            "中位公平賠率": format_odds(
                fair_odds.get(
                    "median"
                )
            ),
        })

    return pd.DataFrame(
        rows
    )


def movement_dataframe(
    audits: List[Dict[str, Any]],
) -> pd.DataFrame:
    rows = []

    for audit in audits:
        primary = audit.get(
            "pinnacle_confirmation",
            {},
        )

        hkjc = audit.get(
            "hkjc_response",
            {},
        )

        rows.append({
            "ID": audit.get("id"),
            "候選盤": audit.get(
                "label"
            ),
            "時段": audit.get(
                "period"
            ),
            "市場": audit.get(
                "market"
            ),
            "結果": status_chinese(
                audit.get(
                    "verdict"
                )
            ),
            "強度": status_chinese(
                audit.get(
                    "strength"
                )
            ),
            "外部莊家數": audit.get(
                "external_book_count"
            ),
            "一致比例": format_probability(
                audit.get(
                    "agreement_ratio"
                )
            ),
            "開盤概率": format_probability(
                audit.get(
                    "consensus_opening_probability"
                ),
                2,
            ),
            "最新概率": format_probability(
                audit.get(
                    "consensus_latest_probability"
                ),
                2,
            ),
            "概率變動": (
                _fmt_market_change(
                    audit.get(
                        "market_implied_probability_change_pp"
                    )
                )
            ),
            "Pinnacle": status_chinese(
                primary.get(
                    "status"
                )
            ),
            "HKJC": status_chinese(
                hkjc.get(
                    "status"
                )
            ),
            "行動提示": optional_text(
                audit.get(
                    "actionability"
                )
            ).replace("_", " "),
        })

    return pd.DataFrame(
        rows
    )


# ============================================================
# 9. Portal helpers
# ============================================================

def configured_api_url() -> str:
    try:
        value = optional_text(
            st.secrets[
                "portal_api"
            ]["url"]
        )

        if value:
            return value

    except Exception:
        pass

    return (
        optional_text(
            os.getenv(
                "AEGIS_API_URL"
            )
        )
        or DEFAULT_API_URL
    )


def configured_api_token() -> str:
    try:
        value = optional_text(
            st.secrets[
                "portal_api"
            ]["token"]
        )

        if value:
            return value

    except Exception:
        pass

    return optional_text(
        os.getenv(
            "AEGIS_API_TOKEN"
        )
    )


def portal_request(
    payload: Dict[str, Any],
    timeout: int = 40,
) -> Dict[str, Any]:
    token = configured_api_token()

    if not token:
        raise ValueError(
            "Portal API token 未設定。"
        )

    request_payload = deepcopy(
        payload
    )

    request_payload[
        "token"
    ] = token

    request = urllib.request.Request(
        configured_api_url(),
        data=json.dumps(
            request_payload,
            ensure_ascii=False,
            default=json_default,
        ).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": (
                "application/json; charset=utf-8"
            ),
            "Accept": "application/json",
            "User-Agent": (
                f"AEGIS-ULTRA/{APP_VERSION}"
            ),
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            text = (
                response.read()
                .decode(
                    "utf-8-sig",
                    errors="replace",
                )
            )

    except urllib.error.HTTPError as error:
        text = (
            error.read()
            .decode(
                "utf-8-sig",
                errors="replace",
            )
        )

        raise RuntimeError(
            f"API HTTP {error.code}: {text}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"無法連接 Portal API："
            f"{error.reason}"
        ) from error

    result = json.loads(
        text
    )

    if (
        not isinstance(result, dict)
        or result.get("ok") is not True
    ):
        raise RuntimeError(
            "Portal API 拒絕要求："
            + optional_text(
                result.get("error")
                if isinstance(result, dict)
                else result
            )
        )

    return result


def _json_or_empty(value: Any) -> str:
    """
    把一個值序列化為 JSON 字串，用於塞進 analysis 表的
    *_json 欄位。None / 空結構一律回空字串，
    避免 Sheet 裡堆滿 "null" / "[]" 雜訊。
    """

    if value is None:
        return ""

    if isinstance(
        value,
        (dict, list),
    ):
        if (
            isinstance(
                value,
                list,
            )
            and not value
        ):
            return ""

        if (
            isinstance(
                value,
                dict,
            )
            and not value
        ):
            return ""

        return json.dumps(
            value,
            ensure_ascii=False,
            default=json_default,
        )

    return optional_text(value)


def _extract_movement_audits(
    result: Dict[str, Any],
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    優先取 engine 產出的結構化走勢審計；找不到時退回到各
    候選盤上的 odds_movement 快照，再退回到單一分析容器。
    """

    audits: List[Dict[str, Any]] = []

    # 建立 label → candidate_id 映射，用於從走勢審計反查所屬推薦
    label_to_cid: Dict[str, str] = {}

    for candidate in candidates:
        if not isinstance(
            candidate,
            dict,
        ):
            continue

        cid = optional_text(
            candidate.get("id")
        )

        if not cid:
            continue

        for key in (
            "label",
            "name",
            "title",
            "candidate_label",
        ):
            label = optional_text(
                candidate.get(key)
            )

            if label and label not in label_to_cid:
                label_to_cid[label] = cid

    for container_name in (
        "odds_movement_analysis",
        "odds_shift_analysis",
    ):
        container = result.get(
            container_name
        )

        if isinstance(
            container,
            dict,
        ):
            series = (
                container.get("candidate_audits")
                or container.get("audits")
                or container.get("movements")
                or container.get("series")
            )

            if isinstance(
                series,
                list,
            ):
                for item in series:
                    if not isinstance(
                        item,
                        dict,
                    ):
                        continue

                    # 帶上所屬 candidate_id，供 Portal 端按推薦過濾
                    if "candidate_id" not in item:
                        cid = (
                            container.get("candidate_id")
                            or container.get("id")
                        )

                        if not cid:
                            # 嘗試從 label / id 反查
                            for lookup_key in (
                                "label",
                                "name",
                                "market",
                                "market_name",
                                "id",
                            ):
                                label_val = optional_text(
                                    item.get(lookup_key)
                                )

                                if (
                                    label_val
                                    and label_val in label_to_cid
                                ):
                                    cid = label_to_cid[
                                        label_val
                                    ]
                                    break

                        if cid:
                            item = dict(
                                item,
                                candidate_id=cid,
                            )

                    audits.append(item)

    if not audits:
        seen = set()

        for candidate in candidates:
            movement = candidate.get(
                "odds_movement"
            )

            cid = optional_text(
                candidate.get("id")
            )

            if isinstance(
                movement,
                list,
            ):
                for item in movement:
                    if not isinstance(
                        item,
                        dict,
                    ):
                        continue

                    key = json.dumps(
                        item,
                        sort_keys=True,
                        default=str,
                    )

                    if key not in seen:
                        seen.add(key)

                        if cid:
                            item = dict(
                                item,
                                candidate_id=cid,
                            )

                        audits.append(item)

    return audits


def build_analysis_payload(
    result: Dict[str, Any],
    match_id: str,
    published_at: Optional[str] = None,
) -> Dict[str, Any]:
    """
    產出對應 GAS analysis 表結構的 payload。所有可序列化的
    遙測都保留下來，正式推薦的 model_direction 也一併帶入，
    讓會員端能直接顯示賽事方向而不用反查 matches 表。
    """

    if not isinstance(
        result,
        dict,
    ):
        return {}

    candidates = result.get(
        "candidate_markets",
        [],
    )

    if not isinstance(
        candidates,
        list,
    ):
        candidates = []

    quality = result.get(
        "model_quality",
        {},
    )

    coherence = result.get(
        "ht_ft_coherence",
        {},
    )

    movement_container = (
        result.get("odds_movement_analysis")
        or result.get("odds_shift_analysis")
        or {}
    )

    if not isinstance(
        movement_container,
        dict,
    ):
        movement_container = {}

    family_out_records: List[Dict[str, Any]] = []
    stress_records: List[Dict[str, Any]] = []
    prior_records: List[Dict[str, Any]] = []
    correct_score_records: List[Dict[str, Any]] = []

    for candidate in candidates:
        if not isinstance(
            candidate,
            dict,
        ):
            continue

        family = candidate.get(
            "family_out_audit"
        )

        if isinstance(
            family,
            dict,
        ):
            family_out_records.append({
                "candidate_id": optional_text(
                    candidate.get("id")
                ),
                "label": optional_text(
                    candidate.get("label")
                ),
                "period": optional_text(
                    candidate.get("period")
                ),
                **family,
            })

        stress = candidate.get(
            "stress_audit"
        )

        if isinstance(
            stress,
            dict,
        ):
            stress_records.append({
                "candidate_id": optional_text(
                    candidate.get("id")
                ),
                "label": optional_text(
                    candidate.get("label")
                ),
                **stress,
            })

        # prior 實際結構：candidate["pre_projection_prior_comparison"]["priors"]
        prior_comparison = candidate.get(
            "pre_projection_prior_comparison"
        ) or candidate.get(
            "prior_comparison"
        )

        if isinstance(
            prior_comparison,
            dict,
        ):
            # 如果是完整的比較容器，取出 priors 部分
            priors = prior_comparison.get(
                "priors",
                {},
            )

            if not isinstance(
                priors,
                dict,
            ):
                priors = {}

            prior_records.append({
                "candidate_id": optional_text(
                    candidate.get("id")
                ),
                "label": optional_text(
                    candidate.get("label")
                ),
                "priors": priors,
                "disparity": prior_comparison.get(
                    "disparity",
                    {},
                ),
                **{
                    k: v
                    for k, v in prior_comparison.items()
                    if k not in (
                        "priors",
                        "disparity",
                    )
                },
            })

        # correct_score_references / correct_scores 是「整場一份」的結構，
        # 不在單一 candidate 上，所以迴圈內不再逐條撈取。
        pass

    # ---- 波膽參考：整場層級（correct_scores.recommendations）----
    # engine 產出的波膽結構為：
    #   result["correct_scores"] = {
    #       "warning": "...",
    #       "recommendations": [{"score": "2-1", "probability": {...}}, ...]
    #   }
    # 因此要讀取 correct_scores.recommendations，而非 candidate 上的欄位。
    cs_container = (
        result.get("correct_scores")
        or result.get("correct_score_references")
    )

    if isinstance(
        cs_container,
        dict,
    ):
        cs_list = (
            cs_container.get("recommendations")
            or cs_container.get("scores")
            or cs_container.get("items")
        )

        if isinstance(
            cs_list,
            list,
        ):
            correct_score_records.extend(
                item
                for item in cs_list
                if isinstance(
                    item,
                    dict,
                )
            )

    elif isinstance(
        cs_container,
        list,
    ):
        correct_score_records.extend(
            item
            for item in cs_container
            if isinstance(
                item,
                dict,
            )
        )

    consensus = result.get(
        "consensus",
        {},
    )

    if not isinstance(
        consensus,
        dict,
    ):
        consensus = {}

    runtime = (
        result.get(
            "runtime",
            {},
        )
        if isinstance(
            result.get("runtime"),
            dict,
        )
        else {}
    )

    now = (
        published_at
        or datetime.now()
        .astimezone()
        .isoformat(
            timespec="seconds",
        )
    )

    manual_direction = (
        st.session_state.get(
            "manual_model_direction"
        )
        if "manual_model_direction" in st.session_state
        else ""
    )

    engine_direction = ""

    if isinstance(
        quality,
        dict,
    ):
        engine_direction = optional_text(
            quality.get("direction")
            or quality.get("model_direction")
        )

    return {
        "match_id": match_id,
        "model_quality_status": optional_text(
            quality.get("status")
            if isinstance(
                quality,
                dict,
            )
            else quality
        ),
        "ht_ft_coherence_status": optional_text(
            coherence.get("status")
            if isinstance(
                coherence,
                dict,
            )
            else coherence
        ),
        "odds_movement_status": optional_text(
            movement_container.get("status")
        ),
        "model_direction": (
            manual_direction
            or engine_direction
        ),
        "engine_version": ENGINE_VERSION,
        "runtime_seconds": (
            runtime.get("total_seconds")
            if isinstance(
                runtime,
                dict,
            )
            else None
        ),
        "published_at": now,
        "updated_at": now,
        "movement_audits_json": _json_or_empty(
            _extract_movement_audits(
                result,
                candidates,
            )
        ),
        "family_out_json": _json_or_empty(
            family_out_records
        ),
        "stress_audits_json": _json_or_empty(
            stress_records
        ),
        "prior_comparison_json": _json_or_empty(
            prior_records
        ),
        "correct_scores_json": _json_or_empty(
            correct_score_records
        ),
        "consensus_json": _json_or_empty(
            consensus
        ),
    }


def stable_match_id(
    result: Dict[str, Any],
) -> str:
    match = result.get(
        "match",
        {},
    )

    identity = "|".join([
        optional_text(
            match.get("home")
        ).casefold(),
        optional_text(
            match.get("away")
        ).casefold(),
        optional_text(
            match.get("competition")
        ).casefold(),
        optional_text(
            match.get("kickoff")
        ),
    ])

    digest = hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()[:20]

    return f"match_{digest}"


def build_portal_bundle(
    result: Dict[str, Any],
    selected_ids: set,
    publish_status: str,
) -> Dict[str, Any]:
    match = result.get(
        "match",
        {},
    )

    match_id = stable_match_id(
        result
    )

    records = []

    candidates = result.get(
        "candidate_markets",
        [],
    )

    for candidate in candidates:
        candidate_id = optional_text(
            candidate.get("id")
        )

        if candidate_id not in selected_ids:
            continue

        identity = "|".join([
            match_id,
            candidate_id,
            optional_text(
                candidate.get("period")
            ),
            optional_text(
                candidate.get("market")
            ),
            optional_text(
                candidate.get("selection")
            ),
            optional_text(
                candidate.get("line")
            ),
        ])

        rec_id = (
            "rec_"
            + hashlib.sha256(
                identity.encode("utf-8")
            ).hexdigest()[:22]
        )

        # 讀取手動 tier（session_state）
        manual_tier_key = (
            "manual_tier_"
            + candidate_id
        )

        manual_tier = (
            st.session_state.get(
                manual_tier_key
            )
            if manual_tier_key in st.session_state
            else None
        )

        if not manual_tier:
            manual_tier = (
                "OFFICIAL"
                if candidate.get("official")
                else "ALTERNATIVE"
            )

        # 讀取手動 commentary（session_state）
        manual_commentary_key = (
            "manual_commentary_"
            + candidate_id
        )

        manual_commentary = (
            st.session_state.get(
                manual_commentary_key
            )
            if manual_commentary_key in st.session_state
            else ""
        )

        records.append({
            "rec_id": rec_id,
            "match_id": match_id,
            "tier": manual_tier,
            "commentary": manual_commentary,
            "rank": (
                candidate.get(
                    "official_rank"
                )
                or 999
            ),
            "rec_title": candidate.get(
                "label"
            ),
            "market": candidate.get(
                "market"
            ),
            "selection": candidate.get(
                "selection"
            ),
            "line": (
                candidate.get("line")
                if candidate.get("line")
                is not None
                else ""
            ),
            "odds": candidate.get(
                "hkjc_odds"
            ),
            "conservative_hit": probability_value(
                candidate,
                "hit",
                "minimum",
            ),
            "median_hit": probability_value(
                candidate,
                "hit",
                "median",
            ),
            "nonloss_probability": probability_value(
                candidate,
                "nonloss",
                "minimum",
            ),
            "full_loss_probability": probability_value(
                candidate,
                "full_loss",
                "maximum",
            ),
            "fair_odds": summary_value(
                candidate,
                "fair_odds",
                "maximum",
            ),
            "price_status": candidate.get(
                "price_status"
            ),
            "stars": (
                4
                if candidate.get("official")
                else 3
            ),
            "is_heavy": False,
            "compatibility_group": "",
            "conflict_ids": "",
            "result": "pending",
            "status": publish_status,
            "period": candidate.get(
                "period"
            ),
            "market_scope": (
                candidate.get("team")
                or ""
            ),
            "edge": "",
            "expected_value": summary_value(
                candidate,
                "expected_return",
                "minimum",
            ),
        })

    return {
        "action": "publish_bundle",
        "replace_recommendations": True,
        "match": {
            "match_id": match_id,
            "match_name": (
                match.get("name")
                or (
                    f"{match.get('home', '')} "
                    f"vs {match.get('away', '')}"
                )
            ),
            "home_team": match.get(
                "home"
            ),
            "away_team": match.get(
                "away"
            ),
            "competition": match.get(
                "competition"
            ),
            "kickoff": match.get(
                "kickoff"
            ),
            "status": publish_status,
            "model_direction": (
                st.session_state.get(
                    "manual_model_direction"
                )
                if "manual_model_direction" in st.session_state
                and st.session_state.get(
                    "manual_model_direction"
                )
                else (
                    "；".join(
                        optional_text(
                            item.get("label")
                        )
                        for item in result.get(
                            "recommendations",
                            [],
                        )
                    )
                    or "沒有正式推薦"
                )
            ),
            "model_summary": (
                f"AEGIS Engine V{ENGINE_VERSION}"
            ),
            "top_scores": "",
            "final_score": "",
        },
        "recommendations": records,
        # V3 增量：把完整遙測包進同一份 bundle，
        # 由 GAS 端的 publish_analysis 寫入 analysis 表。
        # 若本次結果沒有可序列化的遙測，此欄會是空 dict，
        # 發布時應略過 analysis 呼叫。
        "analysis": build_analysis_payload(
            result,
            match_id,
        ),
    }


# ============================================================
# 10. Session state
# ============================================================

DEFAULTS = {
    "result": None,
    "input_snapshot": None,
    "analysis_hash": None,
    "error": None,
    "traceback": None,
    "json_input": json_text(
        example_json_input()
    ),
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[
            key
        ] = value


# ============================================================
# 11. Header
# ============================================================

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-badge">
            ENGINE V{html_escape(ENGINE_VERSION)}
            · APP V{APP_VERSION}
        </div>
        <h1 class="hero-title">
            🛡️ AEGIS ULTRA V3
        </h1>
        <div class="hero-text">
            Sharp-market reconstruction with Multiplicative,
            Power and Shin de-vigging; Dixon–Coles,
            Independent Poisson and COM-Poisson prior
            comparison; target-line-out reconstruction;
            stress audits; HT–FT coherence; and structured
            external/Pinnacle/HKJC odds-movement analysis.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 12. Sidebar
# ============================================================

with st.sidebar:
    st.markdown(
        "## 🛡️ AEGIS ULTRA"
    )

    st.caption(
        f"App V{APP_VERSION} · "
        f"Engine V{ENGINE_VERSION}"
    )

    st.success(
        "V3 features enabled:\n\n"
        "• Shin de-vig\n"
        "• Prior comparison\n"
        "• Odds movement audit"
    )

    st.divider()

    if st.button(
        "🗑️ 清除分析",
        use_container_width=True,
    ):
        cached_engine_run.clear()

        st.session_state[
            "result"
        ] = None

        st.session_state[
            "input_snapshot"
        ] = None

        st.session_state[
            "analysis_hash"
        ] = None

        st.session_state[
            "error"
        ] = None

        st.session_state[
            "traceback"
        ] = None

        st.rerun()

    st.divider()

    if st.button(
        "🧹 清除 Engine Cache",
        use_container_width=True,
        help="只清 engine 的 @st.cache_data，不影響目前分析結果。用於釋放記憶體。",
    ):
        cached_engine_run.clear()
        st.toast("Engine cache 已清除")

    st.divider()

    st.caption(
        "CORRECT_SCORE 不可作為輸入市場。"
        "波膽由 FT 模型自動產生。"
    )


# ============================================================
# 13. Input interface
# ============================================================

input_tab, upload_tab, movement_help_tab = st.tabs([
    "📋 完整 V3 JSON",
    "📁 上載 JSON",
    "📈 Odds movement 格式",
])

input_to_run = None


with input_tab:
    st.info(
        "可直接修改完整 V3 JSON。"
        "devig_methods 可包含 SHIN；"
        "odds_movements 可留空。"
    )

    json_input = st.text_area(
        "AEGIS ULTRA V3 輸入",
        key="json_input",
        height=680,
    )

    first, second = st.columns(2)

    with first:
        run_json = st.button(
            "🚀 執行 V3 分析",
            type="primary",
            use_container_width=True,
        )

    with second:
        st.download_button(
            "⬇️ 下載輸入 JSON",
            data=json_input,
            file_name=download_name(
                "aegis_ultra_v3_input"
            ),
            mime="application/json",
            use_container_width=True,
        )

    if run_json:
        try:
            parsed = json.loads(
                json_input
            )

            input_to_run = normalize_v3_input(
                parsed
            )

        except Exception as error:
            st.session_state[
                "error"
            ] = str(error)

            st.session_state[
                "traceback"
            ] = traceback.format_exc()


with upload_tab:
    uploaded_file = st.file_uploader(
        "上載 V3 JSON",
        type=["json"],
    )

    if uploaded_file is not None:
        try:
            uploaded_data = json.loads(
                uploaded_file
                .getvalue()
                .decode("utf-8-sig")
            )

            st.json(
                uploaded_data
            )

            if st.button(
                "🚀 執行上載 JSON",
                type="primary",
                use_container_width=True,
            ):
                input_to_run = normalize_v3_input(
                    uploaded_data
                )

        except Exception as error:
            st.error(
                f"JSON 讀取失敗：{error}"
            )


with movement_help_tab:
    st.markdown(
        """
        ### Odds movement series example

        Each series needs:

        - bookmaker/key
        - role: `EXTERNAL`, `PRIMARY`, or `HKJC`
        - period and market
        - line where required
        - at least two observations
        - complete market odds at every observation

        HK odds may be supplied with `"odds_format": "HK"`.
        """
    )

    st.code(
        json_text({
            "odds_movements": [
                {
                    "id": "MOVE_001",
                    "bookmaker": "Bookmaker A",
                    "key": "book_a",
                    "role": "EXTERNAL",
                    "period": "FT",
                    "market": "OU",
                    "line": 2.25,
                    "odds_format": "DECIMAL",
                    "observations": [
                        {
                            "timestamp": "2026-09-20T10:00:00+08:00",
                            "odds": {
                                "over": 1.95,
                                "under": 1.95,
                            },
                        },
                        {
                            "timestamp": "2026-09-20T12:00:00+08:00",
                            "odds": {
                                "over": 2.05,
                                "under": 1.85,
                            },
                        },
                    ],
                }
            ]
        }),
        language="json",
    )


# ============================================================
# 14. Execute engine
# ============================================================

if input_to_run is not None:
    st.session_state[
        "error"
    ] = None

    st.session_state[
        "traceback"
    ] = None

    with st.expander(
        "提交給引擎的標準化輸入",
        expanded=False,
    ):
        st.json(
            input_to_run
        )

    try:
        with st.spinner(
            "執行 V3 市場重建、三種 prior 比較、"
            "壓力測試、HT–FT 一致性及市場走勢分析……"
        ):
            execute_engine(
                input_to_run
            )

        st.success(
            "AEGIS ULTRA V3 分析完成。"
        )

    except Exception as error:
        st.session_state[
            "error"
        ] = str(error)

        st.session_state[
            "traceback"
        ] = traceback.format_exc()


if st.session_state.get(
    "error"
):
    st.error(
        "引擎執行失敗："
        + st.session_state[
            "error"
        ]
    )

    with st.expander(
        "技術錯誤詳情",
        expanded=False,
    ):
        st.code(
            st.session_state.get(
                "traceback"
            )
            or st.session_state[
                "error"
            ],
            language="text",
        )


# ============================================================
# 15. Results
# ============================================================

result = st.session_state.get(
    "result"
)

if result:
    st.divider()

    match = result.get(
        "match",
        {},
    )

    st.header(
        "📡 "
        + optional_text(
            match.get("name")
        )
    )

    caption = " ｜ ".join(
        optional_text(value)
        for value in [
            match.get("competition"),
            match.get("kickoff"),
            match.get("snapshot_time"),
        ]
        if optional_text(value)
    )

    if caption:
        st.caption(
            caption
        )

    recommendations = result.get(
        "recommendations",
        [],
    )

    candidates = result.get(
        "candidate_markets",
        [],
    )

    quality = (
        result.get(
            "model_quality",
            {},
        ).get(
            "status",
            "UNKNOWN",
        )
    )

    coherence = (
        result.get(
            "ht_ft_coherence",
            {},
        ).get(
            "status",
            "NOT_AVAILABLE",
        )
    )

    movement_status = (
        result.get(
            "odds_shift_analysis",
            {},
        ).get(
            "status",
            "NOT_PROVIDED",
        )
    )

    runtime = (
        result.get(
            "runtime",
            {},
        ).get(
            "total_seconds"
        )
    )

    first, second, third, fourth, fifth = st.columns(
        5
    )

    with first:
        result_summary_card(
            "模型品質",
            status_chinese(
                quality
            ),
            "Projection and grid quality",
            status_css_class(
                quality
            ),
        )

    with second:
        result_summary_card(
            "正式推薦",
            str(
                len(recommendations)
            ),
            f"候選盤 {len(candidates)}",
        )

    with third:
        result_summary_card(
            "HT–FT",
            status_chinese(
                coherence
            ),
            "Transport coherence",
            status_css_class(
                coherence
            ),
        )

    with fourth:
        result_summary_card(
            "Odds movement",
            status_chinese(
                movement_status
            ),
            "External/Pinnacle/HKJC",
            status_css_class(
                movement_status
            ),
        )

    with fifth:
        result_summary_card(
            "執行時間",
            (
                f"{runtime:.2f} 秒"
                if safe_float(runtime)
                is not None
                else "—"
            ),
            f"Engine V{ENGINE_VERSION}",
        )

    # ── V3 模型健康診斷面板（Hero 正下方、tabs 之前）──
    render_health_panel(
        result
    )

    section = st.radio(
        "結果部分",
        options=[
            "正式推薦",
            "所有候選盤",
            "Prior 比較",
            "Odds movement",
            "穩健性",
            "波膽參考",
            "模型診斷",
            "市場共識",
            "Portal 發佈",
            "完整 JSON",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

    if section == "正式推薦":
        st.subheader(
            "正式推薦"
        )

        if not recommendations:
            st.warning(
                "沒有候選盤通過正式推薦條件。"
            )

        for recommendation in sorted(
            recommendations,
            key=lambda item: (
                PERIOD_ORDER.get(
                    item.get("period"),
                    9,
                ),
                safe_int(
                    item.get("rank"),
                    999,
                ),
            ),
        ):
            recommendation_card(
                recommendation
            )

    elif section == "所有候選盤":
        st.subheader(
            "所有候選盤"
        )

        table = candidate_dataframe(
            candidates
        )

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
        )

    elif section == "Prior 比較":
        st.subheader(
            "Pre-projection prior comparison"
        )

        st.info(
            "Dixon–Coles 仍是唯一 projection baseline。"
            "Independent Poisson 與 COM-Poisson 只作"
            " projection 前敏感度診斷。"
        )

        if not candidates:
            st.info(
                "沒有候選盤。"
            )

        else:
            labels = [
                (
                    f"{candidate.get('id')}｜"
                    f"{candidate.get('period')}｜"
                    f"{candidate.get('label')}"
                )
                for candidate in candidates
            ]

            selected_label = st.selectbox(
                "候選盤",
                labels,
            )

            candidate = candidates[
                labels.index(
                    selected_label
                )
            ]

            comparison = candidate.get(
                "pre_projection_prior_comparison",
                {},
            )

            disparity = comparison.get(
                "disparity",
                {},
            )

            first, second, third = st.columns(
                3
            )

            first.metric(
                "最低 prior",
                disparity.get(
                    "minimum_prior"
                )
                or "—",
            )

            second.metric(
                "最高 prior",
                disparity.get(
                    "maximum_prior"
                )
                or "—",
            )

            third.metric(
                "中位命中率差距",
                _fmt_market_change(
                    disparity.get(
                        "median_hit_range_pp"
                    )
                ),
            )

            st.dataframe(
                prior_dataframe(
                    candidate
                ),
                use_container_width=True,
                hide_index=True,
            )

            with st.expander(
                "完整 prior comparison",
                expanded=False,
            ):
                st.json(
                    comparison
                )

    elif section == "Odds movement":
        st.subheader(
            "Structured odds-movement audit"
        )

        movement = result.get(
            "odds_shift_analysis",
            {},
        )

        status = movement.get(
            "status",
            "NOT_PROVIDED",
        )

        st.info(
            "狀態："
            + status_chinese(
                status
            )
        )

        audits = movement.get(
            "candidate_audits",
            [],
        )

        if audits:
            st.dataframe(
                movement_dataframe(
                    audits
                ),
                use_container_width=True,
                hide_index=True,
            )

            labels = [
                (
                    f"{audit.get('id')}｜"
                    f"{audit.get('label')}"
                )
                for audit in audits
            ]

            selected_label = st.selectbox(
                "查看完整走勢分析",
                labels,
            )

            st.json(
                audits[
                    labels.index(
                        selected_label
                    )
                ]
            )

        else:
            st.warning(
                movement.get(
                    "note",
                    "沒有可用 odds movement 資料。",
                )
            )

    elif section == "穩健性":
        st.subheader(
            "Family-out and stress audit"
        )

        if candidates:
            labels = [
                (
                    f"{candidate.get('id')}｜"
                    f"{candidate.get('label')}"
                )
                for candidate in candidates
            ]

            selected_label = st.selectbox(
                "候選盤",
                labels,
                key="robustness_candidate",
            )

            candidate = candidates[
                labels.index(
                    selected_label
                )
            ]

            family = candidate.get(
                "family_out_audit",
                {},
            )

            family_hit = (
                family.get(
                    "probability",
                    {},
                ).get(
                    "hit",
                    {},
                )
            )

            first, second, third = st.columns(
                3
            )

            first.metric(
                "Family-out",
                status_chinese(
                    family.get(
                        "status"
                    )
                ),
            )

            second.metric(
                "最低命中率",
                format_probability(
                    family_hit.get(
                        "minimum"
                    )
                ),
            )

            third.metric(
                "中位命中率",
                format_probability(
                    family_hit.get(
                        "median"
                    )
                ),
            )

            stress = candidate.get(
                "stress_audit",
                {},
            )

            stress_rows = []

            for key, label in [
                ("light", "輕度"),
                ("medium", "中度"),
                ("heavy", "重度"),
            ]:
                record = stress.get(
                    key,
                    {},
                )

                stress_rows.append({
                    "程度": label,
                    "最低命中率": format_probability(
                        record.get(
                            "minimum_hit_probability"
                        )
                    ),
                    "中位命中率": format_probability(
                        record.get(
                            "median_hit_probability"
                        )
                    ),
                    "情境數": record.get(
                        "scenario_count"
                    ),
                })

            st.dataframe(
                pd.DataFrame(
                    stress_rows
                ),
                use_container_width=True,
                hide_index=True,
            )

    elif section == "波膽參考":
        st.subheader(
            "🎯 FT 波膽參考"
        )

        correct_scores = result.get(
            "correct_scores",
            {},
        )

        st.warning(
            correct_scores.get(
                "warning",
                "波膽屬高風險市場。",
            )
        )

        scores = correct_scores.get(
            "recommendations",
            [],
        )

        if scores:
            columns = st.columns(
                len(scores)
            )

            for column, score in zip(
                columns,
                scores,
            ):
                probability = score.get(
                    "probability",
                    {},
                )

                with column:
                    st.markdown(
                        f"""
                        <div class="score-card">
                            <div class="score-value">
                                {html_escape(score.get("score"))}
                            </div>
                            <div class="score-note">
                                保守概率
                                {format_probability(
                                    probability.get("minimum"),
                                    2
                                )}
                            </div>
                            <div class="score-note">
                                中位概率
                                {format_probability(
                                    probability.get("median"),
                                    2
                                )}
                                <br>
                                公平賠率
                                {format_odds(
                                    score.get("central_fair_odds"),
                                    2
                                )}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.info(
                "沒有波膽參考。"
            )

    elif section == "模型診斷":
        st.subheader(
            "模型診斷"
        )

        model = result.get(
            "model",
            {},
        )

        periods = model.get(
            "periods",
            {},
        )

        for period, period_record in sorted(
            periods.items(),
            key=lambda item: PERIOD_ORDER.get(
                item[0],
                9,
            ),
        ):
            st.markdown(
                f"### {period}"
            )

            first, second, third, fourth = st.columns(
                4
            )

            first.metric(
                "最高入球",
                period_record.get(
                    "max_goals_per_team"
                ),
            )

            second.metric(
                "狀態數",
                period_record.get(
                    "state_count"
                ),
            )

            third.metric(
                "完整情境",
                period_record.get(
                    "full_scenario_count"
                ),
            )

            fourth.metric(
                "網格完整",
                (
                    "是"
                    if period_record.get(
                        "grid_complete"
                    )
                    else "否"
                ),
            )

            with st.expander(
                f"{period} full scenarios",
                expanded=False,
            ):
                st.json(
                    period_record.get(
                        "full_scenarios",
                        [],
                    )
                )

        with st.expander(
            "HT–FT coherence",
            expanded=False,
        ):
            st.json(
                result.get(
                    "ht_ft_coherence",
                    {},
                )
            )

        with st.expander(
            "Methodology",
            expanded=False,
        ):
            st.json(
                result.get(
                    "methodology",
                    {},
                )
            )

    elif section == "市場共識":
        st.subheader(
            "📊 市場共識檢查"
        )

        st.info(
            "此表顯示每個候選盤的靜態尾盤共識狀態："
            "多家莊家的 implied probability 是否一致、"
            "Pinnacle 是否站在多數方、各家偏差多大。"
            "這些指標由 engine 計算，不含任何閾值判定。"
        )

        # 從 candidates 收集 consensus 資料
        consensus_records = []

        for candidate in candidates:
            consensus = candidate.get(
                "market_consensus",
                {},
            )

            if not isinstance(
                consensus,
                dict,
            ) or not consensus:
                # 沒有共識資料時，用 candidate 上的扁平欄位建一筆
                if candidate.get(
                    "consensus_pct"
                ) is not None:
                    consensus_records.append({
                        "market": candidate.get(
                            "market"
                        ),
                        "period": candidate.get(
                            "period"
                        ),
                        "selection": candidate.get(
                            "selection"
                        ),
                        "line": candidate.get(
                            "line"
                        ),
                        "pinnacle_probability": candidate.get(
                            "pinnacle_probability"
                        ),
                        "consensus_pct": candidate.get(
                            "consensus_pct"
                        ),
                        "pinnacle_alignment": candidate.get(
                            "pinnacle_alignment"
                        ),
                        "mean_deviation_pp": candidate.get(
                            "mean_deviation_pp"
                        ),
                        "max_deviation_pp": candidate.get(
                            "max_deviation_pp"
                        ),
                        "n_books": candidate.get(
                            "n_books"
                        ),
                    })

                continue

            consensus_records.append({
                "market": consensus.get(
                    "market"
                ),
                "period": consensus.get(
                    "period"
                ),
                "selection": consensus.get(
                    "selection"
                ),
                "line": consensus.get(
                    "line"
                ),
                "pinnacle_probability": consensus.get(
                    "pinnacle_probability"
                ),
                "consensus_pct": consensus.get(
                    "consensus_pct"
                ),
                "pinnacle_alignment": consensus.get(
                    "pinnacle_alignment"
                ),
                "mean_deviation_pp": consensus.get(
                    "mean_deviation_pp"
                ),
                "max_deviation_pp": consensus.get(
                    "max_deviation_pp"
                ),
                "n_books": consensus.get(
                    "n_books"
                ),
            })

        if not consensus_records:
            st.warning(
                "沒有共識資料。engine 可能未執行 market consensus 檢查。"
            )

        else:
            df = consensus_dataframe(
                consensus_records
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

    elif section == "Portal 發佈":
        st.subheader(
            "📤 Portal 發佈"
        )

        publish_status = st.selectbox(
            "狀態",
            [
                "published",
                "draft",
            ],
        )

        # ── 手動輸入區（整場一次填） ──────────────────────
        st.divider()

        st.markdown(
            "**✍️ 手動編輯（整場適用）**"
        )

        manual_direction = st.text_area(
            "賽事方向（Ultra V2 模型方向）",
            key="manual_model_direction",
            placeholder="例：利物浦主勝方向，預計低比分節奏",
            height=68,
        )

        st.divider()

        selected_ids = set()

        for candidate in candidates:
            candidate_id = optional_text(
                candidate.get("id")
            )

            default_selected = bool(
                candidate.get("official")
            )

            if st.checkbox(
                (
                    f"{candidate_id}｜"
                    f"{candidate.get('period')}｜"
                    f"{candidate.get('label')}"
                ),
                value=default_selected,
                key=(
                    "publish_"
                    + candidate_id
                ),
            ):
                selected_ids.add(
                    candidate_id
                )

        # ── 只對「已勾選要發布」的候選盤開放 tier + 短評編輯 ──
        #
        # 手寫賽事方向（整場共用，永遠可編輯）與
        # 逐條 tier / 短評（僅限本次要發布的項目）分開處理：
        # 前者影響整場的比賽敘事，後者只針對即將送出的推薦。
        # 這樣可避免對幾十條候選盤逐條調整，改為先選定目標、
        # 再集中微調進取程度。
        st.divider()

        selected_for_edit = [
            candidate
            for candidate in candidates
            if optional_text(
                candidate.get("id")
            ) in selected_ids
        ]

        if not selected_for_edit:
            st.info(
                "尚未勾選任何要發布的候選盤。"
                "請先在上方的清單中勾選，"
                "才會在此開放等級與短評編輯。"
            )

        else:
            st.markdown(
                f"**✍️ 已勾選 {len(selected_for_edit)} 項"
                f"的等級與短評**"
            )

            st.caption(
                "以下編輯只會套用到本次要發布的項目。"
                "調整正式 / 進取程度，或為「雨姐短評」補充說明。"
            )

            for candidate in selected_for_edit:
                candidate_id = optional_text(
                    candidate.get("id")
                )

                label = (
                    f"{candidate_id}｜"
                    f"{candidate.get('period')}｜"
                    f"{candidate.get('label')}"
                )

                default_tier = (
                    "OFFICIAL"
                    if candidate.get("official")
                    else "ALTERNATIVE"
                )

                # 若 session_state 裡還留著上次的值，
                # 就沿用，否則用 engine 的建議。
                state_key = (
                    "manual_tier_"
                    + candidate_id
                )

                if state_key in st.session_state:
                    default_tier = (
                        st.session_state[state_key]
                    )

                with st.expander(
                    label,
                    expanded=(
                        len(selected_for_edit) <= 3
                    ),
                ):
                    st.selectbox(
                        "推薦等級（調整進取程度）",
                        options=[
                            "OFFICIAL",
                            "ALTERNATIVE",
                            "CORRECT_SCORE",
                        ],
                        index=(
                            0
                            if default_tier == "OFFICIAL"
                            else 1
                            if default_tier == "ALTERNATIVE"
                            else 2
                        ),
                        key=(
                            "manual_tier_"
                            + candidate_id
                        ),
                        help=(
                            "OFFICIAL 為正式推薦，"
                            "ALTERNATIVE 為進取/備選，"
                            "CORRECT_SCORE 為波膽參考"
                        ),
                    )

                    st.text_area(
                        "雨姐短評",
                        key=(
                            "manual_commentary_"
                            + candidate_id
                        ),
                        placeholder=(
                            "例：利物浦主場讓半球的支持度一般，"
                            "需留意"
                        ),
                        height=68,
                    )

        bundle = build_portal_bundle(
            result,
            selected_ids,
            publish_status,
        )

        with st.expander(
            "Portal payload",
            expanded=False,
        ):
            st.json(
                bundle
            )

        st.download_button(
            "⬇️ 下載 Portal payload",
            data=json_text(
                bundle
            ),
            file_name=download_name(
                "aegis_portal_bundle"
            ),
            mime="application/json",
            use_container_width=True,
        )

        if st.button(
            f"📤 發佈 {len(selected_ids)} 項",
            type="primary",
            use_container_width=True,
            disabled=not bool(
                selected_ids
            ),
            help=(
                "先發布 analysis（V3 遙測），"
                "成功後再發布 recommendations 與 match 資料。"
            ),
        ):
            analysis_payload = bundle.get(
                "analysis",
                {},
            )

            has_analysis = bool(
                analysis_payload
            ) and any(
                key.endswith("_json")
                and analysis_payload.get(key)
                for key in (
                    "movement_audits_json",
                    "family_out_json",
                    "stress_audits_json",
                    "prior_comparison_json",
                    "correct_scores_json",
                    "consensus_json",
                )
            )

            bundle_to_send = {
                key: value
                for key, value in bundle.items()
                if key != "analysis"
            }

            analysis_response = None
            bundle_response = None

            try:
                with st.spinner(
                    "正在發佈 analysis（V3 遙測）……"
                    if has_analysis
                    else "正在發佈……"
                ):
                    if has_analysis:
                        analysis_response = portal_request({
                            "action": "publish_analysis",
                            "analysis": analysis_payload,
                        })

                with st.spinner(
                    "正在發佈 match 與 recommendations……"
                ):
                    bundle_response = portal_request(
                        bundle_to_send
                    )

                if has_analysis:
                    st.success(
                        "✅ Analysis（V3 遙測）與 Portal "
                        "推薦已發布成功。"
                    )

                    with st.expander(
                        "Analysis 發布回應",
                        expanded=False,
                    ):
                        st.json(
                            analysis_response
                        )

                else:
                    st.success(
                        "Portal 發布成功。"
                    )

                st.json(
                    bundle_response
                )

            except Exception as error:
                st.error(
                    f"Portal 發布失敗：{error}"
                )

                with st.expander(
                    "錯誤詳情",
                    expanded=False,
                ):
                    st.code(
                        traceback.format_exc(),
                        language="text",
                    )

    elif section == "完整 JSON":
        st.subheader(
            "完整引擎輸出"
        )

        first, second = st.columns(
            2
        )

        with first:
            st.download_button(
                "⬇️ 下載完整結果",
                data=json_text(
                    result
                ),
                file_name=download_name(
                    "aegis_ultra_v3_result"
                ),
                mime="application/json",
                use_container_width=True,
            )

        with second:
            st.download_button(
                "⬇️ 下載標準化輸入",
                data=json_text(
                    st.session_state.get(
                        "input_snapshot"
                    )
                    or {}
                ),
                file_name=download_name(
                    "aegis_ultra_v3_input"
                ),
                mime="application/json",
                use_container_width=True,
            )

        if st.checkbox(
            "顯示完整 JSON",
            value=False,
        ):
            st.json(
                result
            )

else:
    st.info(
        "貼上或上載 AEGIS ULTRA V3 JSON，然後開始分析。"
    )


# ============================================================
# 16. Footer
# ============================================================

st.divider()

st.caption(
    f"{ENGINE_NAME} · Engine V{ENGINE_VERSION} · "
    f"Command Center V{APP_VERSION} · "
    "市場重建及風險分析只供參考，不保證投注結果。"
)
