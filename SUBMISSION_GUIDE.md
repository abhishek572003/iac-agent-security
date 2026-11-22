# Submission guide
Paper: *Do Coding Agents Widen the Cloud Attack Surface? A Matched Study of Security Misconfigurations in Agent- and Human-Authored Infrastructure-as-Code Changes*
Files: `paper/main.pdf` (named, for the preprint) · `paper/main_anon.pdf` (anonymous, for double-blind review) · sources in `paper/`.

---

## 1. Before anything goes public (you, about 1 hour)
- [ ] **Confirm the 110 validation labels.** After you confirm them, change the Validation sentence in `paper/main.tex` to "...and reviewed by the author" and rebuild with `paper/build.sh` (Claude can do this for you) in `03-Education/PhD/Validation_Sheet_LABEL_ME.xlsx` (Claude pre-filled them; change any you disagree with, then tell Claude to re-run `scripts/05_compare.py`).
- [ ] **Read the whole paper once.** You must be able to explain every sentence (reviewers and professors will ask). Note anything unclear and ask Claude.
- [ ] **Make the GitHub repo public** (`abhishek572003/iac-agent-security`): Settings → Danger zone → Change visibility. The paper's Data Availability section points to it. Raw downloaded files are not in git, only scripts and summary data.

## 2. Preprint (do this first; it goes on your CV the same week)
**Option A: arXiv (best known).** Category: `cs.SE` (cross-list `cs.CR`).
1. Create an account at https://arxiv.org/user/register using your normal email.
2. Start a new submission and upload the files: `main.tex`, `numbers.tex`, `refs.bib`, `main.bbl` (run Tectonic first), `fig_agents.pdf`, `fig_categories.pdf`. Licence: CC BY 4.0.
3. If arXiv asks for an **endorsement**, it shows you a code. Email that code to an endorser (template below). Good endorsers: Dr. Junjie Xiong (Missouri S&T), or authors of the closest papers (Barrak et al.; Rahman et al.).
4. After endorsement, submit. It appears within about 1–2 working days.

**Option B: TechRxiv (no endorsement needed).** IEEE's preprint server: https://www.techrxiv.org. Upload `main.pdf`, add title, abstract and keywords. You get a DOI. Use this if no endorser replies within a week.

**Endorsement email template**
> Subject: arXiv endorsement request (cs.SE): security of AI-agent-authored IaC changes
>
> Dear Dr. [Name],
> I am an independent researcher (B.E. CSE, University of Mumbai; Analyst at Capgemini) preparing my first preprint, a matched study of security misconfigurations in Terraform/Kubernetes pull requests written by AI coding agents versus humans, built on the AIDev dataset. Your work on [their paper] is central to it. The draft is attached and the code is at https://github.com/abhishek572003/iac-agent-security.
> If you are comfortable doing so, could you endorse me for cs.SE? My endorsement code is: [CODE]. Any feedback on the paper would also be very welcome.
> Thank you for your time.
> Abhishek Tiwari

## 3. Peer-reviewed venues (checked 23 Nov 2026)
Already closed for the 2027 cycle: MSR 2027 technical (23 Oct), FORGE 2027 (30 Oct; 15 Nov data track), all ICSE 2027 workshops (13–20 Nov). The MSR 2027 Mining Challenge (23 Dec) requires its own datasets (GitSkills / SpecMine), so it is not a fit.

Realistic targets, best fit first. **Check each call for the current deadline before submitting.**
| Venue | Type | Why it fits | Typical timing |
|---|---|---|---|
| **EASE 2027** (Evaluation and Assessment in SE) | Conference, short and full papers | Empirical SE, welcomes MSR-style studies | Deadline usually Jan–Feb |
| **ESEM 2027** (Empirical SE and Measurement) | Conference, including emerging-results short papers | Matched empirical design | Deadline usually May |
| **ASE 2027 NIER / FSE 2027 IVR** (new ideas tracks) | Short papers | Agents + security is a "new idea" fit | Spring 2027 |
| **IEEE SecDev 2027** | Security dev conference | Practical security of development tooling | Spring 2027 |
| **Empirical Software Engineering journal** (Springer) | Journal, submit any time | Same journal as Minna et al. 2025 | Rolling; longer review |
| **MSR 2028** | Top MSR venue | Extended version with a larger sample and Helm | Oct 2027 |

Formats: most use the IEEE template already in `paper/`; many are **double-blind**, so submit `main_anon.pdf` and link code through https://anonymous.4open.science.

## 4. "Will they reject it because AI helped?"
- **Using AI tools is allowed** by arXiv, IEEE, ACM and the venues above, as long as you disclose it and take responsibility. AI cannot be listed as an author. The paper already has a "Use of AI Tools" section (anonymous version too).
- **What gets papers rejected is not AI use but:** made-up results, fake or wrong references, vague contributions, and copied text. This paper avoids all four: every number comes from scripts on real data (`numbers.tex` is auto-generated), every reference was verified on scite, and the code is public.
- **AI-text detectors are unreliable,** and venues do not reject on detector scores alone. Your real protection is (1) honest disclosure, (2) the reproducible package, and (3) being able to explain the work yourself. Rewrite any sentence in your own words where you would phrase it differently.

## 5. "Is the topic meaningful enough?"
Reviewers will ask "so what?". The paper's answers:
1. **Timely:** coding agents now edit cloud configuration in hundreds of repositories (AIDev), and nobody had measured the security effect at the change level.
2. **A non-obvious result:** raw numbers say agents are worse; a fair comparison says they are not. This warns every future agent study about a confound.
3. **Actionable:** review filters these changes for both groups, so the place to invest is scanners in CI and agent-side pre-checks.
4. **Reusable:** an open pipeline others can extend (Helm rendering, more agents, runtime checks).
An honest limitation reviewers may raise: the matched sample is modest, so confidence intervals are wide. The paper states this, and the MSR 2028 extension can grow it.
