# From Dashboard to Conversation — the Fabric App (Rayfin) UX starter

> **Status: draft to iterate on *after* the notebook demo lands.** This sketches where the
> "replace-the-dashboard" narrative goes: a hosted **Fabric App** (built with **Rayfin**) that does
> both the scheduled analytics *and* a conversational analytics interface over the same lakehouse.

> **One assumption to confirm:** I'm treating **Rayfin** as the Fabric capability for building and
> hosting a data-backed web app that runs inside a Fabric workspace against lakehouse tables (a
> "vibe-coded app that is hosted and runs in MS Fabric," per your brief). If Rayfin means something
> more specific in your environment (a particular template, SDK, or internal build), tell me and
> I'll align the scaffold to it. See the open questions at the bottom.

---

## The narrative: "why this replaces the dashboard"

A traditional turnover/agency dashboard is where this whole demo went *wrong*: it encoded the
builder's assumptions (blame pay, blame Cherry) and it silently undercounted the worst units because
of the post-merger join defect. The Fabric App inverts that:

| Traditional dashboard | Vibe Analytics Fabric App |
|---|---|
| Answers the question the builder anticipated | Answers the question the leader actually has, right now |
| Static tiles; one grain, one filter model | Conversational; re-segments on demand |
| Hides its assumptions and its data-quality gaps | **Surfaces** competing hypotheses and DQ caveats |
| "Agency spend is up 30%" | "Agency spend is up 30% **because** of a schedule failure on 3 units — here's the $ and the fix" |
| You trust it or you don't | It shows its work in the notebook underneath |

The tagline for the room: **"Stop shipping answers. Ship a reasoning partner that shows its work."**

---

## Proposed UX (three panes)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Nurse Labor Intelligence · Metro│Valley│Cherry            [network ▾] [FY ▾] │
├───────────────┬──────────────────────────────────────────┬───────────────────┤
│  ASK          │  CANVAS (answer + chart + table)          │  EVIDENCE / TRUST │
│               │                                           │                   │
│  "Why is      │   Agency $ by unit ▁▂▃▅█                   │  Sources used:    │
│   agency      │   ── 85% on 3 Cherry units ──             │  • kronos.AGENCY  │
│   spend up    │                                           │  • peoplesoft.JOB │
│   on Cherry?" │   Root cause: SCHEDULE (not pay)          │  • epic.Census    │
│               │   • OT 26% vs 8%  • consec 8 vs 3          │  • mgr xlsx       │
│  suggested ▸  │   • self-scheduling suspended (Apr)       │                   │
│   • Which     │                                           │  ⚠ DQ flags:      │
│     units?    │   Recommendation:                         │  • 761 agency hrs │
│   • Pay vs    │   Restore self-scheduling + cap consec.   │    in FLOATPOOL   │
│     schedule? │   Est. avoidable: ~$1.2M/yr vs $4M bonus  │  • TER reasons    │
│   • Show the  │                                           │    miscoded       │
│     manager's │   [Open the notebook that produced this]  │                   │
│     notes     │                                           │                   │
└───────────────┴──────────────────────────────────────────┴───────────────────┘
```

**Left — ASK.** A prompt box seeded with the CRIT ethos plus *suggested follow-ups* generated from
the last answer (keeps the leader "thinking a meta-layer higher" instead of accepting the first
reply).

**Center — CANVAS.** The natural-language answer, the chart it chose, and the underlying table.
Every answer ends with a **decision + dollar figure**, not just a visual.

**Right — EVIDENCE / TRUST.** The differentiator and the governance story (important given the
customer's governed-AI posture): which tables/columns were used, and any **data-quality flags** the
agent raised (the FLOATPOOL bucket, the miscoded reason codes). One click opens the generating
notebook cell — the app *shows its work*.

---

## Reference conversation flows to build first

1. **"Where is agency spend concentrated, and is it pay or schedule?"** → the core arc, ending in
   the $ recommendation.
2. **"Prove the low-pay theory wrong (or right)."** → pay vs. turnover scatter + verdict.
3. **"What does the nurse manager's log say about 5 West in Q2?"** → pulls the Excel notes inline.
4. **"What would the $4M bonus actually buy vs. fixing the schedule?"** → side-by-side ROI.
5. **"Show me every data-quality caveat behind this answer."** → the trust pane, expanded.

---

## Suggested build shape (to refine once Rayfin specifics are confirmed)

- **Data layer:** the same `epic` / `peoplesoft` / `kronos` lakehouse tables + the manager's Excel;
  a couple of curated **gold views** (`v_unit_labor_scorecard`, `v_agency_reconciled`) so the app
  isn't re-deriving the join defect every turn — the *corrected* agency reconciliation lives here.
- **Semantic/metrics layer:** named measures (turnover %, agency reliance %, schedule-stress index,
  avoidable-agency $) so NL questions map to trustworthy definitions.
- **Agent/NL2SQL layer:** conversational analytics grounded on those gold views (this is the bridge
  from the [nl2sql](https://github.com/davew-msft/nl2sql) work referenced in the top-level README).
- **App layer (Rayfin):** the three-pane UX above, hosted in the Fabric workspace, with the
  "open the notebook" deep-link for transparency.

---

## Open questions for you

1. **Rayfin specifics** — is it a Fabric app template / SDK / internal framework? Any starter repo,
   required language (React? Python?), or hosting constraints I should scaffold to?
2. **Governance framing** — do you want the Trust pane to explicitly echo the customer's governed-AI
   (Qualified Health) posture, or stay generic?
3. **Scope for v1** — build all five flows, or nail flow #1 (the core arc) end-to-end first?
4. **Personas** — is the primary user the CNO/nurse manager, the CFO/finance partner, or both (which
   changes default language: clinical vs. dollars)?
