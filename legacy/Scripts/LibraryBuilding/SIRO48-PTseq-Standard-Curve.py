
# -*- coding: utf-8 -*-
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
	#temp_set({"Name":"M2_tempB","Temp": 6.00, "Duration": -1})#4度，POS10

a = parallel_block(blockA)

'''==================================================================自动计算取枪头位置逻辑v6======================================================'''
# 更新内容
# 本版本新增reuse指令，可以生成n列没有被使用过的空枪头列，用来放回单根枪头返回值为板，列元组组成的列表
# 本版本修复了自动取枪头枪头盒更换问题



import sys
class Tips:
	def __init__(self,tip_pos,backup_tip_pos=[]):
		self.transposition =  "M2_POS30" # 交换枪头的中转板位
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
	# 将列表中所有枪头依次存入tip_list,存储顺序为剩余枪头数、枪头所在板位、
	def add_tips(self,target):
		for i in range(1,13):
			self.tip_list.append([8,target,i])
	def refresh_tip_list(self):
		'''刷新枪头列表，主要用于清空已使用的枪头列'''
		if not self.backup_tip_pos:
			sys.exit('No backup tip')
		new_tip_pos = self.backup_tip_pos.pop(0)
		odd_tip_pos = self.tip_pos.pop(0)
		self.tip_pos.append(odd_tip_pos)
		self.tip_list = [tip for tip in self.tip_list if tip[1] != odd_tip_pos]
		# while self.tip_list and self.tip_list[0][1] == odd_tip_pos:
		# 	self.tip_list.pop(0)
		# 删除used_tip_set中所有与odd_tip_pos相关的元素
		self.used_tip_set = {tip for tip in self.used_tip_set if tip[0] != odd_tip_pos}
		self.blank_tip_list = [tip for tip in self.blank_tip_list if tip[1] != odd_tip_pos]
		self.add_tips(odd_tip_pos)
		return new_tip_pos,odd_tip_pos
	'''取枪头逻辑：
		依次遍历已有的枪头列，返回可用枪头,返回顺序为板，列，行
		tip_num_per_time:单次取枪头个数，reuse_index：是否复用枪头，为0表示用枪头不复用，为1表示枪头会复用'''
	def load(self, tip_num, tip_num_per_time=8, reuse_index=0):
		result = []  # 用于存储结果的列表
		while tip_num > 0:
			found = 0
			cur_tip_num = min(8, tip_num, tip_num_per_time)
			for i, each in enumerate(self.tip_list):
				# x为当前剩余枪头数，y为当前所在板，z为当前所在列
				x, y, z = each
				#如果当前枪头列没有被占用
				if x >= cur_tip_num and (y,z) not in self.used_tip_set:
					x -= cur_tip_num
					self.tip_list[i][0] = x
					if reuse_index ==1:
						self.used_tip_set.add((y,z))
					elif x == 0:
						empty_tip = self.tip_list.pop(i)
						self.blank_tip_list.append((empty_tip[1],empty_tip[2]))
					found = 1
					# 将结果添加到列表中，而不是yield
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

#===========================================================================优化取枪头逻辑=======================================================================
def p8_load_modified(loc):
	p8_load_tips({"Position":loc[0],"Col":loc[1],"Row":loc[2],"Tips":8})
def p8_unload_modified(loc):
	p8_unload_tips({"Position":loc[0],"Col":loc[1],"Row":loc[2],"Tips":8})

def p1_load_modified(loc):
	p1_load_tips({"Position":loc[0],"Col":loc[1],"Row":loc[2],"Tips":1})
def p1_unload_modified(loc):
	p1_unload_tips2({"Position":loc[0],"Col":loc[1],"Row":loc[2],"Tips":1})

def p8_load_modified_BubblePurge(loc):
	p8_load_tips({"Position":loc[0],"Col":loc[1],"Row":loc[2],"Tips":8,"IsBubblePurge": True, "PreAirSpeed": 100, "PreAirVolume": 20, "BubblePurgeSpeed": 100})


'''============================================================枪头位置=============================================================='''

tip_300_loc = ['M2_POS5','M2_POS6']
backup_tip_300_loc = ['M2_POS19','M2_POS28','M2_POS29']
tip_300 = Tips(tip_300_loc,backup_tip_300_loc)

tip_1000_loc = ['M2_POS18']
tip_1000 = Tips(tip_1000_loc)

tip_50_loc = ['M2_POS15','M2_POS12']
backup_tip_50_loc = ['M2_POS25']
tip_50 = Tips(tip_50_loc,backup_tip_50_loc)


