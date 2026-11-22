"""Step 4: compare agent vs human IaC PRs (same repositories, size-controlled) + robustness checks.

Outputs:
  data/results.md          human-readable results
  paper/numbers.tex        LaTeX macros with every number used in the paper (never type numbers by hand)
  paper/fig_categories.pdf, paper/fig_agents.pdf
"""
import json, sys
import numpy as np, pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.contingency_tables import mcnemar
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import DATA, ROOT
from rules import context, tier

PAPER = ROOT / "paper"
pd.set_option("display.width", 200)


def repo_of(url):
    return "/".join(url.split("github.com/")[1].split("/")[:2])


def load(group):
    pr = pd.read_parquet(DATA / f"pr_scan_{group}.parquet")
    meta = pd.read_parquet(DATA / ("iac_prs.parquet" if group == "agent" else "human_prs.parquet"))
    cols = ["pr_id", "html_url"] + (["agent"] if group == "agent" else [])
    pr = pr.merge(meta[cols], on="pr_id")
    if group == "human":
        pr["agent"] = "Human"
    pr["repo"] = pr.html_url.map(repo_of)
    pr["is_agent"] = int(group == "agent")
    intro = pd.read_parquet(DATA / f"introduced_{group}.parquet")
    intro["ctx"] = intro.file.map(context)
    intro["tier"] = intro.check_name.map(tier)
    return pr, intro


ag, ia = load("agent")
hu, ih = load("human")
pr = pd.concat([ag, hu], ignore_index=True)
intro = pd.concat([ia, ih], ignore_index=True)
pr["log_size"] = np.log1p(pr.iac_additions.clip(lower=0))


def flag(mask_name, mask):
    s = intro[mask].groupby("pr_id").size()
    pr[mask_name] = pr.pr_id.map(s).fillna(0).astype(int)


flag("n_all", intro.pr_id.notna())
flag("n_prod", intro.ctx == "prod")
flag("n_high", (intro.ctx == "prod") & (intro.tier == "high"))
for k in ("all", "prod", "high"):
    pr[f"any_{k}"] = (pr[f"n_{k}"] > 0).astype(int)

both = set(ag.repo) & set(hu.repo)
m = pr[pr.repo.isin(both)].copy()
m.to_parquet(DATA / "analysis_table.parquet", index=False)

N = {}  # numbers for LaTeX


def put(k, v, fmt="{}"):
    if fmt == "{}" and isinstance(v, (int, np.integer)) and v >= 1000:
        fmt = "{:,}"
    N[k] = fmt.format(v)


put("NagentAll", len(ag)); put("NhumanAll", len(hu))
put("Nrepos", m.repo.nunique()); put("NagentSame", int((m.is_agent == 1).sum())); put("NhumanSame", int((m.is_agent == 0).sum()))
put("RawAgentPct", 100 * ag.introduced.gt(0).mean(), "{:.1f}"); put("RawHumanPct", 100 * hu.introduced.gt(0).mean(), "{:.1f}")


def logit(d, y):
    try:
        f = smf.glm(f"{y} ~ is_agent + log_size", data=d, family=sm.families.Binomial()).fit(
            cov_type="cluster", cov_kwds={"groups": pd.factorize(d.repo)[0]})
        o = np.exp(f.params["is_agent"]); lo, hi = np.exp(f.conf_int().loc["is_agent"])
        return o, lo, hi, f.pvalues["is_agent"]
    except Exception:
        return (np.nan,) * 4


def pairs(d, y):
    out = []
    for _, g in d.groupby("repo"):
        h = g[g.is_agent == 0]
        for _, a in g[g.is_agent == 1].iterrows():
            if h.empty:
                break
            j = (h.log_size - a.log_size).abs().idxmin()
            out.append((a[y], h.loc[j, y])); h = h.drop(j)
    p = pd.DataFrame(out, columns=["a", "h"])
    t = pd.crosstab(p.a, p.h).reindex(index=[0, 1], columns=[0, 1], fill_value=0)
    return len(p), int(t.loc[1, 0]), int(t.loc[0, 1]), mcnemar(t.values, exact=True).pvalue


lines = ["# Results (scanner findings; validation sample precision reported separately)", "",
         f"Scannable PRs: agent {len(ag)}, human {len(hu)}. Same-repository sample: {m.repo.nunique()} repos, "
         f"{(m.is_agent==1).sum()} agent PRs, {(m.is_agent==0).sum()} human PRs.", ""]
