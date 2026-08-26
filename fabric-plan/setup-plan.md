# Building the plan in Fabric IQ Plan

What are we doing?  

* a **planning sheet** for the FY2026 revenue plan (Planning Sheets do the budget/forecast/scenario)
* a **cube** for driver-based allocation
* **scenarios** for the three plan versions
* an **intelligence sheet** for the variance story (these do no-code reporting in Plan)
* a **PowerTable sheet** for governed reference data.
* **Infobridge** (cross-sheet/system integration - we don't use this).

Prerequisite: you've completed [data-loading.md](./data-loading.md) and have a semantic model with the `mNet Revenue` and `Exit Run-Rate (Annualized)` measures.

## Step 1 — Create the semantic model connection

Plan reaches a semantic model through a **shared cloud connection** (a workspace admin/member
creates it once; others reuse it).

1. On the Fabric toolbar, select **Settings ⚙ → Manage connections and gateways → New**.
2. Choose **Cloud**, name it something memorable, set **Connection type = Power BI Semantic Model**.
3. Pick an **Authentication method** (use a ServicePrincipal if you want CI/CD reuse).
4. Select **Create**. Optionally **Manage users → Share**.

> Import-mode models connect with no extra requirements. Direct Lake / DirectQuery need a gateway
> with fixed credentials (no SSO).  For now.  


## Step 2 — Create the Plan item

1. In your workspace, select **New item → Plan**.
2. Name it and select **Create**.

> Creating the Plan item automatically provisions a **Fabric SQL database** in the workspace. This
> database stores the plan's metadata and is where scenario **writeback** lands.


## Step 3 — Create the planning sheet (the +8% base plan)

1. In the Plan item, choose to start from a **semantic model** and select **Planning**. Name the
   sheet `FY2026 Revenue Plan`.
2. Select **Add → Select a Connection → <your connection>**, pick your semantic model,
   and **Add**.
3. Lay the sheet out:
   - **Rows:** `dim_product[Category]` → `dim_product[SKU]` (drag Category above SKU to nest).
   - **Columns:** `dim_date[Year]` and `dim_date[Month]`.
   - **Filters/pages:** `dim_region[Region]`, `dim_channel[Channel]`.
   - **Values:** the `mNet Revenue` measure.
4. Now we want a flat "8% increase" forecast for all categories
   - Click **Forecast**
   - Call it `Plan Net Revenue`
   - Formula:  `Net Revenue * 1.08`
4. (skip)Add a **forecast/data-input row model** for FY2026. Create a planning measure `Plan Net Revenue`
   and seed it from FY2025 actuals grown by a flat rate:
   - Use an **insert formula row** (or a data-input series) with `Plan Net Revenue = Net Revenue *
     1.08`.
   - Use **Distribution → Copy to all rows** to apply the +8% uniformly across every SKU/region/
     channel.

This is the **obvious-but-wrong** plan. Confirm the grand total lands around **\$165M**.


## Step 4 — Add the cube for driver-based allocation

A **cube** allocates a value entered at a high level down across dimensions using a **driver
measure**, instead of a flat percentage. This is the mechanism that exposes the mix error.

1. In the planning sheet, open **Model → Cube** and create a cube on `Plan Net Revenue`.
2. Set the **allocation driver** to the **`Exit Run-Rate (Annualized)`** measure. (Allocation =
   `Entered Value × (driver at intersection ÷ Σ driver in scope)`.)
3. Configure the cube breakdown across `Category → SKU`, `Region`, and `Channel`.
4. Enter the **board target total** (~\$165M) at the top level and let the cube allocate it.

Because the run-rate driver already reflects that cola is shrinking and MegaMart is gone, the cube
distributes the same total very differently from the flat +8% — cola gets less, sparkling water
gets more. Contrast this sheet with Step 3 to make the mix point on screen.

> See the concept docs for cube allocation math and driver selection:
> *planning-concept-cube* and *planning-how-to-input-data*.


## Step 5 — Create the three scenarios

Scenarios let you hold multiple plan versions in one sheet without disturbing the base.

1. **Base** is the committed reference (the +8% uniform plan from Step 3).
2. Go to **Model → Scenario → New**. Create **`Driver-Based`**; include the `Plan Net Revenue`
   series. Use the cube (Step 4) to populate it.
3. Create **`Distributor-Adjusted`**: start from `Driver-Based`, then **reduce the Midwest × Club
   base** to remove the MegaMart phantom before growth. Use **Bulk Edit** on Midwest × Club (or the
   value slider) to strip the ~\$3.2M dead base, then let the driver grow what remains.
4. Use **Compare Scenario** (`Compare` = Base, `With` = Distributor-Adjusted, `Measures` = Net
   Revenue) to show the delta grid — positive/negative variance by Category and time period.

Expected totals: Base ~\$165.5M, Driver-Based ~\$159.0M, Distributor-Adjusted ~\$155.5M.


## Step 6 — (Optional) PowerTable sheet for governed reference data

PowerTable turns database/semantic-model tables into a no-code, governed **table app** — the right
home for the reference data that *should* have informed the plan.

1. Add a **PowerTable** sheet named `Reference Data`.
2. **SKU lifecycle:** create a table app from `dim_product` (or import the `SKU_Lifecycle` sheet of
   `distributor_contracts.xlsx`). Editors maintain `LifecycleStatus` and planner notes here, with
   approval workflow and audit history.
3. **Distributor contracts:** import the `Contracts` sheet. This is the artifact that, had it been
   governed reference data instead of a laptop spreadsheet, would have caught the MegaMart phantom
   before the plan was drafted.
4. **Region SCD (Type II):** model `dim_region[DistributorStatus]` as a **slowly changing
   dimension** so "Midwest lost its distributor on 2025-09-01" is a tracked, dated change rather
   than tribal knowledge. (Matches the `region_dimension_pt.xlsx` SCD pattern in fabric-samples.)

> The teaching point: the smoking gun only lived in Excel. PowerTable is how you *prevent the next
> one* by governing this reference data inside Fabric.


## Step 7 — Create the intelligence sheet (the variance story)

Intelligence sheets are the no-code reporting layer — IBCS-formatted tables, 100+ charts, and
real-time links to the planning sheet.

1. Add an **Intelligence** sheet named `FY2026 Plan Review`.
2. Connect it to the planning sheet so it reads Base / Driver-Based / Distributor-Adjusted live.
3. Build the three views that carry the talk track:
   - **Variance table** — Category rows; columns for `Prior-Year Net Revenue`, `Base (+8%)`,
     `Driver-Based`, `Distributor-Adjusted`, and the Δ. Apply **IBCS** variance formatting (green
     up / red down).
   - **Waterfall chart** — bridge from Base to Distributor-Adjusted showing the two corrections:
     the mix adjustment (~−\$6.5M) and the distributor removal (~−\$3.5M).
   - **Marimekko** (or column) — Net Revenue by Category × Region so the audience *sees* cola
     shrinking while sparkling water grows.
4. Add a **note/annotation** on the Midwest × Club cliff pointing at the MegaMart termination.
5. **Export** to PDF/PNG for the board pack.


## Step 8 — Enable writeback (so the notebook can reason over it)

1. Configure the planning sheet's **writeback destination** (the Plan SQL database created in
   Step 2). See *planning-how-to-write-back-data*.
2. On the **Scenario** toolbar, select **Writeback → Writeback All** to persist the three
   committed scenarios.
3. Check **Scenario → Logs** to confirm the writeback completed.

Now the three scenarios live in the Plan SQL database. Continue to
[Notebook-companion.ipynb](./Notebook-companion.ipynb), where the LLM reasons over that committed
plan data and quantifies the recommendation.

> **No Plan-enabled capacity yet?** The companion notebook also runs fully **offline** against the
> CSVs in [`data/`](./data), reproducing the same three plan totals and the dollar figures — so you
> can rehearse the entire talk track before you build anything in Fabric.
