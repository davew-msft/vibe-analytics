# Next steps — pick this up in a new chat

> When you return, open this folder and tell Copilot: **"Read healthcare/NEXT-STEPS.md and let's
> continue."** Start a **new chat** (don't append to the old one — long threads get slower, costlier,
> and less accurate; everything you need is captured in these files).

## Where things stand (done)

- **Scenario chosen & built:** *"The \$4M Bonus That Wasn't the Answer"* — travel-agency nurse spend
  at a fictionalized newly-merged system (Metro / Valley / Cherry). Root cause = a **scheduling**
  failure on 3 units, not pay/acuity.
- **Data generated** (synthetic, deterministic) across 3 systems + a manager's Excel:
  `epic`, `peoplesoft` (Oracle PeopleSoft HCM), `kronos`, and `unit_manager_scheduling_log.xlsx`.
  Regenerate with [`data/generate_healthcare_data.py`](./data/generate_healthcare_data.py).
- **Narratives woven in:** tribal knowledge (manager's Excel), DQ #1 (miscoded PeopleSoft
  termination reasons), DQ #2 (post-merger cost-center drift + a `FLOATPOOL` bucket that hides ~\$82K).
- **Runnable notebook verified:** [`Notebook-with-prompts.ipynb`](./Notebook-with-prompts.ipynb)
  executes end-to-end offline (pandas) and lands the decision memo: agency ≈ **\$721K / 6 mo**,
  ~**100%** on the 3 Cherry units, **\$1.44M** annualized.
- **Docs:** [`README.md`](./README.md) (talk track + CRIT prompts), [`data-loading.md`](./data-loading.md)
  (Fabric load steps), [`WHY-THIS-DEMO.md`](./WHY-THIS-DEMO.md) (Jefferson news context).

## What's left (the fork in the road)

1. **Rayfin / Fabric App** — *you're researching this first.* Draft UX is in
   [`fabric-app-ux.md`](./fabric-app-ux.md) (three-pane Ask / Canvas / Trust). When ready, confirm
   what Rayfin actually is (template? SDK? language/hosting?) and we'll scaffold **flow #1** (the
   core arc) end-to-end.
2. **Optional polish before customer delivery:**
   - Run the demo live in a real Fabric lakehouse to confirm the Prompt-0 auto-load works and the
     agent's charts look good (the offline notebook has tables, not charts).
   - Decide personas for the app language: **CNO/nurse manager** (clinical) vs **CFO/finance**
     (dollars) — we agreed to support **both**.
   - Consider a short slide/one-pager framing (position *against* layoffs; complements the
     customer's governed-AI posture — see WHY-THIS-DEMO.md).

## Open questions still on the table

- Rayfin specifics (see fabric-app-ux.md "Open questions").
- Whether to add a couple of pre-rendered charts to the offline notebook, or keep chart generation
  as a live-agent moment in the room.
