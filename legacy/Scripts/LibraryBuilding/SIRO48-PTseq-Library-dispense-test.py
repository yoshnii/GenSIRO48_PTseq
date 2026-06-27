
# -*- coding: utf-8 -*-
#####################################################################
# SIRO48-PTseq-Library-dispense-test
#####################################################################
# 测试脚本：验证 T2/T3 cDNA mix 中转分装精度
# P1 从 POS17 Col1 Row1 吸 7µL 分装到 POS7 Col1 Row1-8
# P8 从 POS7 Col1 吸 4µL 分装到 POS20 Col1
# 优化参数：AspirateOffsetOfZ=-0.2, DelayAfterAspirate=3, PostAirVolume=3, TipTouch=2
#####################################################################
#Timestamp:2024/11/18 9:46:21
#Head - 共用头部，包含所有功能。
from library import *
spxsiro = globals().get("library")
set_siro(spxsiro)
import math
"""
不要修改HEAD
"""

home()
def blockA():
	temp_set({"Name":"M2_tempC","Temp": 6.00, "Duration": -1})#4度，POS17
	temp_set({"Name":"M2_tempB","Temp": 6.00, "Duration": -1})#4度，POS10

a = parallel_block(blockA)

'''==================================================================自动计算取枪头位置逻辑v6======================================================'''
import sys
class Tips:
	def __init__(self,tip_pos,backup_tip_pos=[]):
		self.transposition =  "M2_POS30"
		self.tip_pos = tip_pos
		self.backup_tip_pos = backup_tip_pos
		self.tip_list = []
		self.blank_tip_list = []
		self.used_tip_set = set()
		for i in range(len(self.tip_pos)):
			self.add_tips(self.tip_pos[i])
	def exchange(self,x,y):
		print('exchange:',x,y)
		try:
			transfer({"StartPosition":x,"EndPosition":self.transposition,"LoosenOffsetOfZ":0})
			transfer({"StartPosition":y,"EndPosition":x,"LoosenOffsetOfZ":0})
			transfer({"StartPosition":self.transposition,"EndPosition":y,"LoosenOffsetOfZ":0})
			return (x,y)
		except:
		   pass
	def add_tips(self,target):
		for i in range(1,13):
			self.tip_list.append([8,target,i])
	def refresh_tip_list(self):
		if not self.backup_tip_pos:
			sys.exit('No backup tip')
		new_tip_pos = self.backup_tip_pos.pop(0)
		odd_tip_pos = self.tip_pos.pop(0)
		self.tip_pos.append(odd_tip_pos)
		self.tip_list = [tip for tip in self.tip_list if tip[1] != odd_tip_pos]
		self.used_tip_set = {tip for tip in self.used_tip_set if tip[0] != odd_tip_pos}
		self.blank_tip_list = [tip for tip in self.blank_tip_list if tip[1] != odd_tip_pos]
		self.add_tips(odd_tip_pos)
		return new_tip_pos,odd_tip_pos
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
					if reuse_index ==1:
						self.used_tip_set.add((y,z))
					elif x == 0:
						empty_tip = self.tip_list.pop(i)
						self.blank_tip_list.append((empty_tip[1],empty_tip[2]))
					found = 1
					result.append((y, z, x + 1))
					break
			if not found:
				x,y = self.refresh_tip_list()
				self.exchange(x,y)
				pre_l = len(result)
				result = [each for each in result if each[0]!= y]
				cur_l = len(result)
				tip_num += (pre_l-cur_l)*tip_num_per_time
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

def p1_load_modified(loc):
	p1_load_tips({"Position":loc[0],"Col":loc[1],"Row":loc[2],"Tips":1})
def p1_unload_modified(loc):
	p1_unload_tips2({"Position":loc[0],"Col":loc[1],"Row":loc[2],"Tips":1})

tip_50_loc = ['M2_POS15','M2_POS12']
backup_tip_50_loc = ['M2_POS25']
tip_50 = Tips(tip_50_loc,backup_tip_50_loc)

tip_300_loc = ['M2_POS5','M2_POS6']
backup_tip_300_loc = ['M2_POS19','M2_POS28','M2_POS29']
tip_300 = Tips(tip_300_loc,backup_tip_300_loc)

'''==================================================================
    测试参数
=================================================================='''
SampleCount = 48
sample_num = SampleCount
col_num = (sample_num+7)//8

'''==================================================================
    T2/T3 mix 中转分装测试（优化参数）
    Step A: P1 从 POS17 Col1 Row1 吸 7µL 分装到 POS7 Col1 Row1-8
    Step B: P8 从 POS7 Col1 吸 4µL 分装到 POS20 Col1

    优化项：
    - P1 aspirate: AspirateOffsetOfZ -1→-0.2, DelayAfterAspirate 0.5→3,
      PostAirVolume 0→3, TipTouch 0→2
    - P1 empty: EmptyOffsetOfZ -1→1.7
    - P8 aspirate: PreAirVolume 4→8, AspirateOffsetOfZ -1→-0.2
=================================================================='''
lang=get_lang()
if lang==1:
 report({"Phase": "测试", "Step": "T2/T3 mix 中转分装测试（优化参数）", "TaskType": "library", "RemainingTime": None})
elif lang==2:
 report({"Phase": "Test", "Step": "T2/T3 mix intermediate dispense (optimized)", "TaskType": "library", "RemainingTime": None})

# 8样本时的体积计算 (复刻 line 482)
target_volume_list = [7*(SampleCount//8+1)]*(SampleCount%8)+[7*(SampleCount//8)]*(8-SampleCount%8)

# 开试剂盖
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})

# Step A: P1 从 POS17 Col1 Row1 中转到 POS7 Col1 Row1-8
# 优化: AspirateOffsetOfZ=-0.2, DelayAfterAspirate=3, PostAirVolume=3, TipTouch=2, EmptyOffsetOfZ=1.7
p1_load_modified(tip_50.load(1)[0])
for i in range(8):
	p1_aspirate({"Position":"M2_POS17","Col":1,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":-0.2,"AspirateSpeed":10,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":3,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p1_empty({"Position":"M2_POS7","Col":1,"Row":i+1,"EmptyOffsetOfZ":1.7,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# 盖试剂盖
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})

# Step B: P8 从 POS7 Col1 吸 4µL 分装到 POS20 Col1
# 优化: PreAirVolume=8, AspirateOffsetOfZ=-0.2
p8_load_modified(tip_50.load(8)[0])
p8_aspirate({"Position":"M2_POS7","Col":1,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":-0.2,"AspirateSpeed":10,"AspirateVolume":4,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS20","Col":1,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_mix({"Position":"M2_POS20","Col":1,"Row":1,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":0.5,"MixVolume":20,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

lang=get_lang()
if lang==1:
 report({"Phase": "测试", "Step": "测试完成", "TaskType": "library", "RemainingTime": None})
elif lang==2:
 report({"Phase": "Test", "Step": "Test done", "TaskType": "library", "RemainingTime": None})

home()
