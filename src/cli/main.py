import os

import typer

from cli.version_detectors import DETECTORS
from cli.vulnerablity_detectors import detect_vulnerablities
from cli.formatters import format_report
from cli.utils import normalized_version
from cli.utils import blue_str


def _main():
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


def main():
    typer.run(_main)


if __name__ == "__main__":
    main()
