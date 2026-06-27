# -*- coding: utf-8 -*-
#####################################################################
# Test script: POS7 Col1 -> POS16 Col1 using P8 and one full 300 uL tip rack.
#
# Purpose:
#   Verify the PTplus final-library elution aspirate style on POS7 water.
#
# Deck:
#   Use the paired deck.json copied from current PTseq library-only deck.
#
# Manual setup:
#   POS7 Col1 A-H: water
#   POS16 Col1 A-H: receiving deep-well column
#   Tip positions use the same definitions as current PTseq library-only script.
#
# Behavior:
#   For the first full 300 uL tip rack from tip_300.load(96, 8, 1):
#     1. Load P8 300 uL tips from the current column.
#     2. Aspirate TEST_VOLUME_UL from POS7 Col1 A-H with P8.
#     3. Empty into POS16 Col1 A-H with P8.
#     4. Return the tips to the same tip column.
#
# No delay, wait, temperature, PCR, shaking, or gripper movement.
#####################################################################

from library import *

spxsiro = globals().get("library")
set_siro(spxsiro)

import sys

class Tips:
	def __init__(self,tip_pos,backup_tip_pos=[]):
		self.tip_pos = tip_pos
		self.backup_tip_pos = backup_tip_pos
		self.tip_list = []
		self.blank_tip_list = []
		self.used_tip_set = set()
		for i in range(len(self.tip_pos)):
			self.add_tips(self.tip_pos[i])
	def add_tips(self,target):
		for i in range(1,13):
			self.tip_list.append([8,target,i])
	def refresh_tip_list(self):
		sys.exit('This test uses only the first full tip rack and does not exchange backup tips')
	def load(self, tip_num, tip_num_per_time=8, reuse_index=0):
		result = []
		while tip_num > 0:
			found = 0
			cur_tip_num = min(8, tip_num, tip_num_per_time)
			for i, each in enumerate(self.tip_list):
				x, y, z = each
				if x >= cur_tip_num and (y,z) not in self.used_tip_set:
					x -= cur_tip_num
					self.tip_list[i][0] = x
					if reuse_index == 1:
						self.used_tip_set.add((y,z))
					elif x == 0:
						empty_tip = self.tip_list.pop(i)
						self.blank_tip_list.append((empty_tip[1],empty_tip[2]))
					found = 1
					result.append((y, z, x + 1))
					break
			if not found:
				self.refresh_tip_list()
			else:
				tip_num -= cur_tip_num
		return result
	def reuse(self,n):
		if len(self.blank_tip_list)>=n:
			res = self.blank_tip_list[:n]
			self.blank_tip_list = self.blank_tip_list[n:]
		else:
			res = []
		return res

def p8_load_modified(loc):
	p8_load_tips({"Position":loc[0],"Col":loc[1],"Row":loc[2],"Tips":8})

def p8_unload_modified(loc):
	p8_unload_tips({"Position":loc[0],"Col":loc[1],"Row":loc[2],"Tips":8})

tip_300_loc = ['M2_POS5','M2_POS6']
backup_tip_300_loc = ['M2_POS28','M2_POS29']
tip_300 = Tips(tip_300_loc,backup_tip_300_loc)

tip_1000_loc = ['M2_POS18']
tip_1000 = Tips(tip_1000_loc)

tip_50_loc = ['M2_POS15','M2_POS12']
backup_tip_50_loc = ['M2_POS25','M2_POS19']
tip_50 = Tips(tip_50_loc,backup_tip_50_loc)

home()

SOURCE_POS = "M2_POS7"
SOURCE_COL = 1
SOURCE_START_ROW = 1
DEST_POS = "M2_POS16"
DEST_COL = 1
DEST_START_ROW = 1
TEST_VOLUME_UL = 25

test_tip_columns = tip_300.load(96, 8, 1)

for tip_loc in test_tip_columns:
	p8_load_modified(tip_loc)

	# PTplus final-library elution aspirate parameters, using 300 uL P8 tips.
	p8_aspirate({
		"Position": SOURCE_POS,
		"Col": SOURCE_COL,
		"Row": SOURCE_START_ROW,
		"PreAirVolume": 2,
		"AspirateOffsetOfZ": 0.5,
		"AspirateSpeed": 50,
		"AspirateVolume": TEST_VOLUME_UL,
		"PreAirSpeed": 50,
		"DelayAfterAspirate": 0.5,
		"TipTouchTimes": 0,
		"PostAirSpeed": 50,
		"PostAirVolume": 5,
		"IfTrack": False,
		"FirstSegmentSpeed": 100,
		"SpeedChangeOffsetOfZ": 0,
		"SecondSegmentSpeed": 80
	})

	p8_empty({
		"Position": DEST_POS,
		"Col": DEST_COL,
		"Row": DEST_START_ROW,
		"EmptyOffsetOfZ": 0.8,
		"EmptySpeed": 20,
		"DelayAfterEmpty": 0.8,
		"TipTouchTimes": 0,
		"PostAirSpeed": 50,
		"PostAirVolume": 5,
		"FirstSegmentSpeed": 100,
		"SpeedChangeOffsetOfZ": 0,
		"SecondSegmentSpeed": 80
	})

	p8_unload_modified(tip_loc)

home()
