"""
============================================================
NIST GAS VISCOSITY DATA EXTRACTOR
Automatically pulls methane and nitrogen viscosity data
from the NIST Chemistry WebBook for HPHT conditions
============================================================
Author: Prince Clarence Akpan
Project: B.Eng Final Year Project
University of Port Harcourt, Dept. of Gas Engineering
============================================================

HOW TO USE:
-----------
1. Make sure you have Python installed with requests and pandas:
   pip install requests pandas

2. Run: python nist_data_extractor.py

3. The script will generate:
   - methane_viscosity_nist.csv
   - nitrogen_viscosity_nist.csv
   - gas_viscosity_data.csv (combined, ready for the AI models)

NOTE: This script uses the NIST WebBook's public web interface.
      It sends requests slowly (1 second between each) to avoid
      overloading the server. Be patient, it takes a few minutes.
============================================================
"""

import requests
import pandas as pd
import time
import re
import sys

# ============================================================
# CONFIGURATION
# ============================================================

# HPHT conditions and extended range for training
# Pressures in MPa (NIST uses SI units internally)
# 1 MPa = 145.038 psia
# 10,000 psia = 68.95 MPa
# 25,000 psia = 172.37 MPa

# We collect data from moderate to HPHT to give the models
# enough training range. The HPHT subset (>10,000 psia, >300F)
# will be the primary focus for evaluation.

METHANE_CONFIG = {
    "name": "Methane",
    "cas": "C74828",  # NIST CAS identifier for methane
    "gas_sg": 0.5539,  # specific gravity relative to air
    "co2_frac": 0.0,
    "n2_frac": 0.0,
}

NITROGEN_CONFIG = {
    "name": "Nitrogen",
    "cas": "C7727379",  # NIST CAS identifier for nitrogen
    "gas_sg": 0.9672,  # specific gravity relative to air
    "co2_frac": 0.0,
    "n2_frac": 1.0,  # pure nitrogen
}

# Temperature points in Kelvin
# 300F = 422K, 600F = 589K
# We include some below HPHT threshold for training data
TEMPERATURES_K = [
    300,
    320,
    340,
    360,
    380,
    400,  # below HPHT threshold
    422,
    440,
    460,
    480,
    500,  # HPHT range starts (~300F = 422K)
    520,
    540,
    560,
    580,
    600,  # deep HPHT
    620,
    640,
    660,
    680,
    700,  # extreme HPHT
]

# Pressure points in MPa
# 10,000 psia = 68.95 MPa
# We include moderate pressures for training
PRESSURES_MPA = [
    10,
    15,
    20,
    25,
    30,
    35,
    40,
    45,
    50,  # moderate (1,450 - 7,252 psia)
    55,
    60,
    65,
    70,
    75,
    80,
    85,
    90,  # approaching HPHT
    95,
    100,
    110,
    120,
    130,
    140,
    150,  # HPHT range (14,504 - 21,756 psia)
    160,
    170,  # extreme HPHT (23,206 - 24,656 psia)
]

# Conversion factors
MPA_TO_PSIA = 145.038
K_TO_F = lambda k: (k - 273.15) * 9 / 5 + 32
PA_S_TO_CP = 1e3  # 1 Pa.s = 1000 cp, but NIST gives microPa.s


# ============================================================
# NIST DATA FETCHER
# ============================================================


def fetch_nist_isobar(
    cas_id, temperature_low_k, temperature_high_k, pressure_mpa, gas_name="Gas"
):
    """
    Fetch viscosity data from NIST WebBook for a single isobar.

    The NIST WebBook provides data via URL parameters.
    We request isobaric data at a fixed pressure across a temperature range.
    """

    url = "https://webbook.nist.gov/cgi/fluid.cgi"

    params = {
        "Action": "Data",
        "Wide": "on",
        "ID": cas_id,
        "Type": "IsoBar",
        "Digits": "5",
        "P": str(pressure_mpa),
        "THigh": str(temperature_high_k),
        "TLow": str(temperature_low_k),
        "TInc": "20",  # increment in K
        "RefState": "DEF",
        "TUnit": "K",
        "PUnit": "MPa",
        "DUnit": "kg/m3",
        "HUnit": "kJ/kg",
        "WUnit": "m/s",
        "VisUnit": "uPa*s",  # microPa.s
        "STUnit": "N/m",
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"    Warning: Failed to fetch data at P={pressure_mpa} MPa: {e}")
        return None


