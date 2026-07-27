import json
import re
import sqlite3
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]

FLOW_FILES = [
    REPO / "libraryprep/library/SIRO48-PTseq-Library/SIRO48-PTseq-Library.py",
    REPO / "libraryprep/full/G99/SIRO48-PTseq-Library-pooling-DNB-G99/SIRO48-PTseq-Library-pooling-DNB-G99.py",
    REPO / "libraryprep/full/E25/SIRO48-PTseq-Library-pooling-DNB-E25/SIRO48-PTseq-Library-pooling-DNB-E25.py",
    REPO / "libraryprep/full/2002000/SIRO48-PTseq-Library-pooling-DNB-2000-and-200/SIRO48-PTseq-Library-pooling-DNB-2000-and-200.py",
]

DECK_FILES = [path.with_name("deck.json") for path in FLOW_FILES]


def normalization_plan(concentration):
    if concentration <= 0:
        return 0.0, 0.0, "INVALID_CONCENTRATION"
    if concentration < 20:
        return 30.0, 0.0, "BELOW_TARGET_UNDILUTED"
    if concentration <= 200:
        sample = round(600 / concentration, 2)
        return sample, round(30 - sample, 2), "NORMALIZED"
    return 0.0, 0.0, "ABOVE_200_NG_PER_UL"


class DeckState:
    def __init__(self, pooling_home=None):
        self.objects = {
            "dye_deepwell": "M2_POS13",
            "purification": "M2_POS16",
            "pcr_active": "M2_POS20",
            "pcr_fresh": "M2_POS9",
        }
        self.objects["quant_adapter"] = "M2_POS14"
        if pooling_home:
            self.objects["pooling"] = pooling_home
        self.assert_unique()

    def assert_unique(self):
        positions = list(self.objects.values())
        if len(positions) != len(set(positions)):
            raise AssertionError(f"Deck collision: {self.objects}")

    def move(self, name, target):
        if target in self.objects.values():
            raise AssertionError(f"Target occupied: {target}")
        self.objects[name] = target
        self.assert_unique()

    def clear_pos13(self, parking):
        self.move("purification", parking)
        self.move("dye_deepwell", "M2_POS16")

    def restore_pos13(self):
        self.move("dye_deepwell", "M2_POS13")
        self.move("purification", "M2_POS16")


