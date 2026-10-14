# Citizen Services Agents

Multi-agent citizen-services assistant built on
[Neuro SAN Studio](https://github.com/cognizant-ai-lab/neuro-san-studio) (Cognizant AI Lab hackathon, Track 2).
All data in this repo is public or synthetic.

## Layout

| Folder | What it holds |
|---|---|
| `networks/` | Our agent networks (`.hocon`) and their `manifest.hocon` |
| `coded_tools/` | Our Python tools used by the networks |
| `data/` | Grounding data: the source workbook and the CSVs generated from it |
| `config/` | `llm_config.hocon`, Anthropic-only model config |
| `scripts/` | `setup.sh`, `sync.sh`, `check.sh`, `run.sh`, `xlsx_to_csv.py` |

`neuro-san-studio/` and `.venv/` are created by `setup.sh` and are not tracked. `sync.sh` symlinks our folders into
the studio, so edits take effect immediately.

## Run it

Requires [uv](https://docs.astral.sh/uv/) and git.

```bash
git clone <this repo> && cd citizen-services-agents
./scripts/setup.sh                    # Python 3.12 venv, clones and installs the studio, links our files in
export ANTHROPIC_API_KEY="..."        # never commit your key; see .env.example
./scripts/check.sh                    # ns check-llm-keys and ns check-config
./scripts/run.sh                      # server on localhost:8080, UI on localhost:4173
```

## Regenerate the CSVs

```bash
.venv/bin/python -I scripts/xlsx_to_csv.py
```

## Data notes

Rows still needing an official source (`UNVERIFIED_SOURCE_NEEDED`):

- `data/Fraud_Report_Steps.csv`, step 3 ("Contact the bank, card provider, wallet or UPI app as well.").

Rows with a partial source, as stated in their `data_status`:

- `data/Helplines.csv`, H-102: the number is confirmed, "free" is not.
- `data/Helplines.csv`, H-108: confirmed on a state health mission page only.
- `data/Fraud_Report_Steps.csv`, step 4: the source lists name, mobile number, address and transaction details only.
