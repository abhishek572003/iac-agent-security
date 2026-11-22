"""Step 2a/2c: for each PR, get base/head commits and download changed IaC files at both.

Usage:
  python scripts/02_fetch_prs.py agent    # PRs from data/iac_prs.parquet
  python scripts/02_fetch_prs.py human    # PRs from data/human_prs.parquet (made by 03_human_prs.py)

Writes data/raw/<group>/<pr_id>/{base,head}/<original path> and appends one JSON line per PR
to data/<group>_fetch.jsonl. Re-running skips PRs already in that file.
"""
import json, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from common import DATA, RAW, api, raw_file, save, iac_kind, is_k8s_manifest

group = sys.argv[1]
src = DATA / ("iac_prs.parquet" if group == "agent" else "human_prs.parquet")
log = DATA / f"{group}_fetch.jsonl"
done = set()
if log.exists():
    done = {json.loads(l)["pr_id"] for l in log.read_text().splitlines() if l.strip()}

prs = pd.read_parquet(src)
prs = prs[~prs.pr_id.isin(done)]
print(f"{group}: {len(prs)} PRs to fetch ({len(done)} already done)", flush=True)


def owner_repo(url):  # https://github.com/o/r/pull/n
    p = url.split("github.com/")[1].split("/")
    return f"{p[0]}/{p[1]}"


def work(row):
    repo, num, pid = owner_repo(row.html_url), int(row.number), int(row.pr_id)
    meta = api(f"repos/{repo}/pulls/{num}")
    if not meta:
        return {"pr_id": pid, "ok": False, "reason": "pr_unavailable"}
    base, head = meta["base"]["sha"], meta["head"]["sha"]
    files, page = [], 1
    while True:
        batch = api(f"repos/{repo}/pulls/{num}/files", {"per_page": 100, "page": page})
        if not batch:
            break
        files += batch
        if len(batch) < 100 or page >= 30:
            break
        page += 1
    kept = []
    for f in files:
        kind = iac_kind(f["filename"])
        if not kind:
            continue
        old = f.get("previous_filename") or f["filename"]
        before = None if f["status"] == "added" else raw_file(repo, base, old)
        after = None if f["status"] == "removed" else raw_file(repo, head, f["filename"])
        if kind == "k8s-candidate":
            if not any(t and is_k8s_manifest(t) for t in (before, after)):
                continue
            kind = "k8s"
        if before is not None:
            save(RAW / group / str(pid) / "base" / old, before)
        if after is not None:
            save(RAW / group / str(pid) / "head" / f["filename"], after)
        kept.append({"path": f["filename"], "old": old, "status": f["status"], "kind": kind,
                     "additions": f["additions"], "deletions": f["deletions"],
                     "got_base": before is not None, "got_head": after is not None})
    return {"pr_id": pid, "ok": True, "repo": repo, "number": num, "base": base, "head": head,
            "merged": bool(meta.get("merged_at")), "pr_additions": meta.get("additions"),
            "pr_deletions": meta.get("deletions"), "pr_changed_files": meta.get("changed_files"),
            "review_comments": meta.get("review_comments"), "comments": meta.get("comments"),
            "files": kept}


n = 0
with ThreadPoolExecutor(max_workers=8) as ex, open(log, "a") as out:
    for fut in as_completed([ex.submit(work, r) for r in prs.itertuples()]):
        try:
            rec = fut.result()
        except Exception as e:  # keep going; failed PRs are retried on the next run
            print("error:", e, flush=True)
            continue
        out.write(json.dumps(rec) + "\n"); out.flush()
        n += 1
        if n % 200 == 0:
            print(f"{n}/{len(prs)} done", flush=True)
print("finished", n, flush=True)
