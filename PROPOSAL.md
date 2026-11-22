# Research Proposal (working draft)

**Working title:** Do Coding Agents Widen the Cloud Attack Surface? Security Misconfigurations in Agent-Authored vs Human-Authored Infrastructure-as-Code Pull Requests

**Author:** Abhishek Sunil Tiwari · **Started:** 21 Nov 2026 · **Target:** arXiv preprint by end of Feb 2027, then a workshop or MSR/ESEM-style venue

---

## 1. Why this question (the gap)
- AI coding agents (Claude Code, GitHub Copilot coding agent, Codex, Devin, Cursor) now write a growing share of GitHub pull requests [Robbes et al. 2026, "Agentic Much?"].
- Barrak et al. (2026) studied 349,156 IaC pull requests and found agent PRs are larger and more often change core infrastructure. But they only compared **sustainability** smells (e.g., missing remote state). They did **not** measure security.
- "Trust but Verify?" (2026) found security smells in 38.9% of agent PRs, but across all code, judged by an LLM. It did not focus on cloud configuration or compare against human PRs with deterministic scanners.
- Existing IaC security studies (Rahman et al. 2019, 2021, 2023; Minna et al. 2025; Eom et al. 2026) measure misconfigurations in repositories **as they are**, not **who introduced them**.

**Gap:** No study measures whether agent-authored IaC changes *introduce* security misconfigurations (over-broad IAM, public network exposure, privileged containers, plaintext secrets) at a different rate than comparable human changes.

## 2. Research questions
- **RQ1 (Prevalence):** How often do agent-authored and human-authored Terraform/Kubernetes PRs introduce new security misconfigurations?
- **RQ2 (Type):** Which categories dominate for each group: IAM wildcards / privilege, network exposure, encryption off, logging off, container privilege, secrets?
- **RQ3 (Review):** Are PRs that introduce misconfigurations merged anyway? Do reviewers comment on them? Does this differ between agent and human PRs?
- **RQ4 (Fixes, optional):** When a PR claims to fix a security issue, does the misconfiguration really disappear, or is it moved or hidden (the "deceptive fix" idea from TerraProbe, 2026)?

## 3. Method
1. **Find PRs.** GitHub Search API for merged and closed PRs (Jan 2025 – Dec 2026) that change `.tf` files or Kubernetes YAML.
   - *Agent PRs:* author is a known agent account (e.g. `Copilot`, `devin-ai-integration[bot]`, `chatgpt-codex-connector`), or the PR body or commits carry disclosed traces ("Generated with Claude Code", "Co-Authored-By: Claude", Codex or Cursor footers).
   - *Human PRs:* same repositories, same period, no agent or bot traces. Exclude Dependabot/Renovate.
2. **Match.** Pair each agent PR with human PRs from the **same repository** and a similar size (files and lines changed). Same-repo matching controls for project style and the repo's own scanner settings.
3. **Measure the change, not the repo.** For each changed file, run **Checkov** (and **KICS** as a second scanner) on the base version and the head version. **Introduced misconfiguration = a failed check present in head but not in base.** Map check IDs into the categories of RQ2.
4. **Validate by hand.** Two raters label a random sample (~150 findings) as true or false positive, and report Cohen's kappa. If no second rater is available, the author labels twice, two weeks apart. This answers the scanner-noise problem shown by Eom et al. (2026).
5. **Statistics.** Rates per PR and per 100 changed lines. Paired comparison with McNemar's test or conditional logistic regression on the matched pairs. Report odds ratios with 95% CIs.
6. **Ethics and reproducibility.** Public data only. No contacting developers, no exploiting anything. Release scripts and the PR list (IDs, not code copies) on GitHub.

## 4. Threats to validity (write these early)
- Silent agent use cannot be detected, so some "human" PRs are agent-assisted. This biases the result toward *no difference*; state it.
- Scanners have false positives and false negatives (manual validation helps).
- Agents may be used for different tasks than humans. Mitigate by same-repo matching and size matching, and by reporting change type.

## 5. Plan (alongside the full-time job, ~10–12 h/week)
| Week | Dates | Work |
|---|---|---|
| 1 | 21–29 Nov | Read the core papers below. Finalise RQs. **Pilot: 20–30 PRs end-to-end.** |
| 2–3 | 30 Nov – 13 Dec | Collection script at scale; agent-trace detection rules; matching |
| 4–5 | 14–27 Dec | Run scanners on all pairs; build the categories |
| 6 | 28 Dec – 3 Jan | Manual validation sample |
| 7 | 4–10 Jan | Statistics, figures |
| 8–9 | 11–24 Jan | Write the paper (IEEE / ACM template, Overleaf) |
| 10 | 25 Jan – 7 Feb | Feedback (an SIES professor), polish, release the code |
| 11 | by end Feb | arXiv submission; add to CV, website, professor follow-ups |

GRE (mid/late Jan) overlaps weeks 8–9: write in small daily blocks; the analysis must be finished by 10 Jan.

