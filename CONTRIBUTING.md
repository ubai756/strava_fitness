# Contributing

Thanks for your interest in improving this project.

## How to contribute

1. **Fork** the repository and create a new branch for your change.
2. Make your changes (new charts, cleaned-up ETL logic, bug fixes, etc.).
3. Test locally:
   ```bash
   pip install -r requirements.txt
   python etl.py --data-dir "./data/Fitabase Data 4.12.16-5.12.16" --out fitness.db
   streamlit run app.py
   ```
4. Open a **pull request** describing what you changed and why.

## Reporting issues

If you find a bug or have a feature request, please open an issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce (if applicable)

## Style guidelines

- Keep functions small and single-purpose (see `etl.py` for the pattern).
- Document any new data-cleaning step with a short print/log line, the same
  way the existing ETL steps do.
- Match the existing glassmorphic dashboard styling (`ACCENT` color variables
  in `app.py`) rather than introducing a new visual style per page.