def parse_nist_response(html_text):
    """
    Parse the NIST WebBook HTML response to extract data.
    The data is in an HTML table with tab-separated values.
    """
    if html_text is None:
        return []

    data_points = []

    # Look for the data table
    # NIST returns data in a simple text format between <pre> tags
    # or as tab-separated values
    lines = html_text.split("\n")

    header_found = False
    header_cols = []

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Find header line (contains "Temperature" and "Viscosity")
        if "Temperature" in line and "Viscosity" in line:
            header_cols = [col.strip() for col in line.split("\t")]
            header_found = True
            continue

        # Parse data lines (tab-separated numbers)
        if header_found and line and line[0].isdigit():
            parts = line.split("\t")
            if len(parts) >= 2:
                try:
                    values = {}
                    for i, col in enumerate(header_cols):
                        if i < len(parts):
                            try:
                                values[col.strip()] = float(parts[i].strip())
                            except ValueError:
                                values[col.strip()] = None

                    data_points.append(values)
                except (ValueError, IndexError):
                    continue

    return data_points


def collect_gas_data(config):
    """
    Collect viscosity data for a single gas across all P-T conditions.
    """
    gas_name = config["name"]
    cas_id = config["cas"]

    print(f"\n{'='*60}")
    print(f"  Collecting {gas_name} data from NIST WebBook")
    print(f"{'='*60}")

    all_data = []
    total_requests = len(PRESSURES_MPA)

    for i, p_mpa in enumerate(PRESSURES_MPA):
        p_psia = p_mpa * MPA_TO_PSIA
        print(
            f"  [{i+1}/{total_requests}] Fetching P = {p_mpa} MPa ({p_psia:.0f} psia)...",
            end=" ",
        )

        html = fetch_nist_isobar(
            cas_id,
            temperature_low_k=min(TEMPERATURES_K),
            temperature_high_k=max(TEMPERATURES_K),
            pressure_mpa=p_mpa,
            gas_name=gas_name,
        )

        if html:
            points = parse_nist_response(html)

            for pt in points:
                # Extract temperature and viscosity
                temp_k = None
                viscosity_upas = None
                density = None

                for key, val in pt.items():
                    if "Temperature" in key and val is not None:
                        temp_k = val
                    if "Viscosity" in key and val is not None:
                        viscosity_upas = val
                    if "Density" in key and val is not None:
                        density = val

                if temp_k is not None and viscosity_upas is not None:
                    temp_f = K_TO_F(temp_k)
                    # Convert microPa.s to centipoise
                    # 1 cp = 1000 microPa.s? No: 1 cp = 1 mPa.s = 1000 uPa.s
                    viscosity_cp = viscosity_upas / 1000.0

                    all_data.append(
                        {
                            "Pressure_psia": round(p_psia, 1),
                            "Temperature_F": round(temp_f, 1),
                            "Temperature_K": round(temp_k, 1),
                            "Pressure_MPa": p_mpa,
                            "Gas_SG": config["gas_sg"],
                            "CO2_fraction": config["co2_frac"],
                            "N2_fraction": config["n2_frac"],
                            "Viscosity_cp": round(viscosity_cp, 6),
                            "Density_kg_m3": round(density, 4) if density else None,
                            "Gas_Type": gas_name,
                        }
                    )

            print(f"got {len(points)} points")
        else:
            print("failed")

        # Be polite to NIST servers
        time.sleep(1.0)

    print(f"\n  Total {gas_name} data points: {len(all_data)}")
    return all_data


