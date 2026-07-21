# Manufacturing OEE Root-Cause Analysis

### *"The \$500,000 Press That Wasn't the Problem"*

A Vibe Analytics demo for **discrete manufacturing** — specifically **extrusion blow molding
of HDPE engine-oil bottles**. It shows how LLM-assisted analytics helps a plant *reason* its way
past the obvious-but-wrong answer to the real root cause of low **OEE** (Overall Equipment
Effectiveness) — and avoids a half-million-dollar capital mistake.

> **The one-line pitch:** A dashboard told the plant manager which machine to blame. An LLM,
> working across three disconnected systems, told him what was *actually* wrong — and it wasn't
> the machine.

---

## Who this demo is for

- **Primary audience:** plant leadership / operations leaders (outcome- and dollar-focused)
- **Length:** ~15 minutes, single clean twist
- **Manufacturing type:** discrete (injection/blow-molded plastics), but the pattern generalizes
  to any OEE / unplanned-downtime problem

## The business situation (set the stage)

> "Our plant runs four blow molders making HDPE engine-oil bottles. Our OEE has been stuck below
> world-class. The monthly report keeps flagging **press BM-07** as our worst performer, and
> maintenance is convinced it's worn out. There's a **\$500,000 capital request** on my desk to
> replace it. Before I sign it, I want to be sure we're solving the right problem."

## The data (three systems, one story)

No single system has the answer — that's the whole point.

| Layer | Real-world system | Tables |
|---|---|---|
| System of record | **SAP MII** | `production_orders`, `downtime_events`, `material_lots`, `machines` |
| Process historian | **MES / PI / AVEVA** | `process_telemetry` |
| Tribal knowledge | **Process engineer's Excel** | `material_qc_log.xlsx` |

Load it with **[data-loading.md](./data-loading.md)**, then open
**[ManufacturingOEE.ipynb](./ManufacturingOEE.ipynb)**.

---

## The arc of the story (the talk track)

The demo deliberately walks the audience *into* a wrong conclusion, then uses the LLM to climb
back out. This mirrors how real analysis feels — and it's far more memorable than a tidy dashboard.

### Act 1 — The obvious (wrong) answer
1. **OEE by machine** → BM-07 is worst. *"See, it's BM-07."*
2. **Downtime Pareto** → `MACHINE_FAULT` dominates BM-07's downtime. *"The data confirms it —
   the machine is broken. Buy the new press."*

> **The teaching beat:** the "data" is confirming a story we already believed. Downtime reason
> codes are typed in by operators mid-crisis. Trusting them is *automation bias*. This is exactly
> where most analyses stop — and where the \$500K mistake gets made.

