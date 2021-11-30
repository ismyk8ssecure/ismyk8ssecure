from shutil import which
from subprocess import CalledProcessError
from typing import Callable

from typer import echo
from colorama import Fore, Style


def requires_kubectl(detector: Callable):
    def new_detector():
        if not which("kubectl"):
            echo("kubectl not found, aborting")
            return []
        else:
            return detector()

    return new_detector


def normalized_version(version: str):
    version = version.strip()
    if version.startswith("v"):
        version = version[1:]
    return version


def version_error(error: CalledProcessError):
    command = " ".join(error.cmd)
    return red_str(f'got error while running command "{command}" ')


def blue_str(string: str) -> str:
    return Fore.BLUE + string + Style.RESET_ALL


def red_str(string: str) -> str:
    return Fore.RED + string + Style.RESET_ALL