#===========================================================================优化吸液逻辑=======================================================================


def p8_aspirate_modified(Position,Row,Col,AspirateVolume,FirstSegmentSpeed=100,SpeedChangeOffsetOfZ=5,PreAirSpeed=100,SecondSegmentSpeed = 50,\
						 PreAirVolume=10,AspirateSpeed=80,DelayAfterAspirate=0.5,AspirateOffsetOfZ=0.5,\
						 TipTouchTimes=0, TipTouchOffsetOfZ=45.5, TipTouchRangeOfX=1.2,TipTouchSpeed=10.0,PostAirSpeed=50.0, PostAirVolume=0,liquid=0,IfTrack=False):
	if not liquid:
		p8_aspirate({
		"Position": Position, "Row": Row, "Col": Col,
		"FirstSegmentSpeed": FirstSegmentSpeed, "SpeedChangeOffsetOfZ": SpeedChangeOffsetOfZ, "PreAirSpeed": PreAirSpeed, "PreAirVolume": PreAirVolume,
		"SecondSegmentSpeed": SecondSegmentSpeed,   "AspirateOffsetOfZ": AspirateOffsetOfZ, "AspirateSpeed": AspirateSpeed, "AspirateVolume": AspirateVolume, "DelayAfterAspirate": DelayAfterAspirate,
		"TipTouchTimes": TipTouchTimes, "TipTouchOffsetOfZ": TipTouchOffsetOfZ, "TipTouchRangeOfX": TipTouchRangeOfX, "TipTouchSpeed": TipTouchSpeed,
		"PostAirSpeed": PostAirSpeed, "PostAirVolume": PostAirVolume,
		"IfTrack": False})
	else:
		p8_aspirate({"Position": Position, "Row": Row, "Col": Col,'AspirateVolume':AspirateVolume}.update(liquid.aspirate()))

def p1_aspirate_modified(Position,Row,Col,AspirateVolume,FirstSegmentSpeed=100,SpeedChangeOffsetOfZ=5,PreAirSpeed=100,SecondSegmentSpeed = 50,\
						 PreAirVolume=10,AspirateSpeed=80,DelayAfterAspirate=0.5,AspirateOffsetOfZ=0.5,\
						 TipTouchTimes=0, TipTouchOffsetOfZ=45.5, TipTouchRangeOfX=1.2,TipTouchSpeed=10.0,PostAirSpeed=50.0, PostAirVolume=0,liquid=0,IfTrack=False):
	if not liquid:
		p1_aspirate({
		"Position": Position, "Row": Row, "Col": Col,
		"FirstSegmentSpeed": FirstSegmentSpeed, "SpeedChangeOffsetOfZ": SpeedChangeOffsetOfZ, "PreAirSpeed": PreAirSpeed, "PreAirVolume": PreAirVolume,
		"SecondSegmentSpeed": SecondSegmentSpeed,   "AspirateOffsetOfZ": AspirateOffsetOfZ, "AspirateSpeed": AspirateSpeed, "AspirateVolume": AspirateVolume, "DelayAfterAspirate": DelayAfterAspirate,
		"TipTouchTimes": TipTouchTimes, "TipTouchOffsetOfZ": TipTouchOffsetOfZ, "TipTouchRangeOfX": TipTouchRangeOfX, "TipTouchSpeed": TipTouchSpeed,
		"PostAirSpeed": PostAirSpeed, "PostAirVolume": PostAirVolume,
		"IfTrack": False})
	else:
		p1_aspirate({"Position": Position, "Row": Row, "Col": Col,'AspirateVolume':AspirateVolume}.update(liquid.aspirate()))

#===========================================================================优化排空逻辑=======================================================================
def p8_empty_modified(Position,Row,Col,FirstSegmentSpeed= 100, SpeedChangeOffsetOfZ= 0, SecondSegmentSpeed=100,\
EmptyOffsetOfZ=2, EmptySpeed= 100, DelayAfterEmpty= 0.5,
TipTouchTimes= 0, TipTouchOffsetOfZ= 10, TipTouchRangeOfX= 1.2, TipTouchSpeed= 100,
PostAirSpeed= 50.0, PostAirVolume= 5.0,liquid = 0):
	if not liquid:
		p8_empty({
			"Position": Position, "Row": Row, "Col": Col,
			"FirstSegmentSpeed": FirstSegmentSpeed, "SpeedChangeOffsetOfZ": SpeedChangeOffsetOfZ, "SecondSegmentSpeed": SecondSegmentSpeed,
			"EmptyOffsetOfZ": EmptyOffsetOfZ, "EmptySpeed": EmptySpeed, "DelayAfterEmpty": DelayAfterEmpty,
			"TipTouchTimes": TipTouchTimes, "TipTouchOffsetOfZ": TipTouchOffsetOfZ, "TipTouchRangeOfX": TipTouchRangeOfX, "TipTouchSpeed": TipTouchSpeed,
			"PostAirSpeed": PostAirSpeed, "PostAirVolume": PostAirVolume})
	else:
		p8_empty({"Position": Position, "Row": Row, "Col": Col}.update(liquid.empty()))

