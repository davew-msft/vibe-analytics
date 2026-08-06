# Loading the Healthcare Demo Data into Fabric

This demo ships a small, self-contained dataset (~500 rows total) representing three source
systems plus a nurse manager's spreadsheet — the kind you'd find in a newly-merged health system.

| Source system (real world) | What it is | Files in [`data/`](./data) |
|---|---|---|
| **Epic** (Caboodle / Clarity) | Nursing-unit dimension + daily clinical workload/acuity | `epic.DepartmentDim.csv`, `epic.NursingUnitCensusFact.csv` |
| **Oracle PeopleSoft HCM** | HR system of record: job data, dept & jobcode masters, reason codes | `peoplesoft.PS_JOB.csv`, `peoplesoft.PS_DEPT_TBL.csv`, `peoplesoft.PS_JOBCODE_TBL.csv`, `peoplesoft.PS_ACTION_REASON.csv` |
| **Kronos / UKG** | Timekeeping: monthly worked hours, agency hours, pay-code master | `kronos.TIMECARD_SUMMARY.csv`, `kronos.AGENCY_HOURS.csv`, `kronos.PAYCODE.csv` |
| **Nurse manager's Excel** | Tribal knowledge: closed beds, self-scheduling, mandatory OT, notes | `unit_manager_scheduling_log.xlsx` |

> The whole point of the demo is that **no single system tells the whole story.** Epic shows the
> *clinical context*, PeopleSoft holds *miscoded* termination reasons, Kronos shows the *symptoms*,
> and only the manager's spreadsheet holds the *cause*.

All data is **synthetic**. To regenerate or tweak it, run
[`data/generate_healthcare_data.py`](./data/generate_healthcare_data.py)
(`pip install pandas numpy openpyxl`, then `python generate_healthcare_data.py`). It is
deterministic (fixed seed), so the story numbers are reproducible.

---

## Option A — Load via the UI + a copilot prompt (recommended for the demo)

1. In your Fabric workspace, create (or open) a **Lakehouse** (Lakehouse **schemas** must be
   enabled so we can use `epic` / `peoplesoft` / `kronos`).
2. In the Lakehouse **Files** view, create a folder `staging` and **upload** all seven `.csv`
   files and the `.xlsx` from [`data/`](./data).
3. Create a new **Spark notebook** and attach it to the Lakehouse.
4. Open Copilot Chat in the notebook and use this prompt:

```text
I uploaded 7 CSVs and 1 XLSX to Files/staging in my lakehouse.

Load each CSV as a Delta table using the filename to determine the schema and table name: the part
before the first dot is the SCHEMA (epic, peoplesoft, kronos) and the part after is the TABLE name
(e.g., epic.DepartmentDim.csv -> table DepartmentDim in schema epic). Infer the schema and keep the
column names exactly as in the header.

Do NOT load unit_manager_scheduling_log.xlsx yet — leave it in Files; we'll read it later in the
demo as the nurse manager's "tribal knowledge" spreadsheet.

Then show me 5 rows from each Delta table so I can confirm the load. Show all work in the notebook.
```

> Leaving the Excel file *unloaded* is intentional — pulling it in mid-analysis is a more powerful
> story beat than having it already sitting in the warehouse.

---

## Option B — Load with a notebook cell (deterministic fallback)

If you'd rather not rely on the copilot to load, paste this into the first cell. It creates the
three schemas and loads the seven CSVs; the Excel stays in Files.

```python
from pathlib import PurePosixPath

STAGING = "Files/staging"
csvs = [
    "epic.DepartmentDim", "epic.NursingUnitCensusFact",
    "peoplesoft.PS_JOB", "peoplesoft.PS_DEPT_TBL",
    "peoplesoft.PS_JOBCODE_TBL", "peoplesoft.PS_ACTION_REASON",
    "kronos.TIMECARD_SUMMARY", "kronos.AGENCY_HOURS", "kronos.PAYCODE",
]

for name in csvs:
    schema, table = name.split(".", 1)
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    df = (spark.read.option("header", True).option("inferSchema", True)
          .csv(f"{STAGING}/{name}.csv"))
    df.write.mode("overwrite").saveAsTable(f"{schema}.{table}")
    print(f"loaded {schema}.{table}: {df.count()} rows")

# The nurse manager's Excel stays in Files on purpose — read it live during the demo:
#   import pandas as pd
#   mgr = pd.read_excel(f"/lakehouse/default/{STAGING}/unit_manager_scheduling_log.xlsx",
#                       sheet_name="Scheduling Log")
```

> If your workspace doesn't have Lakehouse schemas enabled, drop the `CREATE SCHEMA` /
> `schema.` prefix and just load flat tables named `epic_DepartmentDim`, etc.

---

## The tables at a glance

**Epic (`epic`)**
- `DepartmentDim` — 9 nursing units across 3 legacy networks (Metro / Valley / Cherry). Carries
  `EpicCostCenter`, `SpecialtyType`, `LicensedBeds`, `MagnetDesignated`.
- `NursingUnitCensusFact` — monthly `PatientDays`, `AvgDailyCensus`, `AcuityIndex`, `TargetHPPD`,
  `RequiredNursingHours`. **The worst-turnover units are NOT the highest acuity** — this kills the
  "sicker patients" hypothesis.

**PeopleSoft (`peoplesoft`)**
- `PS_JOB` — one current row per RN with `DEPTID`, `JOBCODE`, `COMPRATE` (hourly), `FTE`,
  `HIRE_DT`, and for leavers `ACTION='TER'` + `ACTION_REASON` + `TERMINATION_DT`. **Note the worst
  units carry the HIGHEST pay** (base + market adjustment) — this kills the "low pay" hypothesis.
- `PS_ACTION_REASON` — reason-code lookup. `SCH` (Scheduling/Work-Life) exists but is **almost
  never used** even though it's the true driver — the miscoding trap (DQ #1).
- `PS_DEPT_TBL`, `PS_JOBCODE_TBL` — department and jobcode masters. `DEPTID` uses a network prefix
  (`CHR8105`) that differs from Epic's cost center (`8105`) — the join trap (DQ #2).

**Kronos (`kronos`)**
- `TIMECARD_SUMMARY` — monthly per RN: `REG_HRS`, `OT_HRS`, `FLOAT_HRS`, `CALLOFF_HRS`,
  `SHIFTS_WORKED`, `MAX_CONSECUTIVE_SHIFTS`, plus `HOME_LABOR_ACCT` vs `WORKED_LABOR_ACCT`
  (float shows up when they differ). **OT and consecutive shifts spike Apr–Jun on the Cherry
  units** — the symptom.
- `AGENCY_HOURS` — monthly agency hours by labor account with `BILL_RATE` and `VENDOR`. Some Cherry
  hours are booked to `0FLOATPOOL-CHR` instead of the unit, so a naive join **undercounts** the
  worst units (DQ #2, ~$82K hidden).
- `PAYCODE` — pay-code descriptions (REG, OT, FLT, CALL, ORI, AGY).

**Nurse manager's Excel — `unit_manager_scheduling_log.xlsx`** (kept in Files)
- Monthly per unit: `BedsClosed`, `SelfSchedulingEnabled`, `MandatoryOT`, `FloatPolicy`, and
  free-text `Notes`. **This is the smoking gun** — it's the only place that records the renovation,
  the suspended self-scheduling, the mandatory OT, and the exit-interview quotes.
