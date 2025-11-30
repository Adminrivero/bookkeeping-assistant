# 🤝 Contributing Guide

We welcome contributions to Bookkeeping Assistant!  
This guide explains workflow, branching, commit hygiene, and pull requests.

---

## Workflow

1. **Fork & Clone**

    ```bash
    git clone https://github.com/<your-username>/bookkeeping-assistant.git
    cd bookkeeping-assistant
    ```

2. **Create a Branch**

    ```bash
    git checkout -b feature/<issue-number>-short-description
    ```

3. **Make Changes**

   - Keep code modular and documented
   - Add or update tests
   - Run `pytest -v` before committing

4. **Commit**

   - Use Conventional Commits:

     - `feat:` new feature
     - `fix:` bug fix
     - `docs:` documentation
     - `test:` tests
     - `refactor:` code restructuring

   - Example:

        ```bash
        git commit -m "feat(cli): add --bank flag for multi-bank ingestion (#37)"
        ```

5. **Push & Open PR**

    ```bash
    git push origin feature/<issue-number>-short-description
    ```

   - Open a Pull Request against `main`

   - Reference the issue with *“Closes #{issue-number}”*

---

## Branching Strategy

- `main` → stable, production-ready code
- `feature/*` → new features or fixes
- `hotfix/*` → urgent fixes

---

## Commit Hygiene

- Small, atomic commits
- Clear messages
- Reference issues when relevant

---

## Pull Requests

- Include description of changes
- Link related issues
- Ensure CI tests pass
- Request review before merging

---

## Code Style

- Follow PEP8
- Use type hints
- Keep functions small and focused
- Document public functions with docstrings

---
