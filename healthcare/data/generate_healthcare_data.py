"""
Generate the synthetic dataset for the Vibe Analytics healthcare demo.

Three source systems + one manager's spreadsheet, designed so that NO single
system tells the whole story:

  epic         (Caboodle/Clarity-style)  -> clinical workload / acuity  (the SYMPTOM context)
  peoplesoft   (Oracle PeopleSoft HCM)   -> HR system of record         (term reasons are MISCODED)
  kronos       (UKG/Kronos timekeeping)  -> the actual clock            (OT / float / consecutive shifts)
  <manager xlsx> unit_manager_scheduling_log.xlsx -> tribal knowledge   (the CAUSE + stay-interview notes)

The story: a newly-merged 3-network health system wants to spend $4M on blanket
RN sign-on/retention bonuses to cut travel-agency nurse spend. The dashboard
blames Legacy Cherry / low pay. The real driver is a SCHEDULING pattern (float +
forced OT + suspended self-scheduling + closed beds) on ~3 units -- and two data
quality problems hide it:
  DQ1: PeopleSoft termination reason codes are miscoded (Personal/Relocation).
  DQ2: post-merger cost-center formats differ across systems AND Cherry agency
       hours are booked to a FLOATPOOL labor account -> naive joins UNDERCOUNT
       agency on exactly the worst units.

Run:  python generate_healthcare_data.py
Deterministic (fixed seed).
"""

import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(20260805)
OUT = Path(__file__).parent
MONTHS = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]

# ---------------------------------------------------------------------------
# Unit master. Note the DELIBERATELY different cost-center formats per system:
#   epic_cc     e.g. "8105"        (Epic Caboodle)
#   ps_deptid   e.g. "CHR8105"     (PeopleSoft SETID-prefixed)
#   kronos_acct e.g. "08105-RN"    (Kronos labor account, zero-padded)
# They all describe the same unit but you must NORMALIZE to join them. (DQ2)
# ---------------------------------------------------------------------------
UNITS = [
    # key, name, network, epic_cc, specialty, beds, n_rns, base_rate, mkt_adj,
    #   ot, float, consec, selfsched_suspend_mo, beds_closed_mo, beds_closed_n,
    #   terms, acuity, regime
    dict(key="DEP5E",  name="5 East Med/Surg",      net="Legacy Metro",  epic_cc="6101", spec="MedSurg",   beds=32, n=7, base=44.0, adj=2.0, ot=0.10, flt=0.06, consec=4, susp=None,      bc_mo=None,     bc_n=0, terms=1, acuity=1.02, regime="stable"),
    dict(key="DEP7T",  name="7 Tower Telemetry",    net="Legacy Metro",  epic_cc="6110", spec="Telemetry", beds=28, n=6, base=46.0, adj=2.0, ot=0.08, flt=0.05, consec=3, susp=None,      bc_mo=None,     bc_n=0, terms=0, acuity=1.15, regime="stable"),
    dict(key="DEPMIC", name="Medical ICU",          net="Legacy Metro",  epic_cc="6120", spec="ICU",       beds=20, n=8, base=52.0, adj=3.0, ot=0.11, flt=0.04, consec=4, susp=None,      bc_mo=None,     bc_n=0, terms=1, acuity=1.85, regime="stable"),
    dict(key="DEP3N",  name="3 North Med/Surg",     net="Legacy Valley", epic_cc="7101", spec="MedSurg",   beds=30, n=7, base=41.0, adj=0.0, ot=0.07, flt=0.05, consec=3, susp=None,      bc_mo=None,     bc_n=0, terms=0, acuity=1.00, regime="stable-lowpay"),
    dict(key="DEPORT", name="Ortho Surgical",       net="Legacy Valley", epic_cc="7130", spec="Surgical",  beds=26, n=6, base=43.0, adj=1.0, ot=0.09, flt=0.06, consec=4, susp=None,      bc_mo=None,     bc_n=0, terms=1, acuity=1.10, regime="stable"),
    dict(key="DEPSIC", name="Surgical ICU",         net="Legacy Valley", epic_cc="7120", spec="ICU",       beds=18, n=7, base=51.0, adj=2.0, ot=0.12, flt=0.05, consec=4, susp=None,      bc_mo=None,     bc_n=0, terms=1, acuity=1.80, regime="stable"),
    dict(key="DEP4E",  name="4 East Med/Surg",      net="Legacy Cherry", epic_cc="8101", spec="MedSurg",   beds=24, n=6, base=45.0, adj=3.0, ot=0.18, flt=0.14, consec=5, susp="2026-05", bc_mo=None,     bc_n=0, terms=2, acuity=1.05, regime="problem"),
    dict(key="DEP5W",  name="5 West Med/Surg",      net="Legacy Cherry", epic_cc="8105", spec="MedSurg",   beds=28, n=7, base=47.0, adj=6.0, ot=0.26, flt=0.22, consec=7, susp="2026-04", bc_mo="2026-04", bc_n=6, terms=4, acuity=1.04, regime="worst"),
    dict(key="DEPPCU", name="Progressive Care",     net="Legacy Cherry", epic_cc="8115", spec="PCU",       beds=22, n=7, base=48.0, adj=4.0, ot=0.22, flt=0.18, consec=6, susp="2026-04", bc_mo="2026-05", bc_n=4, terms=3, acuity=1.35, regime="problem"),
]

