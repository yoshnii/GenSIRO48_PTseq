# -*- coding: utf-8 -*-
#####################################################################
# TEST ONLY
# Bead transfer isolation test for GenSIRO48 G99.
# Not for production.
# Intermediate: POS7 Col11.
# Target: POS16 Col1.
# POS7 input volume per well: 70 uL.
# POS7 output volume per well: 50 uL.
# Expected residual volume per well: 20 uL.
# Parameter style: PTplus first-bead-transfer style.
#####################################################################

from library import *
spxsiro = globals().get("library")
set_siro(spxsiro)
import sys


home()


class Tips:
	def __init__(self, tip_pos, backup_tip_pos=[]):
		self.transposition = "M2_POS30"
		self.tip_pos = tip_pos
		self.backup_tip_pos = backup_tip_pos
		self.tip_list = []
		self.blank_tip_list = []
		self.used_tip_set = set()
		for i in range(len(self.tip_pos)):
			self.add_tips(self.tip_pos[i])

	def exchange(self, x, y):
		print("exchange:", x, y)
		try:
			transfer({"StartPosition": x, "EndPosition": self.transposition, "LoosenOffsetOfZ": 0})
			transfer({"StartPosition": y, "EndPosition": x, "LoosenOffsetOfZ": 0})
			transfer({"StartPosition": self.transposition, "EndPosition": y, "LoosenOffsetOfZ": 0})
			return (x, y)
		except:
			pass

	def add_tips(self, target):
		for i in range(1, 13):
			self.tip_list.append([8, target, i])

	def refresh_tip_list(self):
		if not self.backup_tip_pos:
			sys.exit("No backup tip")
		new_tip_pos = self.backup_tip_pos.pop(0)
		odd_tip_pos = self.tip_pos.pop(0)
		self.tip_pos.append(odd_tip_pos)
		self.tip_list = [tip for tip in self.tip_list if tip[1] != odd_tip_pos]
		self.used_tip_set = {tip for tip in self.used_tip_set if tip[0] != odd_tip_pos}
		self.blank_tip_list = [tip for tip in self.blank_tip_list if tip[1] != odd_tip_pos]
		self.add_tips(odd_tip_pos)
		return new_tip_pos, odd_tip_pos

	def load(self, tip_num, tip_num_per_time=8, reuse_index=0):
		result = []
		while tip_num > 0:
			found = 0
			cur_tip_num = min(8, tip_num, tip_num_per_time)
			for i, each in enumerate(self.tip_list):
				x, y, z = each
				if x >= cur_tip_num and (y, z) not in self.used_tip_set:
					x -= cur_tip_num
					self.tip_list[i][0] = x
					if reuse_index == 1:
						self.used_tip_set.add((y, z))
					elif x == 0:
						empty_tip = self.tip_list.pop(i)
						self.blank_tip_list.append((empty_tip[1], empty_tip[2]))
					found = 1
					result.append((y, z, x + 1))
					break
			if not found:
				x, y = self.refresh_tip_list()
				self.exchange(x, y)
				pre_l = len(result)
				result = [each for each in result if each[0] != y]
				cur_l = len(result)
				tip_num += (pre_l - cur_l) * tip_num_per_time
			else:
				tip_num -= cur_tip_num
		return result

	def reuse(self, n):
		if len(self.blank_tip_list) >= n:
			res = self.blank_tip_list[:n]
			self.blank_tip_list = self.blank_tip_list[n:]
		else:
			res = []
		return res


def p8_load_modified(loc):
	p8_load_tips({"Position": loc[0], "Col": loc[1], "Row": loc[2], "Tips": 8})


def p1_load_modified(loc):
	p1_load_tips({"Position": loc[0], "Col": loc[1], "Row": loc[2], "Tips": 1})


tip_300 = Tips(["M2_POS5", "M2_POS6"], ["M2_POS19", "M2_POS28", "M2_POS29"])
tip_1000 = Tips(["M2_POS18"])

SampleCount = 8
sample_num = 8
col_num = 1

bead_stock = {"Position": "M2_POS24", "Col": 1, "Row": 1}
pos7_beads = {"Position": "M2_POS7", "Col": 11, "Row": 1}
target_plate = {"Position": "M2_POS16", "Col": 1, "Row": 1}
pos7_input_volume = 70
pos7_output_volume = 50

