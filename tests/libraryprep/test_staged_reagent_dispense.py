"""Offline checks for staged T2 and ethanol distribution in library scripts."""

import ast
import json
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIBRARY_SCRIPTS = [
    "libraryprep/library/SIRO48-PTseq-Library/GenSIRO48-PTseq-LibraryBuilding.py",
    "libraryprep/full/G99/SIRO48-PTseq-Library-pooling-DNB-G99/GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-G99.py",
    "libraryprep/full/E25/SIRO48-PTseq-Library-pooling-DNB-E25/GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-E25.py",
    "libraryprep/full/2002000/SIRO48-PTseq-Library-pooling-DNB-2000-and-200/GenSIRO48-PTseq-LibraryBuilding&SequencingPrep-2000&200.py",
]
POOLING_SCRIPTS = [
    LIBRARY_SCRIPTS[1],
    "libraryprep/sequencingprep/G99/SIRO48-PTseq-SequencingPrep-G99/GenSIRO48-PTseq-SequencingPrep-G99.py",
    "libraryprep/sequencingprep/2002000/SIRO48-PTseq-SequencingPrep-2000-and-200/GenSIRO48-PTseq-SequencingPrep-2000&200.py",
]


def function_namespace(tree, names, **environment):
    definitions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    namespace = dict(environment)
    exec(compile(ast.fix_missing_locations(ast.Module(definitions, [])), "<isolated>", "exec"), namespace)
    return namespace


class FakeTips:
    def __init__(self):
        self.consumed = 0

    def load(self, count, *_):
        self.consumed += count
        return [("M2_POS18", 1, 1)]


def dict_argument(call):
    if not call.args or not isinstance(call.args[0], ast.Dict):
        return {}
    return {
        key.value: value for key, value in zip(call.args[0].keys, call.args[0].values)
        if isinstance(key, ast.Constant)
    }


