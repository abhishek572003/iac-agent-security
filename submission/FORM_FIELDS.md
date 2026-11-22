# Copy-paste for TechRxiv / arXiv forms

**Title:** Do Coding Agents Widen the Cloud Attack Surface? A Matched Study of Security Misconfigurations in Agent- and Human-Authored Infrastructure-as-Code Changes

**Author:** Abhishek Sunil Tiwari, Independent Researcher, Mumbai, India

**Abstract (plain text):**
AI coding agents now open pull requests that modify Infrastructure-as-Code (IaC), the files that define cloud identities, network exposure and container privileges. Whether these agents introduce security misconfigurations more often than human developers is unknown. We start from the AIDev dataset, identify 3,271 agent-authored pull requests that change Terraform or Kubernetes files, and obtain 915 with scannable configuration. We collect a comparison group of 820 human-authored pull requests from the same repositories. For every pull request we reconstruct each changed file before and after the change and count the security checks that fail only after it. In raw counts, agent pull requests introduce findings more often than human ones (21.4% vs. 13.3%). Within the same repositories, however, and controlling for change size, we find no significant difference (462 agent vs. 631 human pull requests in 107 repositories; odds ratio 0.64, 95% CI [0.26, 1.57] for misconfigurations in deployable files). The apparent gap reflects where agents are used rather than how they write. Agents differ: Claude Code is close to humans, while Copilot and Codex introduce fewer misconfigurations, although these per-agent differences do not survive correction for multiple comparisons. Pull requests that introduce a deployable misconfiguration tend to be merged less often for both agents and humans. Our results caution against judging agent security from repository-level counts, and suggest that code review is an important control point for agent-written cloud configuration. 

**Keywords:** infrastructure as code; coding agents; security misconfiguration; Terraform; Kubernetes; mining software repositories

**arXiv primary category:** cs.SE (cross-list cs.CR) · **TechRxiv subject:** Computing and Processing › Software engineering

**Licence:** CC BY 4.0

**Comments field (arXiv):** 6 pages, 4 figures, 5 tables. Code and data: https://github.com/abhishek572003/iac-agent-security

**Upload:** TechRxiv → submission/Tiwari_IaC_Agents_preprint.pdf · arXiv → submission/arxiv_upload.zip
