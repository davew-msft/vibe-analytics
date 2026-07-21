"""
generate_data.py
================
Deterministic sample-data generator for the Vibe Analytics
"Manufacturing OEE Root-Cause" demo.

Scenario: a plastics plant running EXTRUSION BLOW MOLDING of HDPE
engine-oil bottles (1-quart and 5-quart). Four blow molders (BM-04,
BM-07, BM-09, BM-12) fed by two regrind blenders (BL-1, BL-2).

The demo "arc":
  1. Descriptive OEE by machine says BM-07 is the worst -> "buy a new press".
  2. Downtime Pareto says "MACHINE_FAULT" -> reinforces the bad-machine story.
  3. But BM-07 is NOT the oldest machine, so the age hypothesis is weak.
  4. MES/PI historian shows bottle-weight + melt-pressure INSTABILITY and
     slow cycles on specific days -- symptoms, not causes.
  5. The process engineer's Excel regrind log shows those exact days had
     REGRIND % pushed way over target on blender BL-2, plus a contaminated
     black color-changeover purge (black specks) fed into BL-2.
  6. BL-2 feeds BM-07 and BM-09. Re-segment by blender + date window and the
     "bad machine" effect vanishes. Root cause = wet/over-blended/contaminated
     regrind, which drives Availability, Performance AND Quality losses at once.
  7. Fix the regrind spec + segregate the bad regrind -> recover OEE, avoid capex.

Outputs (written to ./data):
  machines.csv            (SAP MII-like dimension)
  material_lots.csv       (SAP MII-like)
  production_orders.csv   (SAP MII-like transactional; RAW counts, no OEE precomputed)
  downtime_events.csv     (SAP MII / MES; reason codes deliberately MISCODED)
  process_telemetry.csv   (MES / PI-AVEVA-like historian, hourly)
  material_qc_log.xlsx    (process-engineer Excel -- the smoking gun)

Run:  python generate_data.py
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------
START_DATE = datetime(2026, 6, 1)
N_DAYS = 30
DATES = [START_DATE + timedelta(days=d) for d in range(N_DAYS)]

# The "regrind incident" window. BL-2 regrind % is pushed high across this
# whole window; the contaminated black-purge sub-window is narrower.
WINDOW_START = datetime(2026, 6, 10)
WINDOW_END = datetime(2026, 6, 18)          # inclusive
CONTAM_START = datetime(2026, 6, 12)
CONTAM_END = datetime(2026, 6, 16)          # inclusive black-speck sub-window

SHIFTS = ["A", "B"]  # A = day (06:00-18:00), B = night (18:00-06:00)
SHIFT_START_HOUR = {"A": 6, "B": 18}
PLANNED_MINUTES = 720  # 12h per shift/order


def in_window(dt: datetime, start: datetime, end: datetime) -> bool:
    return start.date() <= dt.date() <= end.date()


# ---------------------------------------------------------------------------
# 1) machines dimension
#    NOTE: BM-07 (the "villain" in the naive story) is NOT the oldest machine.
#          BM-12 is the oldest and performs fine -> kills the age hypothesis.
# ---------------------------------------------------------------------------
machines = pd.DataFrame(
    [
        # machine_id, model,           install_year, num_heads, clamp_tons, blender_id
        ("BM-04", "Uniloy 350R2", 2019, 6, 35, "BL-1"),
        ("BM-07", "Uniloy 350R2", 2021, 6, 35, "BL-2"),
        ("BM-09", "Bekum H-121", 2018, 4, 25, "BL-2"),
        ("BM-12", "Bekum H-155", 2015, 6, 40, "BL-1"),
    ],
    columns=[
        "machine_id",
        "model",
        "install_year",
        "num_heads",
        "clamp_tons",
        "blender_id",
    ],
)
MACHINE_BLENDER = dict(zip(machines.machine_id, machines.blender_id))

# ---------------------------------------------------------------------------
# 2) products
# ---------------------------------------------------------------------------
PRODUCTS = {
    "BOT-1QT-BLK": dict(desc="1-Quart Engine Oil Bottle, Black HDPE", ideal_upm=28.0,
                        target_weight_g=48.0),
    "BOT-5QT-GRY": dict(desc="5-Quart Engine Oil Jug, Gray HDPE", ideal_upm=11.0,
                        target_weight_g=165.0),
}
# assign a "primary" product to each machine (small machines -> 1qt)
MACHINE_PRODUCT = {
    "BM-04": "BOT-1QT-BLK",
    "BM-07": "BOT-1QT-BLK",
    "BM-09": "BOT-5QT-GRY",
    "BM-12": "BOT-5QT-GRY",
}

# ---------------------------------------------------------------------------
# 3) material lots (virgin HDPE + colorant) -- SAP MII-like
# ---------------------------------------------------------------------------
lot_rows = []
suppliers = ["PolyOne", "Nova Chem", "ExxonMobil"]
for i in range(24):
    recv = START_DATE - timedelta(days=int(rng.integers(0, 25)))
    lot_rows.append(
        (
            f"HDPE-{2600 + i}",
            "HDPE_VIRGIN",
            "HDPE 55A blow grade",
            suppliers[i % len(suppliers)],
            recv.strftime("%Y-%m-%d"),
            round(float(rng.normal(0.35, 0.03)), 3),  # melt flow index g/10min
            int(rng.integers(18000, 24000)),
        )
    )
for i, color in enumerate(["Black", "Gray"]):
    lot_rows.append(
        (
            f"COL-{color[:3].upper()}-{100 + i}",
            "COLORANT",
            f"{color} masterbatch",
            "Ampacet",
            (START_DATE - timedelta(days=10)).strftime("%Y-%m-%d"),
            np.nan,
            2000,
        )
    )
material_lots = pd.DataFrame(
    lot_rows,
    columns=[
        "lot_id",
        "material_type",
        "grade",
        "supplier",
        "received_date",
        "melt_index_g10min",
        "qty_kg",
    ],
)
VIRGIN_LOTS = material_lots[material_lots.material_type == "HDPE_VIRGIN"].lot_id.tolist()

# ---------------------------------------------------------------------------
# Downtime reason codes. KEY POINT: the true root cause during the window is
# material/regrind related, but the operators log the resulting blowouts and
# parison-sag micro-stops as "MACHINE_FAULT" (miscoded) -> the naive Pareto trap.
# ---------------------------------------------------------------------------
REASON_CATALOG = {
    "CHANGEOVER": "Mold / color changeover",
    "MACHINE_FAULT": "Machine fault - unplanned stop",
    "MATERIAL_OUT": "Material outage / feed empty",
    "NO_OPERATOR": "No operator / break",
    "STARTUP": "Startup / warm-up",
    "QUALITY_HOLD": "Quality hold",
    "PARISON": "Parison / process adjustment",
}


def sample_downtime_events(order_id, machine_id, date, shift, is_bad):
    """Return list of downtime event tuples for one order."""
    events = []
    base_hour = SHIFT_START_HOUR[shift]
    day_anchor = date.replace(hour=base_hour, minute=0, second=0)

    # baseline planned-ish stops every order gets
    baseline = [
        ("STARTUP", rng.integers(8, 18)),
        ("NO_OPERATOR", rng.integers(10, 25)),
    ]
    if rng.random() < 0.5:
        baseline.append(("CHANGEOVER", rng.integers(20, 45)))

    extra = []
    if is_bad:
        # regrind-driven blowouts / parison sag -> MISCODED as MACHINE_FAULT
        n_fault = int(rng.integers(3, 7))
        for _ in range(n_fault):
            extra.append(("MACHINE_FAULT", rng.integers(12, 40)))
        # a couple correctly-ish coded parison adjustments
        for _ in range(int(rng.integers(1, 3))):
            extra.append(("PARISON", rng.integers(8, 20)))
        if rng.random() < 0.4:
            extra.append(("QUALITY_HOLD", rng.integers(20, 50)))
    else:
        # occasional normal machine fault
        if rng.random() < 0.35:
            extra.append(("MACHINE_FAULT", rng.integers(10, 25)))
        if rng.random() < 0.15:
            extra.append(("MATERIAL_OUT", rng.integers(10, 30)))

    cursor = 0
    for code, dur in baseline + extra:
        dur = int(dur)
        start = day_anchor + timedelta(minutes=int(cursor + rng.integers(15, 45)))
        end = start + timedelta(minutes=dur)
        cursor = (start - day_anchor).total_seconds() / 60 + dur
        events.append(
            (
                order_id,
                machine_id,
                date.strftime("%Y-%m-%d"),
                shift,
                start.strftime("%Y-%m-%d %H:%M:%S"),
                end.strftime("%Y-%m-%d %H:%M:%S"),
                dur,
                code,
                REASON_CATALOG[code],
            )
        )
    return events


# ---------------------------------------------------------------------------
# 4) production orders + downtime events
# ---------------------------------------------------------------------------
order_rows = []
downtime_rows = []
order_seq = 0
event_seq = 0

for date in DATES:
    for shift in SHIFTS:
        for m in machines.machine_id:
            order_seq += 1
            order_id = f"PO-{order_seq:05d}"
            blender = MACHINE_BLENDER[m]
            product_id = MACHINE_PRODUCT[m]
            p = PRODUCTS[product_id]

            # Is this a "bad" run? BL-2 machines during the incident window.
            bad = (blender == "BL-2") and in_window(date, WINDOW_START, WINDOW_END)
            # secondary correlation trap: night shift ran a bit more high-regrind
            night_bias = bad and (shift == "B")

            # --- downtime ---
            events = sample_downtime_events(order_id, m, date, shift, bad)
            if night_bias:
                events += sample_downtime_events(order_id, m, date, shift, True)[:2]
            # BM-07 is the high-visibility, newest press and runs the most
            # high-regrind volume in the window -> it takes the worst hit, which
            # is exactly why leadership fixates on "replace BM-07".
            if bad and m == "BM-07":
                events += sample_downtime_events(order_id, m, date, shift, True)[:2]
            downtime_min = int(sum(e[6] for e in events))
            downtime_min = min(downtime_min, 360)  # cap
            for e in events:
                event_seq += 1
                downtime_rows.append((f"DT-{event_seq:05d}",) + e)

            run_minutes = PLANNED_MINUTES - downtime_min

            # --- performance (slow cycles when regrind melt strength is poor) ---
            if bad:
                perf = float(rng.normal(0.84, 0.03))
            else:
                perf = float(rng.normal(0.965, 0.015))
            perf = float(np.clip(perf, 0.60, 1.0))

            total_units = int(run_minutes * p["ideal_upm"] * perf)

            # --- quality (leak fails + black specks when contaminated) ---
            if bad and in_window(date, CONTAM_START, CONTAM_END):
                qual = float(rng.normal(0.86, 0.03))
            elif bad:
                qual = float(rng.normal(0.92, 0.02))
            else:
                qual = float(rng.normal(0.985, 0.006))
            qual = float(np.clip(qual, 0.70, 0.999))

            good_units = int(total_units * qual)
            scrap_units = total_units - good_units

            virgin_lot = VIRGIN_LOTS[int(rng.integers(0, len(VIRGIN_LOTS)))]
            colorant = "COL-BLA-100" if product_id.endswith("BLK") else "COL-GRA-101"

            order_rows.append(
                (
                    order_id,
                    date.strftime("%Y-%m-%d"),
                    shift,
                    m,
                    blender,
                    product_id,
                    p["desc"],
                    "HDPE",
                    colorant,
                    virgin_lot,
                    f"MOLD-{product_id[-3:]}",
                    PLANNED_MINUTES,
                    downtime_min,
                    run_minutes,
                    round(p["ideal_upm"], 2),
                    total_units,
                    good_units,
                    scrap_units,
                )
            )

production_orders = pd.DataFrame(
    order_rows,
    columns=[
        "order_id",
        "date",
        "shift",
        "machine_id",
        "blender_id",
        "product_id",
        "product_desc",
        "resin",
        "colorant_lot_id",
        "virgin_lot_id",
        "mold_id",
        "planned_minutes",
        "downtime_minutes",
        "run_minutes",
        "ideal_units_per_min",
        "total_units",
        "good_units",
        "scrap_units",
    ],
)

downtime_events = pd.DataFrame(
    downtime_rows,
    columns=[
        "event_id",
        "order_id",
        "machine_id",
        "date",
        "shift",
        "start_ts",
        "end_ts",
        "duration_min",
        "reason_code",
        "reason_desc",
    ],
)

# ---------------------------------------------------------------------------
# 5) process telemetry (MES / PI-AVEVA-like), hourly per machine
#    Shows SYMPTOMS: bottle-weight + melt-pressure instability, slow cycles,
#    during the incident window on BL-2 machines. Does NOT contain regrind %
#    (that lives in the process engineer's Excel) -- so telemetry alone can't
#    crack the case, on purpose.
# ---------------------------------------------------------------------------
tele_rows = []
for date in DATES:
    for hour in range(24):
        ts = date.replace(hour=hour)
        for m in machines.machine_id:
            product_id = MACHINE_PRODUCT[m]
            p = PRODUCTS[product_id]
            blender = MACHINE_BLENDER[m]
            num_heads = int(machines.loc[machines.machine_id == m, "num_heads"].iloc[0])
            nominal_cycle_s = num_heads * 60.0 / p["ideal_upm"]
            bad = (blender == "BL-2") and in_window(date, WINDOW_START, WINDOW_END)
            contam = bad and in_window(date, CONTAM_START, CONTAM_END)

            melt_temp = rng.normal(205, 1.5)
            if bad:
                melt_press = rng.normal(230, 4.0)
                melt_press_std = rng.normal(11.0, 1.5)      # instability up
                weight = p["target_weight_g"] * rng.normal(1.03, 0.004)  # heavier + drift
                weight_std = p["target_weight_g"] * rng.normal(0.055, 0.01)
                wall = rng.normal(0.92, 0.05)               # thinner/variable walls
                cycle_time = nominal_cycle_s * rng.normal(1.15, 0.03)  # slow cycles
                extruder_amps = rng.normal(118, 6)
            else:
                melt_press = rng.normal(212, 2.0)
                melt_press_std = rng.normal(3.2, 0.6)
                weight = p["target_weight_g"] * rng.normal(1.0, 0.002)
                weight_std = p["target_weight_g"] * rng.normal(0.015, 0.003)
                wall = rng.normal(1.02, 0.02)
                cycle_time = nominal_cycle_s * rng.normal(1.0, 0.02)
                extruder_amps = rng.normal(104, 3)

            if contam:
                # contamination doesn't move classic process tags much -> another
                # reason telemetry alone misleads you.
                weight_std *= 1.1

            tele_rows.append(
                (
                    ts.strftime("%Y-%m-%d %H:%M:%S"),
                    m,
                    blender,
                    round(float(melt_temp), 1),
                    round(float(melt_press), 1),
                    round(float(max(melt_press_std, 0.5)), 2),
                    round(float(extruder_amps), 1),
                    round(float(cycle_time), 2),
                    round(float(rng.normal(9.5, 0.3)), 2),   # blow_pressure_bar
                    round(float(rng.normal(14.0, 0.6)), 1),  # mold_cool_temp_c
                    round(float(weight), 2),
                    round(float(max(weight_std, 0.1)), 3),
                    round(float(max(wall, 0.4)), 3),
                    round(float(rng.normal(48, 6)), 1),      # ambient_humidity_pct (control)
                )
            )

process_telemetry = pd.DataFrame(
    tele_rows,
    columns=[
        "ts",
        "machine_id",
        "blender_id",
        "melt_temp_c",
        "melt_pressure_bar",
        "melt_pressure_std",
        "extruder_amps",
        "cycle_time_s",
        "blow_pressure_bar",
        "mold_cool_temp_c",
        "bottle_weight_g",
        "bottle_weight_std_g",
        "wall_thickness_mm",
        "ambient_humidity_pct",
    ],
)

# ---------------------------------------------------------------------------
# 6) process engineer's Excel -- the SMOKING GUN.
#    Daily regrind blend log per blender. On BL-2 during the window, regrind %
#    is pushed far over target (cost pressure) and a contaminated black
#    color-changeover purge is fed in -> black specks + leak failures.
# ---------------------------------------------------------------------------
qc_rows = []
for date in DATES:
    for blender in ["BL-1", "BL-2"]:
        bad = (blender == "BL-2") and in_window(date, WINDOW_START, WINDOW_END)
        contam = bad and in_window(date, CONTAM_START, CONTAM_END)

        target = 15
        if bad:
            actual = int(rng.integers(34, 46))
            source = "Trim/tails + color-changeover purge" if contam else "Trim/tails (grinder backlog)"
            passes = int(rng.integers(3, 5))
            blackspecks = int(rng.integers(18, 40)) if contam else int(rng.integers(4, 10))
            leak_fails = int(rng.integers(20, 60)) if contam else int(rng.integers(6, 18))
            mfi = round(float(rng.normal(0.55, 0.05)), 2)  # degraded regrind -> higher MFI
            if contam:
                note = "Black specks in BM-07 bottles - suspect black changeover purge in regrind. Leak test rejects up."
            else:
                note = "BL-2 blend over target - grinder backlog, ran extra regrind to hit material cost target."
        else:
            actual = int(np.clip(rng.normal(15, 2), 8, 22))
            source = "Trim/tails"
            passes = int(rng.integers(1, 3))
            blackspecks = int(rng.integers(0, 3))
            leak_fails = int(rng.integers(0, 4))
            mfi = round(float(rng.normal(0.37, 0.03)), 2)
            note = ""

        qc_rows.append(
            (
                date.strftime("%Y-%m-%d"),
                blender,
                "HDPE",
                target,
                actual,
                source,
                passes,
                mfi,
                blackspecks,
                leak_fails,
                note,
                "J. Alvarez",
            )
        )

material_qc_log = pd.DataFrame(
    qc_rows,
    columns=[
        "date",
        "blender_id",
        "resin",
        "regrind_pct_target",
        "regrind_pct_actual",
        "regrind_source",
        "regrind_passes",
        "regrind_mfi_g10min",
        "blackspeck_count_per_kg",
        "leak_fail_count",
        "notes",
        "process_engineer",
    ],
)

# ---------------------------------------------------------------------------
# Write everything
# ---------------------------------------------------------------------------
machines.to_csv(os.path.join(OUT_DIR, "machines.csv"), index=False)
material_lots.to_csv(os.path.join(OUT_DIR, "material_lots.csv"), index=False)
production_orders.to_csv(os.path.join(OUT_DIR, "production_orders.csv"), index=False)
downtime_events.to_csv(os.path.join(OUT_DIR, "downtime_events.csv"), index=False)
process_telemetry.to_csv(os.path.join(OUT_DIR, "process_telemetry.csv"), index=False)
material_qc_log.to_excel(
    os.path.join(OUT_DIR, "material_qc_log.xlsx"), index=False, sheet_name="regrind_log"
)

# ---------------------------------------------------------------------------
# Console sanity check (the "answer key")
# ---------------------------------------------------------------------------
po = production_orders.copy()
po["availability"] = po.run_minutes / po.planned_minutes
po["performance"] = po.total_units / (po.run_minutes * po.ideal_units_per_min)
po["quality"] = po.good_units / po.total_units
po["oee"] = po.availability * po.performance * po.quality

print("Rows written:")
print(f"  machines           {len(machines):>5}")
print(f"  material_lots      {len(material_lots):>5}")
print(f"  production_orders  {len(production_orders):>5}")
print(f"  downtime_events    {len(downtime_events):>5}")
print(f"  process_telemetry  {len(process_telemetry):>5}")
print(f"  material_qc_log    {len(material_qc_log):>5}")
print()
print("OEE by machine (the naive view -> BM-07 looks worst):")
print((po.groupby("machine_id").oee.mean().round(3)).to_string())
print()
print("OEE by machine, INSIDE incident window (BL-2 machines tank):")
mask = (pd.to_datetime(po.date) >= WINDOW_START) & (pd.to_datetime(po.date) <= WINDOW_END)
print((po[mask].groupby("machine_id").oee.mean().round(3)).to_string())
print()
print("OEE by machine, OUTSIDE window (BM-07 is fine -> the reveal):")
print((po[~mask].groupby("machine_id").oee.mean().round(3)).to_string())