class StagedReagentDispenseTest(unittest.TestCase):
    def test_t2_phase_budget_and_placement(self):
        for relative_path in LIBRARY_SCRIPTS:
            tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
            with self.subTest(script=relative_path):
                for sample_count in (1, 8, 9, 16, 24, 32, 40, 48):
                    with self.subTest(samples=sample_count):
                        tips = FakeTips()
                        aspirates, dispenses = [], []
                        namespace = function_namespace(
                            tree, {"active_col_count_for_row", "dispense_t2_to_pos7"},
                            SampleCount=sample_count, c=1.4, tip_1000=tips,
                            p1_load_modified=lambda _: None,
                            p1_unload_tips2=lambda _: None,
                            p1_aspirate=lambda request: aspirates.append(request),
                            p1_empty=lambda request: dispenses.append(request),
                        )
                        namespace["dispense_t2_to_pos7"](25)
                        split = len(aspirates)
                        namespace["dispense_t2_to_pos7"](23)
                        self.assertEqual(tips.consumed, 2)
                        self.assertAlmostEqual(
                            sum(request["AspirateVolume"] for request in aspirates),
                            48 * 1.4 * sample_count,
                        )
                        self.assertEqual(len(aspirates), len(dispenses))
                        self.assertTrue(all(r["Position"] == "M2_POS24" and r["Col"] == 1 and r["Row"] == 2 for r in aspirates))
                        self.assertTrue(all(r["Position"] == "M2_POS7" and r["Col"] == 7 for r in dispenses))
                        for stage, destinations, per_sample in (
                            (aspirates[:split], dispenses[:split], 25),
                            (aspirates[split:], dispenses[split:], 23),
                        ):
                            row_volumes = {
                                destination["Row"]: request["AspirateVolume"]
                                for request, destination in zip(stage, destinations)
                            }
                            for row in range(8):
                                expected = per_sample * 1.4 * namespace["active_col_count_for_row"](sample_count, row)
                                self.assertAlmostEqual(row_volumes.get(row + 1, 0), expected)

                stage_calls = [
                    node for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "dispense_t2_to_pos7"
                ]
                self.assertEqual(sorted(node.args[0].value for node in stage_calls), [23, 25])
                la_call = next(node for node in stage_calls if node.args[0].value == 23)
                la_wash = next(
                    node for node in tree.body if isinstance(node, ast.For)
                    and any(
                        isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                        and call.func.id == "p8_aspirate"
                        and isinstance(dict_argument(call).get("Position"), ast.Subscript)
                        and "ethanol_pos" in ast.unparse(dict_argument(call)["Position"])
                        for call in ast.walk(node)
                    )
                )
                self.assertGreater(la_call.lineno, la_wash.lineno)
                self.assertLess(la_call.lineno, la_wash.end_lineno)
                self.assertIn(
                    "LA_ethanol_predispense_wait",
                    {target.id for node in tree.body if isinstance(node, ast.Assign)
                     for target in node.targets if isinstance(target, ast.Name)},
                )
                la_predispense = next(
                    node for node in tree.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == "LA_ethanol_predispense_wait"
                            for target in node.targets)
                )
                la_wait = next(
                    node for node in tree.body if isinstance(node, ast.Expr)
                    and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
                    and isinstance(node.value.func.value, ast.Name)
                    and node.value.func.value.id == "LA_ethanol_predispense_wait"
                    and node.value.func.attr == "Wait"
                )
                la_supernatant = next(
                    node for node in ast.walk(tree) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name) and node.func.id == "p8_aspirate"
                    and isinstance(dict_argument(node).get("AspirateVolume"), ast.Constant)
                    and dict_argument(node)["AspirateVolume"].value == 85
                )
                self.assertLess(la_predispense.lineno, la_wait.lineno)
                self.assertLess(la_wait.lineno, la_supernatant.lineno)

    def test_ethanol_phase_budget_and_source_capacity(self):
        for relative_path in LIBRARY_SCRIPTS:
            path = ROOT / relative_path
            tree = ast.parse(path.read_text(encoding="utf-8"))
            deck = json.loads(path.with_name("deck.json").read_text(encoding="utf-8"))
            pos3 = next(position for position in deck if position["Position"] == "M2_POS3")
            self.assertIn("A1,A2,A3", pos3["AdapterInfo"]["WellInfo"][0]["Wells"])
            reservoir = pos3["AdapterInfo"]["WellInfo"][0]["ConsumableInfo"]
            self.assertEqual(reservoir["ConsumableName"], "Single Reservoir, 50mL")
            self.assertGreaterEqual(reservoir["WellInfo"][0]["ContentInfo"]["Volume"], 39000)
            with self.subTest(script=relative_path):
                tip_loads = [
                    node for node in ast.walk(tree) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute) and node.func.attr == "load"
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == "tip_1000"
                ]
                # Include a second call to each staged helper and conservatively count
                # every branch's literal load plus up to three DNB-specific tips.
                upper_bound = sum(
                    node.args[0].value if isinstance(node.args[0], ast.Constant) else 3
                    for node in tip_loads
                ) + 9
                self.assertLessEqual(upper_bound, 96)
                for sample_count in (8, 16, 24, 32, 40, 48):
                    with self.subTest(samples=sample_count):
                        tips = FakeTips()
                        aspirates, dispenses = [], []
                        namespace = function_namespace(
                            tree, {"predispense_ethanol_to_pos7"},
                            col_num=(sample_count + 7) // 8, tip_1000=tips,
                            p8_load_modified=lambda _: None,
                            p8_unload_tips=lambda _: None,
                            p8_aspirate=lambda request: aspirates.append(request),
                            p8_empty=lambda request: dispenses.append(request),
                        )
                        namespace["predispense_ethanol_to_pos7"](1)
                        namespace["predispense_ethanol_to_pos7"](2)
                        self.assertEqual(tips.consumed, 16)
                        self.assertEqual(len(aspirates), len(dispenses))
                        per_well = defaultdict(float)
                        for request, destination in zip(aspirates, dispenses):
                            self.assertEqual(request["Position"], "M2_POS3")
                            self.assertEqual(destination["Position"], "M2_POS7")
                            self.assertLessEqual(request["AspirateVolume"], 195)
                            per_well[(request["Col"], destination["Col"])] += request["AspirateVolume"]
                        for source in (1, 2):
                            stage = [request for request in aspirates if request["Col"] == source]
                            self.assertEqual(8 * sum(r["AspirateVolume"] for r in stage), 500 * 8 * ((sample_count + 7) // 8))
                            self.assertLessEqual(8 * sum(r["AspirateVolume"] for r in stage) + 15000, 50000)
                            for col in range(1, (sample_count + 7) // 8 + 1):
                                self.assertEqual(per_well[(source, col)], 500)
                        self.assertLessEqual(500 - 400 + 500, 1300)

    def test_pos8_pooling_mix_has_one_tip_touch(self):
        for relative_path in POOLING_SCRIPTS:
            tree = ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))
            with self.subTest(script=relative_path):
                matches = [
                    dict_argument(node) for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "p8_mix"
                    and isinstance(dict_argument(node).get("Position"), ast.AST)
                    and (
                        "DilutingWellPosition" in ast.unparse(dict_argument(node)["Position"])
                        or "dilution_access_position" in ast.unparse(dict_argument(node)["Position"])
                    )
                ]
                self.assertEqual(len(matches), 1)
                self.assertEqual(matches[0]["TipTouchTimes"].value, 1)


if __name__ == "__main__":
    unittest.main()
