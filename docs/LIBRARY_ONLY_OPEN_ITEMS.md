# Library Only Open Items

Branch: `libraryprep-only-updates`

Purpose: maintain a running list of library-only observations, suspected causes, code changes, and water-run items. This is not limited to one water run.

Status key:

- `observed`: seen in experiment or simulation, not yet fixed.
- `changed`: code has been changed, needs water-run confirmation.
- `candidate`: possible change discussed, not implemented.
- `closed`: verified and no further action needed.

## Current Open Items

| ID | Status | Area | Observation | Current Understanding | Current / Proposed Action | Water-Run Check |
|---|---|---|---|---|---|---|
| LIB-001 | changed | POS7 Col9 cDNA T2/T3 mix | For 34 samples, desktop package staged too much T2/T3 mix and 50 uL tip was overfilled. | Old POS7 dead-volume logic added 10 uL per downstream draw instead of 10 uL per POS7 well. | Code changed so POS7 Col9/Col10/Col11 use `active_cols * draw_volume + 10 uL`. | Water run full path: T2/T3 mix from POS17 to POS7 Col9, then POS7 Col9 to POS20 cDNA reaction wells. Confirm 34-sample Col9 volumes: Row A-B 30 uL, Row C-H 26 uL; 50 uL tip does not overfill; POS20 receives 4 uL/well without bubbles or shortage. |
| LIB-002 | changed | POS7 Col10 TA mix | TA mix to POS7 final row can run low in desktop package; collection tube had little residual. | Desktop package used old dead-volume logic and only 15 uL POS17 collection tube dead volume. New code reduces POS7 staged volume, but collection tube residual should still be watched. | POS7 dead-volume logic changed. No separate TA collection tube dead-volume increase yet. | Confirm POS17 Col4 Row2 TA mix remains sufficient through final POS7 Col10 row. |
| LIB-003 | observed | POS7 ethanol staging | For non-multiple-of-8 sample counts, ethanol staging is by full columns, while later pipetting uses only active tips in final partial column. | For 34 samples, POS7 ethanol staging fills 5 full columns, but final column only uses 2 tips. This increases ethanol consumption but should not harm sample handling if enough ethanol is loaded. | No code change yet. | Confirm final partial column uses only active tips and extra staged ethanol does not affect workflow. |
| LIB-004 | changed | Ethanol waste wet-tip reuse | Reused 300 uL tips can drip when moving from tip rack back to plate after ethanol/waste handling. | Wet reused tips may retain ethanol/waste; BubblePurge on reload can push residual liquid out. | Added high-position extra empty/tip touch in POS11 after TA/LA ethanol waste empty, before returning or discarding tips. | Confirm high empty reduces dripping and does not splash. |
| LIB-005 | changed | POS11 waste high empty | New high empty uses `EmptyOffsetOfZ=30` and `TipTouchOffsetOfZ=30` in POS11 1.3 mL deepwell. | Height may be safe but must be verified against actual deck/consumable geometry and calibration. | Code changed with helper `p8_empty_waste_high`. | Confirm no collision with rim/adjacent wells and no excessive splashing/aerosol. |
| LIB-006 | candidate | Ethanol waste tip reuse policy | Current script reuses the same 300 uL tips across ethanol addition and first waste removal. | PTplus uses similar wet-tip reuse with BubblePurge, so PTplus is not a clean solution for dripping. | If high empty is insufficient, consider not using BubblePurge for wet-tip reload or discarding tips after first waste. | If dripping remains after LIB-004, compare with no-BubblePurge wet-tip reload or no-reuse strategy. |
| LIB-007 | observed | POS7 Col11 LA/PCR mix | T7/T8/T2 LA/PCR mix to POS7 can run short at the last well/last column, with bubbles observed. Similar "last batch/last well short" behavior has repeated in staging steps. | This likely points to POS17 collection tube residual and aspiration behavior, not T7/T8 split itself. Current shared collection tube residual is only 15 uL, and final aspirates can pull air if actual recoverable volume is lower due to wall retention, tip residual, or bubbles. Current script path is POS17 Col4 Row3 to POS7 Col11, then POS7 Col11 to POS20 LA/PCR reaction wells; user also wants this water-run item tracked as "T7/T8 to POS7, then to POS16" because POS16 is the later purification/shaker position to watch. | T7/T8 split remains unchanged for now. Candidate fixes: increase POS17 collection tube residual for reaction mix staging, tune final aspirate height/speed, or add a staged-volume safety factor per POS7 row. | Water run full path: T7/T8/T2 mix from POS17 to POS7 Col11, then downstream transfer from POS7 Col11 to the actual reaction plate position used by the script. Confirm whether the expected target is POS20 or POS16 during the run; watch final row/last column, bubbles, and POS17 Col4 Row3 residual. |

## Notes From Current Calculations

### 34-sample current branch POS7 reaction mix staging

- POS7 Col9 cDNA T2/T3 mix:
  - Row A-B: 30 uL
  - Row C-H: 26 uL
  - Total POS7 staged volume: 216 uL
  - POS17 mix total with 15 uL residual: 231 uL
  - T2/T3 each aspirated by code: 115.5 uL

- POS7 Col10 TA mix:
  - Row A-B: 85 uL
  - Row C-H: 70 uL
  - Total POS7 staged volume: 590 uL
  - POS17 mix total with 15 uL residual: 605 uL
  - T2/T4/T5 aspirated by code: 282.33 / 201.67 / 121.00 uL

- POS7 Col11 LA/PCR mix:
  - Row A-B: 160 uL
  - Row C-H: 130 uL
  - Total POS7 staged volume: 1100 uL
  - POS17 mix total with 15 uL residual: 1115 uL
  - T7/T8/T2 aspirated by code: 743.33 / 44.20 / 334.50 uL

### Desktop package old logic, 34 samples

- POS7 Col10 TA mix:
  - Row A-B: 125 uL
  - Row C-H: 100 uL
  - Total POS7 staged volume: 850 uL
  - POS17 mix total with 15 uL residual: 865 uL
  - T2/T4/T5 aspirated by code: 403.67 / 288.33 / 173.00 uL

## Code Locations

- Main script: `libraryprep/library/SIRO48-PTseq-Library/SIRO48-PTseq-Library.py`
- POS7 reaction mix volume helper: `pos7_reaction_mix_dispense_volume`
- Ethanol waste high-empty helper: `p8_empty_waste_high`
- TA ethanol waste: search `Ligation_purification_tips2`
- LA ethanol waste: search `LA 乙醇洗涤流程`

## Explicit Water-Run Paths To Track

- T2/T3 cDNA mix:
  - `POS17 Col4 Row1` collection tube to `POS7 Col9`
  - `POS7 Col9` to `POS20` cDNA reaction wells
  - Watch for 50 uL tip overfill, bubbles, final-row shortage, and POS17 residual.

- T7/T8/T2 LA/PCR mix:
  - `POS17 Col4 Row3` collection tube to `POS7 Col11`
  - Current script downstream target: `POS7 Col11` to `POS20` LA/PCR reaction wells
  - User-facing water-run concern also names `POS16`; confirm during water run whether any observed transfer reaches POS16 at this stage or only after LA purification begins.
  - Watch for final-row/last-column shortage, bubbles, and POS17 residual.
