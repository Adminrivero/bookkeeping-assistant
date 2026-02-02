# Rule Generator — Overview

Purpose
- Central landing page for the Rule Generator documentation: constraints, evaluation contract, and test-harness contract.
- Serves authors, reviewers, and automation agents implementing or validating rules.

Canonical artifacts
- Rule schema (authoritative): `config/schemas/rule_schema.json`
- Legacy allocation rules: `config/allocation_rules.json`
- Schema validation tests: `tests/rule_generator/test_rule_schema_validation.py`

Primary docs
- Constraints (authoritative design & invariants): `docs/rule_generator/rule_generator_constraints.md`
- Evaluation contract (legacy-compatible rules): `docs/rule_generator/rule_evaluation_contract.md`
- Test harness contract (canonical tx shape & match-report): `docs/rule_generator/test_harness_contract.md`

How to validate locally
- Run schema validation tests:
```bash
pytest tests/rule_generator/test_rule_schema_validation.py -q
```

How to use `rule_generator_constraints.md` with Copilot Agents
This section helps avoid common mistakes when delegating work to VS Code Copilot Agents.

1) Always attach these artifacts to Agent Briefs
- Include: this constraints file (`rule_generator_constraints.md`), the rule schema (`config/schemas/rule_schema.json`), and the evaluation contract (`docs/rule_generator/rule_evaluation_contract.md`).
- Agents must import, not infer.

2) Limit agent scope: implement, don't design
- Agents should only implement modules or modify specified files following explicit instructions.
- Agents must never decide high-level architecture, create new modules, or change schemas without a human-approved design.

3) One work unit per agent run
- Valid units: implement a validator, add a priority resolver, implement CLI prompts.
- Invalid units: “Build the whole Wizard” or “Implement schema + CLI + tests” in one run.

4) Always provide
- Inputs, outputs, constraints, success criteria, and out-of-scope items.

5) Human review is mandatory
- Agents are executors, not architects. Review every agent output before merging.

Change process (short)
- Schema or invariant changes require human review, updated tests, and an updated constraints doc.
- See `docs/github_agent_workflow.md` for branching, PR, and agent rules.

Contact / Owner
- Owner: Hector Rivero
- For design review, open a PR against `main` and request at least one human reviewer.