def epic_to_ps(cc):     return f"{UNIT_NET_PREFIX[cc]}{cc}"
def epic_to_kronos(cc): return f"0{cc}-RN"

UNIT_NET_PREFIX = {}
for u in UNITS:
    UNIT_NET_PREFIX[u["epic_cc"]] = {"Legacy Metro": "MET", "Legacy Valley": "VAL", "Legacy Cherry": "CHR"}[u["net"]]

# ---------------------------------------------------------------------------
# epic.DepartmentDim
# ---------------------------------------------------------------------------
dept_dim = pd.DataFrame([
    dict(DepartmentKey=i + 1000, DepartmentName=u["name"], LegacyNetwork=u["net"],
         EpicCostCenter=u["epic_cc"], SpecialtyType=u["spec"], LicensedBeds=u["beds"],
         MagnetDesignated=("Y" if u["net"] != "Legacy Cherry" else "N"))
    for i, u in enumerate(UNITS)
])
dept_dim.to_csv(OUT / "epic.DepartmentDim.csv", index=False)

# ---------------------------------------------------------------------------
# epic.NursingUnitCensusFact  (monthly clinical workload / acuity)
# Note: problem units are NOT higher acuity -> kills "sicker patients" story.
# ---------------------------------------------------------------------------
census_rows = []
for u in UNITS:
    for m in MONTHS:
        occ = RNG.uniform(0.80, 0.94)
        beds = u["beds"] - (u["bc_n"] if (u["bc_mo"] and m >= u["bc_mo"]) else 0)
        adc = round(beds * occ, 1)
        days = int(round(adc * 30))
        acuity = round(u["acuity"] * RNG.uniform(0.97, 1.03), 2)
        target_hppd = {"ICU": 18.0, "PCU": 12.0, "Telemetry": 10.0,
                       "Surgical": 8.5, "MedSurg": 8.0}[u["spec"]]
        req_hours = int(round(days * target_hppd * acuity))
        census_rows.append(dict(
            Month=m, DepartmentKey=1000 + UNITS.index(u), EpicCostCenter=u["epic_cc"],
            AvgDailyCensus=adc, PatientDays=days, AcuityIndex=acuity,
            TargetHPPD=target_hppd, RequiredNursingHours=req_hours))
census = pd.DataFrame(census_rows)
census.to_csv(OUT / "epic.NursingUnitCensusFact.csv", index=False)

# ---------------------------------------------------------------------------
# peoplesoft.PS_DEPT_TBL / PS_JOBCODE_TBL / PS_ACTION_REASON
# ---------------------------------------------------------------------------
ps_dept = pd.DataFrame([
    dict(SETID="SHARE", DEPTID=epic_to_ps(u["epic_cc"]), DESCR=u["name"],
         COMPANY="JEF", LOCATION=u["net"], COST_CENTER=f"CC-{u['epic_cc']}",
         EFFDT="2025-07-01", EFF_STATUS="A")
    for u in UNITS
])
ps_dept.to_csv(OUT / "peoplesoft.PS_DEPT_TBL.csv", index=False)

ps_jobcode = pd.DataFrame([
    dict(SETID="SHARE", JOBCODE="RN001", DESCR="Staff Nurse I",   SAL_ADMIN_PLAN="NUR", GRADE="N1"),
    dict(SETID="SHARE", JOBCODE="RN002", DESCR="Staff Nurse II",  SAL_ADMIN_PLAN="NUR", GRADE="N2"),
    dict(SETID="SHARE", JOBCODE="RN003", DESCR="Charge Nurse",    SAL_ADMIN_PLAN="NUR", GRADE="N3"),
    dict(SETID="SHARE", JOBCODE="NA001", DESCR="Nursing Assistant", SAL_ADMIN_PLAN="NUR", GRADE="A1"),
])
ps_jobcode.to_csv(OUT / "peoplesoft.PS_JOBCODE_TBL.csv", index=False)

