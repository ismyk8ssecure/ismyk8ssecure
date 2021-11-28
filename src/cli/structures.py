from typing import NamedTuple

Vulnerability = NamedTuple("Vulnerablity", [("cve_id", str), ("link", str)])
DetectedVulnerability = NamedTuple(
    "DetectedVulnerability", [("vulnerability", Vulnerability), ("component", str)]
)
