# Agent instructions

- The Home Assistant integration is in `custom_components/saleryd_hrv`; tests are in
  `tests`.
- Follow `CONTRIBUTING.md` and update relevant documentation when behavior changes.
- Run `pre-commit run --all-files` before submitting changes. The hooks use the
  versions pinned in `.pre-commit-config.yaml`.
- For tests, use Python 3.14.2 or newer and install dependencies as described in
  `tests/README.md`. Run targeted tests first, then `pytest tests/` as appropriate.
- Do not log installer passwords or other sensitive values.
