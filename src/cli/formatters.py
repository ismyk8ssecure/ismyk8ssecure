from typing import Dict, Set, Callable
from typer import echo

from cli.structures import DetectedVulnerability
from cli.utils import blue_str, red_str


def human_formatter(vuln_report: Set[DetectedVulnerability]):
    for detected_vuln in vuln_report:
        echo(
            f"Detected vulnerability {red_str(detected_vuln.vulnerability.cve_id)} in component {blue_str(detected_vuln.component)}"
        )
        echo(f"For more info check {blue_str(detected_vuln.vulnerability.link)}\n")


FORMATTERS: Dict[str, Callable] = {"human": human_formatter}


def format_report(vuln_report: Set[DetectedVulnerability], format: str = "human") -> None:
    FORMATTERS[format](vuln_report)
