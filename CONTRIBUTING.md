# Contributing

Thanks for helping improve this project!

## Dev setup

1. Python 3.9+
2. Install deps:

   ```bash
   pip install -r requirements.txt
   pip install ruff==0.5.7 black==24.8.0 mypy==1.10.0
   ```

3. Run checks:

   ```bash
   ruff check .
   black --check .
   mypy suno_metadata_collector.py
   ```

## Versioning

- Update the version string and notes at the top of `suno_metadata_collector.py` and the README.
- Use semver-like bumps: major.minor.patch (e.g., 2.1.0, 2.0.2).

## Pull requests

- Include OS, Python version, and repro steps.
- Attach a sample log snippet (with sensitive parts removed) if reporting HTTP errors.