### Act 2 — Think a meta-layer higher
3. We refuse to accept the obvious answer and ask the LLM for **five competing hypotheses**
   (CRIT prompt #1 below). Its top pick is usually **"old / worn-out machine."**
4. **Test it:** join OEE to `install_year`. **BM-07 is one of the *newest* machines (2021);
   BM-12 is the oldest (2015) and runs great.** The age hypothesis is dead.

### Act 3 — Bring in the data the dashboard ignored
5. **Process historian:** plot bottle-weight and melt-pressure *variation* over time. A sharp
   **window of instability (Jun 10–18)** erupts — and it hits **BM-07 *and* BM-09 together**.
6. **OEE over time:** those two machines are perfectly healthy *except* in that window. *"A worn
   machine doesn't heal itself. What do BM-07 and BM-09 share that the others don't?"*

### Act 4 — The smoking gun
7. BM-07 and BM-09 are both fed by **regrind blender BL-2**. The historian never recorded regrind
   — it only lives in the **process engineer's spreadsheet**. Bring it in: during that exact
   window, **BL-2 ran regrind at 35–45% vs. a 15% target** (to hit a material-cost target), and
   for several days pulled in a **contaminated black color-changeover purge** (black specks,
   leak-test failures). The engineer even *wrote it down* in the notes column.
8. **Re-segment by blender + window:** the machine effect **vanishes**. Outside the window all
   four machines are identical (~0.88). The entire OEE gap is BL-2 + bad regrind.

### Act 5 — The prescription
9. Quantify the lost bottles and margin; contrast with the **\$500K capex we're about to avoid.**
10. Fix the regrind spec, segregate the purge, and add a proper downtime code + a regrind tag to
    the historian so this is visible next time.

> **The punchline:** *One* root cause — over-blended, contaminated regrind — drove **all three**
> OEE losses at once: Availability (blowouts miscoded as machine faults), Performance (slow
> cycles), and Quality (specks + leaks). A new press would have run the same bad regrind.

---

## The CRIT prompts

### Prompt 1 — Generate competing hypotheses (do NOT accept the obvious)

```text

You are attached to a Microsoft Fabric Spark Notebook with an attached lakehouse.

I have 2 schemas in this lakehouse:  sapmii and aveva.  Each schema has a few tables in it.  

Can you show me which tables exist in those schemas?  I want to run some analytics on them with you.  
Show all of your work in the actual Spark notebook. You have permission to run all cells.


> Context:
Look at my lakehouse. I have 5 tables from a plastics plant that runs extrusion blow molding of
HDPE engine-oil bottles: production_orders, downtime_events, machines, material_lots,
process_telemetry (an MES/PI historian).  OEE by machine shows BM-07 is our worst press, and its downtime Pareto is dominated
by "MACHINE_FAULT". Leadership wants to spend $500K on a new press to replace BM-07. Assume the
data is roughly accurate but VERIFY anything before you rely on it — including whether the
downtime reason codes are trustworthy.

> Role:
You are a manufacturing data scientist with 15 years on the plant floor doing OEE and root-cause
analysis. You are deeply skeptical of "obvious" answers and of hand-entered reason codes. You know
that in blow molding, material and regrind problems frequently masquerade as machine faults.  But you aren't familiar with the data just yet because you are new to this plant and its data quality and processes.  So, consider doing "Exploratory Data Analysis" first.  

> Interview:
I am the plant operations manager. Do NOT tell me to buy the press. Instead, give me FIVE competing
hypotheses for why BM-07's OEE is low, ranked by how testable they are with the data I have. For
each, tell me exactly which table(s) and which query would confirm or REFUTE it. Then ask me any
clarifying questions. We will test them together — I want you to actively try to prove the
"bad machine" story WRONG.

> Task:  
Go!
```

### Prompt 2 — Kill the first hypothesis (asset age)

```text
> Task:
Let's test the "BM-07 is just old / worn out" hypothesis first. Join average OEE per machine to
the install_year in the machines table. If age drove OEE, older machines should be worse. Show me
the result and tell me honestly whether this hypothesis survives. Don't soften it — if the data
refutes it, say so and tell me what to look at next.
```

### Prompt 3 — Follow the symptoms (historian) then find what's shared

```text
> Task:
The age story is dead. Now use process_telemetry to look at process STABILITY over time, not just
downtime. Plot daily bottle-weight variation and melt-pressure variation per machine. If you see a
time window where specific machines destabilize, tell me which machines and which dates — and
importantly, tell me what those machines have in COMMON (check the machines table for anything
shared, like the blender that feeds them). Frame this as: "what shared factor could hit these
machines together during this window?"
```

### Prompt 4 — Crack it with the spreadsheet, then quantify

```text
> Task:
The suspect machines share regrind blender BL-2, and they only degrade during a specific window.
The historian doesn't record regrind %, but the process engineer's material_qc_log (from Excel)
does. Join it in. Show me regrind % vs target by blender over time, plus black-speck counts, leak
failures, and the free-text notes for BL-2 during that window. Then re-segment OEE by blender and
by inside/outside the window to test whether the "bad machine" effect disappears once we account
for regrind. Finally, quantify the good bottles and margin we lost, and contrast that with the
$500K press we were about to buy. Give me a prescriptive recommendation.
```

---

## Key takeaways (say these out loud at the end)

- **The dashboard wasn't wrong — it was incomplete.** OEE-by-machine is a real number; it just
  wasn't the *cause*. Correlation (BM-07 low) is not causation (bad press).
- **No single system had the answer.** SAP MII had miscoded downtime, the historian had symptoms,
  and the *cause* was sitting in a spreadsheet on one engineer's laptop. The LLM is what stitched
  them together.
- **We used the LLM to reason, not to answer.** We forced it to generate competing hypotheses and
  to *disprove* the obvious one — the antidote to confirmation bias and LLM sycophancy.
- **The business outcome is a dollar figure and an avoided \$500K capex** — not a chart. That's
  what makes it land with leadership.

## Reproduce / regenerate

The dataset is deterministic. To rebuild it:

```bash
cd ManufacturingOEE
pip install numpy pandas openpyxl
python generate_data.py
```

The generator prints an "answer key" (OEE inside vs. outside the window) — that's the punchline,
so don't show it to the audience.

## Files

| File | Purpose |
|---|---|
| [`generate_data.py`](./generate_data.py) | Deterministic data generator (the "answer key" is in here) |
| [`data/`](./data) | The six ready-to-load datasets (5 CSV + 1 Excel) |
| [`data-loading.md`](./data-loading.md) | Load the data into a Fabric Lakehouse |
| [`ManufacturingOEE.ipynb`](./ManufacturingOEE.ipynb) | The Spark notebook that walks the arc |
