"""Step 5: extra analyses for the full paper. Run after 05_compare.py.
Writes paper/numbers2.tex (macros), paper/tab_dataset.tex, paper/tab_checks.tex, paper/tab_validation.tex,
paper/fig_size.pdf, paper/examples.tex (real introduced findings with code), and data/extra.md.
"""
import json, re
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import DATA, RAW, ROOT
from rules import context, tier

P = ROOT / "paper"
m = pd.read_parquet(DATA / "analysis_table.parquet")
N, out = {}, []


def put(k, v, fmt="{}"):
    if fmt == "{}" and isinstance(v, (int, np.integer)) and v >= 1000:
        fmt = "{:,}"
    N[k] = fmt.format(v)


def tex_escape(s):
    return re.sub(r"([_%&#$])", r"\\\1", str(s))


# ---- fetch metadata (file status, comments) ----
meta = {}
for g in ("agent", "human"):
    for l in (DATA / f"{g}_fetch.jsonl").read_text().splitlines():
        r = json.loads(l)
        if r.get("ok"):
            meta[r["pr_id"]] = r
m["comments"] = m.pr_id.map(lambda i: (meta[i].get("comments") or 0) + (meta[i].get("review_comments") or 0) if i in meta else np.nan)
m["only_added"] = m.pr_id.map(lambda i: all(f["status"] == "added" for f in meta[i]["files"]) if i in meta else False)

# ---- Table: dataset ----
rows = []
for name, d in [("Claude Code", m[m.agent == "Claude_Code"]), ("Copilot", m[m.agent == "Copilot"]),
                ("Codex", m[m.agent == "OpenAI_Codex"]), ("Other agents", m[m.agent.isin(["Google_Jules", "Cursor", "Devin"])]),
                ("All agents", m[m.is_agent == 1]), ("Humans", m[m.is_agent == 0])]:
    rows.append(f"{name} & {len(d)} & {d.repo.nunique()} & {int(d.kinds.str.contains('terraform').sum())} & "
                f"{int(d.kinds.str.contains('k8s').sum())} & {int(d.iac_additions.median())} & {100*d.merged.mean():.0f}\\% \\\\")
(P / "tab_dataset.tex").write_text(
    "\\begin{table}[t]\\centering\\caption{Matched sample: pull requests (PRs), repositories, IaC types, median IaC lines added, and merge rate.}"
    "\\label{tab:dataset}\\small\\begin{tabular}{@{}lrrrrrr@{}}\\toprule Author & PRs & Repos & TF & K8s & Lines & Merged\\\\\\midrule\n"
    + "\n".join(rows[:4]) + "\n\\midrule\n" + "\n".join(rows[4:]) + "\n\\bottomrule\\end{tabular}\\end{table}\n")

# ---- introduced findings (deployable) ----
intro = pd.concat([pd.read_parquet(DATA / "introduced_agent.parquet").assign(is_agent=1),
                   pd.read_parquet(DATA / "introduced_human.parquet").assign(is_agent=0)])
intro["ctx"] = intro.file.map(context); intro["tier"] = intro.check_name.map(tier)
im = intro[intro.pr_id.isin(m.pr_id) & (intro.ctx == "prod")]
top = (im.groupby(["check_name", "is_agent"]).pr_id.nunique().unstack(fill_value=0)
       .rename(columns={0: "h", 1: "a"}))
top["tot"] = top.a + top.h
top = top.sort_values("tot", ascending=False).head(10)
na, nh = int((m.is_agent == 1).sum()), int((m.is_agent == 0).sum())
trows = [f"{tex_escape(c[:62] + ('…' if len(c) > 62 else ''))} & {int(r.a)} ({100*r.a/na:.1f}) & {int(r.h)} ({100*r.h/nh:.1f}) \\\\" for c, r in top.iterrows()]
(P / "tab_checks.tex").write_text(
    "\\begin{table}[t]\\centering\\caption{Most frequent checks introduced in deployable files: number (\\%) of agent and human PRs introducing each.}"
    "\\label{tab:checks}\\footnotesize\\begin{tabular}{@{}p{5.1cm}rr@{}}\\toprule Check (Checkov name) & Agent & Human\\\\\\midrule\n"
    + "\n".join(trows) + "\n\\bottomrule\\end{tabular}\\end{table}\n")

# ---- net effect: introduced vs fixed ----
for k, d in (("A", m[m.is_agent == 1]), ("H", m[m.is_agent == 0])):
    put(f"FixShare{k}", 100 * (d.fixed > 0).mean(), "{:.1f}")
    put(f"NetWorse{k}", 100 * (d.n_prod > d.fixed).mean(), "{:.1f}")
    put(f"NetBetter{k}", 100 * (d.fixed > d.n_prod).mean(), "{:.1f}")
mf = smf.glm("fx ~ is_agent + log_size", data=m.assign(fx=(m.fixed > 0).astype(int)), family=sm.families.Binomial()).fit(
    cov_type="cluster", cov_kwds={"groups": pd.factorize(m.repo)[0]})
put("ORFix", np.exp(mf.params["is_agent"]), "{:.2f}"); put("PFix", mf.pvalues["is_agent"], "{:.2f}")
lo, hi = np.exp(mf.conf_int().loc["is_agent"]); put("ORloFix", lo, "{:.2f}"); put("ORhiFix", hi, "{:.2f}")

# ---- review discussion ----
c = m.dropna(subset=["comments"])
for k, d in (("A", c[c.is_agent == 1]), ("H", c[c.is_agent == 0])):
    put(f"CommClean{k}", d[d.any_prod == 0].comments.median(), "{:.0f}")
    put(f"CommFind{k}", d[d.any_prod == 1].comments.median(), "{:.0f}")
