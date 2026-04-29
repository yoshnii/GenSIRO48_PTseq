# -*- coding: utf-8 -*-
# Quick Fluorescent Measurement Test (PTseq)
#
# PURPOSE: Take a manually prepared fluorescent tube from POS11 (Col 1, Row A),
#          run the fluorescent measurement, read back concentration, and finish.
#          No tip pickup, no mixing — tube is pre-prepared by user.
#
# SETUP: Place your prepared fluorescent tube strip at M2_POS11, Column 1.
#
# OUTPUT:
#   - Prints concentration for all 8 rows (A-H) to console
#   - Saves to D:\data\PTseq_Library.xlsx via output_quantitative_data
#   - Saves to D:\data\quantification_test.txt as backup

from library import *
from datetime import datetime
spxsiro = globals().get("library")
set_siro(spxsiro)

# ============== CONFIGURATION ==============
SAMPLE_TYPE = "dsDNA_HS"
STANDARD_TO_SAMPLE_RATIO = 5

# Tube position: M2_POS11, Column 1, Row 1 (= position A)
QUANT_TUBE_POS = "M2_POS11"
QUANT_TUBE_COL = 1
QUANT_TUBE_ROW = 1

# Output file paths
excel_path = "D:\\data\\PTseq_Library.xlsx"
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
txt_path = f"D:\\data\\quantification_test_{current_datetime}.txt"

# Helper: read concentration from machine memory after measurement
def get_concentration_modified(pos):
    spx_concentration = find_sampling_concentration(pos[0], pos[2], pos[1])
    return spx_concentration.Consistence

# ============== START ==============
home()

print("=" * 60)
print("FLUORESCENT MEASUREMENT - PTseq SINGLE TUBE TEST")
print("=" * 60)
print(f"Position: {QUANT_TUBE_POS}, Col {QUANT_TUBE_COL}")
print(f"Sample Type: {SAMPLE_TYPE}")
print("=" * 60)

try:
    # Step 1: Load tube from POS11 into the reader
    print("\n[1/4] Loading tube from POS11 into reader...")
    p8_load_quantification_tube({
        "Position": QUANT_TUBE_POS,
        "Row": QUANT_TUBE_ROW,
        "Col": QUANT_TUBE_COL,
        "Tips": 8
    })

    # Step 2: Run fluorescent measurement
    print("[2/4] Running fluorescent measurement...")
    spx_quantity_result = quantity_run_sample({
        "Name": "",
        "SampleType": SAMPLE_TYPE,
        "ProductType": "PTseq_Test",
        "StandardToSampleRatio": STANDARD_TO_SAMPLE_RATIO,
        "DilutionRatio": 1,
        "Label": "",
        "DilutionAssessment": 60
    })

    # Step 3: Read back concentration for all 8 rows (A-H)
    print("[3/4] Reading concentrations...")
    concentration_list = [
        get_concentration_modified((QUANT_TUBE_POS, QUANT_TUBE_COL, j))
        for j in range(1, 9)
    ]

    # Unload tube back to POS11
    print("[4/4] Unloading tube back to POS11...")
    p8_unload_quantification_tube({
        "Position": QUANT_TUBE_POS,
        "Row": QUANT_TUBE_ROW,
        "Col": QUANT_TUBE_COL,
        "Tips": 8
    })

    # ============== RESULTS ==============
    print("\n" + "=" * 60)
    print("RESULTS (ng/uL):")
    print("=" * 60)
    row_labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    for label, conc in zip(row_labels, concentration_list):
        print(f"  Row {label}: {conc:.2f} ng/uL")
    print("=" * 60)
    print(f"Your sample (A1): {concentration_list[0]:.2f} ng/uL")
    print("=" * 60)

    # Save to Excel via machine's built-in export
    output_quantitative_data({"ProductType": "PTseq_Test", "FilePath": excel_path})
    print(f"\nExcel saved to: {excel_path}")

    # Save to text file as backup
    with open(txt_path, "w") as f:
        f.write(f"PTseq Fluorescent Measurement - {current_datetime}\n")
        f.write(f"Position: {QUANT_TUBE_POS}, Col {QUANT_TUBE_COL}\n")
        f.write(f"SampleType: {SAMPLE_TYPE}\n")
        f.write("-" * 40 + "\n")
        for label, conc in zip(row_labels, concentration_list):
            f.write(f"Row {label}: {conc}\n")
    print(f"Text backup saved to: {txt_path}")

except Exception as e:
    print("\n" + "=" * 60)
    print(f"ERROR: {e}")
    print("Check: Is the standard curve set up? Run 'SIRO48-Standard curve.py' if not.")
    print("=" * 60)

print("\nTest complete.")
