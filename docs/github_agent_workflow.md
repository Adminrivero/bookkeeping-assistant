# **Git / GitHub Workflow for Humans & Agents**  
**Version:** 1.0.0  
**Status:** Stable  
**Owner:** Hector Rivero  
**Last Updated:** _2026‑01‑31_

---

## **Purpose**

- Provide a compact, reproducible workflow for humans and Copilot Agents to create, test, review, and merge changes safely.  
- Keep process separate from product constraints (see `docs/rule_generator_constraints.md`).  
- Ensure all contributions remain small, auditable, and reversible.

---

## **Principles**

- Small, focused branches and commits.  
- Tests must pass locally and in CI before merging.  
- PRs require at least one human reviewer and passing CI.  
- Agents follow the same rules as humans.  
- Every change must include human‑readable intent.

---

## **Branching Model**

Always branch off `main`.

### **Branch naming**
- `feat/<short-desc>`
- `fix/<short-desc>`
- `chore/<short-desc>`
- `test/<short-desc>`

### **Create branch**
```bash
git fetch origin
git checkout -b feat/my-feature
```

---

## **Commit Messages (Conventional Commits)**

Format:  
`<type>(<scope>): short summary`

### **Examples**
- `feat(export): add set_tax_year to SpreadsheetExporter`
- `fix(pdf_ingest): avoid dropping entire table when header drop >= available rows`

### **Create commit**
```bash
git add -A
git commit -m "feat(<scope>): short description"
```

Keep commits small and focused.

---

## **Local Checks Before Pushing**

Run tests and linters:

```bash
pytest -q
# run a single test:
pytest tests/test_export_summary.py::test_add_annual_summary_section_basic -q
```

---

## **Push & Open PR**

Push branch:

```bash
git push -u origin feat/my-feature
```

Open PR:

```bash
gh pr create --fill
```

### **PR body should include:**
- Short description and motivation  
- Testing instructions / commands  
- Summary of files changed  
- Links to related issues  
- Links to constraints (`docs/rule_generator_constraints.md`)  

---

## **Review & Iteration**

- Wait for human review and CI.  
- Address feedback with small commits.

### **Fixup commits**
```bash
git commit --fixup=<sha>
```

### **Interactive rebase**
```bash
git rebase -i origin/main
git push --force-with-lease
```

Avoid force‑pushing to shared branches without communication.

---

## **CI & Merge Rules**

A PR may be merged only after:

- CI passes  
- Required approvals are present  

### **Merge strategy**
- Prefer **Squash and merge** for small features  
- Keep commit summary clean when squashing  

---

## **Releases & Tags**

- Follow semantic versioning.  
- Update changelog as needed.  
- Tag releases on merge.

---

## **Agent‑Specific Rules**

Agents must:

- Use a single‑purpose branch and PR  
- Include tests and update docs when behavior changes  
- Reference `docs/rule_generator_constraints.md` in PR description  
- Not modify unrelated files  
- Not perform multi‑step or multi‑module changes  
- Never push directly to `main`  
- Never merge their own PRs  

Agents must operate within:

- The constraints document  
- The system contracts  
- The Agent Brief for the task  

---

## **Security & Secrets**

- Never commit secrets or credentials.  
- Use environment variables or GitHub Secrets for CI.  

---

## **PR Checklist (for templates)**

- [ ] Tests added/updated where relevant  
- [ ] Linting passes locally  
- [ ] CI is green  
- [ ] PR description explains intent and testing steps  
- [ ] Linked to relevant docs or issues  
- [ ] At least one human reviewer assigned  

---

## **Contact / Exceptions**

For emergencies or large refactors:

- Include a design note in the PR  
- Request a design review  
