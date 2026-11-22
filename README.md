# IaC security in agent-authored pull requests (research project)
Read `PROPOSAL.md` first.

## Run the pilot
```
cd "research-iac-agents"
.venv/bin/python scripts/pilot.py --agent-prs 20 --humans-per-repo 2
```
Needs the `gh` CLI logged in. Checkov is installed in `.venv` (run it as `.venv/bin/python -m checkov.main`, because the folder path has a space).
