# Citizen Services Agents

Hackathon entry built on Neuro SAN Studio (Cognizant AI Lab, Track 2). This repository is **public**.

## Rules

- **Never write an API key into any file.** The key lives only in the `ANTHROPIC_API_KEY` environment variable.
  Commit only `.env.example` with `ANTHROPIC_API_KEY=` and no value.
- **Public or synthetic data only.** Use open-source/public datasets or synthetic data. No client data.
- **No references to other projects, websites or domains** in any file or commit message.
- **Neutral naming:** call the project "Citizen Services Agents".

## Setup

- Python 3.12 via uv (the system Python 3.14 is not used).
- Upstream framework is cloned into `neuro-san-studio/` and is git-ignored.
- Run `ns` commands from inside `neuro-san-studio/` with the `.venv` environment.
