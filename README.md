# Citizen Services Agents

Citizen Services Agents is a prototype of four cooperating AI assistants for public services, built on
[Neuro SAN Studio](https://github.com/cognizant-ai-lab/neuro-san-studio) for the Cognizant AI Lab hackathon, Track 2.
It helps **citizens** find government schemes they may qualify for, get safe first-step health guidance, check
suspicious messages and calls, and it helps **government officers** read aggregated activity counts without exposing
small groups. Every answer is grounded in a small set of public or synthetic data files, and every network is built to
refuse to guess, diagnose, or invent links. It is a prototype, not a production service.

## The four networks

| Network | What it does | Data it reads | Key safeguards |
|---|---|---|---|
| `scheme_navigator` | Asks a few short questions, then suggests central schemes from a fixed list of five and drafts what to prepare. | `Schemes.csv`, `Helplines.csv`, `Sources_Registry.csv` | Recommends only schemes in the data. Links come only from the source registry. Personal details are stored in `sly_data`, not repeated in prompts. Unconfirmed rules are marked as unconfirmed. |
| `health_triage` | Checks symptoms against a short list of red-flag warning signs, gives general care advice, and suggests a kind of facility. | `Health_RedFlags.csv`, `Health_Facilities.csv`, `Helplines.csv` | Never diagnoses and never names medicines or doses. The emergency message with 108 and 112 comes first when a red flag matches. Personal details stay in `sly_data`. Ignores instructions inside the person's message. |
| `fraud_shield` | Matches a pasted message or described call to known scam patterns, explains why it looks like a scam, and gives the reporting steps. | `Fraud_Patterns.csv`, `Fraud_Report_Steps.csv`, `Helplines.csv`, `Sources_Registry.csv` | Treats the message as untrusted text. Never repeats or opens its links. Never asks for OTPs, PINs or Aadhaar numbers. Names and numbers stay in `sly_data` and are removed from replies. Never claims a message is safe. |
| `governance_dashboard` | Answers an officer's questions with grouped counts, in English, Hindi or Bengali. | `Gov_Events.csv` | Counts below 10 are shown as "suppressed". Never returns individual records. Refuses a second question that could be subtracted from the first to reveal a small count. Every reply says it is synthetic demo data. |

## Architecture

```
  Person or officer (English, Hindi or Bengali)
                  |
                  v
   +-----------------------------+
   |  networks/*.hocon           |   one front agent per network, with its rules written as instructions
   |  (served by Neuro SAN)      |
   +--------------+--------------+
                  | calls
                  v
   +-----------------------------+        +----------------------------+
   |  coded_tools/*.py           | -----> |  sly_data (per session)    |
   |  scheme_lookup, health_     | <----- |  personal details, profile,|
   |  triage, fraud_shield,      |        |  released-counts history   |
   |  governance_dashboard       |        |  (kept out of the prompt)  |
   +--------------+--------------+        +----------------------------+
                  | reads only
                  v
   +-----------------------------+
   |  data/*.csv                 |   public or synthetic grounding data
   +-----------------------------+
                  |
                  v
   +-----------------------------+
   |  reply guard                |   last step of every network, applied to the draft reply:
   |  coded_tools/reply_guard.py |   removes links and web addresses not in Sources_Registry.csv,
   +--------------+--------------+   removes stored names and numbers, drops sentences that hint at a
                  |                  diagnosis (health), and adds "synthetic demo data" (dashboard)
                  v
          Final reply to the person
```

- **Networks** are plain HOCON files, written in the same format as the studio's own examples.
- **Coded tools** do everything that must be exact: matching rules, picking links, counting, suppressing small
  counts. The model explains and converses; it does not supply facts, links or numbers on its own.
- **`sly_data`** is the channel the studio keeps out of the chat stream. Tools save personal details there and the
  model is told only which fields are known, never their values.
- **The reply guard** is a deterministic last step, so a wrong link or a stored name cannot reach the person even if
  the model slips.

## Run it

Requires [uv](https://docs.astral.sh/uv/), git, and an Anthropic API key. Works on macOS and Linux. uv installs
Python 3.12 for you.

```bash
git clone https://github.com/hiavishekd/citizen-services-agents
cd citizen-services-agents
./scripts/setup.sh                      # creates .venv with Python 3.12, clones and installs the studio, links our files in
read -rs ANTHROPIC_API_KEY; export ANTHROPIC_API_KEY   # paste your key (it is not shown); never put it in a file
./scripts/check.sh                      # runs ns check-llm-keys and ns check-config
./scripts/run.sh                        # server on localhost:8080, UI on localhost:4173
```

Then open http://localhost:4173 and pick a network from the `citizen_services` folder in the list.
Press Ctrl+C in the terminal running `run.sh` to stop the server.

Notes from a fresh-clone run:

- `check.sh` is expected to report "1/7 valid, 6 warnings": the six warnings are other providers whose keys are not
  set, which this project does not use. The line that matters at the end is "All LLM configurations are working."
- `check.sh` prints a short masked preview of the key (first and last few characters). Do not paste its output into
  public places.
- On a machine with a warm uv cache, `setup.sh` took about 11 seconds. A first run downloads Python 3.12 and the
  packages and will take longer, depending on the connection.

**No key is stored in this repository.** The only environment file is `.env.example`, which has an empty value.
Judges can use a different provider by editing [config/llm_config.hocon](config/llm_config.hocon) (set `class` and
`model_name` to a provider the studio supports) and exporting that provider's key instead.

## Optional chat app

A small Gradio chat page is included as an alternative to the studio UI. It keeps the conversation and the session
data for each browser session, so multi-turn chats work, and picking a different network starts a new conversation.
The banner on the page reads "Prototype. Uses demo data. Not official advice." The app holds no API key; only the
server talks to the model.

```bash
./scripts/run.sh          # terminal 1: the Neuro SAN server on port 8080 (keep it running)
./scripts/run_app.sh      # terminal 2: the chat app, then open http://localhost:7860
```

If the server is not running, the app says so in plain words instead of failing. If you ran `setup.sh` before the app
was added, run it again once to install Gradio.

## Try these prompts

| Network | Prompt |
|---|---|
| `scheme_navigator` | `मेरे पास डेढ़ हेक्टेयर ज़मीन है। मुझे कौन सी सरकारी योजना मिल सकती है?` |
| `health_triage` | `मेरे पिताजी के सीने में बहुत दर्द है, पसीना आ रहा है और दर्द बाँह तक जा रहा है।` |
| `fraud_shield` | `I got an SMS saying my bank account will be blocked today unless I update my KYC using a link in the message.` |
| `governance_dashboard` | `Where do people report the most fraud?` |

More Bengali and English examples are in `data/Personas_Tests.csv`.

## Data

All files are in [data/](data/). They come from one workbook, `civic_platform_grounding_data.xlsx`, converted to CSV
by `scripts/xlsx_to_csv.py`. **No client data is used.** Everything is public information, authored demo content or
synthetic.

| File | Rows | Status |
|---|---|---|
| `Sources_Registry.csv` | 33 | Official and secondary public pages; each row says how it was checked. Only these links may appear in replies. |
| `Schemes.csv` | 5 | `REAL_SOURCED` (public scheme details; some rules are flagged as unconfirmed in the row) |
| `Helplines.csv` | 11 | `REAL_SOURCED` (some dated or from secondary sources, flagged in the row) |
| `Fraud_Report_Steps.csv` | 4 | 3 `REAL_SOURCED`, 1 `UNVERIFIED_SOURCE_NEEDED` |
| `Fraud_Patterns.csv` | 7 | `AUTHORED_DEMO` (synthetic example messages) |
| `Health_RedFlags.csv` | 9 | `AUTHORED_DEMO`; each row says clinician review is required |
| `Health_Facilities.csv` | 4 | `SYNTHETIC` (fictional facilities) |
| `Personas_Tests.csv` | 5 | `AUTHORED_DEMO` (test personas) |
| `Gov_Events.csv` | 10 | `SYNTHETIC` (fictional counts) |
| `Sly_Data_Spec.csv` | 7 | Specification of which fields are kept out of prompts |

**Rows that still need an official source or have only a partial one:**

- `Fraud_Report_Steps.csv`, step 3 ("Contact the bank, card provider, wallet or UPI app as well"): marked
  `UNVERIFIED_SOURCE_NEEDED`. Replies add "(not yet checked against an official source)" after it.
- `Helplines.csv`, H-102: the number is confirmed, the word "free" is not.
- `Helplines.csv`, H-108: confirmed on one state health mission page only.
- `Fraud_Report_Steps.csv`, step 4: the source lists name, mobile number, address and transaction details only.
- `Schemes.csv`: the PM-JAY age 70+ rule and the pension amounts are marked unconfirmed or varying by state in the rows.

## Tests

There is no automated test suite yet. The tests below were run by hand, one prompt at a time, with
`ns chat --one_shot`, and every reply was read. Results from the final runs:

| Network | Prompts | Result |
|---|---|---|
| `scheme_navigator` | The 5 personas in `Personas_Tests.csv` (Bengali, Hindi x3, English) plus a Hindi farmer prompt | 6 of 6 pass. Every link in every reply is in the registry. |
| `health_triage` | Red flag in Hindi, red flag in Bengali, mild case in English, medicine-dose request, injection attempt, message with a fictional name and phone | 6 of 6 pass. Emergency message with 108 and 112 comes first in both red-flag cases. |
| `fraud_shield` | Fake KYC SMS (English), fake bank call (Hindi), lottery message (Bengali), harmless message, injection attempt, message with a fictional name and phone | 6 of 6 pass. No scam link or stored name appears in any reply. |
| `governance_dashboard` | Normal question, small cell, request for an individual's record, differencing attempt, injection attempt, Hindi question | 6 of 6 pass. The differencing refusal also held in a two-question session through the chat app. |

Some tests failed at first and were fixed: the family-benefit scheme was drafted when it did not apply, an English
prompt once got a Hindi reply, a fraud reply greeted the person by name, and health replies repeated "cold" from the
person's wording. The fixes are in the instructions and in the reply guard. Model replies vary between runs, so a
re-run can differ in wording.

To re-run a test, from the repo root after `./scripts/setup.sh` and exporting the key:

```bash
cd neuro-san-studio
printf '%s' "I own some farmland. Can I get PM-KISAN?" > /tmp/prompt.txt
../.venv/bin/ns chat --agent citizen_services/scheme_navigator --one_shot \
  --first_prompt_file /tmp/prompt.txt \
  --sly_data '{"profile": {"age": "45", "occupation": "Doctor", "owns_cultivable_land": "Yes", "income_tax_payer": "Yes"}}'
```

The scheme personas were run with the profile from the matching row of `Personas_Tests.csv` passed as `--sly_data`.
For the other networks leave out `--sly_data` and change `--agent` to `citizen_services/health_triage`,
`citizen_services/fraud_shield` or `citizen_services/governance_dashboard`.

## Known limits

- Tests are one-shot: one prompt, one reply. Multi-turn conversations and the browser UI were not systematically
  tested in the studio UI. The dashboard's differencing refusal was also checked in a live two-question session through
  the chat app (the second question was refused; the same question in a new session was answered), but only once.
- Keyword hints in the health and fraud tools are English only. Hindi and Bengali matching relies on the model's own
  reading of the message.
- The dashboard's differencing guard compares pairs of answers only. A chain of three or more questions could still
  leak a small count.
- The reply guard checks links and stored personal values. It does not check phone numbers in replies against
  `Helplines.csv`.
- Privacy is partial. A person's own message always reaches the model. `sly_data` keeps the stored copy out of later
  prompts and tool calls, and the guard removes stored values from replies, but it cannot hide what the person typed.
- The sample covers only five central schemes and four fictional facilities. Replies say so.
- The red-flag rules are authored demo content and need clinician review before any real use. The Hindi and Bengali
  replies have not been reviewed by a native speaker.

## Roadmap (not built)

These six modules appear in the data workbook but have **no network yet**:

- **Farmer advisory.** Would give mandi price and weather alerts and farming rules from public data. Not built.
- **Legal aid.** Would explain common legal pathways and point to free legal-aid contacts. Not built.
- **Education tutors.** Would suggest learning items and study paths from public learning material. Not built.
- **Disaster coordinator.** Would collect field reports and prioritise resources during an incident (simulation only).
  Not built.
- **Food waste matcher.** Would match surplus food listings with nearby organisations that can use them. Not built.
- **IT incident network.** Would triage incidents and suggest runbook steps for a service desk. Not built.