rows = []
for k, label in (("all", "All findings"), ("prod", "Deployable configs only"), ("high", "High-impact, deployable")):
    o, lo, hi, p = logit(m, f"any_{k}")
    n, ao, ho, mp = pairs(m, f"any_{k}")
    a_pct, h_pct = 100 * m[m.is_agent == 1][f"any_{k}"].mean(), 100 * m[m.is_agent == 0][f"any_{k}"].mean()
    rows.append([label, f"{a_pct:.1f}%", f"{h_pct:.1f}%", f"{o:.2f} [{lo:.2f}, {hi:.2f}]", f"{p:.3f}", f"{n}", f"{ao}/{ho}", f"{mp:.3f}"])
    K = k.capitalize()
    put(f"Agent{K}Pct", a_pct, "{:.1f}"); put(f"Human{K}Pct", h_pct, "{:.1f}")
    put(f"OR{K}", o, "{:.2f}"); put(f"ORlo{K}", lo, "{:.2f}"); put(f"ORhi{K}", hi, "{:.2f}"); put(f"P{K}", p, "{:.2f}")
    put(f"Pairs{K}", n); put(f"PairsA{K}", ao); put(f"PairsH{K}", ho); put(f"McP{K}", mp, "{:.2f}")
tab = pd.DataFrame(rows, columns=["Outcome", "Agent", "Human", "OR [95% CI]", "p", "pairs", "agent-only/human-only", "McNemar p"])
lines += ["## RQ1", "", tab.to_markdown(index=False), ""]

# per agent (same repos)
pa = m.groupby("agent").agg(PRs=("pr_id", "size"), any_all=("any_all", "mean"), any_prod=("any_prod", "mean"),
                            any_high=("any_high", "mean"), median_lines=("iac_additions", "median")).sort_values("PRs", ascending=False)
lines += ["## Per agent (same repos)", "", (pa.assign(**{c: (pa[c] * 100).round(1) for c in ["any_all", "any_prod", "any_high"]})).to_markdown(), ""]
for a in ["Claude_Code", "OpenAI_Codex", "Copilot"]:
    if a in pa.index:
        put(f"{a.replace('_','').replace('OpenAI','')}N", int(pa.loc[a, "PRs"])); put(f"{a.replace('_','').replace('OpenAI','')}Pct", 100 * pa.loc[a, "any_prod"], "{:.1f}")

# each major agent vs humans (same repos, size-adjusted)
for a, key in (("Claude_Code", "Claude"), ("Copilot", "Copilot"), ("OpenAI_Codex", "Codex")):
    d = m[m.agent.isin([a, "Human"])]
    o, lo, hi, p = logit(d, "any_prod")
    lines.append(f"- {a} vs human (deployable): OR {o:.2f} [{lo:.2f}, {hi:.2f}], p={p:.3f}, n={int((d.agent==a).sum())}")
    put(f"OR{key}", o, "{:.2f}"); put(f"ORlo{key}", lo, "{:.2f}"); put(f"ORhi{key}", hi, "{:.2f}"); put(f"P{key}", p, "{:.2f}")
    put(f"N{key}", int((d.agent == a).sum())); put(f"Pct{key}", 100 * d[d.agent == a].any_prod.mean(), "{:.1f}")
lines.append("")

# file-type split (all scannable PRs)
for kind in ("terraform", "k8s"):
    d = m[m.kinds.str.contains(kind)]
    o, lo, hi, p = logit(d, "any_prod")
    lines.append(f"- {kind}: {len(d)} PRs, agent {100*d[d.is_agent==1].any_prod.mean():.1f}% vs human {100*d[d.is_agent==0].any_prod.mean():.1f}% (deployable); OR {o:.2f} [{lo:.2f}, {hi:.2f}], p={p:.3f}")
    K = "Terraform" if kind == "terraform" else "Kube"
    put(f"N{K}", len(d)); put(f"OR{K}", o, "{:.2f}"); put(f"P{K}", p, "{:.2f}")
lines.append("")

# RQ2 categories (deployable findings, same repos)
im = intro[intro.pr_id.isin(m.pr_id) & (intro.ctx == "prod")].merge(m[["pr_id", "is_agent"]], on="pr_id")
share = (im.groupby(["is_agent", "category"]).pr_id.nunique().unstack(0).fillna(0)
         .div(m.groupby("is_agent").size(), axis=1) * 100).rename(columns={0: "Human", 1: "Agent"}).sort_values("Agent", ascending=False)