def p1_empty_modified(Position,Row,Col,FirstSegmentSpeed= 100, SpeedChangeOffsetOfZ= 0, SecondSegmentSpeed=100,\
EmptyOffsetOfZ=2, EmptySpeed= 100, DelayAfterEmpty= 0.5,
TipTouchTimes= 0, TipTouchOffsetOfZ= 10, TipTouchRangeOfX= 1.2, TipTouchSpeed= 100,
PostAirSpeed= 50.0, PostAirVolume= 5.0,liquid = 0):
	if not liquid:
		p1_empty({
			"Position": Position, "Row": Row, "Col": Col,
			"FirstSegmentSpeed": FirstSegmentSpeed, "SpeedChangeOffsetOfZ": SpeedChangeOffsetOfZ, "SecondSegmentSpeed": SecondSegmentSpeed,
			"EmptyOffsetOfZ": EmptyOffsetOfZ, "EmptySpeed": EmptySpeed, "DelayAfterEmpty": DelayAfterEmpty,
			"TipTouchTimes": TipTouchTimes, "TipTouchOffsetOfZ": TipTouchOffsetOfZ, "TipTouchRangeOfX": TipTouchRangeOfX, "TipTouchSpeed": TipTouchSpeed,
			"PostAirSpeed": PostAirSpeed, "PostAirVolume": PostAirVolume})
	else:
		p1_empty({"Position": Position, "Row": Row, "Col": Col}.update(liquid.empty()))




# '''=========================================PCR相关操作==================================================='''
# def pcr_run_method(*args, **kwargs):
	# print('pcr_run_method', args)

# def pcr_open_door(*args, **kwargs):
	# print('pcr_open_door', args)

# def pcr_close_door(*args, **kwargs):
	# print('pcr_close_door', args)
# '''=========================================其他操作==================================================='''
# def output_quantitative_data(*args, **kwargs):
	# print('output_quantitative_data', args, kwargs)

# def delay(*args, **kwargs):
	# print('delay', args, kwargs)

# def get_volume_file(*args, **kwargs):
	# print('get_volume_file', args, kwargs)
	# return [{"SampleWellColumn": 1, "SampleWellRow": 1, "Concentration": 10, "DilutingSampleVolume": 0, "DilutingBufferVolume": 0}]

# def find_sampling_concentration(*args, **kwargs):
	# print('find_sampling_concentration', args, kwargs)
	# class Result:
		# def __init__(self, Consistence):
			# self.Consistence = Consistence
	# return Result(Consistence=20)

# def temp_set(*args, **kwargs):
	# print('temp_set', args)

# def temp_shaker_set(*args, **kwargs):
	# print('temp_shaker_set', args)

# def temp_shaker_stop(*args, **kwargs):
	# print('temp_shaker_stop', args)

# def parallel_block(*args, **kwargs):
	# class Result:
		# def __init__(self):
			# pass
		# def Wait(self):
			# pass
	# return Result()

# def quantity_run_sample(*args, **kwargs):
	# print('quantity_run_sample', args)
	# class Result:
		# def __init__(self, Consistence):
			# self.Consistence = Consistence
	# return Result(Consistence=20)

# def quantity_run_standard(*args, **kwargs):
	# print('quantity_run_standard', args)
	# class Result:
		# def __init__(self, Consistence):
			# self.Consistence = Consistence
	# return Result(Consistence=20)
	
# def p8_load_quantification_tube(*args, **kwargs):
	# print('p8_load_quantification_tube', args)

# def p8_unload_quantification_tube(*args, **kwargs):
	# print('p8_unload_quantification_tube', args, kwargs)

# 试剂放大倍数



'''=====================================标曲制作=============================================================='''

