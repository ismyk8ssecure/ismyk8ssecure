from typing import Dict, List, Set

from cli.vulnerability_index import vulnerability_index
from cli.structures import DetectedVulnerability

VULNERABILITY_DETECTORS = {}


def detect_vulnerablities(
    versions_by_component: Dict[str, List[str]]
) -> Set[DetectedVulnerability]:
    detected_vulnerabilities: Set[DetectedVulnerability] = set()
    for component, versions in versions_by_component.items():
        if component not in vulnerability_index:
            continue

        for version in versions:
            if version not in vulnerability_index[component]:
                continue

            for vuln in vulnerability_index[component][version]:
                if (
                    vuln.cve_id in VULNERABILITY_DETECTORS
                    and not VULNERABILITY_DETECTORS[vuln.cve_id]()
                ):
                    continue
                detected_vulnerabilities.add(
                    DetectedVulnerability(vulnerability=vuln, component=f"{component}:{version}")
                )

    return detected_vulnerabilities
