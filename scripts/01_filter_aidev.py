"""Step 1: find AIDev agent pull requests that change Terraform or Kubernetes files.

Reads only the needed columns of the remote AIDev parquet files with DuckDB (no 12 GB download).
Outputs:
  data/iac_files.parquet  one row per changed IaC file (pr_id, sha, filename, status, additions, deletions, kind)
  data/iac_prs.parquet    one row per PR with agent, state, repo, url and file counts
  data/summary_step1.md   counts per agent and per IaC kind
"""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
BASE = "https://huggingface.co/datasets/hao-li/AIDev/resolve/main/"

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs; SET enable_progress_bar=false;")

# Terraform: .tf/.tfvars. Kubernetes: YAML under k8s/helm/manifests/charts paths, kustomization, Chart.yaml.
KIND = r"""
CASE
  WHEN lower(filename) LIKE '%.tf' OR lower(filename) LIKE '%.tfvars' THEN 'terraform'
  WHEN regexp_matches(lower(filename), '(^|/)(chart\.yaml|values(\.[a-z0-9_-]+)?\.ya?ml|kustomization\.ya?ml)$') THEN 'k8s'
  WHEN regexp_matches(lower(filename), '\.ya?ml$')
   AND regexp_matches(lower(filename), '(^|/)(k8s|kube|kubernetes|helm|charts?|manifests?|deploy|deployments?|kustomize|overlays|base)(/|$)')
   AND NOT regexp_matches(lower(filename), '(^|/)\.github/') THEN 'k8s'
  ELSE NULL END
"""

con.execute(f"""
COPY (
  SELECT pr_id, sha, filename, status, additions, deletions, {KIND} AS kind
  FROM read_parquet('{BASE}pr_commit_details.parquet')
  WHERE {KIND} IS NOT NULL
) TO '{DATA}/iac_files.parquet' (FORMAT parquet)
""")

con.execute(f"""
COPY (
  SELECT p.id AS pr_id, p.number, p.agent, p.state, p.created_at, p.merged_at, p.repo_id, p.repo_url, p.html_url, p.title,
         f.n_files, f.kinds, f.added
  FROM read_parquet('{BASE}pull_request.parquet') p
  JOIN (SELECT pr_id, count(DISTINCT filename) n_files, string_agg(DISTINCT kind, ',') kinds, sum(additions) added
        FROM read_parquet('{DATA}/iac_files.parquet') GROUP BY pr_id) f ON f.pr_id = p.id
) TO '{DATA}/iac_prs.parquet' (FORMAT parquet)
""")

by_agent = con.execute(f"""
  SELECT agent, count(*) prs, count(DISTINCT repo_id) repos,
         sum(CASE WHEN merged_at IS NOT NULL THEN 1 ELSE 0 END) merged,
         sum(CASE WHEN kinds LIKE '%terraform%' THEN 1 ELSE 0 END) terraform_prs,
         sum(CASE WHEN kinds LIKE '%k8s%' THEN 1 ELSE 0 END) k8s_prs
  FROM read_parquet('{DATA}/iac_prs.parquet') GROUP BY agent ORDER BY prs DESC
""").df()
total = con.execute(f"SELECT count(*), count(DISTINCT repo_id) FROM read_parquet('{DATA}/iac_prs.parquet')").fetchall()[0]

md = ["# Step 1 summary: AIDev pull requests that change IaC files", "",
      f"Total PRs: **{total[0]}** across **{total[1]}** repositories (from AIDev `pull_request`, 361,296 PRs).", "",
      by_agent.to_markdown(index=False)]
(DATA / "summary_step1.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