nb = smf.glm("comments ~ any_prod + is_agent + log_size", data=c, family=sm.families.NegativeBinomial()).fit(
    cov_type="cluster", cov_kwds={"groups": pd.factorize(c.repo)[0]})
put("IRRComm", np.exp(nb.params["any_prod"]), "{:.2f}"); put("PComm", nb.pvalues["any_prod"], "{:.2f}")

# ---- robustness: PRs that modify existing files only ----
d = m[~m.only_added]
r = smf.glm("any_prod ~ is_agent + log_size", data=d, family=sm.families.Binomial()).fit(
    cov_type="cluster", cov_kwds={"groups": pd.factorize(d.repo)[0]})
put("NModOnly", len(d)); put("ORModOnly", np.exp(r.params["is_agent"]), "{:.2f}"); put("PModOnly", r.pvalues["is_agent"], "{:.2f}")
# robustness: repo fixed effects (conditional) via within-repo demeaning proxy: add repo dummies where feasible
try:
    rf = smf.glm("any_prod ~ is_agent + log_size + C(repo)", data=m, family=sm.families.Binomial()).fit()
    put("ORRepoFE", np.exp(rf.params["is_agent"]), "{:.2f}"); put("PRepoFE", rf.pvalues["is_agent"], "{:.2f}")
except Exception:
    put("ORRepoFE", "n/a"); put("PRepoFE", "n/a")

# ---- validation breakdown ----
v = pd.read_csv(DATA / "validation_prelabels.csv")
v["tp"] = v.pre.str.startswith("TP")
vr = []
for name, d in (("All sampled findings", v), ("High-impact checks", v[v.tier == "high"]), ("Hygiene checks", v[v.tier == "hygiene"]),
                ("Terraform files", v[v.file.str.endswith((".tf", ".tfvars"))]), ("Kubernetes files", v[~v.file.str.endswith((".tf", ".tfvars"))])):
    vr.append(f"{name} & {len(d)} & {100*d.tp.mean():.0f}\\% \\\\")
(P / "tab_validation.tex").write_text(
    "\\begin{table}[t]\\centering\\caption{Manual validation: share of sampled introduced findings that are real problems in deployable configuration.}"
    "\\label{tab:validation}\\small\\begin{tabular}{@{}lrr@{}}\\toprule Subset & Findings & Real\\\\\\midrule\n" + "\n".join(vr) +
    "\n\\bottomrule\\end{tabular}\\end{table}\n")
put("ValFPtest", int((~v.tp).sum()))

# ---- size distribution figure ----
fig, ax = plt.subplots(figsize=(3.4, 1.9))
bins = np.logspace(0, 4, 30)
ax.hist(m[m.is_agent == 0].iac_additions.clip(lower=1), bins=bins, alpha=.6, label="Human", color="#9aa0ad")
ax.hist(m[m.is_agent == 1].iac_additions.clip(lower=1), bins=bins, alpha=.6, label="Agent", color="#2a4bff")
ax.set_xscale("log"); ax.set_xlabel("IaC lines added per PR (log scale)", fontsize=8); ax.set_ylabel("PRs", fontsize=8)
ax.tick_params(labelsize=7); ax.legend(fontsize=7, frameon=False)
plt.tight_layout(); plt.savefig(P / "fig_size.pdf"); plt.close()

# ---- real examples: high-impact deployable findings in agent PRs, short snippet from the head file ----
ex = intro[(intro.is_agent == 1) & (intro.ctx == "prod") & (intro.tier == "high") & intro.pr_id.isin(m.pr_id)]
picked, blocks = set(), []
for pat in [r"\"\*\"|wildcard|IAM", r"privilege ?escalation|privileged", r"0\.0\.0\.0|public|ingress"]:
    cand = ex[ex.check_name.str.contains(pat, case=False, regex=True) & ~ex.pr_id.isin(picked)]
    for _, row in cand.iterrows():
        f = RAW / "agent" / str(row.pr_id) / "head" / row.file
        if not f.exists():
            continue
        lines = f.read_text(errors="ignore").splitlines()
        key = str(row.resource).split(".")[-1].split("/")[-1]
        hit = next((i for i, L in enumerate(lines) if key and key in L), None)
        if hit is not None and not row.file.endswith((".tf", ".tfvars")):
            hit = next((i for i in range(hit, len(lines)) if re.match(r"\s*containers\s*:", lines[i])), hit)
        if hit is None:
            continue
        snip = [L.rstrip()[:70] for L in lines[hit:hit + 9]]
        agent = m.loc[m.pr_id == row.pr_id, "agent"].iloc[0].replace("_", " ").replace("OpenAI ", "")
        blocks.append((agent, row.check_name, row.file.split("/")[-1], snip))
        picked.add(row.pr_id)
        break
tex = []
for i, (agent, chk, fname, snip) in enumerate(blocks, 1):
    tex.append(f"\\noindent\\textit{{Example {i}}} ({agent}, \\texttt{{{tex_escape(fname)}}}): {tex_escape(chk)}.\n"
               "\\begin{lstlisting}\n" + "\n".join(snip) + "\n\\end{lstlisting}\n")
(P / "examples.tex").write_text("\n".join(tex) if tex else "% no examples found\n")
put("NExamples", len(blocks))

for g in ("agent", "human"):
    recs = [json.loads(l) for l in (DATA / f"{g}_fetch.jsonl").read_text().splitlines()]
    put(f"N{g}Fetched", sum(r["ok"] for r in recs)); put(f"N{g}Requested", len(recs))
(P / "numbers2.tex").write_text("% AUTO-GENERATED by scripts/06_extra.py\n" + "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in N.items()) + "\n")
print(json.dumps(N, indent=0))
print("examples:", [(b[0], b[1]) for b in blocks])
