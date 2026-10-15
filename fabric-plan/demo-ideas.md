# More Vibe Analytics demo ideas for Fabric IQ Plan

The built-out demo in this folder is **#2, the CPG revenue forecast**
([README.md](./README.md)). Here are four more that use the same Vibe Analytics arc - *walk the
audience into the obvious-but-wrong plan, then climb out with the LLM* - each leaning on a different
Plan component. They're outlines, not built assets.

Every idea follows the same recipe:

1. **Synthetic financial data** -> Fabric Lakehouse -> Power BI semantic model (per
   [data-loading.md](./data-loading.md)).
2. A **planning sheet** for the obvious plan, a **cube / scenarios** for the correction, an
   **intelligence sheet** for the variance story, and **writeback** to the Plan SQL DB.
3. A **companion notebook** with generic **CRIT** prompts that reasons over the committed plan and
   quantifies the decision in dollars.


## 1. "The \$2M Budget Cut That Backfired" (SaaS / Tech)

- **Persona:** CFO of a ~\$120M ARR SaaS company facing a margin mandate.
- **Obvious (wrong):** apply a uniform **10% opex cut across every department**. The spreadsheet
  says it hits the EBITDA target.
- **The reasoning:** the flat cut treats a dollar of Sales & Marketing the same as a dollar of G&A.
  A driver-based view (cost per pipeline dollar, magic number, CAC payback) shows the cut lands
  hardest on the **highest-ROI growth motion**, trading \$2M of cost for far more in bookings.
- **Smoking gun:** a cohort/retention table (tribal, outside the semantic model) shows the cut
  region is where net revenue retention is climbing - exactly where *not* to cut.
- **Plan components:** planning sheet (opex budget by department) - **scenarios**
  (`Flat 10%`, `ROI-Weighted`, `Protect-Growth`) - **intelligence** sheet (EBITDA bridge + ROI
  scatter). Cube optional.
- **Best for:** audiences who live in scenario comparison and what-if.


## 2. "The Revenue Forecast Everyone Believed" (CPG) - **BUILT**

The reference implementation in this folder. Driver-based cube exposes mix blindness; a distributor
contract exposes base-period bias. See [README.md](./README.md).


## 3. "The Headcount Plan That Didn't Add Up" (Professional Services)

- **Persona:** COO of a services firm planning next year's hiring.
- **Obvious (wrong):** the plan adds **40 billable heads** and books the revenue as
  `heads x standard bill rate x 2,080 hours`. Looks highly profitable.
- **The reasoning:** the plan ignores **ramp time and realized utilization**. New hires bill ~40%
  in their first two quarters, and blended utilization is ~72%, not 100%. Modeled properly, the
  plan is cash-negative for three quarters before it turns.
- **Smoking gun:** a **PowerTable** of open positions with start-date assumptions and a ramp curve -
  reference data that should govern the plan but usually lives in a recruiter's spreadsheet.
- **Plan components:** **PowerTable sheet** (positions, ramp curves, bill rates as governed master
  data + approval workflow) -> planning sheet (revenue & cost by practice/month) -> **intelligence**
  sheet (utilization waterfall, cash-flow-to-profitability timeline, Gantt of hire starts).
- **Best for:** showing PowerTable as governed reference data feeding a plan; strongest PowerTable
  fit.


## 4. "The Margin Mirage" (Retail / Manufacturing)

- **Persona:** VP Finance signing off a gross-margin budget.
- **Obvious (wrong):** budget a **flat 42% gross margin** because "that's our blended rate." Total
  margin dollars clear the target.
- **The reasoning:** the blended rate hides a **mix shift** - fast-growing volume is in the
  *lowest*-margin products/regions. A **cube** that plans margin by both **GL account** and
  **product line** (two unrelated dimensions) reveals blended margin drifting to ~38% as the mix
  shifts, missing the profit target even as revenue grows.
- **Smoking gun:** a supplier price-increase memo (tribal) confirms COGS is rising on exactly the
  growing SKUs.
- **Plan components:** planning **cube** (driver-based allocation across GL x product - the cube's
  home-turf use case) -> **scenarios** (`Blended 42%`, `Mix-Aware`) -> **intelligence** sheet
  (margin bridge, marimekko of margin by mix). 
- **Best for:** showcasing multidimensional cube allocation across unrelated dimensions; strongest
  cube fit.


## 5. "The Rolling Reforecast" (any industry)

- **Persona:** FP&A lead running the Q3 reforecast.
- **Obvious (wrong):** actuals are \$4M behind plan; the dashboard attributes the gap to **price**,
  so the reforecast cuts price assumptions.
- **The reasoning:** decompose the variance (price x volume x mix x timing). The real driver is
  **timing/phasing** - a big deal slipped a quarter, not a price problem. Cutting price would have
  destroyed margin to fix a gap that self-corrects next quarter.
- **Smoking gun:** the CRM close-date history (tribal) shows the deal moved, not shrank.
- **Plan components:** planning sheet with a **reforecast row model** and **closing forecast
  period** -> **scenarios** (`Price-Cut`, `Timing-Adjusted`) -> **intelligence** sheet (price/volume/
  mix variance bridge).
- **Best for:** teams that live in monthly/quarterly reforecast cycles and variance decomposition.


## Choosing among them

| If the audience cares most about... | Build |
|---|---|
| Scenario what-if and cost trade-offs | #1 SaaS budget cut |
| Forecasting, mix, and driver-based planning | **#2 CPG (built)** |
| Governed reference/master data feeding a plan | #3 Headcount (PowerTable) |
| Multidimensional allocation across unrelated dims | #4 Margin (cube) |
| Reforecast and variance decomposition | #5 Rolling reforecast |