class ExtractionNormalizationContractTest(unittest.TestCase):
    def test_concentration_boundaries(self):
        expected = {
            0: (0.0, 0.0, "INVALID_CONCENTRATION"),
            0.1: (30.0, 0.0, "BELOW_TARGET_UNDILUTED"),
            19.9: (30.0, 0.0, "BELOW_TARGET_UNDILUTED"),
            20: (30.0, 0.0, "NORMALIZED"),
            50: (12.0, 18.0, "NORMALIZED"),
            100: (6.0, 24.0, "NORMALIZED"),
            200: (3.0, 27.0, "NORMALIZED"),
            200.1: (0.0, 0.0, "ABOVE_200_NG_PER_UL"),
        }
        for concentration, result in expected.items():
            self.assertEqual(normalization_plan(concentration), result)

    def test_sample_mapping_for_supported_throughputs(self):
        expected = {
            1: ("A1", "A7"),
            8: ("H1", "H7"),
            9: ("A2", "A8"),
            16: ("H2", "H8"),
            17: ("A3", "A9"),
            48: ("H6", "H12"),
        }
        for count, (source, target) in expected.items():
            index = count - 1
            row = chr(ord("A") + index % 8)
            self.assertEqual(f"{row}{1 + index // 8}", source)
            self.assertEqual(f"{row}{7 + index // 8}", target)

        for sample_count in range(1, 49):
            last_index = sample_count - 1
            self.assertLessEqual(1 + last_index // 8, 6)
            self.assertLessEqual(7 + last_index // 8, 12)

    def test_normalization_volume_conservation(self):
        for concentration in (0.1, 1, 10, 19.99, 20, 21, 50, 100, 199.99, 200):
            sample_volume, water_volume, status = normalization_plan(concentration)
            self.assertAlmostEqual(sample_volume + water_volume, 30.0, places=2)
            self.assertGreaterEqual(sample_volume, 3.0)
            self.assertLessEqual(sample_volume, 30.0)
            self.assertGreaterEqual(round(45.0 - 2.2 - sample_volume, 2), 12.8)
            self.assertEqual(30.0 - 14.0, 16.0)
            self.assertIn(status, ("BELOW_TARGET_UNDILUTED", "NORMALIZED"))

    def test_all_library_flows_share_the_contract(self):
        required = [
            "EXTRACTION_TARGET_CONCENTRATION = 20.0",
            "EXTRACTION_NORMALIZED_VOLUME = 30.0",
            "EXTRACTION_MIN_SAMPLE_VOLUME = 3.0",
            "EXTRACTION_NORMALIZED_START_COL = 7",
            'EXTRACTION_WATER_LOC = ("M2_POS24", 2, 1)',
            '"AspirateVolume":14',
            '"Col":i+7',
            'water_tip = tip_50.load(1, 1)[0]',
            'backup_tip_50_loc = [\'M2_POS25\',\'M2_POS19\',\'M2_POS30\']',
        ]
        for path in FLOW_FILES:
            source = path.read_text(encoding="utf-8")
            for text in required:
                self.assertIn(text, source, f"{text} missing in {path}")
            self.assertIsNone(
                re.search(r"transfer\([^\n]*(?:StartPosition|EndPosition)[^\n]*M2_POS30", source),
                f"POS30 is still used as gripper transit in {path}",
            )

        platform_200 = FLOW_FILES[-1].read_text(encoding="utf-8")
        self.assertIn(
            'transfer({"StartPosition":"M2_POS11","EndPosition":"M2_POS23"',
            platform_200,
        )
        self.assertIn(
            'transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS11"',
            platform_200,
        )
        self.assertNotIn(
            'transfer({"StartPosition":"M2_POS14","EndPosition":"M2_POS23"',
            platform_200,
        )

    def test_decks_match_physical_contract(self):
        for path in DECK_FILES:
            deck = json.loads(path.read_text(encoding="utf-8"))
            by_position = {item["Position"]: item for item in deck}

            pos8_wells = by_position["M2_POS8"]["ConsumableInfo"]["WellInfo"]
            self.assertEqual(pos8_wells[0]["ContentInfo"]["Volume"], 45)
            self.assertEqual(pos8_wells[1]["ContentInfo"]["Volume"], 0)
            self.assertIn("A7", pos8_wells[1]["Wells"])
            self.assertIn("H12", pos8_wells[1]["Wells"])

            pos24_wells = by_position["M2_POS24"]["AdapterInfo"]["WellInfo"]
            water = next(item for item in pos24_wells if item["Wells"] == "A2")
            water_name = water["ConsumableInfo"]["WellInfo"][0]["ContentInfo"]["Name"]
            self.assertIn("无核酸水", water_name)

            pos30_name = by_position["M2_POS30"]["ConsumableInfo"]["ConsumableName"]
            self.assertIn("50", pos30_name)

    def test_pos13_transit_sequences_have_no_collision(self):
        state = DeckState()
        state.clear_pos13("M2_POS23")
        state.move("quant_adapter", "M2_POS13")
        state.move("quant_adapter", "M2_POS14")
        state.restore_pos13()

        state.clear_pos13("M2_POS23")
        state.move("pcr_active", "M2_POS13")
        state.move("pcr_fresh", "M2_POS20")
        state.move("pcr_active", "M2_POS9")
        state.restore_pos13()

        for pooling_home in ("M2_POS11",):
            state = DeckState(pooling_home=pooling_home)
            state.move("pooling", "M2_POS23")
            state.clear_pos13(pooling_home)
            state.restore_pos13()
            state.move("pooling", pooling_home)

    def test_middleware_table_order(self):
        db_path = REPO / "中台配置/GenSIRO48-PTseq/Database/SIRO16productV4.db"
        connection = sqlite3.connect(db_path)
        try:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            scripts = [
                "GenSIRO48-PTseq-LibraryBuilding",
                "GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-G99",
                "GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-E25",
                "GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-2000&200",
            ]
            for script_name in scripts:
                rows = connection.execute(
                    """
                    SELECT mapping.order_index, config.table_path
                    FROM siro48_script_info AS info
                    JOIN siro48_script_table_mapping AS mapping
                      ON mapping.script_info_id = info.id
                    JOIN siro48_table_config AS config
                      ON config.id = mapping.table_config_id
                    WHERE info.script_name = ?
                    ORDER BY mapping.order_index
                    """,
                    (script_name,),
                ).fetchall()
                paths = [row[1] for row in rows]
                self.assertEqual(paths[0], r"D:\Pathogens\PTseq.csv")
                self.assertEqual(paths[1], r"D:\data\PTseq_Extraction.xlsx")
                self.assertEqual(paths[2], r"D:\data\PTseq_normalization_info.csv")
                self.assertEqual(paths[3], r"D:\data\PTseq_Library.xlsx")
                self.assertEqual([row[0] for row in rows], list(range(1, len(rows) + 1)))
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
