# Research toolkit
Everything this study uses, in one place. Updated 22 Nov 2026.

## 1. Data
| What | Link | Use |
|---|---|---|
| **AIDev dataset** (932,791 agent-authored PRs: Codex, Devin, Copilot, Cursor, Claude Code) | https://huggingface.co/datasets/hao-li/AIDev · paper: https://arxiv.org/abs/2602.09185 · code: https://github.com/SAILResearch/AI_Teammates_in_SE3 | **Main source of agent PRs.** Filter to PRs that change `.tf`, `.tfvars`, Helm charts and Kubernetes YAML. Replaces our own GitHub search. |
| AIDev-2.7M (newer, larger release) | https://huggingface.co/datasets/hao-li/AIDev-2.7M | Check whether it adds more IaC PRs. |
| GitHub REST API via `gh` | https://cli.github.com | Fetch base/head file versions and human PRs from the same repos. |

## 2. Scanners (all free, open source)
| Tool | Repo | Why |
|---|---|---|
| **Checkov** (primary) | https://github.com/bridgecrewio/checkov | Terraform + Kubernetes + Helm, 1000+ checks, JSON output. Installed in `.venv`. |
| **KICS** (second scanner) | https://github.com/Checkmarx/kics | Cross-checks Checkov and reduces single-tool bias. Run via Docker. |
| Trivy (config mode) | https://github.com/aquasecurity/trivy | Optional third opinion. |
| GLITCH | https://github.com/sr-lab/GLITCH | Academic security-smell detector (Saavedra & Ferreira 2022), so our results compare with prior papers. |

## 3. Analysis and writing
- Python 3 + pandas + scipy/statsmodels: matched-pair statistics (McNemar, conditional logistic regression)
- matplotlib: figures
- **Overleaf** (free): https://www.overleaf.com. Upload `paper/` and compile with the IEEE template.
- Zotero (free): reference manager. Import `paper/refs.bib`.
- arXiv: https://arxiv.org. Preprint upload (needs a one-time endorsement for first-time authors in cs.SE / cs.CR).

## 4. Claude tools and skills to use (keeps tokens low)
| Tool / skill | Use it for |
|---|---|
| **scite MCP** (connected) | Find papers, verify every reference, check retractions. Already used: 13 references verified. |
| `anthropic-skills:deep-research` | One-off broad literature sweeps. Heavy on tokens, so use rarely. |
| `anthropic-skills:pdf` | Read papers or the final PDF. |
| Explore subagent | Searching large data or code folders without filling the main chat. |
| Background Bash | Long scans (Checkov over thousands of files) run without blocking. |

**Token rules for this project:**
1. Scripts do the heavy work: Claude writes code, Python processes the data, and Claude only reads summary tables.
2. Never paste raw scanner output into chat. Write it to `data/` and summarize with pandas.
3. One task per session: data, analysis, then writing. Start a fresh chat for each phase and point it to this file and `PROPOSAL.md`.
4. Verify references once with scite, then reuse `refs.bib`.

## 5. Where to publish (credible for MS/PhD applications)
| Venue | Type | Notes |
|---|---|---|
| **arXiv** (cs.SE or cs.CR) | Preprint | First step. Citable immediately; professors read it. |
| **MSR** (Mining Software Repositories) | Top SE conference + workshops | Empirical GitHub studies are exactly MSR's area. Check the MSR 2027 dates and whether its Mining Challenge uses AIDev. |
| ESEM / EASE | SE conferences | Good fit for empirical studies. |
| ICSE / FSE workshops (e.g. on AI for software engineering) | Workshop papers (4–8 pages) | Realistic first venue for a solo first paper. |
| IEEE SecDev, ACM CCS workshops | Security workshops | If the security angle is the focus. |

**Avoid:** paid "fast publication" journals and conferences. They hurt applications.

## 6. Reading list (verified)
See `paper/refs.bib` and `PROPOSAL.md` §6.
