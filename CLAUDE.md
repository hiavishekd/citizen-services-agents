# Citizen Services Agents

Multi-agent citizen-services prototype built on Neuro SAN Studio (Cognizant AI Lab hackathon, Track 2). This
repository is public.

## Rules

- **No keys in files.** The API key lives only in the `ANTHROPIC_API_KEY` environment variable. The only environment
  file in the repo is `.env.example`, with `ANTHROPIC_API_KEY=` and no value.
- **Public or synthetic data only.** Every file in `data/` is public information, authored demo content or synthetic.
  No client or personal data.
- **Links only from `data/Sources_Registry.csv`.** A reply may contain only links that appear in the registry. The
  reply guard removes any other link or web address.
- **Personal details only in `sly_data`.** Names, phone numbers, account numbers and similar details are stored in
  `sly_data` by the coded tools. They are never repeated in prompts or replies.
- **Reply guard last.** Every network ends by passing its draft reply through `coded_tools/reply_guard.py` and sends
  back exactly what it returns.
- **Neutral naming.** Call the project "Citizen Services Agents".

## Setup

- Python 3.12 via uv (the system Python 3.14 is not used).
- The upstream framework is cloned into `neuro-san-studio/` by `scripts/setup.sh` and is git-ignored.
- Run `ns` commands from inside `neuro-san-studio/` with the `.venv` environment. See the README for the full steps.
