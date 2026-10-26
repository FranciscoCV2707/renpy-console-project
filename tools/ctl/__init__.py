"""Console Test Lab (ctl) — esqueleto (T-202)."""
from .trace import (
    TraceEvent,
    TraceParseError,
    TraceError,
    parse_line,
    parse_trace,
    parse_file,
    parse_trace_file,
    filter_events,
    events_equal,
    CompareResult,
    compare_events,
    compare_scenario,
    compare,
    compare_traces,
    resolve_scenario_path,
)
from .scenario import (
    Scenario,
    ScenarioError,
    ScenarioValidationError,
    InvalidScenarioError,
    ScenarioParseError,
    CompareSpec,
    LimitsSpec,
    load_scenario,
    load_scenario_text,
    parse_scenario,
    parse,
    read_scenario,
    validate_scenario,
)
from .config import load_config, find_config, get_target
from .report import write_report, generate_report, report_path


def main(argv=None):
    from .__main__ import main as _main
    return _main(argv)


__all__ = [
    "TraceEvent", "TraceParseError", "TraceError", "parse_line", "parse_trace", "parse_file",
    "parse_trace_file", "filter_events", "events_equal", "CompareResult",
    "compare_events", "compare_scenario", "compare", "compare_traces", "resolve_scenario_path",
    "Scenario", "ScenarioError", "ScenarioValidationError", "InvalidScenarioError",
    "ScenarioParseError", "CompareSpec", "LimitsSpec", "load_scenario", "load_scenario_text",
    "parse_scenario", "parse", "read_scenario", "validate_scenario",
    "load_config", "find_config", "get_target", "write_report", "generate_report",
    "report_path", "main",
]