## 6. Core references (all checked on scite, 21 Nov 2026: exist, not retracted, no predatory venue)
1. Barrak, Ksontini, Wehbe et al. (2026). Do AI Coding Agents Write Infrastructure as Code Like Humans? An Empirical Study of GitHub Pull Requests. arXiv. doi:10.48550/arxiv.2610.34613 — **closest work; the gap we fill**
2. Rahman, Shamim, Bose et al. (2023). Security Misconfigurations in Open Source Kubernetes Manifests: An Empirical Study. ACM TOSEM. doi:10.1145/3579639
3. Rahman, Parnin, Williams (2019). The Seven Sins: Security Smells in Infrastructure as Code Scripts. ICSE. doi:10.1109/icse.2019.00033
4. Rahman, Rahman, Parnin et al. (2021). Security Smells in Ansible and Chef Scripts. ACM TOSEM. doi:10.1145/3408897
5. Minna, Massacci, Tuma (2025). Analyzing and mitigating (with LLMs) the security misconfigurations of Helm charts from Artifact Hub. Empirical Software Engineering. doi:10.1007/s10664-025-10688-0
6. Eom, Suk, Hwang et al. (2026). An Empirical Study and Benchmark of Kubernetes Misconfiguration Scanners. Proc. ACM Softw. Eng. doi:10.1145/3832297
7. Alsaid, Nebolisa, Abbas et al. (2026). TerraProbe: Detecting Deceptive Fixes in LLM-Assisted Terraform. arXiv. doi:10.48550/arxiv.2606.26590
8. Saavedra, Ferreira (2022). GLITCH: Automated Polyglot Security Smell Detection in IaC. arXiv. doi:10.48550/arxiv.2205.14371
9. Chiari, De Pascalis, Pradella (2022). Static Analysis of Infrastructure as Code: a Survey. ICSA-C. doi:10.1109/icsa-c54293.2022.00049
10. Zerouali, Opdebeeck, De Roover (2023). Helm Charts for Kubernetes Applications: Evolution, Outdatedness and Security Risks. MSR. doi:10.1109/msr59073.2023.00078
11. Sankaran, Datta, Bates (2020). Workflow Integration Alleviates Identity and Access Management in Serverless Computing. ACSAC. doi:10.1145/3427228.3427665
12. Shin, Kim, Lee et al. (2026). ALPS: Automated Least-Privilege Enforcement for Securing Serverless Functions. arXiv. doi:10.48550/arxiv.2603.25393
13. Yan, Weng, Chen et al. (2026). Do Coding Agents Understand Least-Privilege Authorization? arXiv. doi:10.48550/arxiv.2605.14859

Also read (found 21 Nov, not yet run through the checker): "Trust but Verify? Uncovering the Security Debt of Autonomous Coding Agents" (2026), doi:10.48550/arxiv.2607.12428; "Agentic Much? Adoption of Coding Agents on GitHub" (2026), doi:10.48550/arxiv.2601.18341.

**Reading order for week 1:** 1 → 2 → 3 → 6 → 7 → "Trust but Verify?" → the rest.
For each paper, write 5 lines: question, data, method, main result, and how our study differs.

## 7. Why this helps the PhD application
- It matches Prof. Xiong's interest in overlooked cloud-platform assumptions, and Prof. Madria's work on access control and policy.
- It shows research skill: question → data → measurement → statistics → writing, not just tool use.
- It is a real, reproducible artifact with public code, linked from the CV and website.

## 8. Pilot log — 21 Nov 2026
Script: `scripts/pilot.py` · Output: `data/pilot_results.csv`, `data/pilot_findings.csv`
- Found 15 agent-trace PRs through GitHub search, but **only 5 actually changed `.tf` files**. The `language:HCL` filter is repo-level. **Fix:** filter by changed files (done in the script), and search many more queries (Copilot agent author, Devin, Codex), aiming for 500+ agent PRs.
- 4 matched human PRs came from the same repositories.
- Agent: 1/5 PRs introduced ≥1 new failed check (2 in total). Human: 2/4 PRs (36 in total, mostly from two large PRs).
- **This is not a result.** The sample is tiny, and one big PR dominates. It only shows the method works end to end.
- Lessons for the full study:
  1. Normalise by size: report introduced findings per 100 added lines, and match on size.
  2. Scanning files without their modules misses cross-file context, and some checks fire only on whole modules. **Next:** clone the repo at base and head, and scan the changed directories.
  3. Record which agent produced each PR, for a per-agent breakdown.
  4. Add Kubernetes YAML (Checkov `--framework kubernetes`) and KICS as a second scanner.

## 9. Data log, 22 Nov 2026
- Switched the agent-PR source from our own GitHub search to the **AIDev dataset** (Li et al. 2026, 361,296 curated agent PRs).
- `scripts/01_filter_aidev.py` reads only file-name columns remotely with DuckDB (no 12 GB download).
- Result: **3,271 agent PRs that change IaC files, across 629 repositories**: 561 with Terraform, 2,839 with Kubernetes-path YAML (noisy; content check in step 2). Per agent: Claude Code 2,144 · Copilot 572 · Codex 404 · Cursor 67 · Devin 49 · Jules 35. See `data/summary_step1.md`.
- 23 Nov: agent side fetched and scanned. 3,249/3,271 PRs fetched; **915 PRs have scannable IaC** (rest were Helm templates or non-K8s YAML). Checkov run per PR in parallel (3 PRs timed out at 10 min, excluded: `data/scan_timeouts_agent.txt`).
- First agent-side numbers (before validation): ~21% of agent IaC PRs introduce ≥1 failed check; counts are highly skewed (top 10 PRs = ~40% of findings), so compare per-PR shares and per-100-line rates, not totals.
- 23 Nov, **first comparison (preliminary, unvalidated)**: human side 578 PRs collected (149 repos), 297 scannable. Raw shares 21% (agent) vs 12% (human), but **within the same 60 repositories the difference disappears**: logistic OR 0.73 (95% CI 0.38–1.41, p=0.35); matched pairs 133, McNemar p=0.38. PRs introducing findings are merged less often (humans 43% vs 81%; Claude Code 47% vs 76%), except Codex. Sample too small for strong claims; next: grow the human sample and validate 150 findings (blind sheet in `data/validation_sheet.csv`).
