# Agent instructions

Fairness model for the Anesthetist's Peel Assignment Problem (APAP). See `README.md` for the
problem description and the pipeline.

## Tooling split

* **Preprocessing and models in Python.** Schedule conversion and result export are in
  `code/data/`, the optimisation model (Gurobi) in `code/models/`.
* **Postprocessing and figures in R with ggplot2** (`code/apap_figures.R`). Don't
  make figures with matplotlib. `code/script.R` is the older figure script.
* **Results are exchanged as CSV** (`data/results/`, written by `code/data/apap_export.py`).
  The SQLite database built by `make import` is legacy; don't build new work on it.
* Run scripts from `code/`; paths are relative to it (`../data/...`). Python dependencies go in
  `code/requirements.txt`.

## The paper (`docs/`)

* A single Quarto document, `docs/index.qmd`, with the HÍ theme `haskoli-islands-html`
  (extension pinned in `docs/_extensions/`). Code chunks are hidden.
* `docs/_setup.R` sources `code/apap_figures.R` and loads `docs/data/apap.sqlite`. The compact
  database is derived from `data/results/` by `code/data/build_docs_db.py`. Put plotting
  functions in `apap_figures.R`, not in the chunks.
* The paper is in English. `_setup.R` sets `LC_TIME` to `C` so dates don't follow the system
  locale; keep it.
* `.github/workflows/docs.yml` installs the small set of required R packages and renders the
  document on GitHub Actions. There is no Quarto freeze; `make docs` from `code/` rebuilds the
  compact database when exported results change and renders the paper.
* `docs/_output/` and `docs/.quarto/` are build output and gitignored.

## Pipeline notes

* `make all` and `make assigned` re-solve every week whose inputs or model code are newer than
  its solution, with Gurobi. Don't run them unless asked.
* `make import` writes `data/weekly_assigned_data/database.sqlite`, but `apap_export.py` reads
  the February 2024 build (`database-2024-02-26.sqlite`) by default. Pass `--db` for another.
* `make import` also copies the database to a hard-coded Downloads path; that only works on
  the author's machine.

## Data privacy

* Doctors appear by their initials, as in the schedules they provided for research. The paper
  must use pseudonymous codes before publication: `python -m data.apap_export --pseudonymise`.
* `data/results/` and the pseudonym key `data/doctor_key.csv` are gitignored. Never commit the
  key.
* New codes are assigned in random order, never alphabetically.
* Don't add real names to the paper, figures, commit messages or logs.

## Git

* Commit or push only when asked.
* `*.json` is gitignored. Tracked JSON files elsewhere were added deliberately.
