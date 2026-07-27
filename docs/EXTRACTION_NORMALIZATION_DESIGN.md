# PTseq extraction-product normalization design

## Scope

This branch adds extraction-product quantification and normalization before PTseq
library preparation. Extraction still recovers 45 uL per sample. Quantification and
normalization run on the library module because the extraction module has no Qubit
reader.

## Liquid contract

- Extraction product: 45 uL per sample.
- Quantification sample: 2.2 uL from POS8 Col1-6.
- Target concentration: 20 ng/uL.
- Normalized product target volume: 30 uL in POS8 Col7-12.
- Library input: 14 uL from POS8 Col7-12.
- Concentration below 20 ng/uL: transfer 30 uL undiluted and report the measured
  concentration.
- Concentration from 20 to 200 ng/uL: sample volume is `600 / concentration` uL;
  nuclease-free water is `30 - sample volume` uL.
- Concentration above 200 ng/uL or a missing/non-positive result: stop before
  normalization. This keeps automated sample transfers at or above 3 uL.
- Each sample uses one dedicated 50 uL tip to transfer into the normalized well
  and mix the 30 uL product five times at a 25 uL mix volume.
- Normalization water uses one dedicated 50 uL tip reused only between empty
  target wells; the 0-27 uL water range is not handled by a 1000 uL tip.

## Deck contract

- POS8 Col1-6: extraction products.
- POS8 Col7-12: normalized extraction products.
- POS14 quantification tubes Col7-12: extraction-product quantification.
- POS14 quantification tubes Col1-6: final library quantification.
- POS24 A2 (`Col=2, Row=1`): nuclease-free normalization water.
- POS24 B1 (`Col=1, Row=2`): existing T2 buffer; it is not replaced by the
  normalization water.
- POS30: fifth 50 uL tip rack.
- POS13: temporary gripper transit after its deepwell plate is parked at POS16.
- POS16/POS23: default tracked positions of the purification deepwell plate.
- During full-process pooling, all three platforms move the POS11 deepwell plate
  to POS23 and use the vacated POS11 as the temporary purification-plate parking
  position. POS14 remains the quantification-tube adapter; this prevents the
  extraction-quantification tubes in Col7-12 from colliding with 200/2000 pooling.

PCR plates never use POS16. During the POS20/POS9 PCR plate exchange, the POS13
deepwell plate is parked at POS16, and POS13 is used as the PCR transit position.

## Output files

- `D:\\data\\PTseq_Extraction_Product.csv`: extraction product recovery manifest.
- `D:\\data\\PTseq_Extraction.xlsx`: Qubit extraction-product concentrations.
- `D:\\data\\PTseq_normalization_info.csv`: sample and water volumes plus status.
- `D:\\data\\PTseq_Library.xlsx`: final library quantification (unchanged).

## Middleware contract

- The library-only and three full-process scripts register extraction
  quantification and normalization output tables before the final library output.
- Middleware `is_harmonize_cen` remains disabled for PTseq. Normalization is
  executed by the Python workflow; enabling middleware normalization would apply
  a second, conflicting dilution step.
- The middleware library deck image must show POS24 A2 water, POS14
  quantification tubes, POS19/POS25/POS30 50 uL tip racks, and POS13 as managed
  transit rather than POS30.

## Validation gates

- Python syntax and deck JSON validation.
- No POS30 gripper-transit operations remain.
- POS13 transit always parks and restores its deepwell plate.
- Tip and volume simulation for sample counts 1-48.
- Mechanical water run for tip-rack exchange through POS13.
- Mechanical water run for PCR plate exchange through POS13.
- Qubit Col7-12 and 30 uL normalization water run before biological validation.