lines += ["## RQ2: % of PRs introducing each category (deployable, same repos)", "", share.round(1).to_markdown(), ""]
top = share.Agent.idxmax(); put("TopCat", top.replace("_", " ")); put("TopCatAgent", share.loc[top, "Agent"], "{:.1f}"); put("TopCatHuman", share.loc[top, "Human"], "{:.1f}")
share.index = share.index.str.replace("_", " ")
ax = share.iloc[::-1].plot.barh(figsize=(3.4, 3.0), color=["#9aa0ad", "#2a4bff"], width=0.8)
ax.set_xlabel("% of PRs introducing ≥1 finding", fontsize=8); ax.set_ylabel("")
ax.tick_params(labelsize=7); ax.legend(fontsize=7, frameon=False)
plt.tight_layout(); plt.savefig(PAPER / "fig_categories.pdf"); plt.close()

# RQ3 merge rates
merged = m.dropna(subset=["merged"]).groupby(["is_agent", "any_prod"]).merged.mean().unstack()
lines += ["## RQ3: merge rate by whether a deployable finding was introduced", "", (merged * 100).round(1).to_markdown(), ""]
put("MergeAgentClean", 100 * merged.loc[1, 0], "{:.0f}"); put("MergeAgentFind", 100 * merged.loc[1, 1], "{:.0f}")
put("MergeHumanClean", 100 * merged.loc[0, 0], "{:.0f}"); put("MergeHumanFind", 100 * merged.loc[0, 1], "{:.0f}")
mm = smf.glm("merged ~ any_prod * is_agent + log_size", data=m.dropna(subset=["merged"]).assign(merged=lambda x: x.merged.astype(int)),
             family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(m.dropna(subset=["merged"]).repo)[0]})
put("MergeORFind", np.exp(mm.params["any_prod"]), "{:.2f}"); put("MergePFind", mm.pvalues["any_prod"], "{:.2f}")
lo_, hi_ = np.exp(mm.conf_int().loc["any_prod"]); put("MergeORlo", lo_, "{:.2f}"); put("MergeORhi", hi_, "{:.2f}")
put("MergePInter", mm.pvalues["any_prod:is_agent"], "{:.2f}")
lines += [f"Merge model: finding OR {np.exp(mm.params['any_prod']):.2f} (p={mm.pvalues['any_prod']:.3f}); interaction with agent p={mm.pvalues['any_prod:is_agent']:.2f}", ""]

# figure: per-agent deployable share with counts
fig, ax = plt.subplots(figsize=(3.4, 2.2))
pp = pa[pa.PRs >= 10].sort_values("any_prod")
ax.barh([f"{i.replace('_',' ')} (n={int(r.PRs)})" for i, r in pp.iterrows()], pp.any_prod * 100,
        color=["#9aa0ad" if i == "Human" else "#2a4bff" for i in pp.index])
ax.set_xlabel("% of PRs introducing ≥1 deployable finding", fontsize=8); ax.tick_params(labelsize=7)
plt.tight_layout(); plt.savefig(PAPER / "fig_agents.pdf"); plt.close()

# validation sample
v = DATA / "validation_prelabels.csv"
if v.exists():
    vs = pd.read_csv(v)
    put("ValN", len(vs)); put("ValPrec", 100 * vs.pre.str.startswith("TP").mean(), "{:.0f}")
    lines += [f"Validation sample: {len(vs)} findings, {100*vs.pre.str.startswith('TP').mean():.0f}% labelled real (deployable) problems.", ""]

# step-1 counts
s1 = pd.read_parquet(DATA / "iac_prs.parquet")
put("NaidevIac", len(s1)); put("NaidevRepos", s1.repo_id.nunique()); put("NaidevTotal", "361{,}296")
put("Nintro", int(m.n_prod.sum()))
put("NhumanCollected", len(pd.read_parquet(DATA / "human_prs.parquet"))); put("NhumanRepos", pd.read_parquet(DATA / "human_prs.parquet").repo.nunique())

(DATA / "results.md").write_text("\n".join(lines) + "\n")
(PAPER / "numbers.tex").write_text("% AUTO-GENERATED by scripts/05_compare.py. Do not edit by hand.\n" +
                                   "\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in N.items()) + "\n")
print("\n".join(lines))
