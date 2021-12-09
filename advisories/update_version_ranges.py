"""
HIGH LEVEL OVERVIEW:
This script goes through each advisory file in this directory.
For each advisory file it does the following:
    1. For each 'vulnerable_component' fetch all versions of the component.
    2. For each version of component the version will be added to "vulnerable_versions" if it satifies any
        version range from  "vulnerable_version_ranges". 
    3. Finally it updates the timestamp at "last_updated_at".
"""

import os
from datetime import datetime, timezone
from functools import cache

import yaml
import requests
from univers.version_specifier import VersionSpecifier
from univers.versions import SemverVersion


class ComponentVersionStore:
    def __init__(self):
        self.store = {}
        self.version_fetchers_by_component = {
            "ingress-nginx": self.version_fetcher_ingress_nginx,
            "kubelet": self.version_fetcher_k8s,
            "kube-apiserver": self.version_fetcher_k8s,
            "kube-proxy-windows": self.version_fetcher_k8s,
            "kube-proxy": self.version_fetcher_k8s,
            "kubectl": self.version_fetcher_k8s,
            "kubernetes": self.version_fetcher_k8s,
            "snapshot-controller": self.version_fetcher_snapshot_controller,
            "kube-controller-manager": self.version_fetcher_k8s,
            "kubernetes-dashboard": self.version_fetcher_kubernetes_dashboard,
        }

    def add_component(self, component):
        if component in self.store:
            return
        self.store[component] = self.version_fetchers_by_component[component]()

    def get_versions_of_component(self, component):
        return self.store.get(component, [])

    # Helper
    @staticmethod
    def construct_gh_api_url_for_component(owner, repo):
        return f"https://api.github.com/repos/{owner}/{repo}/git/refs/tags"

    @staticmethod
    @cache
    def version_fetcher_ingress_nginx():
        resp = requests.get(
            "https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/Changelog.md"
        )
        resp.raise_for_status()
        versions = []
        for line in resp.text.split("\n"):
            if line.startswith("###"):
                versions.append(line.split("###")[1].strip())
        return versions

    @staticmethod
    @cache
    def version_fetcher_kubernetes_dashboard():
        url = ComponentVersionStore.construct_gh_api_url_for_component("kubernetes", "dashboard")
        resp = requests.get(url)
        resp.raise_for_status()
        versions = []
        for tag in resp.json():
            versions.append(tag["ref"].split("/")[-1][1:])  # eg "ref": "refs/tags/v0.4" -> "0.4"
        return versions

    @staticmethod
    @cache
    def version_fetcher_k8s():
        url = ComponentVersionStore.construct_gh_api_url_for_component("kubernetes", "kubernetes")
        resp = requests.get(url)
        resp.raise_for_status()
        versions = []
        for tag in resp.json():
            versions.append(tag["ref"].split("/")[-1][1:])  # eg "ref": "refs/tags/v0.4" -> "0.4"
        return versions

    @staticmethod
    @cache
    def version_fetcher_snapshot_controller():
        url = ComponentVersionStore.construct_gh_api_url_for_component(
            "kubernetes-csi", "external-snapshotter"
        )
        resp = requests.get(url)
        resp.raise_for_status()
        resp = resp.json()
        versions = []
        for tag in resp:
            if "client" in tag["ref"]:
                continue
            versions.append(tag["ref"].split("/")[-1][1:])
        return versions


version_store = ComponentVersionStore()


def update_advisory(advisory):
    for i, vc in enumerate(advisory["vulnerable_components"]):
        version_store.add_component(vc["component_name"])
        vulnerable_versions = []
        for version in version_store.get_versions_of_component(vc["component_name"]):
            vulnerable_version_ranges = vc["vulnerable_version_ranges"]
            if any(
                [
                    SemverVersion(version)
                    in VersionSpecifier.from_scheme_version_spec_string("semver", version_range)
                    for version_range in vulnerable_version_ranges
                ]
            ):
                vulnerable_versions.append(version)

        if set(vulnerable_versions) != set(
            advisory["vulnerable_components"][i]["vulnerable_versions"]
        ):
            print(
                f"new versions added in advisory for {advisory['vulnerability_id']}",
                set(vulnerable_versions).difference(
                    advisory["vulnerable_components"][i]["vulnerable_versions"]
                ),
            )
            print(
                f"versions removed in  advisory for {advisory['vulnerability_id']}",
                set(advisory["vulnerable_components"][i]["vulnerable_versions"]).difference(
                    vulnerable_versions
                ),
            )
            advisory["last_updated_at"] = datetime.now(timezone.utc).__str__()
        if not advisory["created_at"]:
            if not advisory["last_updated_at"]:
                advisory["last_updated_at"] = datetime.now(timezone.utc).__str__()
            advisory["created_at"] = advisory["last_updated_at"]

        advisory["vulnerable_components"][i]["vulnerable_versions"] = vulnerable_versions
        return advisory


def update_file(path):
    with open(path) as f:
        advisory = yaml.safe_load(f)
        new_advisory = update_advisory(advisory)
    with open(path, "w") as f:
        yaml.safe_dump(new_advisory, f, sort_keys=False, default_flow_style=False)


def main():
    paths = filter(lambda p: p.startswith("CVE-") and p.endswith("yaml"), os.listdir("./"))
    for p in paths:
        print("processing ", p)
        update_file(os.path.join("./", p))


if __name__ == "__main__":
    main()
