# Agentic Analytics for Healthcare — "The $4M Bonus That Wasn't the Answer"

A **Vibe Analytics** demo for a **newly-merged health system** (Epic on the clinical side,
Oracle PeopleSoft for HR, Kronos for timekeeping). It shows how LLM-assisted analytics helps
nurse-leadership and finance *reason* past the obvious-but-wrong answer to the real driver of
runaway **travel-agency nurse spend** — and avoids a **$4,000,000** blanket-bonus mistake.

> **The one-line pitch:** A turnover dashboard told the CFO to blame low pay on the Cherry
> campus. An LLM, working across three disconnected systems plus a nurse manager's spreadsheet,
> showed that the *highest-paid* units were churning worst — because the real problem was the
> **schedule**, not the paycheck.

> **Why this scenario:** it mirrors what this customer is living through right now — a large,
> recently-combined multi-network system under real financial pressure, trying to cut labor cost
> without cutting care, while stitching together data from formerly-separate hospitals. See
> [`WHY-THIS-DEMO.md`](./WHY-THIS-DEMO.md) for the public news that shaped it.

---

## The business situation (set the stage)

> "We merged three networks — Metro, Valley, and Cherry — into one system. Travel-agency nurse
> spend is out of control, and our turnover dashboard says the **Cherry campus** is the problem
> and that nurses there are leaving for **money**. There's a **$4,000,000** system-wide RN
> **sign-on and retention bonus** proposal on my desk to fix it. Before I sign it, I want to be
> sure we're solving the right problem. The merger data is messy but our teams tell me the core
> HR and clinical data quality is solid."

## The data (three systems + one spreadsheet, one story)

No single system has the answer — that's the whole point.

| Layer | Real-world system | Schema | Tables |
|---|---|---|---|
| Clinical workload / acuity | **Epic** (Caboodle / Clarity) | `epic` | `DepartmentDim`, `NursingUnitCensusFact` |
| HR system of record | **Oracle PeopleSoft HCM** | `peoplesoft` | `PS_JOB`, `PS_DEPT_TBL`, `PS_JOBCODE_TBL`, `PS_ACTION_REASON` |
| The actual clock | **Kronos / UKG** | `kronos` | `TIMECARD_SUMMARY`, `AGENCY_HOURS`, `PAYCODE` |
| **Tribal knowledge** | A nurse manager's **Excel** | *(file)* | `unit_manager_scheduling_log.xlsx` |

> Epic shows the *clinical context* (were the patients actually sicker? no). PeopleSoft is the
> *official record* (but its termination reason codes are **miscoded**). Kronos is the *real clock*
> (overtime, floating, consecutive shifts — the symptoms). And the **cause** — closed beds,
> suspended self-scheduling, mandatory OT, and the exit-interview quotes — only lives in the
> **nurse manager's spreadsheet**. LLM-assisted analytics is what stitches them together.

See [`data-loading.md`](./data-loading.md) to load everything into a Fabric Lakehouse, and
[`data/`](./data) for the files (all synthetic; regenerate with
[`data/generate_healthcare_data.py`](./data/generate_healthcare_data.py)).

---

## The arc of the story (the talk track)

The demo deliberately walks the audience *into* the wrong conclusion, then uses the LLM to climb
back out — exactly how real analysis feels, and far more memorable than a dashboard.

### Step 1 — The obvious (wrong) answer
1. **Agency spend + turnover by campus** → **Legacy Cherry** is worst; **5 West** leads on both.
2. **Termination reasons (PeopleSoft)** → mostly *"Relocation"* and *"Personal."* *"See — they're
   leaving for life reasons and better pay. Approve the $4M bonus."*

> The "data" is confirming a story we already believed. Termination reason codes are typed in by
> busy HR staff during offboarding. Trusting them is **automation bias**. This is exactly where
> most analyses stop — and where the $4M mistake gets made.

