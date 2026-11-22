# Results (scanner findings; validation sample precision reported separately)

Scannable PRs: agent 915, human 820. Same-repository sample: 107 repos, 462 agent PRs, 631 human PRs.

## RQ1

| Outcome                 | Agent   | Human   | OR [95% CI]       |     p |   pairs | agent-only/human-only   |   McNemar p |
|:------------------------|:--------|:--------|:------------------|------:|--------:|:------------------------|------------:|
| All findings            | 11.7%   | 13.8%   | 0.71 [0.36, 1.37] | 0.305 |     279 | 26/24                   |       0.888 |
| Deployable configs only | 5.6%    | 7.8%    | 0.64 [0.26, 1.57] | 0.329 |     279 | 11/16                   |       0.442 |
| High-impact, deployable | 5.0%    | 6.8%    | 0.65 [0.25, 1.69] | 0.379 |     279 | 10/15                   |       0.424 |

## Per agent (same repos)

| agent        |   PRs |   any_all |   any_prod |   any_high |   median_lines |
|:-------------|------:|----------:|-----------:|-----------:|---------------:|
| Human        |   631 |      13.8 |        7.8 |        6.8 |             17 |
| Claude_Code  |   205 |      15.1 |       10.2 |        9.3 |             24 |
| Copilot      |   120 |       5.8 |        1.7 |        0.8 |             45 |
| OpenAI_Codex |   117 |      11.1 |        1.7 |        1.7 |             25 |
| Google_Jules |    17 |       0   |        0   |        0   |             78 |
| Cursor       |     3 |     100   |       33.3 |       33.3 |             34 |

- Claude_Code vs human (deployable): OR 1.39 [0.60, 3.22], p=0.440, n=205
- Copilot vs human (deployable): OR 0.15 [0.03, 0.93], p=0.042, n=120
- OpenAI_Codex vs human (deployable): OR 0.15 [0.02, 1.21], p=0.075, n=117

- terraform: 519 PRs, agent 3.3% vs human 5.0% (deployable); OR 0.28 [0.06, 1.46], p=0.133
- k8s: 579 PRs, agent 8.5% vs human 10.7% (deployable); OR 0.89 [0.37, 2.15], p=0.804

## RQ2: % of PRs introducing each category (deployable, same repos)

| category            |   Human |   Agent |
|:--------------------|--------:|--------:|
| identity_access     |     6   |     3.9 |
| container_privilege |     3.8 |     3.2 |
| image_supply_chain  |     4.6 |     3.2 |
| secrets             |     2.1 |     1.9 |
| resource_limits     |     3.8 |     1.5 |
| namespace_isolation |     1.1 |     1.1 |
| network_exposure    |     1.1 |     0.4 |
| other               |     1.1 |     0.4 |
| encryption          |     1.3 |     0.2 |
| logging_monitoring  |     0.8 |     0.2 |
| data_resilience     |     0.2 |     0   |

## RQ3: merge rate by whether a deployable finding was introduced

|   is_agent |    0 |    1 |
|-----------:|-----:|-----:|
|          0 | 82.1 | 59.2 |
|          1 | 75.2 | 50   |

Merge model: finding OR 0.38 (p=0.077); interaction with agent p=0.99

Validation sample: 110 findings, 78% labelled real (deployable) problems.

