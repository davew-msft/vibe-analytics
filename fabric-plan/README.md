# The Revenue Forecast Everyone Believed

A **Vibe Analytics** demo built on **Microsoft Fabric IQ Plan** — for a mid-size CPG
beverage company. It shows how LLM-assisted reasoning helps a finance team *reason* past the
obvious-but-wrong annual plan (uniform "+8% across the board") to the number the business can
actually hit — and avoids budgeting **millions of dollars of revenue that already walked out the
door.**

> **The one-line pitch:** A top-down spreadsheet said "+8% everywhere and we hit our target."
> An LLM, reasoning across the plan's own writeback data and a distributor contract nobody told
> Finance about, showed that ~$3.5M of that plan is revenue that no longer exists — and another
> ~$7M is over-planned on the cola line that's in structural decline.

This demo is the Plan-flavored sibling of [ManufacturingOEE](../ManufacturingOEE/README.md). Same
Vibe Analytics arc — *walk into the wrong conclusion, then climb out with the LLM* — but the tool
is an Enterprise Performance Management (EPM) planning app, not a Spark notebook.

- [How to set up the data](./data-loading.md)
- [How to build the plan in Fabric (planning + intelligence + PowerTable sheets)](./setup-plan.md)
- [The companion notebook with all the CRIT prompts inline](./Notebook-companion.ipynb)
- [Four more demo ideas](./demo-ideas.md)


## The business situation (set the stage)

> "We're **Cascadia Beverages** — about **\$153M** in net revenue last year across five regions and
> five channels. It's annual planning season. Our VP of Sales walked into the room with a clean,
> confident number: **grow every product line 8% next year.** The math checks out — total revenue
> goes to **~\$165M**, which clears the board's target. Everyone nodded. Before we lock the budget
> and set trade-promo spend behind it, I want to be sure we're planning the right number."


## The four systems (one story)

No single artifact tells the whole story — that's the whole point.

| Layer | Real-world system | What it holds |
|---|---|---|
| Trusted analytics | **Fabric semantic model** | `sales_actuals` fact + `dim_product` / `dim_region` / `dim_channel` / `dim_date` |
| The plan itself | **Fabric IQ Plan** — planning sheet, cube, scenarios | The +8% base plan and the driver-based alternative |
| Plan storage | **Plan writeback SQL database** | Committed scenarios (auto-created with the Plan item) |
| Tribal knowledge | **A distributor contract in someone's Excel** | `distributor_contracts.xlsx` — the smoking gun, *not* in the semantic model |


## The arc of the story (the talk track)

The demo deliberately walks the audience *into* the wrong plan, then uses the LLM to climb back
out. This mirrors how real planning feels — and it's far more memorable than a variance grid.

### Step 1 — The obvious (wrong) plan
1. Build the plan the "normal" way: take FY2025 actuals and grow **every SKU / region / channel by
   a uniform +8%**. The total lands at **~\$165M** and clears the target. *"See — we hit the
   number."*
2. Trade-promo spend is set as a percentage of planned revenue, so the biggest lines get the
   biggest promo budgets. *"The data supports it — fund the plan."*

> This is **anchoring + automation bias**. A uniform growth rate feels objective, but it encodes a
> hidden assumption: that every product and region grows for the *same reason at the same rate*.
> Nothing in the business works that way. This is exactly where most annual plans stop — and where
> the money gets misallocated.

