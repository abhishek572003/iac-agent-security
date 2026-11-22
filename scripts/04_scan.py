"""Step 3: run Checkov once over all downloaded files and compute misconfigurations each PR introduced.

Usage: python scripts/04_scan.py agent|human
Outputs:
  data/checkov_<group>.json             raw scanner output (not committed; large)
  data/findings_<group>.parquet         one row per failed check (pr_id, side, file, check_id, check_name, resource, category)
  data/introduced_<group>.parquet       one row per finding present at head but not at base
  data/pr_scan_<group>.parquet          per-PR counts (introduced, fixed, by category)
"""
import json, re, subprocess, sys
import pandas as pd
from common import DATA, RAW

group = sys.argv[1]
root = RAW / group
out_json = DATA / f"checkov_{group}.json"

# One Checkov run per PR directory, in parallel; results cached per PR so re-runs are cheap.
from concurrent.futures import ThreadPoolExecutor
import os
cache = DATA / f"checkov_{group}"
cache.mkdir(exist_ok=True)


def scan_one(pr_dir):
    out = cache / f"{pr_dir.name}.json"
    if not out.exists():
        cmd = [sys.executable, "-m", "checkov.main", "-d", str(pr_dir), "--framework", "terraform", "kubernetes",
               "-o", "json", "--compact", "--quiet", "--skip-download", "--soft-fail"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            out.write_text(res.stdout or "[]")
        except subprocess.TimeoutExpired:
            out.write_text("[]")
            with open(DATA / f"scan_timeouts_{group}.txt", "a") as t:
                t.write(pr_dir.name + "\n")
    return pr_dir.name


dirs = sorted(p for p in root.iterdir() if p.is_dir())
with ThreadPoolExecutor(max_workers=max(2, (os.cpu_count() or 4) - 1)) as ex:
    for i, _ in enumerate(ex.map(scan_one, dirs), 1):
        if i % 100 == 0:
            print(f"scanned {i}/{len(dirs)}", flush=True)

reports = []
for f in cache.glob("*.json"):
    try:
        r = json.loads(f.read_text() or "[]")
    except json.JSONDecodeError:
        continue
    for rep in (r if isinstance(r, list) else [r]):
        rep["_pr"] = f.stem
        reports.append(rep)

CATS = [
    ("identity_access", r"iam|polic|role|permission|privilege escalation|wildcard|\*|assume|rbac|service ?account|admin"),
    ("network_exposure", r"public|ingress|egress|0\.0\.0\.0|security group|port|network ?polic|expos|hostnetwork|hostport|load ?balancer|internet"),
    ("encryption", r"encrypt|kms|tls|ssl|https|cmk|at rest|in transit"),
    ("logging_monitoring", r"log|monitor|audit|trail|flow log|tracing|alarm"),
    ("container_privilege", r"privileged|root|capabilit|security ?context|read-?only|hostpath|hostpid|hostipc|seccomp|apparmor|allowprivilege|run as"),
    ("namespace_isolation", r"namespace"),
    ("secrets", r"secret|password|credential|token|api key|hard-?coded"),
    ("resource_limits", r"limit|request|cpu|memory|liveness|readiness|probe|replica"),
    ("image_supply_chain", r"image|tag|digest|latest|pull ?policy|registry|commit hash|module source"),
    ("data_resilience", r"versioning|lifecycle|backup|replication|notification|deletion protection|point in time|retention"),
]
cat_res = [(c, re.compile(p, re.I)) for c, p in CATS]


def category(name):
    for c, rx in cat_res:
        if rx.search(name or ""):
            return c
    return "other"


rows = []
for rep in reports:
    for f in rep.get("results", {}).get("failed_checks", []):
        parts = f["file_path"].strip("/").split("/")
        if len(parts) < 2 or parts[0] not in ("base", "head"):
            continue
        pr_id, side, path = int(rep["_pr"]), parts[0], "/".join(parts[1:])
        rows.append({"pr_id": pr_id, "side": side, "file": path, "check_id": f["check_id"],
                     "check_name": f.get("check_name"), "resource": f.get("resource"),
                     "framework": rep.get("check_type"), "category": category(f.get("check_name"))})
fd = pd.DataFrame(rows)
fd.to_parquet(DATA / f"findings_{group}.parquet", index=False)

key = ["pr_id", "check_id", "resource"]
base = fd[fd.side == "base"][key].drop_duplicates()
head = fd[fd.side == "head"].drop_duplicates(key)
intro = head.merge(base, on=key, how="left", indicator=True)
intro = intro[intro._merge == "left_only"].drop(columns="_merge")
fixed = base.merge(head[key], on=key, how="left", indicator=True)
fixed = fixed[fixed._merge == "left_only"]
intro.to_parquet(DATA / f"introduced_{group}.parquet", index=False)

fetch = [json.loads(l) for l in (DATA / f"{group}_fetch.jsonl").read_text().splitlines() if l.strip()]
pr = pd.DataFrame([{"pr_id": r["pr_id"], "ok": r["ok"], "merged": r.get("merged"), "pr_additions": r.get("pr_additions"),
                    "n_iac_files": len(r.get("files", [])),
                    "iac_additions": sum(f["additions"] for f in r.get("files", [])),
                    "kinds": ",".join(sorted({f["kind"] for f in r.get("files", [])}))} for r in fetch])
pr = pr[pr.ok & (pr.n_iac_files > 0)].copy()
pr["introduced"] = pr.pr_id.map(intro.groupby("pr_id").size()).fillna(0).astype(int)
pr["fixed"] = pr.pr_id.map(fixed.groupby("pr_id").size()).fillna(0).astype(int)
for c, _ in CATS + [("other", None)]:
    pr[f"intro_{c}"] = pr.pr_id.map(intro[intro.category == c].groupby("pr_id").size()).fillna(0).astype(int)
pr.to_parquet(DATA / f"pr_scan_{group}.parquet", index=False)

print(f"{group}: {len(pr)} PRs with scannable IaC · {(pr.introduced > 0).mean():.1%} introduced >=1 finding · "
      f"{pr.introduced.sum()} introduced, {pr.fixed.sum()} fixed")
print(intro.category.value_counts().to_string())