# Reason codes. The point: 'SCH' (schedule/work-life) is almost never used even
# though it is the true driver. Exits get dumped into PER / REL / COM.
ps_action_reason = pd.DataFrame([
    dict(ACTION="TER", ACTION_REASON="PER", DESCR="Voluntary - Personal Reasons"),
    dict(ACTION="TER", ACTION_REASON="REL", DESCR="Voluntary - Relocation"),
    dict(ACTION="TER", ACTION_REASON="COM", DESCR="Voluntary - Compensation"),
    dict(ACTION="TER", ACTION_REASON="CAR", DESCR="Voluntary - Career Advancement"),
    dict(ACTION="TER", ACTION_REASON="RET", DESCR="Retirement"),
    dict(ACTION="TER", ACTION_REASON="SCH", DESCR="Voluntary - Scheduling / Work-Life Balance"),
    dict(ACTION="HIR", ACTION_REASON="NEW", DESCR="New Hire"),
    dict(ACTION="DTA", ACTION_REASON="DTA", DESCR="Data Change"),
])
ps_action_reason.to_csv(OUT / "peoplesoft.PS_ACTION_REASON.csv", index=False)

# ---------------------------------------------------------------------------
# peoplesoft.PS_JOB  (one current row per employee; terminated staff carry TER)
# COMPRATE is hourly. Note worst units carry a HIGH market adj -> undercuts the
# "they leave because pay is low" story.
# Terminations on problem units are miscoded to PER/REL/COM (not SCH).
# ---------------------------------------------------------------------------
emp_rows = []
kronos_profiles = []   # carried to Kronos so hours reconcile to the same people
emplid = 700001
for u in UNITS:
    deptid = epic_to_ps(u["epic_cc"])
    n = u["n"]
    n_term = u["terms"]
    for i in range(n):
        jobcode = RNG.choice(["RN001", "RN002", "RN003"], p=[0.35, 0.45, 0.20])
        grade_bump = {"RN001": 0.0, "RN002": 3.0, "RN003": 7.0}[str(jobcode)]
        rate = round(u["base"] + u["adj"] + grade_bump + RNG.uniform(-1.0, 1.5), 2)
        fte = float(RNG.choice([1.0, 0.9, 0.8], p=[0.7, 0.2, 0.1]))
        hire_year = int(RNG.choice([2016, 2018, 2019, 2021, 2022, 2023, 2024]))
        is_term = i < n_term
        if is_term:
            action = "TER"
            # deliberately miscoded away from SCH except one honest case on 5 West
            if u["key"] == "DEP5W" and i == 0:
                reason = "SCH"
            else:
                reason = str(RNG.choice(["PER", "REL", "COM", "CAR"], p=[0.45, 0.25, 0.20, 0.10]))
            term_mo = str(RNG.choice(["2026-04", "2026-05", "2026-06"], p=[0.3, 0.35, 0.35]))
            term_dt = f"{term_mo}-{int(RNG.integers(10, 28)):02d}"
        else:
            action = str(RNG.choice(["HIR", "DTA"], p=[0.2, 0.8]))
            reason = "NEW" if action == "HIR" else "DTA"
            term_dt = ""
        emp_rows.append(dict(
            EMPLID=emplid, EMPL_RCD=0, EFFDT="2026-06-30", EFFSEQ=0,
            DEPTID=deptid, JOBCODE=jobcode, POSITION_NBR=f"P{emplid}",
            ACTION=action, ACTION_REASON=reason, EMPL_STATUS=("T" if is_term else "A"),
            FTE=fte, COMPRATE=rate, COMP_FREQUENCY="H",
            HIRE_DT=f"{hire_year}-{int(RNG.integers(1,12)):02d}-01", TERMINATION_DT=term_dt))
        kronos_profiles.append(dict(emplid=emplid, u=u, rate=rate, fte=fte,
                                    is_term=is_term, term_dt=term_dt))
        emplid += 1
ps_job = pd.DataFrame(emp_rows)
ps_job.to_csv(OUT / "peoplesoft.PS_JOB.csv", index=False)