lang=get_lang()
if lang==1: #
 report({"Phase": "定量", "Step": "标曲制作", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Quantification", "Step": "Standard curve", "TaskType": "library", "RemainingTime": None})
 
 
# 染料位置,板位，列，行
dye_loc = ('M2_POS4',1,1)
# 定量标准品1位置,板位，列，行
standard_1_loc = ('M2_POS17',7,1)
# 定量标准品2位置,板位，列，行
standard_2_loc = ('M2_POS17',8,1)
# 分装定量标准品使用枪头位置,列表形式，内置两个位置元组
standard_tip_loc = tip_50.load(2,1) # 例standard_tip = [('M2_POS15', 1, 8), ('M2_POS15', 1, 7)]
# 分装染液并混匀标准品使用枪头位置,列表形式，内置两个位置元组
standard_mix_tip_loc = tip_300.load(16,8) # standard_mix_tip_loc = [('M2_POS6', 1, 1), ('M2_POS6', 2, 1)]
# 定量管位置，列表形式,两列,内置两个位置元组
standard_quantification_tube_loc = [('M2_POS22',1,1),('M2_POS22',2,1)]
# 50枪头混匀标准品除气泡使用枪头位置,列表形式，内置两个位置元组
standard_mix_50_tip_loc = tip_50.load(16,8)
#S2定量管验证位置
quantification_tube_loc = [('M2_POS22',3,1)]

# 样本定量阶段，只支持PCR，Extract，DNB
sample_stage = 'PCR'
#=====================定量浓度输出文件位置======================================
import time
# 获取当前日期和时间
current_datetime = time.strftime("%Y%m%d_%H%M%S")
# 生成文件路径
file_path = f"D:\\data\\SIRO48_Standard_curve.xlsx"
quantification_fila_path = f"D:\\data\\quantification{current_datetime}.txt"

#=================================== 函数计算部分#===================================
col_num = 1
# 本部分为获取特定位置的浓度,pos为位置元组，板列行
def get_concentration_modified(pos):
	# 文档要求输入为板行列，所以对位置数组做一个预处理
	spx_concentration = find_sampling_concentration(pos[0],pos[2],pos[1])
	return spx_concentration.Consistence
# 单个定量管位置，板列行
#quantification_tubes = [(quantification_tube_loc[0],quantification_tube_loc[1]+i//8,1 + i%8) for i in range(sample_num)]

# 用于存储当前定量结果
concentration_list = []

#=============分装两种定量标准品各10 ul到定量管中===============================
if standard_1_loc[0] == 'M2_POS17' or standard_2_loc[0] == 'M2_POS17':
	transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
p8_load_modified(standard_tip_loc[0])
for i in range(8):
	p8_aspirate_modified(standard_1_loc[0], Row=standard_1_loc[2], Col=standard_1_loc[1], AspirateVolume=10)
	p8_empty_modified(standard_quantification_tube_loc[0][0], Row=standard_quantification_tube_loc[0][2]+i, Col=standard_quantification_tube_loc[0][1])
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

p8_load_modified(standard_tip_loc[1])
for i in range(8):
	p8_aspirate_modified(standard_2_loc[0], Row=standard_2_loc[2], Col=standard_2_loc[1], AspirateVolume=10)
	p8_empty_modified(standard_quantification_tube_loc[1][0], Row=standard_quantification_tube_loc[1][2]+i, Col=standard_quantification_tube_loc[1][1])
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

if standard_1_loc[0] == 'M2_POS17' or standard_2_loc[0] == 'M2_POS17':
	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})

