# Next steps

Done:

- Scheme navigator, health triage and fraud shield networks, each with tests run against sample prompts.
- Reply guard on all three networks: it removes any link not in `Sources_Registry.csv` and any stored name or number.
- Grounding data, setup scripts and official sources for the helplines.

To do:

- [ ] **Governance dashboard.** Uses `Gov_Events.csv` (synthetic counts, small counts suppressed).
- [ ] **Health triage wording.** Replies sometimes repeat "mild cold and cough" from the person's own words. Tighten so no illness is named.
- [ ] **Helpline numbers.** The reply guard checks links only. Add a check that numbers in replies come from `Helplines.csv`.
- [ ] **README.** Add what each network does, example prompts, a test table, and the data notes.
- [ ] **Video.** Record a short demo of the networks in the UI.
- [ ] **Submission form.** Fill in and submit.
- [ ] **Open data questions.** The H-102 text says "Free" but the source confirms only the number. Fraud step 3 still has no official source. Native-speaker check of the Hindi and Bengali replies.
