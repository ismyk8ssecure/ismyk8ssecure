import os
import semantic_version
from datetime import datetime, timezone
from functools import cache

import yaml
import requests
from semantic_version import Version


class ComponentVersionStore:
    def __init__(self):
        self.store = {}
        self.version_fetchers_by_component = {
            "ingress-nginx": self.version_fetcher_ingress_nginx,
            "kubelet": self.version_fetcher_k8s,
            "kube-apiserver": self.version_fetcher_k8s,
            "kube-proxy-windows": self.version_fetcher_k8s,
            "kubectl": self.version_fetcher_k8s,
            "kubernetes": self.version_fetcher_k8s,
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
    def version_fetcher_k8s():
        url = ComponentVersionStore.construct_gh_api_url_for_component("kubernetes", "kubernetes")
        resp = requests.get(url)
        resp.raise_for_status()
        versions = []
        for tag in resp.json():
            versions.append(tag["ref"].split("/")[-1][1:])  # eg "ref": "refs/tags/v0.4" -> "0.4"
        return versions


version_store = ComponentVersionStore()


def update_advisory(advisory):
    for i, vc in enumerate(advisory["vulnerable_components"]):
        version_store.add_component(vc["component_name"])
        vulnerable_versions = []
        for version in version_store.get_versions_of_component(vc["component_name"]):
            vulnerable_version_ranges = [
                semantic_version.NpmSpec(vulnerable_version_range)
                for vulnerable_version_range in vc["vulnerable_version_ranges"]
            ]
            if any(
                [
                    Version.coerce(version) in version_range
                    for version_range in vulnerable_version_ranges
                ]
            ):
                vulnerable_versions.append(version)

        if set(vulnerable_versions) != set(
            advisory["vulnerable_components"][i]["vulnerable_versions"]
        ):
            print(
                "new versions added",
                set(vulnerable_versions).difference(
                    advisory["vulnerable_components"][i]["vulnerable_versions"]
                ),
            )
            print(
                "versions removed",
                set(advisory["vulnerable_components"][i]["vulnerable_versions"]).difference(
                    vulnerable_versions
                ),
            )
            advisory["last_updated_at"] = datetime.now(timezone.utc).__str__()

        advisory["vulnerable_components"][i]["vulnerable_versions"] = vulnerable_versions
        return advisory


def update_file(path):
    with open(path) as f:
        advisory = yaml.safe_load(f)
        new_advisory = update_advisory(advisory)
    with open(path, "w") as f:
        yaml.safe_dump(new_advisory, f, sort_keys=False, default_flow_style=False)


def main():
    paths = filter(lambda p: p.endswith("yaml"), os.listdir("./advisories"))
    for p in paths:
        update_file(os.path.join("./advisories", p))


if __name__ == "__main__":
    main()
