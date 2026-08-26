# Loading the Cascadia Beverages data into Fabric

Fabric IQ Plan connects to a **Power BI semantic model**, so the job here is: land the synthetic
CPG data in a Lakehouse, then build a small star-schema semantic model with the DAX measures the
plan (and the driver-based cube) will use.

This demo ships a small, self-contained dataset (~4,200 fact rows) that represents the systems a
mid-size beverage company would have:

| Source (real world) | What it is | Files in [`data/`](./data) |
|---|---|---|
| **Sales / ERP actuals** | FY2025 monthly net revenue, COGS, margin, trade spend, units | `cascadia.sales_actuals.csv` |
| **Product / region / channel master** | Dimensions incl. lifecycle status and distributor status | `cascadia.dim_product.csv`, `cascadia.dim_region.csv`, `cascadia.dim_channel.csv`, `cascadia.dim_date.csv` |
| **A distributor contract in someone's Excel** | The termination nobody told Finance about | `distributor_contracts.xlsx` |

> The whole point of the demo is that **the semantic model looks complete but isn't.** The
> distributor termination that breaks the plan lives only in the Excel file — the LLM is what
> stitches it back in.




## Step 1 — Land the data in a Lakehouse

1. In your Fabric workspace, create a **Lakehouse** 
2. In the Lakehouse **Files** view, create a folder `plan` and **upload** the files
   from [`data/`](./data). 
3. Open a new **Spark notebook**, attach it to the Lakehouse, and load each CSV as a Delta table.
   You can drive this with a copilot prompt:

   ```text
   I uploaded 5 CSVs to Files/plan in my lakehouse. Load each one as a Delta table, using the part
   of the filename after "cascadia." as the table name (so cascadia.sales_actuals.csv becomes the
   table sales_actuals, etc.). Infer the schema, and cast DateKey to a date. Then show me 5 rows
   from each table so I can confirm it loaded correctly.
   ```

You should end up with five tables: `sales_actuals`, `dim_product`, `dim_region`, `dim_channel`,
`dim_date`.


## Step 2 — Build the semantic model

1. From the Lakehouse, choose **New semantic model** and include all five tables.
2. Create relationships (single-direction, one-to-many from each dimension to the fact)
3. Mark `dim_date` as the date table on `DateKey`.

> This is currently janky (may be fixed by the time you read this): **Connection mode.** Plan supports **Import** mode fully; **Direct Lake** and **DirectQuery** are
> supported with limitations (they require a gateway with fixed credentials and don't support SSO).
> **Import** is the least-friction choice but it won't work unless I install full blown PBI desktop.  Nothin doin.  So, here's the workaround:  

4. In your Fabric workspace:

Semantic model → ... → Settings

Then find:

Gateway and cloud connections.  It will likely say `Default: SSO`.  Change that and walk through building the connection.  Then ensure you change from the default to the new connection.  **Note the NAME of the connection**.  Make sure `Use SSO` is not selected.  




## Step 3 — Add the DAX measures

Plan reads measures from the semantic model — including the **driver measure** the cube uses to
allocate. Add these:

```dax
mNet Revenue = SUM ( sales_actuals[NetRevenue] )

mCOGS = SUM ( sales_actuals[COGS] )

mGross Margin = SUM ( sales_actuals[GrossMargin] )

mGross Margin % = DIVIDE ( [mGross Margin], [mNet Revenue] )

mTrade Spend = SUM ( sales_actuals[TradeSpend] )

mUnits Sold = SUM ( sales_actuals[UnitsSold] )
```

Add a **prior-year run-rate** measure to use as the cube's allocation driver. Because the sample
data is a single fiscal year, use the **last-quarter annualized** run-rate — this is what makes the
driver "see" the mix shift and the distributor cliff instead of the flat full-year average:

```dax
Exit Run-Rate (Annualized) =
VAR LastMonth = MAX ( dim_date[Month] )
VAR Window =
    FILTER ( ALL ( dim_date ), dim_date[Month] > LastMonth - 3 && dim_date[Month] <= LastMonth )
RETURN
    CALCULATE ( [mNet Revenue], Window ) * 4
```

> Using **Exit Run-Rate** (not full-year Net Revenue) as the allocation driver is deliberate: the naive plan anchors on the full-year average, which still contains the dead MegaMart
> revenue; the run-rate driver already reflects that it's gone.


Refresh the semantic model, just to be sure.  

## The tables at a glance

- **`sales_actuals`** — FY2025 monthly fact, one row per Date × Product × Region × Channel.
  Contains raw financial measures only (`NetRevenue`, `COGS`, `GrossMargin`, `TradeSpend`,
  `UnitsSold`) — nothing is pre-aggregated into a plan.
- **`dim_product`** — Category → Brand → SKU, plus **`LifecycleStatus`** (Growth / Mature /
  Declining) and `TargetGrossMarginPct`. The lifecycle column is the honest signal the uniform plan
  ignores.
- **`dim_region`** — Region → City, plus **`DistributorStatus`** — note Midwest already reads
  "Lost distributor 2025-09-01" if anyone bothers to look.
- **`dim_channel`** — five channels; `Club` is where MegaMart lived.
- **`dim_date`** — FY2025 monthly, with `Quarter` and `Half` for the H1/H2 cliff analysis.
- **`distributor_contracts.xlsx`** *(kept out of the model)* — `Contracts` sheet has the MegaMart
  termination, monthly revenue, annualized run-rate, and a free-text note; `SKU_Lifecycle` sheet has
  planner notes. **This is the smoking gun.**

Next: [build the plan in Fabric](./setup-plan.md).
