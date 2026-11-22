"""Shared helpers: GitHub access, IaC file classification, safe file download."""
import re, subprocess, time, threading
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
TOKEN = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
S = requests.Session()
S.headers.update({"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json", "User-Agent": "iac-agent-study"})
_lock = threading.Lock()

TF_RE = re.compile(r"\.(tf|tfvars)$", re.I)
K8S_PATH_RE = re.compile(r"(^|/)(k8s|kube|kubernetes|helm|charts?|manifests?|deploy|deployments?|kustomize|overlays|base)(/|$)", re.I)
YAML_RE = re.compile(r"\.ya?ml$", re.I)
SKIP_RE = re.compile(r"(^|/)\.github/", re.I)
K8S_CONTENT_RE = re.compile(r"^\s*apiVersion\s*:.*$[\s\S]*^\s*kind\s*:", re.M)
AGENT_TRACE_RE = re.compile(r"(generated with \[?claude code|co-authored-by:\s*claude|co-authored-by:\s*copilot|codex|devin-ai|cursor agent|jules|🤖 generated)", re.I)
BOT_RE = re.compile(r"(\[bot\]$|dependabot|renovate|github-actions)", re.I)


def iac_kind(path: str):
    if TF_RE.search(path):
        return "terraform"
    if YAML_RE.search(path) and not SKIP_RE.search(path) and K8S_PATH_RE.search(path):
        return "k8s-candidate"
    return None


def is_k8s_manifest(text: str) -> bool:
    # Plain manifests only: Helm templates with {{ }} cannot be scanned without rendering.
    return bool(K8S_CONTENT_RE.search(text)) and "{{" not in text


def api(url, params=None, retries=5):
    """GET with rate-limit handling. Returns parsed JSON or None for 404/410/422."""
    for i in range(retries):
        try:
            r = S.get(url if url.startswith("http") else f"https://api.github.com/{url}", params=params, timeout=30)
        except requests.RequestException:
            time.sleep(10 * (i + 1)); continue
        if r.status_code == 200:
            return r.json()
        if r.status_code in (404, 410, 422, 451):
            return None
        if r.status_code in (403, 429):
            reset = int(r.headers.get("x-ratelimit-reset", time.time() + 60))
            wait = max(5, reset - time.time() + 2) if r.headers.get("x-ratelimit-remaining") == "0" else 30 * (i + 1)
            with _lock:
                print(f"rate limited, sleeping {int(wait)}s", flush=True)
            time.sleep(wait)
            continue
        time.sleep(3 * (i + 1))
    return None


def graphql(query, variables, retries=5):
    for i in range(retries):
        try:
            r = S.post("https://api.github.com/graphql", json={"query": query, "variables": variables}, timeout=60)
        except requests.RequestException:
            time.sleep(10 * (i + 1)); continue
        if r.status_code == 200:
            j = r.json()
            if "errors" in j and not j.get("data"):
                if any(e.get("type") == "RATE_LIMITED" for e in j["errors"]):
                    time.sleep(60); continue
                return None
            return j["data"]
        if r.status_code in (403, 429, 502, 503):
            time.sleep(30 * (i + 1)); continue
        return None
    return None


def raw_file(owner_repo: str, sha: str, path: str):
    """Download one file at a commit from raw.githubusercontent.com (not API-rate-limited)."""
    url = f"https://raw.githubusercontent.com/{owner_repo}/{sha}/{requests.utils.quote(path)}"
    for i in range(3):
        try:
            r = requests.get(url, timeout=30)
        except requests.RequestException:
            time.sleep(2); continue
        if r.status_code == 200:
            return r.text
        if r.status_code == 404:
            return None
        time.sleep(2 * (i + 1))
    return None


def save(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
