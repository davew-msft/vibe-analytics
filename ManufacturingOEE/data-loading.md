# Loading the Manufacturing OEE Data into Fabric

This demo ships with a small, self-contained dataset (about 4,000 rows total)
that represents three systems you'd find in a real plastics plant:

| Source system (real world) | What it is | Files in [`data/`](./data) |
|---|---|---|
| **SAP MII** (manufacturing execution / system of record) | Production orders, downtime events, material lots, asset master | `production_orders.csv`, `downtime_events.csv`, `material_lots.csv`, `machines.csv` |
| **MES / process historian** (PI / AVEVA style) | High-frequency machine sensor tags | `process_telemetry.csv` |
| **Process engineer's Excel** | Hand-assembled regrind blend log that lives on someone's laptop | `material_qc_log.xlsx` |

> The whole point of the demo is that **no single system tells the whole story.**
> The historian shows *symptoms*, the SAP MII downtime codes are *miscoded*, and
> only the process engineer's spreadsheet holds the *cause*. LLM-assisted
> analytics is what stitches them together.



## Load into a Fabric Lakehouse

1. In your Fabric workspace, create (or open) a **Lakehouse**.
2. In the Lakehouse **Files** view, create a folder `oee` and **upload** all six
   files from [`data/`](./data) (the five `.csv` files).
3. Open a new **Spark notebook** and attach it to the Lakehouse.
4. Open a copilot prompt and load the data with the following prompt:  

```text

I uploaded 5 CSVs to `Files/oee` in my lakehouse. Load each CSV as a Delta table using the filename as the table name (sapmii and aveva should be the schema to load the tables to (this is the first part of the filename)) and inferring schema. 

Then, show me 5 rows from each table just so I can see the data and ensure it was loaded correctly.  

```

## The tables at a glance

- `machines` 
  - 4 blow molders. 
  - `blender_id` maps each press to its regrind blender (BL-1 or **BL-2**)
  - `install_year`: BM-07 is one of the *newest*
  machines, and BM-12 is the oldest — this matters later.
- `production_orders` 
  - one order per machine/shift/day (240 rows). 
  - Contains
  **raw counts only** (`planned_minutes`, `downtime_minutes`, `run_minutes`,
  `ideal_units_per_min`, `total_units`, `good_units`, `scrap_units`). 
  - You compute
  OEE from these — nothing is pre-chewed.
- `downtime_events` 
  - 900+ stoppages with `reason_code`. These codes are
  **deliberately miscoded**: regrind-driven blowouts get logged as
  `MACHINE_FAULT`.
- `process_telemetry` 
  - hourly historian tags: melt pressure & its std,
  bottle weight & its std, wall thickness, cycle time, etc.
- `material_qc_log`** (Excel) — daily regrind blend per blender:
  `regrind_pct_target` vs `regrind_pct_actual`, `regrind_source`,
  `blackspeck_count_per_kg`, `leak_fail_count`, and free-text `notes`. **This is
  the smoking gun.**

