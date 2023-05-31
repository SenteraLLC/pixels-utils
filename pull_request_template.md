# <Title_Here>
## What?
-
## Why?
-
## CR strategy
Goal: guide the reviewer through the code
### CR checklist
- [ ]
## PR Checklist
- [ ] Merged latest main
- [ ] Updated version number
- [ ] Version numbers match between package `_version.py` and `pyproject.toml`
- [ ] Ran `poetry update` and committed `pyproject.toml` and `poetry.lock`
- [ ] Ran `poetry run pre-commit autoupdate`
- [ ] Successfully ran tests via `poetry run pytest`
## Breaking Changes