# ---------------------------------------------------------------------------
# kronos.PAYCODE
# ---------------------------------------------------------------------------
kronos_paycode = pd.DataFrame([
    dict(PAYCODE="REG", DESCR="Regular Worked",        COUNTS_AS_WORKED="Y"),
    dict(PAYCODE="OT",  DESCR="Overtime (1.5x)",       COUNTS_AS_WORKED="Y"),
    dict(PAYCODE="FLT", DESCR="Float to Other Unit",   COUNTS_AS_WORKED="Y"),
    dict(PAYCODE="CALL",DESCR="Call-off / Cancelled",  COUNTS_AS_WORKED="N"),
    dict(PAYCODE="ORI", DESCR="Orientation",           COUNTS_AS_WORKED="Y"),
    dict(PAYCODE="AGY", DESCR="Agency / Travel Worked", COUNTS_AS_WORKED="Y"),
])
kronos_paycode.to_csv(OUT / "kronos.PAYCODE.csv", index=False)

# ---------------------------------------------------------------------------
# kronos.TIMECARD_SUMMARY (monthly per core employee)
# Float shown when WORKED_LABOR_ACCT != HOME_LABOR_ACCT.
# Problem units escalate OT / float / consecutive shifts in the Apr-Jun window.
# ---------------------------------------------------------------------------
def month_stress(u, m):
    """Return multiplier that ramps up on problem units during the window."""
    in_window = m >= "2026-04"
    if u["regime"] in ("problem", "worst") and in_window:
        return 1.6 if u["regime"] == "worst" else 1.35
    return 1.0

tc_rows = []
for p in kronos_profiles:
    u = p["u"]
    home = epic_to_kronos(u["epic_cc"])
    for m in MONTHS:
        # stop generating hours after termination month
        if p["is_term"] and p["term_dt"] and m > p["term_dt"][:7]:
            continue
        base_hours = 12 * 13 * p["fte"]  # ~12h shifts, ~13/month at 1.0 FTE
        stress = month_stress(u, m)
        reg = round(base_hours * RNG.uniform(0.92, 1.0), 1)
        ot = round(base_hours * u["ot"] * stress * RNG.uniform(0.8, 1.2), 1)
        flt = round(base_hours * u["flt"] * stress * RNG.uniform(0.7, 1.3), 1)
        shifts = int(round((reg + ot + flt) / 12))
        consec = int(min(u["consec"] * (stress if stress > 1 else 1) + RNG.integers(-1, 2),
                         10))
        calloff = round(RNG.choice([0, 0, 0, 12], p=[0.7, 0.1, 0.1, 0.1]) * RNG.uniform(0.5, 1), 1)
        worked_acct = home
        # a floated month books some hours to a different unit's account
        if flt > 12 and RNG.random() < 0.6:
            worked_acct = epic_to_kronos(RNG.choice([x["epic_cc"] for x in UNITS if x["net"] == u["net"]]))
        tc_rows.append(dict(
            EMPLID=p["emplid"], MONTH=m, HOME_LABOR_ACCT=home, WORKED_LABOR_ACCT=worked_acct,
            REG_HRS=reg, OT_HRS=ot, FLOAT_HRS=flt, CALLOFF_HRS=calloff,
            SHIFTS_WORKED=shifts, MAX_CONSECUTIVE_SHIFTS=consec))
timecard = pd.DataFrame(tc_rows)
timecard.to_csv(OUT / "kronos.TIMECARD_SUMMARY.csv", index=False)

# ---------------------------------------------------------------------------
# kronos.AGENCY_HOURS (monthly per unit)
# DQ2 smoking gun: on Legacy Cherry, part of agency hours are booked to a shared
# FLOATPOOL labor account -> naive unit joins UNDERCOUNT the worst units.
# ---------------------------------------------------------------------------
agy_rows = []
VENDORS = ["Aya Healthcare", "Cross Country", "Medical Solutions"]
for u in UNITS:
    for m in MONTHS:
        stress = month_stress(u, m)
        # baseline agency reliance driven by regime
        base = {"stable": 0, "stable-lowpay": 0, "problem": 240, "worst": 420}[u["regime"]]
        hrs = int(round(base * stress * RNG.uniform(0.85, 1.15))) if base else 0
        if hrs == 0:
            continue
        bill = round(RNG.uniform(102, 118), 2)
        vendor = str(RNG.choice(VENDORS))
        if u["net"] == "Legacy Cherry" and RNG.random() < 0.5:
            # split: ~40% of hours mis-booked to the Cherry float pool account
            split = int(round(hrs * 0.4))
            agy_rows.append(dict(MONTH=m, LABOR_ACCT=epic_to_kronos(u["epic_cc"]),
                                 AGENCY_HRS=hrs - split, BILL_RATE=bill, VENDOR=vendor))
            agy_rows.append(dict(MONTH=m, LABOR_ACCT="0FLOATPOOL-CHR",
                                 AGENCY_HRS=split, BILL_RATE=bill, VENDOR=vendor))
        else:
            agy_rows.append(dict(MONTH=m, LABOR_ACCT=epic_to_kronos(u["epic_cc"]),
                                 AGENCY_HRS=hrs, BILL_RATE=bill, VENDOR=vendor))
