import json
import subprocess

import yaml
from typer import echo

from utils import requires_kubectl
from utils import version_error


def run(cmd):
    output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        output.check_returncode()
    except subprocess.CalledProcessError as e:
        echo(version_error(e))
        return
    return output


@requires_kubectl
def kubectl_version_detector():
    cmd = ["kubectl", "version", "-o", "json"]
    output = run(cmd)
    if not output:
        return
    output = json.loads(output.stdout)
    if "clientVersion" not in output:
        echo(f"""clientVersion field is absent in '{" ".join(cmd)}' """)

    if "serverVersion" not in output:
        echo(f"""serverVersion field is absent in '{" ".join(cmd)}' """)

    return [output.get("clientVersion", {}).get("gitVersion")]


@requires_kubectl
def ingress_nginx_version_detector():
    echo(" Searching for nginx ingress inside 'ingress-nginx' namespace")
    cmd = [
        "kubectl",
        "get",
        "pods",
        "-n",
        "ingress-nginx",
        "-l",
        "app.kubernetes.io/name=ingress-nginx",
        "--field-selector=status.phase=Running",
        "-o",
        "jsonpath='{.items[0].metadata.name}'",
    ]
    output = run(cmd)
    if not output:
        return
    pod_name = output.stdout.decode()
    if not pod_name:
        echo(" Did not find any nginx ingress pod")
        return

    echo(f" Found nginx ingress in pod {pod_name}")
    cmd = [
        "kubectl",
        "exec",
        "-it",
        pod_name.replace("'", ""),
        "-n",
        "ingress-nginx",
        "--",
        "/nginx-ingress-controller",
        "--version",
    ]
    output = run(cmd)
    if not output:
        return

    # FIXME: This is super brittle.
    output = yaml.safe_load(
        output.stdout.decode().replace("--", "").replace("NGINX Ingress controller", "")
    )
    return [output[0]["Release"]]


@requires_kubectl
def kubelet_version_detector():
    cmd = ["kubectl", "get", "nodes", "-o", "json"]
    output = run(cmd)
    if not output:
        return
    output = json.loads(output.stdout)
    return [node["status"]["nodeInfo"]["kubeletVersion"] for node in output["items"]]


DETECTORS = {
    "kubectl": kubectl_version_detector,
    "ingress-nginx": ingress_nginx_version_detector,
    "kubelet": kubelet_version_detector,
}
