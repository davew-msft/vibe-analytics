#!/usr/bin/env python3
"""Generate the synthetic Cascadia Beverages financial dataset for the Fabric IQ Plan demo.

Deterministic (fixed seed) so the numbers are stable across runs and every talk-track
figure is reproducible. Produces:

  data/cascadia.dim_product.csv     product master (Category > Brand > SKU + LifecycleStatus)
  data/cascadia.dim_region.csv      region master (Region > City + DistributorStatus)
  data/cascadia.dim_channel.csv     channel master
  data/cascadia.dim_date.csv        FY2025 monthly calendar
  data/cascadia.sales_actuals.csv   FY2025 monthly fact (the semantic-model fact table)
  data/distributor_contracts.xlsx   the tribal "smoking gun" NOT in the semantic model

Two traps are embedded on purpose (see README.md):
  1. Base-period bias  - the MegaMart Midwest club distributor terminated 2025-09-01,
     but ~$3.2M of its revenue is baked into the FY2025 base. A uniform +8% plan
     grows revenue that already walked out the door.
  2. Mix blindness      - category YoY trajectories diverge wildly (sparkling +20%,
     cola -6%). A uniform +8% plan over-plans the declining cola line and under-plans
     the growing sparkling-water line.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

SEED = 20260819
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
FY = 2025  # actuals fiscal year; the plan year built on top is FY2026

rng = np.random.default_rng(SEED)


# --------------------------------------------------------------------------------------
# Dimensions
# --------------------------------------------------------------------------------------

# Category-level economics and the "true" YoY trajectory the driver-based plan must find.
CATEGORIES = {
    #  category          yoy    margin  trade   price   lifecycle
    "Sparkling Water": (0.20, 0.55, 0.08, 14.0, "Growth"),
    "Energy":          (0.15, 0.60, 0.11, 22.0, "Growth"),
    "Juice":           (0.03, 0.42, 0.09, 16.0, "Mature"),
    "Still Water":     (0.01, 0.38, 0.06, 9.0,  "Mature"),
    "Cola / CSD":      (-0.06, 0.45, 0.14, 12.0, "Declining"),
}

# SKU -> (category, brand, FY2025 annual net revenue base $)
SKUS = {
    "SPK-LIME":    ("Sparkling Water", "Cascade Sparkling", 9_000_000),
    "SPK-BERRY":   ("Sparkling Water", "Cascade Sparkling", 8_500_000),
    "SPK-PLAIN":   ("Sparkling Water", "Cascade Sparkling", 6_500_000),
    "ENG-ORIG":    ("Energy",          "Volt",              10_000_000),
    "ENG-ZERO":    ("Energy",          "Volt",              8_000_000),
    "JUC-ORANGE":  ("Juice",           "Orchard",           13_000_000),
    "JUC-APPLE":   ("Juice",           "Orchard",           11_000_000),
    "JUC-MANGO":   ("Juice",           "Orchard",           9_000_000),
    "STL-500":     ("Still Water",     "PureSpring",        14_000_000),
    "STL-1L":      ("Still Water",     "PureSpring",        13_000_000),
    "COLA-REG":    ("Cola / CSD",      "ClassicCola",       16_000_000),
    "COLA-DIET":   ("Cola / CSD",      "ClassicCola",       12_000_000),
    "COLA-CHERRY": ("Cola / CSD",      "ClassicCola",       10_000_000),
    "ROOT-BEER":   ("Cola / CSD",      "ClassicCola",       10_000_000),
}

# Region -> (representative city, base share weight)
REGIONS = {
    "West":      ("Los Angeles", 0.26),
    "Mountain":  ("Denver",      0.14),
    "Midwest":   ("Chicago",     0.20),
    "South":     ("Atlanta",     0.22),
    "Northeast": ("Boston",      0.18),
}

# Channel -> base share weight
CHANNELS = {
    "Grocery":     0.34,
    "Convenience": 0.22,
    "Club":        0.20,
    "Foodservice": 0.14,
    "Ecommerce":   0.10,
}

# The smoking gun: a club distributor in the Midwest that leaves mid-year.
MEGAMART_MONTHLY = 400_000          # $/month while active
MEGAMART_LAST_ACTIVE_MONTH = 8      # active Jan..Aug (months 1-8), gone Sep..Dec
MEGAMART_REGION = "Midwest"
MEGAMART_CHANNEL = "Club"
MEGAMART_SKUS = ["COLA-REG", "STL-1L", "COLA-DIET"]  # what MegaMart actually stocked


def build_dim_product() -> pd.DataFrame:
    rows = []
    for sku, (cat, brand, _base) in SKUS.items():
        yoy, margin, trade, price, lifecycle = CATEGORIES[cat]
        rows.append(
            {
                "ProductKey": sku,
                "Category": cat,
                "Brand": brand,
                "SKU": sku,
                "LifecycleStatus": lifecycle,
                "ListPricePerCase": price,
                "TargetGrossMarginPct": margin,
            }
        )
    return pd.DataFrame(rows)


def build_dim_region() -> pd.DataFrame:
    rows = []
    for region, (city, _w) in REGIONS.items():
        status = "Lost distributor 2025-09-01" if region == MEGAMART_REGION else "Active"
        rows.append({"RegionKey": region, "Region": region, "City": city, "DistributorStatus": status})
    return pd.DataFrame(rows)


def build_dim_channel() -> pd.DataFrame:
    return pd.DataFrame({"ChannelKey": list(CHANNELS), "Channel": list(CHANNELS)})


def build_dim_date() -> pd.DataFrame:
    rows = []
    for m in range(1, 13):
        d = pd.Timestamp(year=FY, month=m, day=1)
        rows.append(
            {
                "DateKey": d.strftime("%Y-%m-01"),
                "Year": FY,
                "Month": m,
                "MonthName": d.strftime("%b"),
                "Quarter": f"Q{(m - 1) // 3 + 1}",
                "Half": "H1" if m <= 6 else "H2",
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# Fact table
# --------------------------------------------------------------------------------------

def _seasonality(category: str) -> np.ndarray:
    """Monthly seasonality weights (sum to 1). Summer skew for cold beverages."""
    base = np.array([0.9, 0.88, 0.95, 1.0, 1.08, 1.15, 1.2, 1.18, 1.05, 0.98, 0.92, 0.9])
    if category in ("Energy",):  # flatter, less summer-driven
        base = np.array([1.0, 0.98, 1.0, 1.0, 1.02, 1.05, 1.06, 1.05, 1.0, 0.99, 0.98, 0.97])
    return base / base.sum()


def _intra_year_drift(yoy: float) -> np.ndarray:
    """Within-year monthly multiplier so the December run-rate reflects the YoY direction.

    Growing categories exit the year hot, declining categories exit cold. This makes
    the mix trap visible in the actuals themselves, not just in an external assumption.
    """
    # linear drift from 1-half the annual rate to 1+half, centered on 1.0
    return np.linspace(1.0 - yoy / 2.0, 1.0 + yoy / 2.0, 12)


def build_sales_actuals() -> pd.DataFrame:
    records = []
    for sku, (cat, _brand, annual_base) in SKUS.items():
        yoy, margin, trade, price, _lifecycle = CATEGORIES[cat]
        season = _seasonality(cat)
        drift = _intra_year_drift(yoy)
        monthly_shape = season * drift
        monthly_shape = monthly_shape / monthly_shape.sum()  # renormalize to preserve annual base

        for region, (_city, rw) in REGIONS.items():
            for channel, cw in CHANNELS.items():
                cell_annual = annual_base * rw * cw
                if cell_annual <= 0:
                    continue
                for mi in range(12):
                    month = mi + 1
                    # deterministic per-cell noise, +/- ~4%
                    noise = 1.0 + (rng.random() - 0.5) * 0.08
                    net = cell_annual * monthly_shape[mi] * noise
                    records.append(
                        {
                            "DateKey": f"{FY}-{month:02d}-01",
                            "ProductKey": sku,
                            "RegionKey": region,
                            "ChannelKey": channel,
                            "NetRevenue": net,
                        }
                    )

    # Additive MegaMart block: real revenue in the FY2025 base that will not recur.
    per_sku = MEGAMART_MONTHLY / len(MEGAMART_SKUS)
    for sku in MEGAMART_SKUS:
        for month in range(1, MEGAMART_LAST_ACTIVE_MONTH + 1):
            noise = 1.0 + (rng.random() - 0.5) * 0.04
            records.append(
                {
                    "DateKey": f"{FY}-{month:02d}-01",
                    "ProductKey": sku,
                    "RegionKey": MEGAMART_REGION,
                    "ChannelKey": MEGAMART_CHANNEL,
                    "NetRevenue": per_sku * noise,
                }
            )

    df = pd.DataFrame(records)
    # collapse the additive MegaMart rows into the matching base cells
    df = (
        df.groupby(["DateKey", "ProductKey", "RegionKey", "ChannelKey"], as_index=False)["NetRevenue"]
        .sum()
    )

    # derived financial measures
    cat_by_sku = {sku: v[0] for sku, v in SKUS.items()}
    margin_by_sku = {sku: CATEGORIES[cat_by_sku[sku]][1] for sku in SKUS}
    trade_by_sku = {sku: CATEGORIES[cat_by_sku[sku]][2] for sku in SKUS}
    price_by_sku = {sku: CATEGORIES[cat_by_sku[sku]][3] for sku in SKUS}

    df["NetRevenue"] = df["NetRevenue"].round(2)
    df["GrossMargin"] = (df["NetRevenue"] * df["ProductKey"].map(margin_by_sku)).round(2)
    df["COGS"] = (df["NetRevenue"] - df["GrossMargin"]).round(2)
    df["TradeSpend"] = (df["NetRevenue"] * df["ProductKey"].map(trade_by_sku)).round(2)
    df["UnitsSold"] = (df["NetRevenue"] / df["ProductKey"].map(price_by_sku)).round(0).astype(int)

    return df[
        [
            "DateKey",
            "ProductKey",
            "RegionKey",
            "ChannelKey",
            "UnitsSold",
            "NetRevenue",
            "COGS",
            "GrossMargin",
            "TradeSpend",
        ]
    ].sort_values(["DateKey", "ProductKey", "RegionKey", "ChannelKey"], ignore_index=True)


def build_distributor_contracts() -> dict[str, pd.DataFrame]:
    """Tribal knowledge that lives in someone's spreadsheet, NOT in the semantic model."""
    contracts = pd.DataFrame(
        [
            {
                "DistributorName": "MegaMart Wholesale (Midwest)",
                "Region": MEGAMART_REGION,
                "Channel": MEGAMART_CHANNEL,
                "SKUsCarried": ", ".join(MEGAMART_SKUS),
                "MonthlyRevenue": MEGAMART_MONTHLY,
                "AnnualizedRunRate": MEGAMART_MONTHLY * 12,
                "Status": "TERMINATED",
                "EffectiveEndDate": "2025-09-01",
                "Notes": (
                    "MegaMart consolidated to a competitor's DSD network. Final shipment Aug 2025. "
                    "~$3.2M already booked in FY2025 (Jan-Aug) will NOT recur. Do not carry this "
                    "base into FY2026. Finance was not looped in before the annual plan was drafted."
                ),
            },
            {
                "DistributorName": "Rocky Mountain Beverage Co.",
                "Region": "Mountain",
                "Channel": "Grocery",
                "SKUsCarried": "All",
                "MonthlyRevenue": None,
                "AnnualizedRunRate": None,
                "Status": "ACTIVE",
                "EffectiveEndDate": None,
                "Notes": "Contract renewed through 2027. No change.",
            },
        ]
    )

    lifecycle = pd.DataFrame(
        [
            {"SKU": "COLA-REG", "LifecycleStatus": "Declining", "PlannerNote": "Category in structural decline ~ -6%/yr; do not plan uniform growth."},
            {"SKU": "COLA-DIET", "LifecycleStatus": "Declining", "PlannerNote": "Same category headwind as COLA-REG."},
            {"SKU": "COLA-CHERRY", "LifecycleStatus": "Declining", "PlannerNote": "Consider delist review FY2027."},
            {"SKU": "ROOT-BEER", "LifecycleStatus": "Declining", "PlannerNote": "Regional loyalty only; flat-to-down."},
            {"SKU": "SPK-LIME", "LifecycleStatus": "Growth", "PlannerNote": "Sparkling water +20%/yr; under-served, expand facings."},
            {"SKU": "SPK-BERRY", "LifecycleStatus": "Growth", "PlannerNote": "Fastest-growing SKU; shift trade spend here."},
            {"SKU": "ENG-ORIG", "LifecycleStatus": "Growth", "PlannerNote": "Energy +15%/yr; convenience channel priority."},
        ]
    )
    return {"Contracts": contracts, "SKU_Lifecycle": lifecycle}


