import json
import subprocess

import yaml
from typer import echo

from cli.utils import requires_kubectl
from cli.utils import version_error


def run(cmd):
    output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        output.check_returncode()
    except subprocess.CalledProcessError as e:
        echo(version_error(e))
        return
    return output

@requires_kubectl
def kubectl_version_command_output():
    cmd = ["kubectl", "version", "-o", "json"]
    output = run(cmd)
    if not output:
        return
    output = json.loads(output.stdout)
    if "clientVersion" not in output:
        echo(f"""clientVersion field is absent in '{" ".join(cmd)}' """)

    if "serverVersion" not in output:
        echo(f"""serverVersion field is absent in '{" ".join(cmd)}' """)
    
    return output

@requires_kubectl
def kubectl_version_detector():
    output = kubectl_version_command_output()
    return [output.get("clientVersion", {}).get("gitVersion")]

@requires_kubectl
def kubeapi_server_version_detector():
    output = kubectl_version_command_output()
    return [output.get("serverVersion", {}).get("gitVersion")]

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

#TODO maybe cache this
@requires_kubectl
def container_images_by_pod():
    ans = {}
    cmd = ["kubectl", "get", "pods", "-A", "-o", "json"]
    output = run(cmd)
    if not output:
        return {}
    output = json.loads(output.stdout)
    for pod in output["items"]:
        pod_name = pod["metadata"]["name"]
        if pod_name not in ans:
            ans[pod_name] = []
        for container in  pod["spec"]["containers"]:
            ans[pod_name].append(container["image"])
    return ans

@requires_kubectl
def snapshot_controller_version_detector():
    versions = []
    images_by_pod = container_images_by_pod()
    for pod, images in  images_by_pod.items():
        for image in images:
            if not image.startswith("k8s.gcr.io/sig-storage/snapshot-controller"):
                continue
            version = image.split(":")[-1]
            version = version[1:]
            echo(f" Found snapshot-controller inside pod {pod}")
            versions.append(version)
    return versions

DETECTORS = {
    "kubectl": kubectl_version_detector,
    "ingress-nginx": ingress_nginx_version_detector,
    "kubelet": kubelet_version_detector,
    "snapshot-controller": snapshot_controller_version_detector,
    "kube-apiserver": kubeapi_server_version_detector,

}