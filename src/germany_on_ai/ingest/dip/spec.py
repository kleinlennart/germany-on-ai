"""Audit our DIP requests against DIP's OpenAPI spec, the authoritative API docs.

Only a lock (version, sha256, parameters we use) is committed; the spec itself stays in
the gitignored raw cache, since its reuse terms are unclear.
"""

import hashlib
import json
from pathlib import Path

import httpx
import yaml

SPEC_URL = "https://search.dip.bundestag.de/api/v1/openapi.yaml"
LOCK_PATH = Path("data/fetch/dip-openapi.lock.json")
SNAPSHOT_PATH = Path("data/raw/dip/openapi.yaml")


def documented_parameters(spec: dict) -> dict[str, set[str]]:
    """Query parameter names per path, with $refs resolved."""
    components = spec["components"]["parameters"]
    result = {}
    for path, operations in spec["paths"].items():
        params = operations.get("get", {}).get("parameters", [])
        resolved = (
            components[p["$ref"].split("/")[-1]] if "$ref" in p else p for p in params
        )
        result[path] = {p["name"] for p in resolved}
    return result


def check(lock_path: Path = LOCK_PATH) -> list[str]:
    """Fetch the live spec; return problems (empty means the lock still holds)."""
    raw = httpx.get(SPEC_URL, timeout=60).raise_for_status().content
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_bytes(raw)
    spec = yaml.safe_load(raw)
    lock = json.loads(lock_path.read_text())

    problems = []
    if spec["info"]["version"] != lock["version"]:
        problems.append(
            f"spec version {spec['info']['version']} != locked {lock['version']}"
        )
    if hashlib.sha256(raw).hexdigest() != lock["sha256"]:
        problems.append("spec content changed since the lock was written")
    documented = documented_parameters(spec)
    for path, names in lock["parameters_used"].items():
        if path not in documented:
            problems.append(f"{path}: endpoint no longer documented")
            continue
        missing = set(names) - documented[path]
        if missing:
            problems.append(f"{path}: no longer documented: {sorted(missing)}")
    return problems
