<p align="center">
<img src="https://user-images.githubusercontent.com/28975399/143683893-8304957e-54c8-487a-98e3-84d04c61daeb.png" alt="ismyk8ssecure" title="ismyk8ssecure" width="400" height="400"/>
</p>

**ismyk8ssecure** is a FOSS tool to check whether your K8s cluster contains previously reported vulnerabilities.

## Get Started in 60 seconds !

Make sure you meet the following prerequisites

### Prerequisites:

- **kubectl is configured** to connect to cluster.
- Optional, but highly recommended: make sure you are in a **python venv**.

Simply run the following commands, and run your first scan.

```console
pip install ismyk8ssecure
ismyk8ssecure 
```

## How It Works:

This tool consists of 3 components:

### Advisories:

These are yaml files with following schema:

```yaml
vulnerability_id:
vulnerability_description:
vulnerable_components:
  - component_name:
    vulnerable_versions: [] # These are computed from `vulnerable_version_ranges`
    vulnerable_version_ranges: [] # These are manually filled
references: []
last_updated_at:
created_at:
```

Advisories can be found in the `advisories` directory in this repo.

### Version Detectors:

These are functions which detects the version of a particular k8s component. See examples in TODO. 

### Vulnerability Detectors:

These are functions defined per (vulnerability, k8s component) pair. They are called depending upon the results of above 2 components. They verify whether the corresponding "vulnerability" is present in the detected "k8s component". 


## Roadmap:

- Convert most of the kubernetes security advisories into machine readable format.

- Implement fine tuned vulnerability detectors and eventually become a **smart npm audit**.