### Step 2 — Think a meta-layer higher
3. We refuse the obvious answer and ask the LLM for **five competing hypotheses** (CRIT prompt #1).
   Its top pick is usually **"pay is below market on the Cherry units."**

### Step 3 — Kill the pay hypothesis
4. **Test it:** join PeopleSoft `COMPRATE` (+ Kronos OT earnings) to turnover by unit. **5 West is
   the *highest-paid* staff-nurse unit in the system (~$57/hr avg) and has the *worst* turnover
   (~57%).** Meanwhile low-paid **3 North (~$45/hr)** has **0%** turnover. The pay story is dead.

### Step 3b — Kill the "sicker patients" hypothesis
5. **Bring in Epic:** are the worst units just higher-acuity / higher-workload? **No.** 5 West runs
   *average* acuity (~1.03), while the high-acuity **Medical ICU (~1.87)** is stable. Workload
   isn't the driver either.

### Step 4 — Follow the symptoms in Kronos
6. Plot **OT %, float hours, and max consecutive shifts** over time by unit. A sharp escalation
   erupts **Apr–Jun on three units — 5 West, Progressive Care, and 4 East** (all Legacy Cherry):
   OT jumps to ~20–26% (vs ~8% on stable units) and consecutive shifts climb to 7–8. *"A pay
   problem doesn't switch on in April. What do these three units share that the others don't?"*

### Step 5 — Data-quality reckoning #1 (the reason codes)
7. Re-examine the terminations that cluster in that window. Their PeopleSoft reasons say
   *Personal / Relocation / Career* — but only **one** exit in the whole system is coded
   *"Scheduling / Work-Life."* Cross-referenced with the schedule spike, the reason codes are
   clearly **miscoded**. *"We were told HR data quality was solid. At the row level it looks
   perfect — but the codes don't mean what we assumed."*

### Step 6 — Data-quality reckoning #2 (the join)
8. Try to total agency hours by unit and the numbers **don't reconcile**. The three legacy networks
   use **different cost-center formats** (Epic `8105`, PeopleSoft `CHR8105`, Kronos `08105-RN`),
   and a chunk of Cherry's agency hours are booked to a shared **`0FLOATPOOL-CHR`** labor account.
   A naive unit-level join **undercounts agency on exactly the worst units** (~760 hidden hours /
   ~$82K). *"Our DQ looked fine record-by-record; the merger broke it at the join."*

### Step 7 — The smoking gun (the manager's Excel)
9. None of the systems explain *why* April. The nurse manager's spreadsheet does: **5 West closed
   6 beds for a renovation, suspended self-scheduling, and went to mandatory OT**; Progressive Care
   and 4 East absorbed the overflow and were floated repeatedly. The free-text notes even quote a
   departing nurse: *"I'm on my 6th shift in a row, I can't do this rotation."* This is the
   **tribal knowledge** no system captured.

### Step 8 — Quantify and prescribe
10. Total agency spend is **~$721K over six months (~$1.44M annualized)**, ~85% of it on those
    three units, driven by a **schedule** failure — not pay, not acuity. A **$4M blanket bonus**
    would pay every RN in the system and **never touch the cause**. The prescriptive move: restore
    self-scheduling, cap consecutive shifts, fix the float policy, and backfill the closed-bed
    plan on three units — recovering the agency premium at a fraction of $4M.

> **One** root cause — a broken schedule on three merged-campus units — drove **all** the
> symptoms at once: agency spend (backfilling gaps), overtime (forced coverage), *and* turnover
> (burnout miscoded as "personal"). A blanket bonus would have run the same broken schedule.

---

## The CRIT prompts

Paste these into GitHub Copilot Chat attached to a Fabric Spark notebook with the lakehouse
attached. Full framework background is in the [top-level README](../README.md).

> **Rehearse offline first:** [`Notebook-with-prompts.ipynb`](./Notebook-with-prompts.ipynb)
> interleaves every prompt below with a **local pandas** version of the analysis the agent
> produces, runnable against [`./data`](./data) with no Fabric connection. It executes end-to-end
> and lands on the decision memo (agency ≈ **\$721K / 6 mo**, ~**100%** on the three Cherry units,
> **\$1.44M** annualized — vs. the \$4M bonus).

### Prompt 0 — Orient and load

```text
You are attached to a Microsoft Fabric Spark Notebook with an attached lakehouse.

I have three schemas in this lakehouse: epic, peoplesoft, and kronos. Each has a few tables from a
newly-merged health system (Epic clinical, Oracle PeopleSoft HR, Kronos timekeeping). I also have a
nurse manager's Excel file, unit_manager_scheduling_log.xlsx, uploaded to Files.

Show me which tables exist in each schema and 5 sample rows from each. I want to run analytics on
them with you. Show all your work in the notebook — you have permission to run all cells.
```

### Prompt 1 — Generate competing hypotheses (do NOT accept the obvious)

```text
> Context:
Look at my lakehouse. Travel-agency nurse spend has exploded. Our turnover dashboard says the
Legacy Cherry campus is worst and that nurses are leaving for pay — PeopleSoft termination reasons
are mostly "Relocation" and "Personal." Leadership wants to spend $4,000,000 on a system-wide RN
sign-on/retention bonus. Assume the data is roughly accurate but VERIFY anything before you rely on
it — INCLUDING whether the termination reason codes and the cross-system cost-center joins are
trustworthy after the merger.

> Role:
You are a nursing-workforce data scientist with 15 years in hospital operations doing labor-cost
and retention root-cause analysis. You are deeply skeptical of "obvious" answers and of hand-entered
HR reason codes. You know that in nursing, SCHEDULE and FLOAT problems frequently masquerade as pay
or "personal" problems. You are new to this system and its post-merger data quality, so start with
Exploratory Data Analysis.

> Interview:
I am the CNO working with the CFO. Do NOT tell me to approve the bonus. Give me FIVE competing
hypotheses for why agency spend and turnover are high, ranked by how testable they are with the data
I have. For each, name the exact table(s) and the query that would CONFIRM or REFUTE it. Then ask me
clarifying questions. We will test them together — actively try to prove the "low pay" story WRONG.

> Task:
Go!
```

### Prompt 2 — Kill the pay hypothesis

```text
> Task:
Test the "they leave because pay is below market" hypothesis first. Join PeopleSoft COMPRATE (and
add Kronos overtime earnings for effective pay) to RN turnover rate by unit. If pay drove turnover,
the lowest-paid units should be worst. Show me the ranking and tell me honestly whether this
hypothesis survives. Don't soften it — if the highest-paid units are churning worst, say so, and
tell me what to look at next.
```

### Prompt 3 — Kill the acuity hypothesis, then follow the symptoms

```text
> Task:
The pay story is weak. Now rule out "the worst units just have sicker, heavier patients." Use
epic.NursingUnitCensusFact (AcuityIndex, RequiredNursingHours, PatientDays) to compare the
high-turnover units to the stable ones. Then, regardless of that result, use kronos.TIMECARD_SUMMARY
to plot OT %, float hours, and max consecutive shifts over time by unit. If specific units destabilize
in a specific window, tell me which units and which months — and what those units have in COMMON.
```

### Prompt 4 — Interrogate the data quality (both traps)

```text
> Task:
Two data-quality checks before we trust any of this.
(1) The terminations clustering in that window — what ACTION_REASON did PeopleSoft record? Compare
that to the schedule stress you just found. Is "Scheduling/Work-Life" ever used? Tell me whether you
believe the reason codes.
(2) Total agency hours by unit from kronos.AGENCY_HOURS and reconcile them to the units. The three
legacy networks use different cost-center formats, and watch for any shared/float-pool labor account
that isn't a real unit. Tell me if a naive join UNDER-counts agency on the worst units, and by how
much.
```

### Prompt 5 — Crack it with the spreadsheet, then quantify

```text
> Task:
The suspect units share a Q2 escalation in float, OT, and consecutive shifts, but no system explains
WHY April. Load the nurse manager's unit_manager_scheduling_log.xlsx and bring in BedsClosed,
SelfSchedulingEnabled, MandatoryOT, FloatPolicy, and the free-text Notes for those units and months.
Then quantify total agency spend (hours x bill rate, including the float-pool hours you recovered),
show how concentrated it is on the three units, and contrast that with the $4,000,000 blanket bonus.
Give me a prescriptive recommendation with an estimated dollar impact.
```

---

## What the audience should walk away with

- **Dashboards encode the builder's assumptions.** This one blamed pay and geography; the truth was
  schedule design — and the dashboard literally *undercounted* the worst units because of a
  post-merger join defect.
- **"Good data quality" is a claim to test, not accept.** Row-level validity ≠ analytical
  correctness. Miscoded reason codes and cost-center drift both looked clean.
- **The deliverable is a decision and a dollar figure**, not a chart: don't spend $4M; fix the
  schedule on three units.
- **This is a replacement for the dashboard, not a companion to it** — which is exactly where the
  Fabric App vision goes next. See [`fabric-app-ux.md`](./fabric-app-ux.md).
