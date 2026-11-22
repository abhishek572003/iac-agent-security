# Step 1 summary: AIDev pull requests that change IaC files

Total PRs: **3271** across **629** repositories (from AIDev `pull_request`, 361,296 PRs).

| agent        |   prs |   repos |   merged |   terraform_prs |   k8s_prs |
|:-------------|------:|--------:|---------:|----------------:|----------:|
| Claude_Code  |  2144 |     420 |     1560 |             266 |      1939 |
| Copilot      |   572 |     174 |      356 |             177 |       446 |
| OpenAI_Codex |   404 |     100 |      283 |             109 |       312 |
| Cursor       |    67 |      33 |       37 |               5 |        62 |
| Devin        |    49 |       8 |       34 |               0 |        49 |
| Google_Jules |    35 |       6 |       13 |               4 |        31 |

## Notes (22 Nov 2026)
- Date range of these PRs: 27 Jan 2025 to 31 Mar 2026. States: 2,921 closed (incl. merged), 350 open.
- Files: 7,420 Terraform file changes (561 PRs); 21,399 YAML changes flagged as Kubernetes (2,839 PRs).
- **The Kubernetes filter is path-based and includes noise** (e.g. Ansible tasks, GitHub `action.yml`, Taskfiles, test fixtures). Step 2 must keep only files whose content has both `apiVersion:` and `kind:` (or are Helm templates/values), checked when we download the base/head versions.
- Terraform matches are reliable (extension-based).
- Claude Code dominates (2,144 of 3,271 PRs), so results must be reported per agent and not only pooled.
- Next (step 2): for the same 629 repositories, collect human PRs touching the same file types in the same period, then download base/head files and run Checkov + KICS.
