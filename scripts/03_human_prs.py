"""Step 2b: collect human-authored PRs that change IaC files, from the same repositories as the agent PRs.

For each repository: page through closed/merged PRs (newest first) inside the date window of that
repo's agent PRs (+/- 90 days), keep PRs that touch IaC paths and show no agent or bot traces,
and stop once we have 2x the repo's agent PR count (min 3, max 12) or after 8 pages.
Excludes every PR id that appears in AIDev (all agents), plus trace-based checks.

Output: data/human_prs.parquet (pr_id, number, html_url, repo, created_at, merged_at, author, n_iac_files)
Resumable: repos already in data/human_repos_done.txt are skipped.
"""
from datetime import datetime, timedelta
import json
import duckdb, pandas as pd
import os
from common import DATA, graphql, iac_kind, AGENT_TRACE_RE, BOT_RE

# Settings (env vars) so the sample can be widened without losing earlier runs.
WINDOW = int(os.environ.get('WINDOW_DAYS', 90))
CAP = int(os.environ.get('CAP', 12))
MAXPAGES = int(os.environ.get('PAGES', 8))
SUFFIX = os.environ.get('SUFFIX', '')

agent = pd.read_parquet(DATA / "iac_prs.parquet")
agent["repo"] = agent.html_url.str.split("github.com/").str[1].str.split("/").str[:2].str.join("/")

# all AIDev PR ids in these repos (any agent), so they are never counted as human
ids_file = DATA / "aidev_ids_in_repos.parquet"
if not ids_file.exists():
    con = duckdb.connect(); con.execute("INSTALL httpfs; LOAD httpfs;")
    con.register("r", pd.DataFrame({"repo_url": agent.repo_url.unique()}))
    con.execute(f"""COPY (SELECT a.id, a.html_url FROM read_parquet('https://huggingface.co/datasets/hao-li/AIDev/resolve/main/all_pull_request.parquet') a
                 JOIN r USING (repo_url)) TO '{ids_file}' (FORMAT parquet)""")
aidev_urls = set(pd.read_parquet(ids_file).html_url)

Q = """query($o:String!,$n:String!,$after:String){ repository(owner:$o,name:$n){
  pullRequests(first:25, after:$after, states:[MERGED,CLOSED], orderBy:{field:CREATED_AT,direction:DESC}){
    pageInfo{hasNextPage endCursor}
    nodes{ databaseId number url createdAt mergedAt body additions deletions
      author{login __typename} files(first:40){nodes{path}} commits(last:3){nodes{commit{message}}} } } } }"""

out_file = DATA / f"human_prs{SUFFIX}.jsonl"
done_file = DATA / f"human_repos_done{SUFFIX}.txt"
seen = set()
for f in DATA.glob("human_prs*.jsonl"):
    seen |= {json.loads(l)["pr_id"] for l in f.read_text().splitlines() if l.strip()}
done = set(done_file.read_text().split()) if done_file.exists() else set()

import threading
from concurrent.futures import ThreadPoolExecutor
lock = threading.Lock()


def process(repo, g):
    lo = datetime.fromisoformat(g.created_at.min().replace("Z", "+00:00")) - timedelta(days=WINDOW)
    hi = datetime.fromisoformat(g.created_at.max().replace("Z", "+00:00")) + timedelta(days=WINDOW)
    want = min(CAP, max(3, 3 * len(g)))
    o, n = repo.split("/")
    after, got, pages = None, 0, 0
    rows = []
    if True:
        while pages < MAXPAGES and got < want:
            d = graphql(Q, {"o": o, "n": n, "after": after})
            pages += 1
            if not d or not d.get("repository"):
                break
            prs = d["repository"]["pullRequests"]
            stop = False
            for p in prs["nodes"]:
                created = datetime.fromisoformat(p["createdAt"].replace("Z", "+00:00"))
                if created > hi:
                    continue
                if created < lo:
                    stop = True; break
                a = p.get("author") or {}
                text = (p.get("body") or "") + " ".join(c["commit"]["message"] for c in ((p.get("commits") or {}).get("nodes") or []))
                if p["url"] in aidev_urls or a.get("__typename") == "Bot" or BOT_RE.search(a.get("login", "")) or AGENT_TRACE_RE.search(text):
                    continue
                iac = [f["path"] for f in ((p.get("files") or {}).get("nodes") or []) if iac_kind(f["path"])]
                if not iac:
                    continue
                with lock:
                    dup = p["databaseId"] in seen
                    seen.add(p["databaseId"])
                if dup:
                    got += 1
                    continue
                rows.append(json.dumps({"pr_id": p["databaseId"], "number": p["number"], "html_url": p["url"], "repo": repo,
                                      "created_at": p["createdAt"], "merged_at": p["mergedAt"], "author": a.get("login"),
                                      "additions": p["additions"], "deletions": p["deletions"], "n_iac_files": len(iac)}))
                got += 1
                if got >= want:
                    break
            if stop or not prs["pageInfo"]["hasNextPage"]:
                break
            after = prs["pageInfo"]["endCursor"]
    with lock:
        with open(out_file, "a") as out:
            out.writelines(r + "\n" for r in rows)
        with open(done_file, "a") as f:
            f.write(repo + "\n")
        done.add(repo)
        if len(done) % 50 == 0:
            print(f"{len(done)}/{agent.repo.nunique()} repos", flush=True)



todo = [(r, g) for r, g in agent.groupby("repo") if r not in done]
with ThreadPoolExecutor(max_workers=6) as ex:
    list(ex.map(lambda rg: process(*rg), todo))

df = pd.concat([pd.read_json(f, lines=True) for f in DATA.glob("human_prs*.jsonl")]).drop_duplicates("pr_id")
df.drop(columns=["author"], errors="ignore").to_parquet(DATA / "human_prs.parquet", index=False)  # no usernames in released data
print("human PRs:", len(df), "repos:", df.repo.nunique(), flush=True)
