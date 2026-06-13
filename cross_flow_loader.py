"""
cross_flow_loader.py
====================
Reads cross-data-flow JSON scenario files from the run-test-server workspace
and returns step definitions keyed by test ID.

These step definitions are used by the Python dashboard to render the
per-scenario flowchart modal.

Usage:
    from cross_flow_loader import load_cross_flow_scenarios, get_scenario
    scenarios = load_cross_flow_scenarios()   # dict: { test_id: scenario }
    sc = get_scenario("CROSS_FLOW_BUYER_LIFECYCLE")
"""

import os
import json
import glob

from config import FONT_FAMILY

# ── Path Configuration ──────────────────────────────────────────────────────
# The run-test-server project lives one level above this dashboard.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_RUN_TEST_SERVER_DIR = os.path.join(_SCRIPT_DIR, "..", "run-test-server")
_CROSS_FLOW_DIR = os.path.join(
    _RUN_TEST_SERVER_DIR, "tests", "api", "crossdataflow"
)


def load_cross_flow_scenarios() -> dict:
    """
    Walk the crossdataflow directory and parse every *.json file.
    Returns a dict mapping test_id → scenario dict with keys:
        id, title, description, subType, feature, steps[]
    """
    scenarios = {}

    if not os.path.isdir(_CROSS_FLOW_DIR):
        print(f"[cross_flow_loader] WARNING: crossdataflow dir not found: {_CROSS_FLOW_DIR}")
        return scenarios

    pattern = os.path.join(_CROSS_FLOW_DIR, "*.json")
    files = sorted(glob.glob(pattern))

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Each file is an array of scenario objects
            if isinstance(data, list):
                for sc in data:
                    _id = sc.get("id", "")
                    if _id:
                        scenarios[_id] = sc
            elif isinstance(data, dict) and data.get("id"):
                scenarios[data["id"]] = data

        except Exception as exc:
            print(f"[cross_flow_loader] Skipped {os.path.basename(filepath)}: {exc}")

    print(f"[cross_flow_loader] Loaded {len(scenarios)} cross-flow scenarios.")
    return scenarios


# Module-level cache — loaded once per server start
_SCENARIOS_CACHE: dict | None = None


def get_all_scenarios() -> dict:
    """Return cached scenarios dict (lazy-loaded once)."""
    global _SCENARIOS_CACHE
    if _SCENARIOS_CACHE is None:
        _SCENARIOS_CACHE = load_cross_flow_scenarios()
    return _SCENARIOS_CACHE


def get_scenario(test_id: str) -> dict | None:
    """Return a single scenario by its test ID, or None if not found."""
    return get_all_scenarios().get(test_id)


# ── Step colour helpers ──────────────────────────────────────────────────────

_METHOD_COLORS = {
    "POST":   ("#dbeafe", "#1d4ed8"),   # blue bg / blue text
    "GET":    ("#dcfce7", "#15803d"),   # green
    "DELETE": ("#fee2e2", "#b91c1c"),   # red
    "PUT":    ("#fef9c3", "#92400e"),   # yellow
    "PATCH":  ("#f3e8ff", "#7e22ce"),   # purple
}

_ALWAYS_RUN_BG = ("#fef3c7", "#92400e")  # amber for cleanup/alwaysRun steps


def step_node_colors(step: dict) -> tuple[str, str]:
    """
    Return (background_color, text_color) for a step node.
    Cleanup / alwaysRun steps use amber; otherwise method-driven colors.
    """
    if step.get("alwaysRun"):
        return _ALWAYS_RUN_BG
    method = str(step.get("method", "GET")).upper()
    return _METHOD_COLORS.get(method, ("#f1f5f9", "#334155"))
