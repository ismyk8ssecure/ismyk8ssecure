import typer

from version_detectors import DETECTORS
from vulnerablity_detectors import detect_vulnerablities
from formatters import format_report
from utils import normalized_version
from utils import blue_str

def main():
    versions_by_component = {}
    for component_name, detector in DETECTORS.items():
        typer.echo(f"Detecting version of {component_name}")
        versions = detector()
        if versions:
            versions = list(map(normalized_version, versions))
            versions_by_component[component_name] = versions
            typer.echo(
                f" Detected version {blue_str(','.join(versions))} for {blue_str(component_name)}"
            )
        else:
            typer.echo(f" No version found for {component_name}")
        typer.echo()
    typer.echo()
    vuln_report = detect_vulnerablities(versions_by_component)
    format_report(vuln_report)


if __name__ == "__main__":
    typer.run(main)