# --------------------------------------------------------------------------------------
# Driver / write & reconcile
# --------------------------------------------------------------------------------------

def _reconcile(actuals: pd.DataFrame) -> None:
    total = actuals["NetRevenue"].sum()
    print("\n=== Reconciliation (FY2025 actuals) ===")
    print(f"Total NetRevenue:            ${total:,.0f}")
    print(f"Uniform +8% naive plan:      ${total * 1.08:,.0f}")

    by_cat = (
        actuals.merge(
            pd.DataFrame({"ProductKey": list(SKUS), "Category": [v[0] for v in SKUS.values()]}),
            on="ProductKey",
        )
        .groupby("Category")["NetRevenue"]
        .sum()
    )
    print("\nBy category (FY2025 actual  ->  naive +8%  vs  driver-based YoY):")
    driver_total = 0.0
    for cat, val in by_cat.items():
        yoy = CATEGORIES[cat][0]
        driver = val * (1 + yoy)
        driver_total += driver
        print(f"  {cat:16s} ${val:>13,.0f}  ->  ${val * 1.08:>13,.0f}   ${driver:>13,.0f}  ({yoy:+.0%})")
    print(f"  {'DRIVER TOTAL':16s} {'':>14} {'':>17} ${driver_total:>13,.0f}")

    # distributor phantom in the base
    mm = actuals[
        (actuals["RegionKey"] == MEGAMART_REGION) & (actuals["ChannelKey"] == MEGAMART_CHANNEL)
    ]
    mm_by_half = mm.merge(
        pd.DataFrame(
            {"DateKey": [f"{FY}-{m:02d}-01" for m in range(1, 13)],
             "Half": ["H1"] * 6 + ["H2"] * 6}
        ),
        on="DateKey",
    ).groupby("Half")["NetRevenue"].sum()
    print("\nMidwest x Club (distributor cliff):")
    print(f"  H1 (Jan-Jun): ${mm_by_half.get('H1', 0):,.0f}")
    print(f"  H2 (Jul-Dec): ${mm_by_half.get('H2', 0):,.0f}")
    phantom = MEGAMART_MONTHLY * MEGAMART_LAST_ACTIVE_MONTH
    print(f"  MegaMart phantom in FY2025 base: ~${phantom:,.0f}  (naive +8% budgets ~${phantom * 1.08:,.0f} that cannot recur)")


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    dim_product = build_dim_product()
    dim_region = build_dim_region()
    dim_channel = build_dim_channel()
    dim_date = build_dim_date()
    actuals = build_sales_actuals()
    contracts = build_distributor_contracts()

    dim_product.to_csv(os.path.join(DATA_DIR, "cascadia.dim_product.csv"), index=False)
    dim_region.to_csv(os.path.join(DATA_DIR, "cascadia.dim_region.csv"), index=False)
    dim_channel.to_csv(os.path.join(DATA_DIR, "cascadia.dim_channel.csv"), index=False)
    dim_date.to_csv(os.path.join(DATA_DIR, "cascadia.dim_date.csv"), index=False)
    actuals.to_csv(os.path.join(DATA_DIR, "cascadia.sales_actuals.csv"), index=False)

    xlsx_path = os.path.join(DATA_DIR, "distributor_contracts.xlsx")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as xw:
        for sheet, frame in contracts.items():
            frame.to_excel(xw, sheet_name=sheet, index=False)

    print("Wrote:")
    for f in sorted(os.listdir(DATA_DIR)):
        print(f"  data/{f}  ({len(actuals) if f.endswith('sales_actuals.csv') else ''})".rstrip())
    print(f"\nFact rows: {len(actuals):,}")
    _reconcile(actuals)


if __name__ == "__main__":
    main()