### Step 2 — Think a meta-layer higher
3. Instead of accepting +8%, we ask the LLM for **five competing reasons the uniform plan is
   wrong**, ranked by how testable they are with the data we have (CRIT prompt #1). We explicitly
   tell it to try to prove the "+8% everywhere" story *wrong*.

### Step 3 — Let the driver expose the mix
4. **Kill the uniform assumption with a driver.** In Plan, a **cube** allocates growth using a
   *driver measure* (here, category trajectory / prior-year run-rate) instead of a flat percentage.
   Re-plan the same total through the driver and the composition breaks apart:
   - **Cola / CSD** is in **structural decline (~ −6%/yr)** but the uniform plan grows it +8% — an
     over-plan of roughly **\$7M** on a shrinking line.
   - **Sparkling Water** is growing **~ +20%/yr** but the uniform plan only gave it +8% — leaving
     roughly **\$3M** of realistic upside on the table.
5. *"A flat percentage can hit the right total for entirely the wrong reasons. What is each line
   actually going to do?"*

### Step 4 — The smoking gun
6. One region refuses to behave. Plot **Midwest × Club** revenue by month and there's a **cliff in
   September**: ~\$977K in August collapses to ~\$516K and stays there. A growing business doesn't
   fall off a ledge in one month.
7. The reason isn't in the semantic model. It's in a **distributor contract** on a sales manager's
   laptop: **MegaMart Wholesale terminated effective 2025-09-01.** It carried ~\$400K/month —
   **~\$3.2M is already baked into the FY2025 base** (Jan–Aug), and its **\$3.6M annualized run-rate
   is gone.** The uniform plan grows that dead revenue by 8%, **budgeting ~\$3.5M in FY2026 that
   cannot possibly recur.**
8. **Re-plan with both corrections** — driver-based mix *and* a base cleaned of the MegaMart phantom.
   Commit it as a scenario, write it back, and compare: the "+8% everywhere" plan is overstated by
   millions and points trade-promo dollars at the declining cola line instead of the sparkling-water
   line that's actually growing.

> **One clean plan** replaces two hidden errors at once: a **base-period bias** (dead distributor
> revenue carried forward) and **mix blindness** (a flat rate over a business with wildly different
> category trajectories). The +8% plan wasn't conservative or aggressive — it was simply *wrong in
> both directions at the same time.*


## Where each Plan component shows up

| Plan component | Role in this demo |
|---|---|
| **Planning sheet** | The FY2026 revenue plan by Product × Region × Channel × Month |
| **Planning cube** | Driver-based allocation — the mechanism that exposes the mix error |
| **Scenarios** | `Base (+8% uniform)`, `Driver-Based`, `Distributor-Adjusted`; Compare + variance |
| **Intelligence sheet** | Variance report (Plan vs Driver vs Prior-Year), waterfall & marimekko, IBCS formatting |
| **PowerTable sheet** *(optional)* | Governed reference data: SKU lifecycle + distributor contracts; region SCD |
| **Writeback SQL DB** | Where committed scenarios land — the companion notebook reads it and the LLM reasons over it |


## The CRIT prompts

These use the [CRIT framework](https://sgd.com.au/upgrade-your-ai-prompts-with-the-crit-framework/)
(**C**ontext, **R**ole, **I**nterview, **T**ask) and are written to be **generic** — they run in
this VS Code chat against the companion notebook, or against any assistant attached to the plan
data. The full set with runnable cells is in
[Notebook-companion.ipynb](./Notebook-companion.ipynb).

### Prompt 1 — Generate competing hypotheses (do NOT accept +8%)

```text
> Context:
I work in FP&A at Cascadia Beverages, a ~$153M CPG beverage company. For our FY2026 annual plan,
Sales proposes growing every SKU, region, and channel by a uniform +8%. That total (~$165M) clears
the board target, so there is pressure to just approve it. I have our FY2025 monthly actuals in a
table called sales_actuals (NetRevenue, COGS, GrossMargin, TradeSpend, UnitsSold) with product,
region, channel, and date dimensions. Assume the actuals are roughly accurate but VERIFY anything
before relying on it.

> Role:
You are a CPG financial planning analyst with 15 years of enterprise planning experience. You are
deeply skeptical of flat, top-down growth rates. You know a uniform percentage hides mix shifts,
dying products, and one-time revenue that will not recur. You are new to Cascadia's data, so start
with exploratory data analysis before you trust anything.

> Interview:
I am the FP&A lead. Do NOT tell me to approve the +8% plan. Instead, give me FIVE competing reasons
the uniform +8% plan is likely wrong, ranked by how testable they are with the data I have. For
each, tell me exactly which columns/dimensions and which query would confirm or REFUTE it. Then ask
me clarifying questions. I want you to actively try to prove the "+8% everywhere" story WRONG.

> Task:
Go.
```

### Prompt 2 — Kill the flat-rate assumption with the mix

```text
> Task:
Let's test the "one growth rate fits all" assumption first. Aggregate FY2025 NetRevenue by Category
and compute each category's within-year trajectory (compare the first quarter to the last quarter,
annualized). If a flat +8% were reasonable, every category would be trending similarly. Show me the
categories side by side, tell me honestly which ones a +8% plan OVER-plans and which it UNDER-plans,
and quantify the dollar error per category if we grow each at its own trajectory instead of +8%.
Don't soften it.
```

### Prompt 3 — Follow the one region that won't behave

```text
> Task:
The mix story holds, but I want to check regions too. Plot FY2025 NetRevenue by month for each
Region, and separately for Region x Channel. If any series has a sudden step-change (not a smooth
trend), isolate exactly which Region and Channel and which month it breaks. Then tell me: what could
make a single Region x Channel fall off a cliff in one month while everything else keeps trending?
Frame it as a hypothesis I can go verify outside this dataset.
```

### Prompt 4 — Bring in the contract, then re-plan and quantify

```text
> Task:
The Midwest x Club channel collapses in September. The cause isn't in the semantic model — it's in
distributor_contracts.xlsx: MegaMart Wholesale terminated effective 2025-09-01, ~$400K/month, and
~$3.2M of its revenue is already in the FY2025 base (Jan-Aug). Load that file. Then build TWO
corrected FY2026 plans and compare all three:
  (a) Base: uniform +8% on FY2025 actuals
  (b) Driver-Based: each category grown at its own trajectory
  (c) Distributor-Adjusted: driver-based, PLUS remove the MegaMart phantom base before growing
For each, give me total NetRevenue and the delta vs Base. Quantify: how much of the +8% plan is
revenue that cannot recur, how much is over-planned on the declining cola line, and how the
trade-promo dollars should move. Finish with a prescriptive recommendation I can take to the board.
```


## The payoff (what the numbers say)

Running the demo end to end produces roughly:

| Plan | FY2026 Net Revenue | vs +8% Base | Why |
|---|---|---|---|
| **Base — uniform +8%** | ~\$165.5M | — | Flat growth on last year's actuals |
| **Driver-Based** | ~\$159.0M | **−\$6.5M** | Corrects the mix: cola declines, sparkling grows |
| **Distributor-Adjusted** | ~\$155.9M | **−\$9.6M** | Also removes ~\$3.5M of dead MegaMart revenue |

The recommendation isn't "the plan is too high." It's *"the plan is wrong in a way that would have
mis-pointed our trade-promo budget."* The +8% plan funds a declining cola line and under-funds the
sparkling-water line that's actually growing. **The corrected plan reallocates spend to where the
driver says the growth really is.**

> Numbers are approximate and regenerate deterministically from
> [generate_plan_data.py](./generate_plan_data.py) (seed `20260819`).