# ============================================================
# MAIN
# ============================================================


def main():
    print("=" * 60)
    print("  NIST GAS VISCOSITY DATA EXTRACTOR")
    print("  For HPHT Gas Viscosity Prediction Project")
    print("  Prince Clarence Akpan | U2020/3070033")
    print("=" * 60)
    print()
    print("  This script will pull viscosity data for methane")
    print("  and nitrogen from the NIST Chemistry WebBook.")
    print("  It sends requests slowly to avoid server issues.")
    print("  Estimated time: 3-5 minutes.")
    print()

    # Collect methane data
    methane_data = collect_gas_data(METHANE_CONFIG)

    # Collect nitrogen data
    nitrogen_data = collect_gas_data(NITROGEN_CONFIG)

    # Save individual gas files
    if methane_data:
        df_methane = pd.DataFrame(methane_data)
        df_methane.to_csv("methane_viscosity_nist.csv", index=False)
        print(f"\n  Saved: methane_viscosity_nist.csv ({len(df_methane)} rows)")

    if nitrogen_data:
        df_nitrogen = pd.DataFrame(nitrogen_data)
        df_nitrogen.to_csv("nitrogen_viscosity_nist.csv", index=False)
        print(f"  Saved: nitrogen_viscosity_nist.csv ({len(df_nitrogen)} rows)")

    # Combine into final dataset
    all_data = methane_data + nitrogen_data

    if all_data:
        df_all = pd.DataFrame(all_data)

        # Select only the columns needed for the AI models
        model_cols = [
            "Pressure_psia",
            "Temperature_F",
            "Gas_SG",
            "CO2_fraction",
            "N2_fraction",
            "Viscosity_cp",
        ]
        df_model = df_all[model_cols].copy()

        # Remove any rows with missing viscosity
        df_model = df_model.dropna(subset=["Viscosity_cp"])

        # Remove any non-physical values (viscosity should be positive)
        df_model = df_model[df_model["Viscosity_cp"] > 0]

        df_model.to_csv("gas_viscosity_data.csv", index=False)

        # Stats
        hpht_mask = (df_model["Pressure_psia"] > 10000) & (
            df_model["Temperature_F"] > 300
        )
        n_hpht = hpht_mask.sum()

        print(f"\n  {'='*50}")
        print(f"  FINAL DATASET SUMMARY")
        print(f"  {'='*50}")
        print(f"  Total data points:     {len(df_model)}")
        print(f"  HPHT data points:      {n_hpht}")
        print(f"  Non-HPHT data points:  {len(df_model) - n_hpht}")
        print(f"  Methane points:        {len(methane_data)}")
        print(f"  Nitrogen points:       {len(nitrogen_data)}")
        print(f"")
        print(
            f"  Pressure range:  {df_model['Pressure_psia'].min():.0f} - {df_model['Pressure_psia'].max():.0f} psia"
        )
        print(
            f"  Temp range:      {df_model['Temperature_F'].min():.0f} - {df_model['Temperature_F'].max():.0f} F"
        )
        print(
            f"  Viscosity range: {df_model['Viscosity_cp'].min():.6f} - {df_model['Viscosity_cp'].max():.6f} cp"
        )
        print(f"")
        print(f"  Saved: gas_viscosity_data.csv")
        print(f"  This file is ready for dnn_model.py and")
        print(f"  gradient_boosting_model.py")
        print(f"  {'='*50}")
    else:
        print("\n  ERROR: No data was collected. Check your internet connection.")
        print("  You can also try the manual approach at:")
        print("  https://webbook.nist.gov/chemistry/fluid/")

    # Save full dataset with all columns for reference
    if all_data:
        df_full = pd.DataFrame(all_data)
        df_full.to_csv("gas_viscosity_data_full.csv", index=False)
        print(
            f"\n  Also saved: gas_viscosity_data_full.csv (includes density, K, MPa columns)"
        )


if __name__ == "__main__":
    main()