# 添加并混匀染液
for i in range(2):
	p8_load_modified(standard_mix_tip_loc[i])
	p8_aspirate_modified(dye_loc[0], Row=dye_loc[2], Col=dye_loc[1], AspirateVolume=190)
	p8_empty_modified(standard_quantification_tube_loc[i][0], Row=1, Col=standard_quantification_tube_loc[i][1],EmptyOffsetOfZ=12)
	p8_mix({"Position":standard_quantification_tube_loc[i][0],"Col":standard_quantification_tube_loc[i][1],"Row":standard_quantification_tube_loc[i][2],"PreAirVolume":0,"MixTimes":10,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":12,"MixVolume":120,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":20,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":2,"PostAirSpeed":50,"PostAirVolume":20,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

#除气泡
for i in range(2):
	p8_load_modified(standard_mix_50_tip_loc[i])
	p8_mix({"Position":standard_quantification_tube_loc[i][0],"Col":standard_quantification_tube_loc[i][1],"Row":standard_quantification_tube_loc[i][2],"PreAirVolume":0,"MixTimes":10,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.5,"MixVolume":40,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":20,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":2,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})


p8_load_quantification_tube({"Position": standard_quantification_tube_loc[0][0], "Row": standard_quantification_tube_loc[0][2], "Col": standard_quantification_tube_loc[0][1], "Tips":8})
quantity_run_standard({"Name":"","ReadTimes":10,"Duration":3,"SampleType":"dsDNA_HS","StandardType":"ST1"})
p8_unload_quantification_tube({"Position": standard_quantification_tube_loc[0][0], "Row": standard_quantification_tube_loc[0][2], "Col": standard_quantification_tube_loc[0][1]})
p8_load_quantification_tube({"Position": standard_quantification_tube_loc[1][0], "Row": standard_quantification_tube_loc[1][2], "Col": standard_quantification_tube_loc[1][1], "Tips":8})
quantity_run_standard({"Name":"","ReadTimes":10,"Duration":3,"SampleType":"dsDNA_HS","StandardType":"ST2"})
p8_unload_quantification_tube({"Position": standard_quantification_tube_loc[1][0], "Row": standard_quantification_tube_loc[1][2], "Col": standard_quantification_tube_loc[1][1]})


transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})

#添加S2定量
p8_load_modified(tip_50.load(1)[0])
for i in range(8):
	p8_aspirate_modified(standard_2_loc[0], Row=standard_2_loc[2], Col=standard_2_loc[1], AspirateVolume=2,AspirateSpeed=5)
	p8_empty_modified(quantification_tube_loc[0][0], Row=quantification_tube_loc[0][2]+i, Col=quantification_tube_loc[0][1],EmptyOffsetOfZ=0.6)
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})

#加染液定量
p8_load_modified(tip_300.load(8)[0])
p8_aspirate_modified(dye_loc[0], Row=dye_loc[2], Col=dye_loc[1], AspirateVolume=198)
p8_empty_modified(quantification_tube_loc[0][0], Row=1, Col=quantification_tube_loc[0][1],EmptyOffsetOfZ=12)
p8_mix({"Position":quantification_tube_loc[0][0],"Col":quantification_tube_loc[0][1],"Row":1,"PreAirVolume":0,"MixTimes":10,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":12,"MixVolume":120,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":20,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":2,"PostAirSpeed":50,"PostAirVolume":20,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

#除气泡&混匀
p8_load_modified(tip_50.load(8)[0])
p8_mix({"Position":quantification_tube_loc[0][0],"Col":quantification_tube_loc[0][1],"Row":1,"PreAirVolume":0,"MixTimes":10,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.5,"MixVolume":40,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":20,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":2,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})


#定量
for i in range(col_num):
	p8_load_quantification_tube({"Position": quantification_tube_loc[0][0], "Row": 1, "Col": quantification_tube_loc[0][1]+i, "Tips":8})
	spx_quantity_result = quantity_run_sample({"Name":"","SampleType": "dsDNA_HS", "ProductType": sample_stage, "StandardToSampleRatio": 5, "DilutionRatio":1,"Label":"","DilutionAssessment": 60})
	cur_concentration_list = [get_concentration_modified((quantification_tube_loc[0][0],quantification_tube_loc[0][1]+i,j)) for j in range(1,9)]
	concentration_list += cur_concentration_list
	p8_unload_quantification_tube({"Position": quantification_tube_loc[0][0], "Row": 1, "Col": quantification_tube_loc[0][1]+i, "Tips":8})
output_quantitative_data({"ProductType":sample_stage,"FilePath":file_path})


#============================输出浓度列表=========================
#==================================以下部分为浓度输出部分===================================
column_size = 8
# 打开文件并写入
try:
	float_array = concentration_list
	with open(quantification_fila_path, "w") as file:
		# 计算需要多少列
		num_columns = (len(float_array) + column_size - 1) // column_size

		# 遍历每一行
		for row in range(column_size):
			# 遍历每一列
			for col in range(num_columns):
				# 计算当前元素的索引
				index = col * column_size + row
				# 如果索引在数组范围内，写入当前元素，否则写入空格
				if index < len(float_array):
					file.write(f"{float_array[index]:<10}")  # 每个浮点数占10个字符宽度，左对齐
				else:
					file.write(" " * 10)  # 如果没有数据，占位空格
			file.write("\n")  # 每行结束后换行
except:
	pass


temp_stop({"Name": "M2_tempC"})