agency = pd.DataFrame(agy_rows)
agency.to_csv(OUT / "kronos.AGENCY_HOURS.csv", index=False)

# ---------------------------------------------------------------------------
# Manager's Excel (tribal knowledge) -> unit_manager_scheduling_log.xlsx
# The CAUSE + free-text stay-interview notes that NO system captured.
# ---------------------------------------------------------------------------
notes_map = {
    ("DEP5W", "2026-04"): "Reno on north hall - closed 6 beds. Self-scheduling SUSPENDED, went to assigned rotations. Mandatory OT started. 2 travelers on nights.",
    ("DEP5W", "2026-05"): "Still on mandatory OT. Core RNs floated to 4 East 3-4x each. Stay interview: 'I'm on my 6th shift in a row, I can't do this rotation.'",
    ("DEP5W", "2026-06"): "Two more resignations. Both said scheduling in exit chat but HR coded 'personal'. Travelers now covering 40% of nights.",
    ("DEPPCU", "2026-04"): "Absorbing overflow from 5 West reno. Self-scheduling paused. Charge nurses picking up doubles.",
    ("DEPPCU", "2026-05"): "Closed 4 beds - no aides. Heavy float in from telemetry. Morale low, 2 RNs asked about transfer to Valley.",
    ("DEP4E",  "2026-05"): "Took 5 West float overflow. Self-scheduling paused this month. Consecutive-shift complaints rising.",
    ("DEP3N",  "2026-03"): "Self-scheduling working well. Low OT. Waitlist of RNs wanting to transfer IN.",
    ("DEPMIC", "2026-02"): "Stable. High acuity but predictable rotation, minimal float.",
}
mgr_rows = []
for u in UNITS:
    for m in MONTHS:
        beds_closed = u["bc_n"] if (u["bc_mo"] and m >= u["bc_mo"]) else 0
        selfsched = "N" if (u["susp"] and m >= u["susp"]) else "Y"
        mand_ot = "Y" if (u["regime"] in ("problem", "worst") and m >= "2026-04") else "N"
        floatpol = "Punitive/assigned" if selfsched == "N" else "Volunteer-first"
        note = notes_map.get((u["key"], m), "")
        # keep the sheet small: only emit rows that carry signal or are anchors
        if note or beds_closed or selfsched == "N" or mand_ot == "Y" or m in ("2026-01",):
            mgr_rows.append(dict(
                Month=m, Unit=u["name"], LegacyNetwork=u["net"], EpicCostCenter=u["epic_cc"],
                LicensedBeds=u["beds"], BedsClosed=beds_closed,
                SelfSchedulingEnabled=selfsched, MandatoryOT=mand_ot,
                FloatPolicy=floatpol, Notes=note))
mgr = pd.DataFrame(mgr_rows)
with pd.ExcelWriter(OUT / "unit_manager_scheduling_log.xlsx", engine="openpyxl") as xw:
    mgr.to_excel(xw, sheet_name="Scheduling Log", index=False)

# ---------------------------------------------------------------------------
# Console summary so we can eyeball that the story holds.
# ---------------------------------------------------------------------------
print("Files written to", OUT)
for f in sorted(OUT.glob("*.csv")):
    print(f"  {f.name:40s} {sum(1 for _ in open(f)) - 1:5d} rows")
print(f"  {'unit_manager_scheduling_log.xlsx':40s} {len(mgr):5d} rows")
print("\n--- sanity: agency $ premium by network (naive unit join would miss FLOATPOOL) ---")
print(agency.assign(cost=lambda d: d.AGENCY_HRS * d.BILL_RATE)
      .groupby(agency.LABOR_ACCT.str.contains("FLOATPOOL")).cost.sum().round(0).to_dict())
