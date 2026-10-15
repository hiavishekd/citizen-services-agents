# Next steps

Done:

- Four networks: scheme navigator, health triage, fraud shield and governance dashboard, each tested on sample prompts.
- Reply guard on every network: it removes any link not in `Sources_Registry.csv` and any stored name or number. On health triage it also drops sentences that hint at a likely condition.
- Grounding data, setup scripts and official sources for the helplines.

To do:

- [ ] **README.** Judge-facing overview, run steps, tests and known limits.
- [ ] **Two-question test of the dashboard guard.** Check the differencing refusal in a real session in the UI, not only with a seeded history.
- [ ] **Helpline numbers.** The reply guard checks links only. Add a check that numbers in replies come from `Helplines.csv`.
- [ ] **Video.** Record a short demo of the networks in the UI.
- [ ] **Submission form.** Fill in and submit.
- [ ] **Open data questions.** The H-102 text says "Free" but the source confirms only the number. Fraud step 3 still has no official source. Native-speaker check of the Hindi and Bengali replies.
