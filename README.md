# Learning fairness models for the Anesthetist's Peel Assignment Problem (APAP)

In a hospital anaesthesia department the working day has no fixed end. A consultant may go home
once the operating rooms they cover have closed, so each morning the department agrees on a
*peel-off order*: who is released first, second, and so on. Late positions mean long days, and
the order has to be shared out fairly.

This repository formulates that as a weekly mixed-integer program (Gurobi), applies it to 285
weeks of real call schedules (July 2018 to December 2023, 25 consultants), and reports how
evenly the resulting workload is shared.

* **Paper (working draft):** <https://hi-idn.github.io/IDeLM-APAP-learning-fairness-models/>,
  built from [`docs/`](docs/).
* **Operational background:** [`code/README.md`](code/README.md).
* **Colab notebook:** <https://colab.research.google.com/drive/1FYnkmLxjYgIOFjql5FyeEnBfj_jTFShB?usp=sharing>

## The model

Each weekday, every consultant in the order gets a position; the position is also their
*points* for the day. Most positions follow from the call schedule (post-call leaves first,
on-call leaves last). The 6–7 consultants without a fixed shift are the decision: the model
assigns them the middle positions so that points per day worked stay close to a common target,
subject to:

* each position is held by at most one consultant per day,
* pre-assigned and requested positions are respected,
* the *cardiac* and *in charge* roles are spread evenly, and no one holds both on the same day,
* no one is *in charge* on consecutive days.

The model is in [`code/models/allocation_model.py`](code/models/allocation_model.py); the paper
gives the full formulation.

## Repository layout

```
code/
  data/             schedule conversion (xls -> JSON -> weekly instances) and result export
  models/           allocation model and the weekly solver script
  web/              small web viewer for weekly schedules
  apap_figures.R    figures for the paper
  Makefile          the pipeline, from schedules to the rendered paper
data/
  quarterly_data/   call schedules as provided, one .xls per quarter, and their JSON conversion
  weekly_*_data/    weekly instances, requests and solved weeks (mostly local, gitignored)
  results/          CSV export of the solved weeks (local, gitignored)
  staff.csv         consultants and their roles
docs/               the paper (Quarto), published to GitHub Pages
figures/            earlier figures
```

## Getting started

Requires Python 3 and a [Gurobi](https://www.gurobi.com) licence (free for academics; the
`gurobipy` pip package includes a size-limited trial licence). Rendering the paper needs R,
`DBI`, `RSQLite`, `dplyr`, `tidyr`, `ggplot2`, `scales`, and [Quarto](https://quarto.org) 1.5 or
later.

```bash
pip install -r code/requirements.txt
```

Everything runs from `code/`:

```bash
make quarterly    # .xls schedules  -> quarterly JSON
make weekly       # quarterly JSON  -> weekly call plans
make unassigned   # weekly plans    -> unassigned weekly instances
make assigned     # solve each week with the allocation model
make import       # solved weeks    -> SQLite database

python -m data.apap_export    # database -> CSV files in data/results/
                              # (--pseudonymise for random codes instead of initials)
make docs                     # update docs/data/apap.sqlite and render the paper
```

## The paper and GitHub Pages

The paper is rendered from `docs/` and published by
[`.github/workflows/docs.yml`](.github/workflows/docs.yml) on every push to `main` that touches
`docs/`, the figure code or its database builder.

The compact SQLite snapshot `docs/data/apap.sqlite` contains the result tables used by the paper.
GitHub Actions installs the R dependencies and executes the document on each build; no frozen
Quarto output is committed. After changing exported results, run `make docs` from `code/` and
include the updated database. Preview locally with `quarto preview docs`.

## License

See [LICENSE](LICENSE).