test_name = "TEST_PTplus_style_beads_50ul_POS24_POS7_POS23"
parameter_style = "PTplus first-bead-transfer style"
print(test_name)
print("SampleCount = {}".format(SampleCount))
print("intermediate = {} Col{}".format(pos7_beads["Position"], pos7_beads["Col"]))
print("target = {} Col{}".format(target_plate["Position"], target_plate["Col"]))
print("POS7 pre-dispense per well = {} uL".format(pos7_input_volume))
print("POS7 aspirate volume = {} uL".format(pos7_output_volume))
print("expected POS7 residual = {} uL/well".format(pos7_input_volume - pos7_output_volume))
print("parameter style = {}".format(parameter_style))
report({"Phase": test_name, "Step": parameter_style, "TaskType": "library", "RemainingTime": None})


p1_load_modified(tip_1000.load(1)[0])
p1_mix({"Position": bead_stock["Position"], "Col": bead_stock["Col"], "Row": bead_stock["Row"], "PreAirVolume": 10, "MixTimes": 20, "MixAspirateSpeed": 300, "MixAspirateOffsetOfZ": 0.8, "MixVolume": 900, "MixDispenseOffsetOfZ": 0.8, "MixDispenseSpeed": 400, "DelayAfterMixLoop": 1, "MixEmptyOffsetOfZ": 10, "MixEmptySpeed": 50, "PreAirSpeed": 100, "DelayAfterMixAspirate": 0, "DelayAfterMixDispense": 0, "DelayAfterMixEmpty": 2, "TipTouchTimes": 0, "PostAirSpeed": 100, "PostAirVolume": 0, "FirstSegmentSpeed": 190, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100})
p1_mix({"Position": bead_stock["Position"], "Col": bead_stock["Col"], "Row": bead_stock["Row"], "PreAirVolume": 10, "MixTimes": 20, "MixAspirateSpeed": 300, "MixAspirateOffsetOfZ": 1, "MixVolume": 900, "MixDispenseOffsetOfZ": 30, "MixDispenseSpeed": 400, "DelayAfterMixLoop": 1, "MixEmptyOffsetOfZ": 30, "MixEmptySpeed": 50, "PreAirSpeed": 100, "DelayAfterMixAspirate": 0, "DelayAfterMixDispense": 0, "DelayAfterMixEmpty": 15, "TipTouchTimes": 3, "PostAirSpeed": 100, "PostAirVolume": 0, "FirstSegmentSpeed": 190, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100, "TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
for i in range(8):
	p1_aspirate({"Position": bead_stock["Position"], "Col": bead_stock["Col"], "Row": bead_stock["Row"], "PreAirVolume": 5, "AspirateOffsetOfZ": 0.8, "AspirateSpeed": 50, "AspirateVolume": pos7_input_volume, "PreAirSpeed": 50, "DelayAfterAspirate": 2, "PostAirSpeed": 50, "PostAirVolume": 5, "IfTrack": False, "FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 50, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p1_empty({"Position": pos7_beads["Position"], "Col": pos7_beads["Col"], "Row": pos7_beads["Row"] + i, "EmptyOffsetOfZ": 2, "LiquidLevelDetection": "None", "EmptySpeed": 100, "DelayAfterEmpty": 0.5, "TipTouchTimes": 1, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 2, "TipTouchSpeed": 50, "PostAirSpeed": 100, "PostAirVolume": 5, "FirstSegmentSpeed": 190, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100})
p1_unload_tips2({"Position": "M2_Trash", "Col": None, "Row": None})

p8_tip = tip_300.load(8)[0]
p8_load_modified(p8_tip)
p8_aspirate({"Position": pos7_beads["Position"], "Col": pos7_beads["Col"], "Row": pos7_beads["Row"], "PreAirVolume": 35, "AspirateOffsetOfZ": 0.9, "AspirateSpeed": 50, "AspirateVolume": pos7_output_volume, "PreAirSpeed": 50, "DelayAfterAspirate": 1, "PostAirSpeed": 50, "PostAirVolume": 10, "IfTrack": False, "FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "TipTouchTimes": 3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.4, "TipTouchSpeed": 100})
p8_dispense({"Position": target_plate["Position"], "Col": target_plate["Col"], "Row": target_plate["Row"], "FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "DispenseOffsetOfZ": 0.8, "DispenseSpeed": 30, "DispenseVolume": pos7_output_volume, "DelayAfterDispense": 1, "IsEmpty": True, "EmptyOffsetOfZ": 2, "EmptySpeed": 30, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position": "M2_Trash", "Col": None, "Row": None})
