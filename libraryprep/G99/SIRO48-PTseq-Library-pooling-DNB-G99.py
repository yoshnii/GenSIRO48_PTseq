
# -*- coding: utf-8 -*-
#####################################################################
# Version: v9
# Created: 2026 Feb 10
#####################################################################
#Timestamp:2026 Apr 05 
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
# Temperature control runs in the background; do not block protocol start.

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

'''============================================================Shaker Swap Logic=============================================================='''
# M2_POS16 and M2_POS23 act as shared hubs for orbital shaking and magnetization
# This function implements temporary "shaker swap" to move plates to shaker, mix, and return to home
# POS30 是专用的中转位，用于在换板过程中临时存放板子，以避免与其他操作产生冲突

def shaker_swap(target_plate_pos, operation_callback, current_shaker_occupant=None):
	"""
	Perform a shaker swap operation

	Args:
		target_plate_pos: Position of the plate that needs mixing (e.g., 'M2_POS13' or 'M2_POS14')
		operation_callback: Function to execute while plate is on shaker
		current_shaker_occupant: Current plate on M2_POS16 (if any, e.g., 'M2_POS23')
	"""
	# Step 1: If shaker is occupied, move current occupant to transit spot (M2_POS30)
	if current_shaker_occupant:
		transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS30","LoosenOffsetOfZ":0})

	# Step 2: Move target plate to shaker (M2_POS16)
	transfer({"StartPosition":target_plate_pos,"EndPosition":"M2_POS16","LoosenOffsetOfZ":0})

	# Step 3: Execute the mixing/shaking operation
	operation_callback()

	# Step 4: Return target plate to its home position
	transfer({"StartPosition":"M2_POS16","EndPosition":target_plate_pos,"LoosenOffsetOfZ":0})

	# Step 5: If there was an occupant, restore it to shaker
	if current_shaker_occupant:
		transfer({"StartPosition":"M2_POS30","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})

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


# v12: POS7 reaction-mix capped dead-volume curve.
# Used by POS7 Col 9 cDNA synthesis mix, Col 10 TA Master Mix, and Col 11 LA/PCR Master Mix.
#   downstream_total = p8_volume_per_column * active_col_count_for_row
#   extra            = clamp(downstream_total * 0.2, min=10, max=30)
#   pos7_dispense    = downstream_total + extra
# NOT applied to magnetic beads, ethanol, mineral oil, T2/elution buffer, Qubit, or DNB.
def clamp_value(value, lower, upper):
	return max(lower, min(value, upper))

def active_col_count_for_row(sample_count, row_index):
	full_cols = sample_count // 8
	remainder = sample_count % 8
	return full_cols + (1 if remainder != 0 and row_index < remainder else 0)

def pos7_reaction_mix_dispense_volume(p8_volume_per_column, sample_count, row_index, min_dead=10, ratio=0.2, max_dead=30):
	active_cols = active_col_count_for_row(sample_count, row_index)
	downstream_total = p8_volume_per_column * active_cols
	if downstream_total <= 0:
		return 0
	extra = clamp_value(downstream_total * ratio, min_dead, max_dead)
	return downstream_total + extra

# v12: 2 mL mixing-tube dead volume retained after P1 dispenses to POS7.
MIX_TUBE_DEAD_VOLUME = 15

# Low-throughput P1 direct branch threshold for this feature branch.
LOW_THROUGHPUT_P1_DIRECT_MAX_SAMPLE_COUNT = 16

def use_low_throughput_p1_direct(sample_count):
	return sample_count <= LOW_THROUGHPUT_P1_DIRECT_MAX_SAMPLE_COUNT

def active_sample_wells(sample_count):
	column_count = (sample_count + 7) // 8
	for col_index in range(column_count):
		active_rows = 8 if (col_index < column_count - 1 or sample_count % 8 == 0) else sample_count % 8
		for row in range(1, active_rows + 1):
			yield col_index, row

def report_low_throughput_branch(section, direct_branch, sample_count):
	branch_name = "P1 50 uL direct" if direct_branch else "original POS7/P8"
	message = f"{section}: {branch_name} branch selected; SampleCount={sample_count}"
	print(f"[LOW_THROUGHPUT_P1_DIRECT] {message}")
	report({"Phase":"LOW_THROUGHPUT_P1_DIRECT","Step":message,"TaskType":"library","RemainingTime":None})


'''=====================================样本信息读取____建库仪====================================='''
# 该代码用于读取样本信息文件，并将每一行数据存储为一个 Sample 对象
# 该代码使用了 Python 的内置库，不需要额外安装任何库

# ================================输入部分=============================================

# 样本信息文件位置
sample_info_file_path = r'D:/Pathogens/PTseq.csv'
# 是否有样本孔需要过滤，默认值位True，即有样本孔需要过滤，反之则设为 False
is_filter = False
# 提取过滤的样本质控类型（仅在 is_filter 为 True 时生效）
filtered_sample_qc_type = {'N','P'}

sample_type_list = []
volume_dict = {key:5 for key in sample_type_list}
default_volume = 35

# ================================以下内容为读取样本信息文件=============================================
class Sample:
	def __init__(self, sample_id, position, sample_type, sample_qc_type, barcode, target_position):
		sample_type_list = "".split("，")
		volume_dict = {key:5 for key in sample_type_list}
		default_volume = 35
		self.sample_id = sample_id  # 样本编号
		self.position = position    # 孔位
		self.target_position = target_position
		self.sample_type = sample_type  # 样本类型
		self.sample_qc_type = sample_qc_type  # 样本质控类型
		self.barcode = barcode      # barcode
		 # 计算行列号
		self.row = ord(position[0].upper()) - ord('A') + 1  # 行号（1-based）
		self.column = int(position[1:])  # 列号（1-based）
		self.target_row = ord(self.target_position[0].upper()) - ord('A') + 1  # 行号（1-based）
		self.target_column = int(self.target_position[1:])
		self.volume = volume_dict.get(self.sample_type,default_volume)

	def __repr__(self):
		return (f"Sample(sample_id={self.sample_id}, position={self.position}, "
				f"sample_type={self.sample_type}, sample_qc_type={self.sample_qc_type}, "
				f"barcode={self.barcode}, row={self.row}, column={self.column})")


def get_sample_info(sample_info_file_path, is_filter, filtered_sample_qc_type):
	samples = []
	cur_index = 0

	try:
		# 打开 CSV 文件，使用文本模式并指定编码
		with open(sample_info_file_path, 'rb') as file:
			lines = file.readlines()
	except IOError as e:

		return samples
	except Exception as e:

		return samples

	# 遍历每一行数据（跳过表头）
	for line in lines[1:]:
		# 去掉行首行尾的空白字符（包括换行符）
		line = line.strip()

		# 如果行为空，跳过
		if not line:
			continue

		# 以逗号为分隔符分割每一行
		decoded_str = line.decode('utf-8')
		columns = decoded_str.split(',')

		# 检查列数是否足够
		if len(columns) < 7:  # 根据实际需要调整列数检查

			continue

		# 跳过滤制样本类型
		sample_qc_type = columns[3].strip()
		if is_filter and sample_qc_type in filtered_sample_qc_type:
			continue

		# 计算孔位（从 A1 开始）
		position = u"{}{}".format(chr(ord('A') + cur_index % 8), cur_index // 8 + 1)
		target_position = columns[1]  # 默认目标孔位与当前孔位相同

		sample_id = columns[0].strip()
		sample_type = columns[6].strip()
		barcode = columns[5].strip()

		# 创建 Sample 对象并添加到列表中
		sample = Sample(sample_id, position, sample_type, sample_qc_type, barcode,target_position)
		samples.append(sample)

		cur_index += 1

	return samples


filtered_samples=get_sample_info(sample_info_file_path, False, filtered_sample_qc_type)
SampleCount = len(filtered_samples)
if not filtered_samples:
	a = dialog_textbox({"Title": "请输入样本数量", "Timeout": "02:00:00","Parameters":[{"Name": "样本数量", "Value": "48", "Notes": "未检测到样本信息文件，请输入样本数量"}]})
	SampleCount = int(a["样本数量"])
sample_num = SampleCount
n = SampleCount
col_num = (sample_num+7)//8
target_tip_num_list = [8]*(sample_num//8) + [sample_num%8]
'''=====================================以上为样本信息读取建库仪====================================='''


def blockB():
	pcr_run_method({"Methods": ["PTseq_START"]})
	pcr_run_method({"Methods": ["25-4"]})
b = parallel_block(blockB)



'''=====================================中转位=============================================================='''
transposition = "M2_POS30"

'''===================================================cDNA合成==============================================================='''
#取8的商和余数,计算行列数
Quotient8= SampleCount//8
Remainder8= SampleCount%8
if Remainder8 == 0:
	add8 = 0   
else:
	add8 = 1    
ColNum =Quotient8+add8


lang=get_lang()
if lang==1: #
 report({"Phase": "cDNA合成", "Step": "逆转录反应", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "cDNA synthesis", "Step": "Reverse Transcription", "TaskType": "library", "RemainingTime": None})
 
#分装矿物油
#计算矿物油分装量
p1_load_modified(tip_1000.load(1)[0])
if SampleCount > 24:
	a = 1.2
else:
	a = 1.4
target_volume_list = [80*a*(SampleCount//8+1)]*(SampleCount%8)+[50*a*(SampleCount//8)]*(8-SampleCount%8)

# POS14/POS11 switched: original POS14 oil/waste/pooling plate now lives at POS11.
for i in range(min(8, SampleCount)):
	p1_aspirate({"Position":"M2_POS24","Col":3,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.8,"AspirateSpeed":30,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 3, "TipTouchSpeed": 100})
	p1_dispense({"Position":"M2_POS11","Col":8,"Row":i+1,"DispenseOffsetOfZ":8,"DispenseSpeed":20,"DispenseVolume":target_volume_list[i],"DelayAfterDispense":0.5,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":0,"IsEmpty":True,"EmptyOffsetOfZ":2,"EmptySpeed":30,"DelayAfterEmpty":0.5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# ===== STEP: Dispense T1 cDNA Primer to PCR Plate (POS20) =====
col_num = (sample_num+7)//8  # Number of sample columns

transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0}) #开试剂盖

# [COMMENTED OUT] >20 samples POS7 Col 8 intermediate path (replaced by P1 direct for all sample counts)
# if SampleCount > 20:
# 	t1_safety_factor = 1.15
# 	t1_volume_per_tube = [2.0 * col_num * t1_safety_factor] * 8
# 	p1_load_modified(tip_50.load(1)[0])
# 	for i in range(8):
# 		p1_aspirate({"Position":"M2_POS17","Col":1,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":t1_volume_per_tube[i],"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
# 		p1_empty({"Position":"M2_POS7","Col":8,"Row":i+1,"EmptyOffsetOfZ":1.5,"EmptySpeed":30,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
# 	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
# 	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})
# 	p8_load_modified(tip_50.load(8)[0])
# 	for i in range(col_num):
# 		p8_aspirate({"Position":"M2_POS7","Col":8,"Row":1,"PreAirVolume":4,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":2.0,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
# 		p8_empty({"Position":"M2_POS20","Col":i+1,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
# 	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# v12: RT first-step 2 µL T1 primer 转移 — 参数对齐 PTplus 16+2 system 的 2 µL 模式
# v12 sync: PTplus 16+2 system 2 µL pattern; P1 head retained, sample-loop and POS20 destination mapping unchanged.
p1_load_modified(tip_50.load(1)[0])
for i in range(col_num):
	last_row = 8 if (i < col_num - 1 or sample_num % 8 == 0) else sample_num % 8
	for j in range(last_row):
		p1_aspirate_modified("M2_POS17", 1, 1, 2, AspirateSpeed=10)
		p1_empty_modified("M2_POS20", j+1, i+1, EmptyOffsetOfZ=0.5)
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0}) #盖试剂盖

#将样本从POS8转移到POS20
col_num = (sample_num+7)//8
column_num = col_num
for i in range(col_num):
	p8_load_modified(tip_300.load(target_tip_num_list[i])[0])
	p8_mix({"Position":"M2_POS8","Col":i+1,"Row":1,"PreAirVolume":15,"MixTimes":8,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":0.5,"MixVolume":20,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":50,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":30,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_aspirate({"Position":"M2_POS8","Col":i+1,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.7,"AspirateSpeed":30,"AspirateVolume":14,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS20","Col":i+1,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_mix({"Position":"M2_POS20","Col":i+1,"Row":1,"PreAirVolume":11,"MixTimes":15,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":0.5,"MixVolume":13,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":50,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":30,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	#p8_empty({"Position":"M2_POS20","Col":i+1,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
b.Wait()

# v12: 添加矿物油 (BEFORE PTseq_RT — 保护 RT, cDNA 复用同孔无需再加)
# 计算最后一列去枪头的行
if SampleCount%8 == 0:
	last_row =1
else:
	last_row = 9-SampleCount%8
oil_1 = tip_300.load(8,8,1)

p8_load_tips({"Position":oil_1[0][0],"Col":oil_1[0][1],"Row":last_row,"Tips":8})
for i in range(col_num-1,-1,-1):
	p8_aspirate({"Position":"M2_POS11","Col":8,"Row":1,"PreAirVolume":20,"AspirateOffsetOfZ":1,"AspirateSpeed":10,"AspirateVolume":10,"PreAirSpeed":50,"DelayAfterAspirate":1,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})
	p8_empty({"Position":"M2_POS20","Col":i+1,"Row":1,"EmptyOffsetOfZ":8,"EmptySpeed":30,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	if i == col_num-1 and SampleCount%8 != 0:
		p8_unload_tips({"Position":oil_1[0][0],"Col":oil_1[0][1],"Row":last_row,"Tips":8})
		p8_load_modified(oil_1[0])
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 添加PCR盖板
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0}) #PCR盖板


pcr_close_door()
def spx_p1_f_0():
	pcr_run_method({"Methods":["PTseq_RT"]})

spx_p0_v_0 = parallel_block(spx_p1_f_0)

# Delay reagent setup until PTseq_RT is near completion, avoiding long hold time for T2/T3 mix.
delay({"Duration": 1800})

'''===================================================cDNA一链合成反应体系==============================================================='''
lang=get_lang()
if lang==1: #
 report({"Phase": "cDNA合成", "Step": "cDNA一链合成反应体系", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "cDNA synthesis", "Step": "cDNAFirst-strand synthesis reaction system", "TaskType": "library", "RemainingTime": None})

# 配置一链反应试剂
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
low_throughput_p1_direct_col9 = use_low_throughput_p1_direct(SampleCount)
report_low_throughput_branch("Col9 cDNA mix", low_throughput_p1_direct_col9, SampleCount)
# Low-throughput branch uses direct total volume, without POS7 row dead volume.
# Original branch keeps POS7 Col 9 capped dead-volume curve unchanged.
if low_throughput_p1_direct_col9:
	pos7_col9_volumes = [0] * 8
	mix_total_col9 = 4 * SampleCount + MIX_TUBE_DEAD_VOLUME
else:
	pos7_col9_volumes = [pos7_reaction_mix_dispense_volume(4, SampleCount, r) for r in range(8)]
	mix_total_col9 = sum(pos7_col9_volumes) + MIX_TUBE_DEAD_VOLUME  # 2 mL mixing tube +15 µL dead
t23_vol = mix_total_col9 / 2  # T2 buffer and T3 enzyme each contribute half
# 吸T2 一链合成缓冲液
p8_load_modified(tip_300.load(1)[0])
p8_aspirate({"Position":"M2_POS17","Col":2,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":t23_vol,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS17","Col":4,"Row":1,"EmptyOffsetOfZ":0.1*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
# 吸T3 一链合成酶
p8_load_modified(tip_300.load(1)[0])
p8_aspirate({"Position":"M2_POS17","Col":3,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":t23_vol,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_empty({"Position":"M2_POS17","Col":4,"Row":1,"EmptyOffsetOfZ":0.2*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_mix({"Position":"M2_POS17","Col":4,"Row":1,"PreAirVolume":8,"MixTimes":10,"MixAspirateSpeed":3*SampleCount,"MixAspirateOffsetOfZ":0.6,"MixVolume":4.9*SampleCount,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":2.5*SampleCount,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.5+0.3*SampleCount,"MixEmptySpeed":5,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_mix({"Position":"M2_POS17","Col":4,"Row":1,"PreAirVolume":8,"MixTimes":10,"MixAspirateSpeed":3*SampleCount,"MixAspirateOffsetOfZ":0.6,"MixVolume":4.9*SampleCount,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":2.5*SampleCount,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.5+0.3*SampleCount,"MixEmptySpeed":5,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_empty({"Position":"M2_POS17","Col":4,"Row":1,"EmptyOffsetOfZ":0.2*SampleCount,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

if not low_throughput_p1_direct_col9:
	# v12: POS7 Col 9 per-row dispense list comes from the capped dead-volume curve above.
	target_volume_list = pos7_col9_volumes

	# Pre-dispense cDNA synthesis mix to POS7 Col 9 (intermediate, no lid required)
	# Optimized: Use single tip for all 8 transfers (clean source to clean target)
	p1_load_modified(tip_50.load(1)[0])
	if SampleCount <= 20:
		for i in range(8):
			p1_aspirate({"Position":"M2_POS17","Col":4,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":3,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
			p1_empty({"Position":"M2_POS7","Col":9,"Row":i+1,"EmptyOffsetOfZ":1.7,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	else:
		for i in range(8):
			p1_aspirate({"Position":"M2_POS17","Col":4,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":3,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
			p1_empty({"Position":"M2_POS7","Col":9,"Row":i+1,"EmptyOffsetOfZ":2,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# 盖上试剂盖
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0}) #试剂盖板
# POS7 has no lid, so no lid operations needed
spx_p0_v_0.Wait()

#Block begin:将cDNA合成反应液与样本混合
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})#PCR盖板
# POS7 has no lid, removed unnecessary POS10 lid operation



# 添加一链反应液到样本中
if low_throughput_p1_direct_col9:
	transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
	cDNA_direct_tips = tip_50.load(sample_num, 1)
	for tip_index, (col_index, row) in enumerate(active_sample_wells(SampleCount)):
		p1_load_modified(cDNA_direct_tips[tip_index])
		p1_aspirate_modified("M2_POS17", 1, 4, 4, PreAirVolume=5, AspirateSpeed=10, AspirateOffsetOfZ=0.5, DelayAfterAspirate=0.5, PostAirVolume=0, IfTrack=False)
		p1_empty_modified("M2_POS20", row, col_index+1, EmptyOffsetOfZ=0.8, EmptySpeed=30, DelayAfterEmpty=2, TipTouchTimes=2, TipTouchOffsetOfZ=3, TipTouchRangeOfX=1.2, TipTouchSpeed=100, PostAirVolume=0)
		p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})
	for i in range(col_num):
		p8_load_modified(tip_50.load(target_tip_num_list[i])[0])
		p8_mix({"Position":"M2_POS20","Col":i+1,"Row":1,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":0.5,"MixVolume":20,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
else:
	# v12: AspirateOffsetOfZ 0.1→0.5 (POS7 reaction-mix intermediate dead-volume safety)
	for i in range(col_num):
		p8_load_modified(tip_50.load(target_tip_num_list[i])[0])
		if SampleCount <= 20:
			p8_aspirate({"Position":"M2_POS7","Col":9,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":15,"AspirateVolume":4,"PreAirSpeed":30,"DelayAfterAspirate":5,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		else:
			p8_aspirate({"Position":"M2_POS7","Col":9,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":15,"AspirateVolume":4,"PreAirSpeed":30,"DelayAfterAspirate":5,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS20","Col":i+1,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":30,"DelayAfterEmpty":2,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_mix({"Position":"M2_POS20","Col":i+1,"Row":1,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":0.5,"MixVolume":20,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		#p8_empty({"Position":"M2_POS20","Col":i+1,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# v12: 矿物油已在 PTseq_RT 前添加 (POS20 Cols 1-6), cDNA 复用同孔无需再加

# 盖上PCR盖板
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0}) #PCR盖板



'''==================================================cDNA一链合成反应==============================================================='''
pcr_close_door()
def spx_p2_f_0():
	pcr_run_method({"Methods":["PTseq_cDNA"]})
spx_p2_v_0 = parallel_block(spx_p2_f_0)

# Delay TA reagent setup until PTseq_cDNA is near completion, avoiding long hold time for TA master mix.
delay({"Duration": 4200})

# POS7 has no lid, removed unnecessary POS10 lid operation

'''===================================================靶向扩增反应试剂==============================================================='''
lang=get_lang()
if lang==1: #
 report({"Phase": "cDNA合成", "Step": "靶向扩增反应体系", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "cDNA synthesis", "Step": "Targeted Amplification reaction system", "TaskType": "library", "RemainingTime": None})
 

# 配置靶向扩增反应试剂
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
c = 1.4  # legacy safety coefficient retained for T2 buffer pre-dispense at L687 (POS7 Col 7), out of capped-curve scope
low_throughput_p1_direct_col10 = use_low_throughput_p1_direct(SampleCount)
report_low_throughput_branch("Col10 TA mix", low_throughput_p1_direct_col10, SampleCount)
# Low-throughput branch uses direct total volume, without POS7 row dead volume.
# Original branch keeps POS7 Col 10 capped dead-volume curve unchanged.
if low_throughput_p1_direct_col10:
	pos7_col10_volumes = [0] * 8
	mix_total_col10 = 15 * SampleCount + MIX_TUBE_DEAD_VOLUME
else:
	pos7_col10_volumes = [pos7_reaction_mix_dispense_volume(15, SampleCount, r) for r in range(8)]
	mix_total_col10 = sum(pos7_col10_volumes) + MIX_TUBE_DEAD_VOLUME  # 2 mL mixing tube +15 µL dead
ta_t2_vol = mix_total_col10 * 7 / 15
ta_t4_vol = mix_total_col10 * 5 / 15
ta_t5_vol = mix_total_col10 * 3 / 15

# 吸T2溶解液 (split into two equal P1 transfers, preserves original two-aspiration pattern)
p1_load_modified(tip_1000.load(1)[0])
p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":10,"AspirateOffsetOfZ":0.8,"AspirateSpeed":10,"AspirateVolume":ta_t2_vol/2,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_empty({"Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.1*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":10,"AspirateOffsetOfZ":0.8,"AspirateSpeed":10,"AspirateVolume":ta_t2_vol/2,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_empty({"Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.1*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# 吸T4靶向扩增缓冲液
total_ta_buffer_vol = ta_t4_vol
max_tip_capacity = 240  # 250 limit - 10uL PreAir (threshold ≈ 34 samples)

p8_load_modified(tip_300.load(1)[0])

if total_ta_buffer_vol <= max_tip_capacity:
    # --- Standard Single Aspiration (Samples 1-34) ---
    p8_aspirate({
        "Position":"M2_POS17","Col":1,"Row":2,"PreAirVolume":10,
        "AspirateOffsetOfZ":0.6,"AspirateSpeed":10,
        "AspirateVolume":total_ta_buffer_vol,
        "PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,
        "PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,
        "FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80
    })
    p8_empty({
        "Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.1*SampleCount,
        "EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,
        "PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,
        "SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80
    })

else:
    # --- Split Aspiration (Samples 35-48) ---
    # Split volume into two equal parts to balance the pipetting
    split_vol = total_ta_buffer_vol / 2

    print(f"[INFO] Volume {total_ta_buffer_vol}uL exceeds limit. Splitting into 2x {split_vol}uL.")

    for _ in range(2):
        p8_aspirate({
            "Position":"M2_POS17","Col":1,"Row":2,"PreAirVolume":10,
            "AspirateOffsetOfZ":0.6,"AspirateSpeed":10,
            "AspirateVolume":split_vol,
            "PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,
            "PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,
            "FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80
        })
        p8_empty({
            "Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.1*SampleCount,
            "EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,
            "PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,
            "SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80
        })

p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 吸T5靶向扩增酶
p8_load_modified(tip_300.load(1)[0])
p8_aspirate({"Position":"M2_POS17","Col":2,"Row":2,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":ta_t5_vol,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_empty({"Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.2*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_mix({"Position":"M2_POS17","Col":4,"Row":2,"PreAirVolume":8,"MixTimes":10,"MixAspirateSpeed":3*SampleCount,"MixAspirateOffsetOfZ":0.6,"MixVolume":4.9*SampleCount,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":2.5*SampleCount,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.5+0.3*SampleCount,"MixEmptySpeed":5,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_mix({"Position":"M2_POS17","Col":4,"Row":2,"PreAirVolume":8,"MixTimes":10,"MixAspirateSpeed":3*SampleCount,"MixAspirateOffsetOfZ":0.6,"MixVolume":4.9*SampleCount,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":2.5*SampleCount,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.5+0.3*SampleCount,"MixEmptySpeed":5,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_empty({"Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.2*SampleCount,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

if not low_throughput_p1_direct_col10:
	# v12: POS7 Col 10 per-row dispense list comes from the capped dead-volume curve above.
	target_volume_list = pos7_col10_volumes
	# if SampleCount <= 20:
	# Optimization: Load ONE tip for all 8 dispenses (reduces 8 tips to 1 tip)
	# Use 300 µL tips because the maximum required volume per tube exceeds the 50 µL tip range.
	p1_load_modified(tip_300.load(1)[0])
	for i in range(8):
		p1_aspirate({"Position":"M2_POS17","Col":4,"Row":2,"PreAirVolume":8,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p1_empty({"Position":"M2_POS7","Col":10,"Row":i+1,"EmptyOffsetOfZ":0.5,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# Unload tip after all 8 dispenses
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})

# =============================================
# CRITICAL: Dispense T2 Buffer to POS7 Col 7
# =============================================
# T2 Buffer is used twice downstream:
# 1. Line 918: 25 µL for TA purification binding
# 2. Line 1427: 23 µL for final elution
# Total required: (25 + 23) × safety coefficient per row

# Calculate target volume (48 µL base per row with safety coefficient)
target_volume_list = [48*c*(SampleCount//8+1)]*(SampleCount%8)+[48*c*(SampleCount//8)]*(8-SampleCount%8)

# Load ONE tip for all 8 dispenses (optimization: reduces 8 tips to 1 tip)
# Use 1000 µL tips because the maximum required volume per tube exceeds the 300 µL tip range.
p1_load_modified(tip_1000.load(1)[0])
for i in range(8):
	p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":8,"AspirateOffsetOfZ":0.8,"AspirateSpeed":30,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p1_empty({"Position":"M2_POS7","Col":7,"Row":i+1,"EmptyOffsetOfZ":0.5,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
# Unload tip after all 8 dispenses
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

spx_p2_v_0.Wait()

#Block begin:将靶向扩增反应液与样本混合
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})

# 添加靶向扩增反应液到样本中 (Manual SOP: 15+5+5=25 µL total)
if low_throughput_p1_direct_col10:
	# POS17 and POS10 both park covers at POS27, so direct TA uses a safe source-window design.
	# TA Master Mix, T6 barcode, and cDNA/product each use a fresh independent tip.
	transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
	ta_direct_mix_tips = tip_50.load(sample_num, 1)
	for tip_index, (col_index, row) in enumerate(active_sample_wells(SampleCount)):
		p1_load_modified(ta_direct_mix_tips[tip_index])
		p1_aspirate_modified("M2_POS17", 2, 4, 15, PreAirVolume=5, AspirateSpeed=10, AspirateOffsetOfZ=0.6, DelayAfterAspirate=0.5, PostAirVolume=0, IfTrack=False)
		p1_empty_modified("M2_POS20", row, col_index+7, EmptyOffsetOfZ=3, EmptySpeed=50, DelayAfterEmpty=0.5, TipTouchTimes=0, PostAirVolume=2)
		p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})

	transfer({"StartPosition":"M2_POS10","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
	ta_direct_primer_tips = tip_50.load(sample_num, 1)
	for tip_index, (col_index, row) in enumerate(active_sample_wells(SampleCount)):
		p1_load_modified(ta_direct_primer_tips[tip_index])
		p1_aspirate_modified("M2_POS10", row, col_index+1, 5, PreAirVolume=5, AspirateSpeed=10, AspirateOffsetOfZ=0.5, DelayAfterAspirate=1, PostAirVolume=0, IfTrack=False)
		p1_empty_modified("M2_POS20", row, col_index+7, EmptyOffsetOfZ=3, EmptySpeed=50, DelayAfterEmpty=0.5, TipTouchTimes=0, PostAirVolume=0)
		p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	ta_direct_sample_tips = tip_50.load(sample_num, 1)
	for tip_index, (col_index, row) in enumerate(active_sample_wells(SampleCount)):
		p1_load_modified(ta_direct_sample_tips[tip_index])
		p1_aspirate_modified("M2_POS20", row, col_index+1, 5, PreAirVolume=5, AspirateSpeed=10, AspirateOffsetOfZ=0.5, DelayAfterAspirate=1, PostAirVolume=0, IfTrack=False)
		p1_empty_modified("M2_POS20", row, col_index+7, EmptyOffsetOfZ=3, EmptySpeed=50, DelayAfterEmpty=0.5, TipTouchTimes=0, PostAirVolume=0)
		p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	for i in range(col_num):
		p8_load_modified(tip_50.load(target_tip_num_list[i])[0])
		p8_mix({"Position":"M2_POS20","Col":i+7,"Row":1,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":50,"MixAspirateOffsetOfZ":0.5,"MixVolume":22,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":50,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
else:
	transfer({"StartPosition":"M2_POS10","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
	for i in range(col_num):
		p8_load_modified(tip_50.load(target_tip_num_list[i])[0])
		p8_aspirate({"Position":"M2_POS7","Col":10,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":15,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS20","Col":i+7,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
	for i in range(col_num):
		p8_load_modified(tip_50.load(target_tip_num_list[i])[0])
		p8_aspirate({"Position":"M2_POS10","Col":i+1,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":5,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS20","Col":i+7,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
	for i in range(col_num):
		p8_load_modified(tip_50.load(target_tip_num_list[i])[0])
		p8_aspirate({"Position":"M2_POS20","Col":i+1,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":5,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS20","Col":i+7,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_mix({"Position":"M2_POS20","Col":i+7,"Row":1,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":50,"MixAspirateOffsetOfZ":0.5,"MixVolume":22,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":50,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		#p8_empty({"Position":"M2_POS20","Col":i+1,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# v12: Mineral oil overlay on TA PCR wells (POS20 Cols 7-12) before PTseq_TA. New wells, no prior oil.
if SampleCount%8 == 0:
	last_row = 1
else:
	last_row = 9-SampleCount%8
oil_2 = tip_300.load(8,8,1)

p8_load_tips({"Position":oil_2[0][0],"Col":oil_2[0][1],"Row":last_row,"Tips":8})
for i in range(col_num-1,-1,-1):
	p8_aspirate({"Position":"M2_POS11","Col":8,"Row":1,"PreAirVolume":20,"AspirateOffsetOfZ":1,"AspirateSpeed":10,"AspirateVolume":10,"PreAirSpeed":50,"DelayAfterAspirate":1,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})
	p8_empty({"Position":"M2_POS20","Col":i+7,"Row":1,"EmptyOffsetOfZ":8,"EmptySpeed":30,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	if i == col_num-1 and SampleCount%8 != 0:
		p8_unload_tips({"Position":oil_2[0][0],"Col":oil_2[0][1],"Row":last_row,"Tips":8})
		p8_load_modified(oil_2[0])
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 盖上PCR盖板
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0}) #PCR盖板
# 盖上八连管盖板
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS10","LoosenOffsetOfZ":0})
'''================================================== 二链反应==============================================================='''

pcr_close_door()
def spx_p2_f_1():
	pcr_run_method({"Methods":["PTseq_TA"]})

spx_p2_v_1 = parallel_block(spx_p2_f_1)

# Delay TA purification reagent setup until PTseq_TA is near completion, avoiding long hold time for beads.
delay({"Duration": 4200})

#####################################################T1 磁珠分装##############################################

p1_load_modified(tip_1000.load(1)[0])
#T1 磁珠混匀
p1_mix({"Position":"M2_POS24", "Col": 1, "Row": 1,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":0.8,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":2,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":"M2_POS24", "Col": 1, "Row": 1,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":1,"MixVolume":900,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":30,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":15,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})

# 计算磁珠分装体积，每个样本第一轮纯化使用50µL磁珠 (2:1 ratio for 25 µL TA product)，使用1.4×安全系数
target_volume_list = [50*1.4*(SampleCount//8+1)]*(SampleCount%8)+[50*1.4*(SampleCount//8)]*(8-SampleCount%8)
for i in range(8):
	#p1_aspirate({"Position":"M2_POS24","Col":2,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.8,"AspirateSpeed":50,"AspirateVolume":target_volume_list[i],"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":30,"IfTrack":False,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 1.5, "TipTouchSpeed": 100})
	p1_aspirate({"Position":"M2_POS24", "Col": 1, "Row": 1,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":50,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 50, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS7","Col":12,"Row":i+1,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":1,"TipTouchOffsetOfZ":5,"TipTouchRangeOfX":2,"TipTouchSpeed":50,"PostAirSpeed":100,"PostAirVolume":5,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})


# 分装48的磁珠
total_col_num = (sample_num+7)//8
target_tip_num_list = [8]*(sample_num//8) + [sample_num%8]
temp = tip_300.load(8)[0]
for i in range(col_num-1,-1,-1):
	if i == col_num-1 and target_tip_num_list[i] != 8:
		p8_load_modified((temp[0],temp[1],temp[2]+8-sample_num%8))
	elif i == col_num-1:
		p8_load_modified(temp)
	p8_aspirate({"Position":"M2_POS7","Col":12,"Row":1,"PreAirVolume":35,"AspirateOffsetOfZ":0.9,"AspirateSpeed":50,"AspirateVolume":50,"PreAirSpeed":50,"DelayAfterAspirate":1,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.4, "TipTouchSpeed": 100})
	p8_dispense({"Position": "M2_POS16","Col":7+i,"Row":1,"FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "DispenseOffsetOfZ": 0.8, "DispenseSpeed": 30, "DispenseVolume":50,"DelayAfterDispense": 1, "IsEmpty": True, "EmptyOffsetOfZ": 2, "EmptySpeed": 30, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	if i == col_num-1 and target_tip_num_list[i] != 8:
		p8_unload_modified((temp[0],temp[1],temp[2]+8-sample_num%8))
		p8_load_modified(temp)
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})



spx_p2_v_1.Wait()
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})

TA_purification_tips = tip_300.load(sample_num,8,1)

# 靶向扩增反应后纯化
lang=get_lang()
if lang==1: #
 report({"Phase": "靶向扩增反应后纯化", "Step": "样本与磁珠结合", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Targeted Amplification Purification", "Step": "Sample Binding to Magnetic Beads", "TaskType": "library", "RemainingTime": None})

for i in range(col_num):
	p8_load_modified(TA_purification_tips[i])
	# Step 1: Aspirate 25 µL T2 Buffer FIRST (clean tips → no sample contamination of T2 strip)
	p8_aspirate({"Position":"M2_POS7","Col":7,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":30,"AspirateVolume":25,"PreAirSpeed":50,"DelayAfterAspirate":2,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# Step 2: Aspirate 25 µL TA product (sequential aspirate, same tips)
	p8_aspirate({"Position":"M2_POS20","Col":7+i,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0.5,"AspirateSpeed":40,"AspirateVolume":25,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# Step 3: Dispense combined 50 µL (T2 + TA product) to beads in POS16
	p8_empty({"Position":"M2_POS16","Col":7+i,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":40,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.3, "TipTouchSpeed": 100})
	# Step 4: Mix 50 µL beads + 25 µL TA + 25 µL T2 = 100 µL total (use 95 µL mix volume)
	p8_mix({"Position":"M2_POS16","Col":7+i,"Row":1,"PreAirVolume":20,"MixTimes":5,"MixAspirateSpeed":80,"MixAspirateOffsetOfZ":0.5,"MixVolume":95,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":50,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":10,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":0, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty({"Position":"M2_POS16","Col":7+i,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":20,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.3, "TipTouchSpeed": 100})
	p8_unload_modified(TA_purification_tips[i])
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1000, "Duration": 30}})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 0, "Speed": 1000, "Duration": 30}})

delay({"Duration": 300})

transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})#关PCR盖板
pcr_close_door()  # Close PCR door after lid replacement

# v12: POS3 → POS7 ethanol pre-dispense, PTplus-style (5 cycles × 195 µL = 975 µL/well; staged height 0.5 + 4*tt).
# Pre-stage ethanol before TA supernatant removal so ethanol can be added immediately after the bead pellet is exposed.
Alcohol_1 = tip_1000.load(8,8)
p8_load_modified(Alcohol_1[0])
for x in range(col_num):
	for tt in range(5):
		p8_aspirate({"Position":"M2_POS3","Col":1,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":1.0,"AspirateSpeed":80,"AspirateVolume":195,"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":0})
		p8_empty({"Position":"M2_POS7","Col":1+x,"Row":1,"EmptyOffsetOfZ":0.5+4*tt,"EmptySpeed":50,"DelayAfterEmpty":0.8,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})


###48μL磁珠1振荡位置转移到磁吸位置
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})
delay({"Duration": 180})

# === 废液回收设置 ===
# POS14/POS11 switched: original POS14 deepwell plate now lives at POS11.
# POS11 deepwell 1.3mL 板 Col 1-6 用于回收废液（1:1 列映射）
# 累计废液量: 95 + 420 + 85 + 420 = 1020 µL/孔 (容量 1300 µL)
waste_col_start = 1

Ligation_purification_tips2 = tip_300.load(sample_num,8,0)  # reuse_index=0: tips discarded after the TA ethanol wash block
# NOTE: T2 Buffer is now added BEFORE magnetic separation (see line ~875-880)
# The previous step here that added T2 after supernatant removal was INCORRECT
# and caused DNA loss (DNA needs PEG/salt buffer to bind to SPRI beads)

# 连接后纯化乙醇清洗
lang=get_lang()
if lang==1: #
 report({"Phase": "靶向扩增反应后纯化", "Step": "乙醇清洗", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Targeted Amplification Purification", "Step": "Ethanol Wash", "TaskType": "library", "RemainingTime": None})

# 移除上清 (after adding T2 buffer: 50 beads + 25 TA + 25 T2 = 100 µL total, remove 110 µL for "弃多于打" safety margin)
# Waste recovered to POS11 plate Col 1-6
for i in range(col_num):
	p8_load_modified_BubblePurge(TA_purification_tips[i])
	p8_aspirate({"Position":"M2_POS23","Col":7+i,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":30,"AspirateVolume":110,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# Empty waste to POS11 waste plate, Col 1:1 mapping
	p8_empty({"Position":"M2_POS11","Col":waste_col_start+i,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"TipTouchOffsetOfZ":15,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# Use pre-allocated Ligation_purification_tips2 for ethanol wash.

# v12: TA 乙醇洗涤流程 - 静置等待方案, 加乙醇后不移板/不吹打, 仅做 120 s 磁吸沉降后弃乙醇
for i in range(2):
	# Step 1a: 加乙醇 (板在 POS23 磁铁位)
	for x in range(col_num):
		p8_load_modified_BubblePurge(Ligation_purification_tips2[x])
		p8_aspirate({"Position":"M2_POS7","Col":1+x,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":1.0,"AspirateSpeed":50,"AspirateVolume":200,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS23","Col":7+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":2,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.4, "TipTouchSpeed": 100})
		p8_unload_modified(Ligation_purification_tips2[x])

	# Step 2: 静置磁吸沉降 (板始终在 POS23 磁铁位)
	delay({"Duration": 120})

	# Step 4: 弃乙醇 (板在 POS23 磁铁位; AspirateVolume 210→220, 余 +20 µL)
	for x in range(col_num):
		p8_load_modified_BubblePurge(Ligation_purification_tips2[x])
		p8_aspirate({"Position":"M2_POS23","Col":7+x,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0,"AspirateSpeed":10,"AspirateVolume":220,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS11","Col":waste_col_start+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"TipTouchOffsetOfZ":15,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		# 只在最后一轮丢弃枪头，第一轮放回原位
		if i == 1:
			p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
		else:
			p8_unload_modified(Ligation_purification_tips2[x])

def wait_for_magnetic_beads():
	# v12: TA 纯化晾干延时 5 min (8→5 min, 回退至 SOP 允许下限)
	delay({"Duration": 300})

magetic_wait = parallel_block(wait_for_magnetic_beads)
# 等待磁珠吸附

lang=get_lang()
if lang==1: #
 report({"Phase": "文库扩增准备", "Step": "配置文库扩增反应液", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Library Amplification preparation", "Step": "Preparing Library Amplification reaction mixture", "TaskType": "library", "RemainingTime": None})

#Block begin:配置文库扩增反应液
# T8 UDG volume: tiered coefficients for small volumes (300µL tip dead volume compensation)
# <16 samples: ×1.6 coefficient, minimum 7 µL; ≥16 samples: ×1.3 (standard)
def _t8_vol(n):
	return max(1 * 1.6 * n, 7) if n < 16 else 1 * 1.3 * n

low_throughput_p1_direct_col11 = use_low_throughput_p1_direct(SampleCount)
report_low_throughput_branch("Col11 LA/PCR mix", low_throughput_p1_direct_col11, SampleCount)
# Low-throughput branch uses direct total volume, without POS7 row dead volume.
# Original branch keeps POS7 Col 11 capped dead-volume curve unchanged.
if low_throughput_p1_direct_col11:
	pos7_col11_volumes = [0] * 8
	mix_total_col11 = 30 * SampleCount + MIX_TUBE_DEAD_VOLUME
else:
	pos7_col11_volumes = [pos7_reaction_mix_dispense_volume(30, SampleCount, r) for r in range(8)]
	mix_total_col11 = sum(pos7_col11_volumes) + MIX_TUBE_DEAD_VOLUME  # 2 mL mixing tube +15 µL dead
la_t7_vol = mix_total_col11 * 20 / 30
la_t8_vol = max(_t8_vol(SampleCount), mix_total_col11 * 1 / 30)  # _t8_vol acts as min-floor for T8
la_t2_vol = mix_total_col11 * 9 / 30

transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
if SampleCount > 20:
	p1_load_modified(tip_1000.load(1)[0])
	#吸T7 PCR mix (slowed FirstSegmentSpeed for gentle tip entry)
	p1_aspirate({"Position":"M2_POS17","Col":1,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t7_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	delay({"Duration": 10})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":10,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	p1_load_modified(tip_1000.load(1)[0])
	p1_aspirate({"Position":"M2_POS17","Col":1,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t7_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	#吸T8 UDG 酶 (Updated to 1 µL per well for 30 µL total LA Mix) - second dip, normal speed
	p8_load_modified(tip_300.load(1)[0])
	p8_aspirate({"Position":"M2_POS17","Col":2,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t8_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p8_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
	p8_load_modified(tip_300.load(1)[0])
	p8_aspirate({"Position":"M2_POS17","Col":2,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t8_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p8_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

	#吸T2 溶解液 (Updated to 9 µL per well for 30 µL total LA Mix)
	# Use POS24 Row 2 for T2 buffer; Row 1 is reserved for beads.
	p1_load_modified(tip_1000.load(1)[0])
	p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":150,"AspirateVolume":la_t2_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	p1_load_modified(tip_1000.load(1)[0])
	p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":150,"AspirateVolume":la_t2_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
else:
	p1_load_modified(tip_1000.load(1)[0])
	#吸T7 PCR mix (20 µL per well, slowed FirstSegmentSpeed for gentle tip entry)
	p1_aspirate({"Position":"M2_POS17","Col":1,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t7_vol,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	delay({"Duration": 10})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	#吸T8 UDG 酶 (1 µL per well, slowed FirstSegmentSpeed for gentle tip entry)
	p1_load_modified(tip_300.load(1)[0])
	p1_aspirate({"Position":"M2_POS17","Col":2,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t8_vol,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	#吸T2 溶解液 (Updated to 9 µL per well for 30 µL total LA Mix)
	# Use POS24 Row 2 for T2 buffer; Row 1 is reserved for beads.
	p1_load_modified(tip_1000.load(1)[0])
	p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":150,"AspirateVolume":la_t2_vol,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
# POS17盖已处于打开状态, 无需关再开
#混匀PCR mix
if SampleCount <=20:
	if SampleCount <=5:
		p1_load_modified(tip_300.load(1)[0])
	else:
		p1_load_modified(tip_1000.load(1)[0])
	#p1_mix({"Position":"M2_POS17","Col":4,"Row":3,"PreAirVolume":5,"MixTimes":10,"MixAspirateSpeed":200,"MixAspirateOffsetOfZ":2+0.5*sample_num,"MixVolume":25*sample_num,"MixDispenseOffsetOfZ":2+0.6*sample_num,"MixDispenseSpeed":200,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_mix({"Position":"M2_POS17", "Col": 4, "Row": 3,"PreAirVolume":80,"MixTimes":10,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":30*SampleCount,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_mix({"Position":"M2_POS17", "Col": 4, "Row": 3,"PreAirVolume":80,"MixTimes":15,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":30*SampleCount,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":3, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
else:
	p1_load_modified(tip_1000.load(1)[0])
	# Mix full volume with 900 µL capacity for >20 samples
	p1_mix({"Position":"M2_POS17", "Col": 4, "Row": 3,"PreAirVolume":80,"MixTimes":15,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":900,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_mix({"Position":"M2_POS17", "Col": 4, "Row": 3,"PreAirVolume":80,"MixTimes":15,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":900,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":3, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})

# 靶向扩增反应纯化PCR反应液回溶

# ============ SWAP POS20 (used plate) with POS9 (fresh plate) ============
# After TA, POS20 has used wells. Swap with fresh plate from POS9.
# Fresh plate will be used for LA (Cols 1-6) and DNB (Cols 7-12)
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})#开PCR盖板
transfer({"StartPosition":"M2_POS20","EndPosition":transposition,"LoosenOffsetOfZ":0})#POS20 (used) → POS30 (temp)
transfer({"StartPosition":"M2_POS9","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})#POS9 (fresh) → POS20
transfer({"StartPosition":transposition,"EndPosition":"M2_POS9","LoosenOffsetOfZ":0})#POS30 → POS9 (store used plate)
# ============ END SWAP ============
# State: door OPEN (line 1003), lid at POS26 (line 1004), fresh plate at POS20

lang=get_lang()
if lang==1: #
 report({"Phase": "Pre-PCR", "Step": "添加PCR mix", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Pre-PCR", "Step": "Adding PCR mix", "TaskType": "library", "RemainingTime": None})

# REMOVED: Oil removal step - fresh plate doesn't have oil residue
# (Original code removed TA oil from columns 7-12, not needed with fresh plate)

if not low_throughput_p1_direct_col11:
	# v12: POS7 Col 11 per-row dispense list comes from the capped dead-volume curve above.
	target_volume_list_pre_PCR = pos7_col11_volumes
	transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})


	p1_load_modified(tip_1000.load(1)[0])
	for i in range(8):
		# Removed broken consolidation step - all reagent is already mixed in Col 4, Row 3
		p1_aspirate({"Position":"M2_POS17","Col":4,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":target_volume_list_pre_PCR[i],"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
		p1_empty({"Position":"M2_POS7","Col":11,"Row":i+1,"EmptyOffsetOfZ":0.5,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})

magetic_wait.Wait()

# BEAD-SLURRY TRANSFER WORKFLOW - Add LA Master Mix to dried beads and create slurry
# Step 1: Dispense LA Master Mix onto dried beads at magnet position (M2_POS23)
if low_throughput_p1_direct_col11:
	transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
	LA_direct_tips = tip_50.load(sample_num, 1)
	for tip_index, (col_index, row) in enumerate(active_sample_wells(SampleCount)):
		p1_load_modified(LA_direct_tips[tip_index])
		p1_aspirate_modified("M2_POS17", 3, 4, 30, PreAirVolume=5, AspirateSpeed=50, AspirateOffsetOfZ=0.5, DelayAfterAspirate=0.5, TipTouchTimes=3, TipTouchOffsetOfZ=35, TipTouchRangeOfX=3.5, TipTouchSpeed=100, PostAirVolume=0, IfTrack=True)
		p1_empty_modified("M2_POS23", row, col_index+7, EmptyOffsetOfZ=0.5, EmptySpeed=20, DelayAfterEmpty=0.5, TipTouchTimes=0, PostAirVolume=5)
		p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})
else:
	LA_dispense_tips = tip_50.load(sample_num,8,1)
	for i in range(col_num):
		p8_load_modified(LA_dispense_tips[i])
		# Aspirate 30 µL LA Master Mix from pre-dispensed reservoir
		# PTplus P8-50 small-volume POS7 -> POS23 deepwell style.
		p8_aspirate({"Position":"M2_POS7","Col":11,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":30,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		# Dispense onto dried beads at M2_POS23 (on magnet)
		p8_empty({"Position":"M2_POS23","Col":7+i,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_modified(LA_dispense_tips[i])

# Step 2: Move plate from magnet to shaker for resuspension
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})
# Shake to resuspend dried beads (Speed=1200, 60s) - replaces tip mix
temp_shaker_set({"TempParameters":{"IsEnable":False,"Duration":-1},"ShakerParameters":{"IsEnable":True,"Direction":0,"Speed":1200,"Duration":60}})

# Step 3: Slurry transfer from POS16 to POS20
# NOTE: Beads are at POS16 Cols 7-12, LA destination is fresh plate POS20 Cols 1-6
LA_slurry_tips = tip_300.load(sample_num,8,1)
for i in range(col_num):
	p8_load_modified(LA_slurry_tips[i])
	# Aspirate entire 30 µL bead-slurry from M2_POS16
	p8_aspirate({"Position":"M2_POS16","Col":7+i,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0.5,"AspirateSpeed":20,"AspirateVolume":30,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# Transfer bead-slurry to fresh PCR plate Cols 1-6 (CHANGED from 7-12)
	p8_empty({"Position":"M2_POS20","Col":1+i,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":20,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_modified(LA_slurry_tips[i])

# Add 10 µL T9 Index Primer to PCR plate Cols 1-6
transfer({"StartPosition":"M2_POS10","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})#开盖板 - Open POS10 lid for T9 primer
T9_primer_tips = tip_50.load(sample_num,8,1)
for i in range(col_num):
	p8_load_modified(T9_primer_tips[i])
	# Aspirate 10 µL T9 primer from M2_POS10 columns 7-12 (primer source unchanged)
	p8_aspirate({"Position":"M2_POS10","Col":7+i,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":10,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":2,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# Dispense T9 primer to PCR plate Cols 1-6 (CHANGED from 7-12)
	p8_empty({"Position":"M2_POS20","Col":1+i,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# Mix final 40 µL reaction (30 µL slurry + 10 µL T9 primer)
	p8_mix({"Position":"M2_POS20","Col":1+i,"Row":1,"PreAirVolume":5,"MixTimes":5,"MixAspirateSpeed":50,"MixAspirateOffsetOfZ":0.5,"MixVolume":35,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":50,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":2,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS10","LoosenOffsetOfZ":0})#关盖板 - Close POS10 lid after T9 primer

# v12: 20 µL mineral oil overlay on LA PCR wells (POS20 Cols 1-6, fresh plate after POS9 swap) before PTseq_LA.
if SampleCount%8 == 0:
	last_row =1
else:
	last_row = 9-SampleCount%8
oil_3 = tip_300.load(8,8,0)  # reuse_index=0: oil tips discarded to trash

p8_load_tips({"Position":oil_3[0][0],"Col":oil_3[0][1],"Row":last_row,"Tips":8})
for i in range(col_num-1,-1,-1):
	p8_aspirate({"Position":"M2_POS11","Col":8,"Row":1,"PreAirVolume":20,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":20,"PreAirSpeed":50,"DelayAfterAspirate":1,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 1.5, "TipTouchSpeed": 100})
	# LA PCR oil to Cols 1-6 (CHANGED from 7-12)
	p8_empty({"Position":"M2_POS20","Col":1+i,"Row":1,"EmptyOffsetOfZ":8,"EmptySpeed":30,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	if i == col_num-1 and SampleCount%8 != 0:
		p8_unload_tips({"Position":oil_3[0][0],"Col":oil_3[0][1],"Row":last_row,"Tips":8})
		p8_load_modified(oil_3[0])
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})

def spx_p9_f_0():
	pcr_close_door()
	pcr_run_method({"Methods":["PTseq_LA"]})

Pre_PCR_wait = parallel_block(spx_p9_f_0)

# PCR后纯化准备
lang=get_lang()
if lang==1: #
 report({"Phase": "文库扩增", "Step": "文库扩增后纯化准备", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Library Amplification", "Step": "Preparation for Library Amplification Purification", "TaskType": "library", "RemainingTime": None})


delay({"Duration": 1800})

# C21纯化磁珠分装
'''
=====================================DECK CONFIGURATION========================================
零重用逻辑(Zero-Reuse Logic)：48样本PTseq运行的综合柱配置

Plate 1: M2_POS7 - 试剂中心(Reagent Hub)
此板是甲板的"加油站"。它是固定的，用作所有主混合物和洗涤缓冲液的来源。
- Columns 1-6 (Alcohol): 每列提供足够的80%乙醇用于48个样本的一次完整洗涤循环
- Column 7 (T2 Buffer): 用作整个工作流程中的主要洗脱和重悬缓冲液
- Column 8 (RT Mix): 包含T1/T2反转录主混合物 [预留位置]
- Column 9 (cDNA Mix): 包含T2/T3第一链合成混合物 [预留位置]
- Column 10 (Targeted Amp Mix): 包含T4/T5/T2靶向扩增主混合物
- Column 11 (Library Amp Mix): 包含T7/T8/T2文库扩增主混合物
- Column 12 (T1 Beads): 用于所有清理步骤的磁珠的中央等分试样

Plate 2: M2_POS16 - 共享震荡中心(Shared Orbital Shaking Hub)
M2_POS16 和 M2_POS23 分别作为轨道震荡和磁化的共享中心，而不是特定板的永久位置。
- Columns 1-6 (LA Purification): 最终文库扩增清理的结合位点
- Columns 7-12 (TA Purification): 靶向扩增清理的结合位点
- 废液逻辑: 从这12列吸出的所有上清液直接送到垃圾桶
- 动态使用: 当Plate 3或Plate 4需要高速混合时，临时移动到此位置

Plate 3: M2_POS13 - 库存和测量板(Stock & Measurement Plate) [固定位置]
此板用于高价值存储和测量准备。物理上与珠废物和大容量试剂区域隔离。
- Columns 1-6 (Quantification Mix): 用于等分和混合文库样品与HS dsDNA染料
- Columns 7-12 (Concentrated Library): 最终洗脱的目的地。这些孔包含您的48个高浓度文库产物。
- 震荡器交换: 当需要定量染料混合均质化时，机器人执行临时"震荡器交换"：
  1. 将M2_POS16当前占用者移至M2_POS30中转点
  2. 将Plate 3带入震荡器进行高速服务循环
  3. 混合完成后，将板返回到M2_POS13指定的主位置
  4. 恢复原始占用者到M2_POS16

Plate 4 home moved: M2_POS11 - 废液/矿物油/汇集和DNB站(Waste, Oil, Pooling & DNB Station) [固定位置]
此板原位为POS14，现常驻POS11以减少高频POS14访问。物理上与珠废物和大容量试剂区域隔离。
- Columns 1-6 (Pooling Dilution): 主库存(Plate 3)的等分试样在此稀释以达到目标400ng输入浓度
- Column 7 (Pooling Product): 收集8样本池的最终孔
- Columns 8-9 (Mineral Oil): 矿物油的中间储层，在DNB合成的热循环期间层叠在汇集样品上以防止蒸发
- 震荡器交换: 当需要预汇集稀释的彻底混合时，机器人执行临时"震荡器交换"
  (与Plate 3相同的交换过程)

Quantification tubes home: M2_POS14 [固定位置]
定量阶段临时释放POS13访问位：POS13 product/dye mix整板到空闲POS23，
POS14定量管到POS13执行加液/混匀/读数；定量后POS13定量管回POS14，POS23整板回POS13。

M2_POS30 - 中转点(Transit Spot)
临时存储位置，用于在震荡器交换操作期间保持当前M2_POS16占用者

================================================================================================
'''
# 磁珠位置(板，列，行) - T1 beads for both TA and LA purification
magetic_beads_pos = {"Position":"M2_POS24","Col":1,"Row":1}
# 磁珠预分位置（板，列）- T1 Beads at Column 12
magetic_beads_pre_dispense_pos = {"Position":"M2_POS7","Col":12,"Row":1}
# 回溶液预分位置（板，列）- T2 Buffer at Column 7
elution_buffer_pre_dispense_pos = {"Position":"M2_POS7","Col":7,"Row":1}
# 磁珠分装位置1（板，列，行）- LA Purification at M2_POS16 Columns 1-6
magetic_beads_dispense_pos1 = {"Position":"M2_POS16","Col":1,"Row":1}
magetic_beads_volume1 = 32  # Updated for 0.8× purification of 40 µL LA product

# 磁珠分装位置2（板，列，行）- TA Purification at M2_POS16 Columns 7-12
magetic_beads_dispense_pos2 = {"Position":"M2_POS16","Col":7,"Row":1}
magetic_beads_volume2 = 20

# 计算磁珠分装体积
target_volume_list = [55*(SampleCount//8+1)]*(SampleCount%8)+[55*(SampleCount//8)]*(8-SampleCount%8)

# UPDATED: waste recovered to POS11 deepwell plate Col 1-6 after POS14/POS11 switch
# waste_col_start defined at line ~808, shared by TA and LA purification

# 乙醇位置 - 80% Ethanol at Columns 1-6 (6 wash cycles)
ethanol_pos = {"Position":"M2_POS7","Col":1,"Row":1}

# 双选产物位置 - Concentrated Library destination at POS13 Col 7-12
# Product is dispensed directly to POS13, NOT to POS16
product_pos = {"Position":"M2_POS13","Col":7,"Row":1}



p1_load_modified(tip_1000.load(1)[0])
#增加混匀
p1_mix({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":0.8,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":2,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":30,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":15,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})


for i in range(8):
	p1_aspirate({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":50,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 50, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p1_empty({"Position":magetic_beads_pre_dispense_pos["Position"], "Col":magetic_beads_pre_dispense_pos["Col"], "Row":magetic_beads_pre_dispense_pos["Row"]+i,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":2,"PostAirSpeed":50,"PostAirVolume":25,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

target_tip_num_list = [8]*(sample_num//8) + [sample_num%8]
temp = tip_300.load(8)[0]
p8_load_modified(temp)
p8_mix({"Position":magetic_beads_pre_dispense_pos["Position"], "Col":magetic_beads_pre_dispense_pos["Col"], "Row":1,"PreAirVolume":20,"MixTimes":20,"MixAspirateSpeed":200,"MixAspirateOffsetOfZ":0.5,"MixVolume":60,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":200,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(temp)
for i in range(col_num-1,-1,-1):
	if i == col_num-1 and target_tip_num_list[i] != 8:
		p8_load_modified((temp[0],temp[1],temp[2]+8-sample_num%8))
	elif i == col_num-1:
		p8_load_modified(temp)
	#p8_mix({"Position":magetic_beads_pre_dispense_pos["Position"], "Col":magetic_beads_pre_dispense_pos["Col"], "Row":1,"PreAirVolume":20,"MixTimes":20,"MixAspirateSpeed":200,"MixAspirateOffsetOfZ":0.5,"MixVolume":60,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":200,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	# v12: Conservative PTplus second-bead-transfer style for the LA-product 32 µL aliquot (avoids middle-of-tip air bubble seen in production).
	p8_aspirate({"Position":magetic_beads_pre_dispense_pos["Position"], "Col":magetic_beads_pre_dispense_pos["Col"], "Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.9,"AspirateSpeed":30,"AspirateVolume":magetic_beads_volume1,"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX":1.2, "TipTouchSpeed": 100})
	p8_dispense({"Position":magetic_beads_dispense_pos1["Position"], "Col":magetic_beads_dispense_pos1["Col"]+i, "Row":1,"FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "DispenseOffsetOfZ": 0.8, "DispenseSpeed": 30, "DispenseVolume":magetic_beads_volume1,"DelayAfterDispense": 1, "IsEmpty": True, "EmptyOffsetOfZ": 0.8, "EmptySpeed": 50, "DelayAfterEmpty": 0.5, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})

	# REMOVED: Unused 20 µL bead dispensing to dispense_pos2 (TA purification columns)
	# p8_aspirate({"Position":magetic_beads_pre_dispense_pos["Position"], "Col":magetic_beads_pre_dispense_pos["Col"], "Row":1,"PreAirVolume":35,"AspirateOffsetOfZ":0.5,"AspirateSpeed":30,"AspirateVolume":magetic_beads_volume2,"PreAirSpeed":50,"DelayAfterAspirate":1,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX":1.4, "TipTouchSpeed": 100})
	# p8_dispense({"Position":magetic_beads_dispense_pos2["Position"], "Col":magetic_beads_dispense_pos2["Col"]+i, "Row":1,"FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "DispenseOffsetOfZ": 0.8, "DispenseSpeed": 30, "DispenseVolume":magetic_beads_volume2,"DelayAfterDispense": 1, "IsEmpty": True, "EmptyOffsetOfZ": 2, "EmptySpeed": 30, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})

	if i == col_num-1 and target_tip_num_list[i] != 8:
		p8_unload_modified((temp[0],temp[1],temp[2]+8-sample_num%8))
		p8_load_modified(temp)
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

Pre_PCR_wait.Wait()
pcr_open_door()
# 文库扩增反应后纯化
lang=get_lang()
if lang==1: #
 report({"Phase": "文库扩增反应", "Step": "文库扩增反应后纯化", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Library Amplification", "Step": "Library Amplification Purification", "TaskType": "library", "RemainingTime": None})
 
# 打开pcr盖板
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})

# 转移样本到磁珠1位置
temp = tip_300.load(sample_num,8,1)
for i in range(col_num):
	p8_load_modified(temp[i])
	#p8_mix({"Position":"M2_POS20","Col":1+i,"Row":1,"PreAirVolume":0,"MixTimes":5,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":1,"MixVolume":40,"MixDispenseOffsetOfZ":1,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":1,"MixEmptySpeed":100,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# Transfer 40 µL LA PCR product from Cols 1-6 (CHANGED from 7-12)
	p8_aspirate({"Position":"M2_POS20","Col":1+i,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":30,"AspirateVolume":40,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":magetic_beads_dispense_pos1["Position"], "Col":magetic_beads_dispense_pos1["Col"]+i, "Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ":15, "TipTouchRangeOfX": 1.3, "TipTouchSpeed": 100})
	p8_unload_modified(temp[i])


temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1000, "Duration": 60}})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 0, "Speed": 1000, "Duration": 60}})


delay({"Duration": 300})


###PCR关门
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0}) #PCR盖板
pcr_close_door()

###



###30μL磁珠1振荡位置转移到磁吸位置
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})
delay({"Duration": 120})

# Update position tracking for LA purification (dispense_pos1, not pos2)
if magetic_beads_dispense_pos1["Position"] == "M2_POS16":
	magetic_beads_dispense_pos1["Position"] = "M2_POS23"

# REMOVED: 多余的磁吸-振荡-磁吸循环 (原Lines 1385-1396)
# 正常流程：磁吸分离 → 弃上清，无需再回振荡位重新磁吸

# 逐列去除废液到 POS11 废液板
for i in range(col_num):
	p8_load_modified_BubblePurge(temp[i])
	# Remove 85 µL waste supernatant (Updated from 110 µL for 40 µL product + 32 µL beads)
	# AspirateOffsetOfZ: 0→0.5 (抬起 0.5mm, 和 TA L830 一致, 避免贴底吸入磁珠)
	p8_aspirate({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+i,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":85,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS11","Col":waste_col_start+i,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"TipTouchOffsetOfZ":15,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_modified(temp[i])  # Keep tips for ethanol wash

# 乙醇洗2次
lang=get_lang()
if lang==1: #
 report({"Phase": "Pre-PCR", "Step": "乙醇清洗", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Pre-PCR", "Step": "Ethanol Wash", "TaskType": "library", "RemainingTime": None})

# Reuse temp tips from waste removal for ethanol wash (saves 48 tips)

# v12: LA 乙醇洗涤流程 - 静置等待方案, 加乙醇后不移板/不吹打, 仅做 120 s 磁吸沉降后弃乙醇
for i in range(2):
	# Step 1a: 加乙醇 (板在 POS23 磁铁位)
	for x in range(col_num):
		p8_load_modified_BubblePurge(temp[x])
		p8_aspirate({"Position":ethanol_pos["Position"], "Col":ethanol_pos["Col"]+x, "Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":1.0,"AspirateSpeed":50,"AspirateVolume":200,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x, "Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
		p8_unload_modified(temp[x])

	# Step 2: 静置磁吸沉降 (板始终在 POS23 磁铁位)
	delay({"Duration": 120})

	# Step 4: 弃乙醇 (板在 POS23 磁铁位; AspirateVolume 210→220, 余 +20 µL)
	for x in range(col_num):
		p8_load_modified_BubblePurge(temp[x])
		p8_aspirate({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x, "Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0,"AspirateSpeed":10,"AspirateVolume":220,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS11","Col":waste_col_start+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"TipTouchOffsetOfZ":15,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		# 只在最后一轮丢弃枪头，第一轮放回原位
		if i == 1:
			p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
		else:
			p8_unload_modified(temp[x])

# v12: LA 纯化晾干延时 5 min — 在最后一次乙醇弃液完成后立即起计时
def wait_for_LA_beads_dry():
	delay({"Duration": 300})

LA_dry_wait = parallel_block(wait_for_LA_beads_dry)

LA_dry_wait.Wait()



####回溶
### 25ul洗脱液回溶

Product = tip_50.load(SampleCount,8,1)


for x in range(col_num):
	p8_load_modified(Product[x])
	# Final elution with 23 µL T2 buffer (Updated from 25 µL)
	p8_aspirate({"Position":elution_buffer_pre_dispense_pos["Position"],"Col":elution_buffer_pre_dispense_pos["Col"],"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":23,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_modified(Product[x])

###磁吸位置转移到振荡位置
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1200, "Duration": 30}})

#delay({"Duration": 30})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 0, "Speed": 1200, "Duration": 30}})
delay({"Duration": 300})

###振荡位置转移到磁吸位置
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})
delay({"Duration": 180})

###回收建库产物
# product_pos is already set to M2_POS13 Col 7 - product goes directly there
# (No need to update position - POS13 is fixed destination for concentrated library)
for x in range(col_num):
	p8_load_modified_BubblePurge(Product[x])
	# Recover 21 µL final library product (SOP: 23 µL elution → 21 µL recovery)
	p8_aspirate({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0,"AspirateSpeed":10,"AspirateVolume":21,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":product_pos["Position"],"Col":product_pos["Col"]+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":10,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	#p8_mix({"Position":product_pos["Position"],"Col":product_pos["Col"]+x,"Row":1,"PreAirVolume":0,"MixTimes":8,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":18,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":40,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":2,"TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_mix({"Position":product_pos["Position"],"Col":product_pos["Col"]+x,"Row":1,"PreAirVolume":20,"MixTimes":10,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":10,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":1, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty({"Position":product_pos["Position"],"Col":product_pos["Col"]+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":10,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# Move purification plate back from magnet to shaker position
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})

# REMOVED: No need to transfer plate to POS13 - product was dispensed directly to POS13
# transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS13","LoosenOffsetOfZ":0})
# product_pos["Position"] = "M2_POS13"

'''=====================================定量=============================================================='''

#======================物料设置=============================================================
lang=get_lang()
if lang==1: #
 report({"Phase": "定量", "Step": "定量", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Quantification", "Step": "Quantification", "TaskType": "library", "RemainingTime": None})

# 定量样本数
sample_num = SampleCount

# 样本定量阶段，只支持PCR，Extract，DNB
sample_stage = 'PCR'

# 染料位置,板位，列，行
dye_loc = ('M2_POS4',1,1)

# 分装染料取枪头位置，板位，列，行
dye_tip = tip_300.load(8,8,1)[0]  # reuse_index=1 (tips reused, same as PTseq Plus)

# 稀释样本取枪头位置，列表，内置位置，必须是整列，可多不可少
sample_dilute_tip_loc = tip_50.load(sample_num,8,1)

# 样本来源起始位置,板位，起始列，样本必须从上到下，从左到右，从第一个开始
source_plate = ['M2_POS13',7]

# 样本染料混合起始位置 - Plate 3 (M2_POS13) Quantification Mix at Columns 1-6
# 必须是深孔板，板位，起始列，样本必须从上到下，从左到右，从第一个开始
dye_mix_plate = ['M2_POS13',1]

# POS14/POS11 switched: quantification tubes live at POS14 and are accessed at POS13 after plate swap.
quantification_tube_home_pos = 'M2_POS14'
quantification_tube_operating_pos = 'M2_POS13'
# 定量管操作位置,板位，起始列，样本必须从上到下，从左到右，从第一个开始
quantification_tube_loc = [quantification_tube_operating_pos,1]

#=====================定量浓度输出文件位置======================================
import time
# 获取当前日期和时间
current_datetime = time.strftime("%Y%m%d_%H%M%S")
# 生成文件路径
file_path = f"D:\\data\\PTseq_Library.xlsx"
quantification_fila_path = f"D:\\data\\quantification{current_datetime}.txt"




#=================================== 函数计算部分#===================================
col_num = (sample_num+7)//8
# 本部分为获取特定位置的浓度,pos为位置元组，板列行
def get_concentration_modified(pos):
	# 文档要求输入为板行列，所以对位置数组做一个预处理
	try:
		spx_concentration = find_sampling_concentration(pos[0],pos[2],pos[1])
		if spx_concentration is None:
			print(f"  [WARNING] No concentration data at {pos}")
			return 0.0
		return spx_concentration.Consistence
	except Exception as e:
		print(f"  [WARNING] get_concentration error at {pos}: {e}")
		return 0.0
# 单个定量管位置，板列行
quantification_tubes = [(quantification_tube_loc[0],quantification_tube_loc[1]+i//8,1 + i%8) for i in range(sample_num)]

# 用于存储当前定量结果
concentration_list = []


# 单个定量管位置，板列行
quantification_tubes = [(quantification_tube_loc[0],quantification_tube_loc[1]+i//8,1 + i%8) for i in range(sample_num)]
#=================================== 样本稀释部分#===================================
# TEMPLATE WORKFLOW: Mix in dye_mix_plate (M2_POS13), shake at POS16, transfer to quant tubes after POS14 -> POS13 swap.

# Step 1: Dispense dye to dye_mix_plate (M2_POS13 columns 1-6)
if sample_num%8 == 0:
	last_row = 1
else:
	last_row = 9-(sample_num%8)

for i in range(col_num-1,-1,-1):
	# Handle partial column for last column
	if i == col_num - 1:
		p8_load_tips({"Position":dye_tip[0],"Col":dye_tip[1],"Row":last_row,"Tips":8})
	# Dispense dye 217.8µL x 1 (same as PTseq Plus, 1:100 dilution with 2.2µL sample)
	for j in range(1):
		p8_aspirate_modified(dye_loc[0], Row=dye_loc[2], Col=dye_loc[1], AspirateVolume=217.8, PreAirVolume=10, AspirateOffsetOfZ=1.0)
		p8_empty_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i, EmptyOffsetOfZ=3+2*j, TipTouchTimes=1)
	# Handle tip management for partial column
	if i == col_num - 1 and sample_num%8!=0:
		p8_unload_tips({"Position":dye_tip[0],"Col":dye_tip[1],"Row":last_row,"Tips":8})
		p8_load_tips({"Position":dye_tip[0],"Col":dye_tip[1],"Row":1,"Tips":8})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# Step 2: Add sample to dye_mix_plate and mix
for i in range(col_num):
	p8_load_modified(sample_dilute_tip_loc[i])
	p8_aspirate_modified(source_plate[0], 1, source_plate[1]+i, 2.2, AspirateSpeed=2, AspirateOffsetOfZ=2, IfTrack=True)
	p8_empty_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i, EmptyOffsetOfZ=12)
	# Mix sample with dye in dye_mix_plate
	p8_mix({"Position":dye_mix_plate[0],"Col":dye_mix_plate[1]+i,"Row":1,"PreAirVolume":10,"MixTimes":2,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":1,"MixVolume":40,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_modified(sample_dilute_tip_loc[i])

# Step 3: Shaking - Move POS16 to POS23, move POS13 to POS16, shake, then restore
# Move current POS16 occupant to POS23 (temporary storage)
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})
# Move dye_mix_plate (POS13) to shaker position (POS16)
transfer({"StartPosition":"M2_POS13","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})
# Shake in both directions
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": 60}, "ShakerParameters": {"IsEnable": True,"Direction": 0,"Speed": 1200,"Duration": 60}})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": 60}, "ShakerParameters": {"IsEnable": True,"Direction": 1,"Speed": 1200,"Duration": 60}})
# Move dye_mix_plate back to POS13
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS13","LoosenOffsetOfZ":0})
# Restore original POS16 occupant from POS23
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})

# Step 4: Park the POS13 product/dye mix plate in empty POS23, then move quantification tubes to POS13.
transfer({"StartPosition":"M2_POS13","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})
dye_mix_plate[0] = "M2_POS23"
transfer({"StartPosition":quantification_tube_home_pos,"EndPosition":quantification_tube_operating_pos,"LoosenOffsetOfZ":0})

# Step 5: Transfer from the same dye_mix_plate wells, now parked at POS23, to quantification tubes at POS13.
for i in range(col_num):
	p8_load_modified(sample_dilute_tip_loc[i])
	# Transfer 4x50µL from dye_mix_plate to quantification tubes
	for x in range(4):
		p8_aspirate_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i, PreAirVolume=5, AspirateVolume=50, AspirateOffsetOfZ=1, PostAirVolume=3, IfTrack=True)
		p8_empty_modified(quantification_tube_loc[0], Row=1, Col=quantification_tube_loc[1]+i, EmptyOffsetOfZ=5, EmptySpeed=80)
	# Mix in quantification tubes
	p8_mix({"Position":quantification_tube_loc[0],"Col":quantification_tube_loc[1]+i,"Row":1,"PreAirVolume":0,"MixTimes":5,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.5,"MixVolume":40,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":20,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":2,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty_modified(quantification_tube_loc[0], Row=1, Col=quantification_tube_loc[1]+i, EmptyOffsetOfZ=5, EmptySpeed=80)
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 依次定量
for i in range(col_num):
	p8_load_quantification_tube({"Position": quantification_tube_loc[0], "Row": 1, "Col": quantification_tube_loc[1]+i, "Tips":8})
	spx_quantity_result = quantity_run_sample({"Name":"","SampleType": "dsDNA_HS", "ProductType": sample_stage, "StandardToSampleRatio": 5, "DilutionRatio":1,"Label":"","DilutionAssessment": 60})
	cur_concentration_list = [get_concentration_modified((quantification_tube_loc[0],quantification_tube_loc[1]+i,j)) for j in range(1,9)]
	concentration_list += cur_concentration_list
	p8_unload_quantification_tube({"Position": quantification_tube_loc[0], "Row": 1, "Col": quantification_tube_loc[1]+i, "Tips":8})
output_quantitative_data({"ProductType":sample_stage,"FilePath":file_path})

# Restore quantification tubes to POS14 and the product/dye mix plate to POS13.
transfer({"StartPosition":quantification_tube_operating_pos,"EndPosition":quantification_tube_home_pos,"LoosenOffsetOfZ":0})
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS13","LoosenOffsetOfZ":0})
dye_mix_plate[0] = "M2_POS13"

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





# [v7] 不再交换POS13和POS14，library产物留在POS13 Col 7-12原位
# product_pos 保持 "M2_POS13" 不变














# [v7] 删除了原本在此处的错位"第二次定量(DNB)"段落（原v6第1595-1760行）
# 该段在pooling和make DNB之前就尝试定量DNB产物，逻辑错误
# 正确的DNB定量将在make DNB完成后执行（见脚本末尾）

# Hybridization_num 在pooling段根据SampleCount重新计算，此处不再需要

'''=====================================pooling（带混匀）=============================================================='''
lang=get_lang()
if lang==1: #
 report({"Phase": "pooling", "Step": "pooling", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "pooling", "Step": "pooling", "TaskType": "library", "RemainingTime": None})

pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0}) #PCR盖板
#==========================输入部分=============================

# 单产品pooling方案

#样本来源板,板位，起始列
source_plate = ('M2_POS13',7)

# Pooling dilution: take 2 µL of each library product from POS13 Cols 7-12 to dedicated dilution wells at POS8 Cols 7-12 (independent of the source plate).
sample_dilution_place = ('M2_POS8',7)   # 稀释位置 = POS8 PCR板 col 7-12（独立稀释孔）

# 样本取样体积临界值
min_sample_volume = 2
max_sample_volume = 20


#单个DNB样本数
single_dnb_sample_num = SampleCount
# 单个DNB投入量 (G99说明书: 1pmol ≈ 200ng for ~300bp fragments)
target_dna_ng = 200
#pooling总体积
target_pooling_volume = 48
# 质控浓度
sample_qc_concentration = 10

#pooling取buffer使用1ml枪头
single_tip_loc = tip_1000.load(1)[0]
#pooling稀释buffer位置，板-列-行 - M2_POS24 B1 (Col 1, Row 2) contains T2 buffer
dilution_buffer_loc = ('M2_POS24',1,2)
#pooling产物位置，板位，列，行 - POS14/POS11 switched: pooling product plate now lives at M2_POS11 Column 7
target_tube_loc = [('M2_POS11',7,i) for i in range(1,9)]
# [v7] DNB反应位置 - Column布局: Col 7 Row 1-6 为环化, Col 8 Row 1-6 为DNB制备
# SIRO48最多48样本, 每8个一组, 最多6个pool
target_dnb_loc_list = [('M2_POS20',7,1+i) for i in range(6)]
#pooing取样本枪头位置，要求位置数组，板位，列，行
# sample_pooling_tip_loc = tip_50.load(sample_num,1) # sample_pooling_tip_loc = [('M2_POS15',i//8 + 1,8-i%8) for i in range(sample_num)]
# 混匀DNB的枪头位置，要求位置数组，板位，列，行
dilution_mix_tip_loc = None
# dilution_mix_tip_loc = [('M2_POS15',i//8 + 1,8-i%8) for i in range(4)]

# 转移DNB的枪头位置，要求位置数组，板位，列，行
dilution_transfer_tip_loc = None
# dilution_mix_tip_loc = [('M2_POS15',i//8 + 1,8-i%8) for i in range(4)]


#===================以下部分为可选的补充参数，当需要筛选pooling文库时输入============================
# 这里输入空白部分是否一起pooling，默认不pooling，True为pooling，False为不pooling
Is_blank_pooling = False
# 这里输入样本信息用于确认哪个孔是空白对照,不填无法过滤空白样本位置
sample_info_file = 'D:\\data\\sample_info.txt'
# 浓度不合格样本是否一起pooling，默认不pooling（与 NIFTY Pro、PTseq Plus DNB pre-pool 一致：DNB 制备前剔除低浓度样本）
Is_unqualified_pooling = False
output_file_path = r"D:/data/PTseq_pooling_info.csv"





#====================执行部分==============================================================
#===================本部分依据体积计算所有的样本pooling方案和体积=========================
class Sample:
	def __init__(self, SampleWellPosition,SampleWellColumn ,SampleWellRow , Concentration,DilutingWellPosition,DilutingWellColumn,DilutingWellRow,DilutingSampleVolume=0, DilutingBufferVolume=0, sample_id = ""):
		self.SampleWellPosition = SampleWellPosition
		self.SampleWellRow = SampleWellRow
		self.SampleWellColumn = SampleWellColumn
		self.Concentration = Concentration
		self.DilutingWellPosition = DilutingWellPosition
		self.DilutingWellRow = DilutingWellRow
		self.DilutingWellColumn = DilutingWellColumn
		self.DilutingSampleVolume = DilutingSampleVolume
		self.DilutingBufferVolume = DilutingBufferVolume
		self.NeedDilution = False
		self.sample_id = sample_id
		self.SampleType = ""  # Initialize SampleType attribute to prevent AttributeError
		self.sample_initial_index = 0  # Initialize to prevent AttributeError




#=============================== 函数计算部分#===================================
col_num = (sample_num+7)//8
#根据板位计算孔位，板-列-行
sample_list = [(source_plate[0],source_plate[1]+i//8,1+i%8) for i in range(sample_num)]
dilute_hole = [(sample_dilution_place[0],sample_dilution_place[1]+i//8,1+i%8) for i in range(sample_num)]

# [v7] 使用第一次定量的实际测量浓度值（concentration_list来自第一次定量段落）
# 删除了原本硬编码的48个浓度值





sample_concentration = [Sample(*sample_list[i], concentration_list[i], *dilute_hole[i], DilutingSampleVolume=0, DilutingBufferVolume=0) for i in range(sample_num)]
# Always initialize sample_initial_index for all samples
for i in range(sample_num):
	sample_concentration[i].sample_initial_index = i
	# If filtered_samples exists, update sample_id from CSV
	if filtered_samples and i < len(filtered_samples):
		sample_concentration[i].sample_id = filtered_samples[i].sample_id
	else:
		# Generate default sample_id if no CSV file
		sample_concentration[i].sample_id = f"Sample_{i+1}"
initial_samples = [each for each in filtered_samples] if filtered_samples else []
if not Is_unqualified_pooling:
	sample_concentration = [each for each in sample_concentration if each.Concentration >= sample_qc_concentration]

if not Is_blank_pooling:
	try:
		sample_concentration = [each for each in sample_concentration if each.SampleType != '空白对照']
	except:
		pass




#按浓度计算pooling分组
sample_num = len(sample_concentration)
# 计算DNB数量
target_dnb_num = (sample_num+single_dnb_sample_num-1)//single_dnb_sample_num
# Update Hybridization_num to match calculated DNB count
Hybridization_num = target_dnb_num

x,y = divmod(sample_num,target_dnb_num)
# 把sorted_volume分成target_dnb_num组，分组后每组的样本数为x+1或x，以下位代码实现分组
dnb_list = []
start_index = 0
for i in range(target_dnb_num):
	if i < y:
		group_size = x + 1
	else:
		group_size = x
	end_index = start_index + group_size
	group = sample_concentration[start_index:end_index]
	dnb_list.append(group)
	start_index = end_index

# 存储原本的dnblist - MUST be done AFTER dnb_list is populated
initial_dnb_list = [group.copy() for group in dnb_list]  # Deep copy of groups


# 补水的位置
water_loc_list = []

# 计算每组样本浓度最大值和最小值是否差10倍，如果出现了，就需要将浓度高于最小值10倍的样本标记为需要预稀释，最小值设置为sample_qc_concentration
for i in range(target_dnb_num):
	cur_samples = dnb_list[i]
	cur_l = len(cur_samples)
	max_concentration = max([each.Concentration for each in cur_samples])
	min_concentration = max(min([each.Concentration for each in cur_samples]),sample_qc_concentration)
	for j,each in enumerate(cur_samples):
		if each.Concentration < min_concentration:
			cur_samples[j].Concentration = min_concentration
	if max_concentration/min_concentration > 8:
		for j,each in enumerate(cur_samples):
			if each.Concentration >= min_concentration*8:
				cur_samples[j].NeedDilution = True
				cur_samples[j].Concentration /= 8
				water_loc_list.append((each.DilutingWellPosition,each.DilutingWellRow,each.DilutingWellColumn))
			else:
				cur_samples[j].NeedDilution = False


# 计算每组样本的放大倍数
def get_sample_volume(cur_samples):
	concentrate_times = 1
	res = []
	l = len(cur_samples)
	target_volume_list = [round(target_dna_ng*concentrate_times/l/each.Concentration,2) for each in cur_samples]
	while min(target_volume_list)<min_sample_volume:
		concentrate_times += 1
		target_volume_list = [round(target_dna_ng*concentrate_times/l/each.Concentration,2) for each in cur_samples]
	while min(target_volume_list)>=min_sample_volume and max(target_volume_list) > max_sample_volume:
		concentrate_times -= 0.1
		target_volume_list = [round(target_dna_ng*concentrate_times/l/each.Concentration,2) for each in cur_samples]
	if min(target_volume_list) <min_sample_volume:
		concentrate_times += 0.1
		target_volume_list = [round(target_dna_ng*concentrate_times/l/each.Concentration,2) for each in cur_samples]
	for i,each in enumerate(cur_samples):
		cur_samples[i].DilutingSampleVolume = target_volume_list[i]
	if concentrate_times >=8:
		water_volume = target_pooling_volume*8-sum(target_volume_list)
	else:
		water_volume = target_pooling_volume*concentrate_times-sum(target_volume_list)
	return concentrate_times,water_volume




# 计算每组样本的放大倍数和稀释液体积


#此部分为pooling
temp = [(n,water_volume) for n,water_volume in [get_sample_volume(each) for each in dnb_list]]
water_volume_list = [each[1] for each in temp]
def output_hybrid_pooling_info(samples, temp, output_file_path):
	"""
	将每个样本的 pooling 组、取样体积、稀释倍数和放大倍数输出到文件中
	:param samples: dnb_list分组列表，每组包含Sample对象
	:param temp: 包含放大倍数的列表，格式为 [(放大倍数, 水体积), ...]
	:param output_file_path: 输出文件路径
	"""
	with open(output_file_path, 'w', encoding='utf-8') as f:
		# 写入表头
		f.write("样本编号,Pooling组,杂交浓度,取样体积(ul),稀释倍数,放大倍数\n")
		# 获取当前日期时间
		current_time = time.localtime()
		formatted_time = time.strftime("%yP%m%d%H%M%S", current_time)
		# 记录已输出的样本index，用于识别被过滤掉的样本
		pooled_indices = set()
		# 遍历每个pooling组，直接写每个样本各自的数据
		for i, group in enumerate(samples):
			cur_pooling_id = f"{formatted_time}{i+1}"
			concentrate_times = temp[i][0]
			for sample in group:
				pooled_indices.add(sample.sample_initial_index)
				dilution_type = 8 if sample.NeedDilution else 1
				formated_vol = "%.2f" % sample.DilutingSampleVolume
				idx = sample.sample_initial_index
				conc = concentration_list[idx] if idx < len(concentration_list) else 0
				f.write(f"{sample.sample_id},{cur_pooling_id},{conc},{formated_vol},{dilution_type},{concentrate_times}\n")
		# 输出被过滤掉的样本（不在任何pool中），标记为'-'
		for idx in range(len(concentration_list)):
			if idx not in pooled_indices:
				sid = filtered_samples[idx].sample_id if (filtered_samples and idx < len(filtered_samples)) else f"Sample_{idx+1}"
				f.write(f"{sid},'-',{concentration_list[idx]},,,\n")
# 调用函数输出信息
output_hybrid_pooling_info(dnb_list, temp, output_file_path)
print(f"样本的 pooling 组、取样体积、稀释倍数和放大倍数已输出到文件：{output_file_path}")


# [v7] ===== Normalization + Pooling 重写 =====
# 流程: POS11→POS23 → 原位稀释(POS13) → pooling(POS13→POS23) → 转移到POS20 → POS23→POS11

# Step 1: 移动POS11 (原POS14 pooling板) 到POS23 (空闲, p1/p8均可达)
transfer({"StartPosition":"M2_POS11","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})  # POS11 → POS23

# 操作时pooling管在POS23 Col 7
pooling_tube_pos = 'M2_POS23'
pooling_tube_col = 7

# Step 2: Normalization - 原位稀释高浓度样本 (p1加T2 buffer到POS13 Col 7-12)
p1_load_tips({"Position":single_tip_loc[0],'Col':single_tip_loc[1],'Row':single_tip_loc[2]})

if water_loc_list:
	for i in range(len(water_loc_list)):
		# 加入14µL T2 buffer到POS8 PCR板稀释孔 (2µL sample + 14µL buffer = 16µL, 8x dilution)
		p1_aspirate({"Position": dilution_buffer_loc[0], "Row": dilution_buffer_loc[2], "Col": dilution_buffer_loc[1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "PreAirSpeed": 100, "PreAirVolume": 10, "SecondSegmentSpeed": 100, "AspirateOffsetOfZ": 1.0, "AspirateSpeed": 20, "AspirateVolume": 14, "DelayAfterAspirate": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100, "PostAirSpeed": 100, "PostAirVolume": 10})
		p1_empty({"Position": water_loc_list[i][0], "Row": water_loc_list[i][1], "Col": water_loc_list[i][2], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100, "EmptyOffsetOfZ": 1, "EmptySpeed": 190, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})

# No standalone mix step here: dilution wells are filled later in Step 5 of the pool loop, where sample and buffer are mixed together at dispense time.

# Step 4: p1 加补水到pooling管 (POS23 Col 7) 和 DNB反应孔 (POS20)
for i in range(len(water_volume_list)):
	if temp[i][0]>=8:
		new_water_volume = target_pooling_volume-target_pooling_volume/(temp[i][0]/8)
		p1_aspirate({"Position": dilution_buffer_loc[0], "Row": dilution_buffer_loc[2], "Col": dilution_buffer_loc[1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "PreAirSpeed": 100, "PreAirVolume": 10, "SecondSegmentSpeed": 100, "AspirateOffsetOfZ": 1.0, "AspirateSpeed": 20, "AspirateVolume": new_water_volume, "DelayAfterAspirate": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100, "PostAirSpeed": 100, "PostAirVolume": 10})
		p1_empty({"Position": target_dnb_loc_list[i][0], "Row": target_dnb_loc_list[i][2], "Col": target_dnb_loc_list[i][1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100, "EmptyOffsetOfZ": 2, "EmptySpeed": 190, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})
	p1_aspirate({"Position": dilution_buffer_loc[0], "Row": dilution_buffer_loc[2], "Col": dilution_buffer_loc[1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "PreAirSpeed": 100, "PreAirVolume": 10, "SecondSegmentSpeed": 100, "AspirateOffsetOfZ": 1.0, "AspirateSpeed": 100, "AspirateVolume": water_volume_list[i], "DelayAfterAspirate": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100, "PostAirSpeed": 100, "PostAirVolume": 10})
	p1_empty({"Position": pooling_tube_pos, "Row": i+1, "Col": pooling_tube_col, "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100, "EmptyOffsetOfZ": 5, "EmptySpeed": 190, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})

p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# Step 5: p8 pool 转移（非稀释直转 POS13→POS23；稀释分支 POS13→POS8 mix→POS8→POS23）
for i,poolings in enumerate(temp):
	samples = dnb_list[i]
	for sample in samples:
		p8_load_modified(tip_50.load(1)[0])
		sample_volume = sample.DilutingSampleVolume
		if not sample.NeedDilution:
			p8_aspirate_modified(sample.SampleWellPosition, sample.SampleWellRow, sample.SampleWellColumn, sample_volume, PreAirVolume=10)
			p8_empty_modified(pooling_tube_pos, i+1, pooling_tube_col)
		else:
			p8_aspirate_modified(sample.SampleWellPosition, sample.SampleWellRow, sample.SampleWellColumn, 2, PreAirVolume=5, PostAirVolume=0)
			p8_empty_modified(sample.DilutingWellPosition, sample.DilutingWellRow, sample.DilutingWellColumn, EmptyOffsetOfZ=0.5, EmptySpeed=10)
			p8_mix({"Position":sample.DilutingWellPosition,"Col":sample.DilutingWellColumn,"Row":sample.DilutingWellRow,"PreAirVolume":10,"MixTimes":5,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.5,"MixVolume":30,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":100,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":0,"TipTouchOffsetOfZ":5,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100})
			p8_aspirate_modified(sample.DilutingWellPosition, sample.DilutingWellRow, sample.DilutingWellColumn, sample_volume, PreAirVolume=0, PostAirVolume=0)
			p8_empty_modified(pooling_tube_pos, i+1, pooling_tube_col)
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# Step 6: 混匀pooling管并转移到POS20 Col 7 Row 1-6 (DNB环化反应位)
for i in range(target_dnb_num):
	target_tip_loc = tip_300.load(1)
	target_tip_pos,target_tip_col,target_tip_row = target_tip_loc[0]
	p8_load_tips({"Position": target_tip_pos, "Row": target_tip_row, "Col": target_tip_col})
	# 混匀pooling管
	p8_mix({"Position":pooling_tube_pos,"Col":pooling_tube_col,"Row":i+1,"PreAirVolume":0,"MixTimes":20,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":1,"MixVolume":240,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":100,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":200,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

	# 转移到POS20 Col 7 (环化反应位)
	dilution_transfer_tip_loc_tmp = tip_50.load(1)
	target_tip_pos,target_tip_col,target_tip_row = dilution_transfer_tip_loc_tmp[0]
	p8_load_tips({"Position": target_tip_pos, "Row": target_tip_row, "Col": target_tip_col})
	if temp[i][0] >= 8:
		target_sample_volume = target_pooling_volume/(temp[i][0]/8)
	else:
		target_sample_volume = target_pooling_volume
	p8_aspirate_modified(pooling_tube_pos,i+1,pooling_tube_col,target_sample_volume,AspirateSpeed=10)
	p8_empty_modified(target_dnb_loc_list[i][0],target_dnb_loc_list[i][2],target_dnb_loc_list[i][1])
	p8_mix({"Position":target_dnb_loc_list[i][0],"Col":target_dnb_loc_list[i][1],"Row":target_dnb_loc_list[i][2],"PreAirVolume":0,"MixTimes":3,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.5,"MixVolume":40,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":100,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":200,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty_modified(target_dnb_loc_list[i][0],target_dnb_loc_list[i][2],target_dnb_loc_list[i][1])
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# Step 7: 移回POS23 → POS11，关PCR盖板
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS11","LoosenOffsetOfZ":0})  # POS23 → POS11 (恢复)
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})  #关PCR盖板
pcr_close_door()




#######################################################make DNB#########################################
DNB_Num = target_dnb_num

#假设pooling产物在POS20第1列，make DNB暂定POS20第2列

##################################################################################### 单链环化 ######################################################################################
### Note: PCR door is already closed by the pcr_close_door() above; do not reopen it here.
### blockSS needs door CLOSED to run PTseq_DNB_cycling_1st.
lang=get_lang()
if lang==1: #
 report({"Phase": "单链环化", "Step": "单链反应程序", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Single-Strand Cyclization", "Step": "Single-Strand Reaction Program", "TaskType": "library", "RemainingTime": None})

def blockSS():
	pcr_run_method({"Methods": ["PTseq_DNB_cycling_1st"]})
ss = parallel_block(blockSS)

transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})###开试剂盖板

#配置环化反应液——D1 Buffer打入D2 Enzyme源管混合（big-into-small, D4工作管保留但不使用）
#DNB Cycling: D1 buffer(大体积) → D2 enzyme tube → mix in D2 → 后续直接从D2分装
p8_load_modified(tip_300.load(1)[0])
# Step 1: 吸取D1环化反应缓冲液——手工配置环化酶量 = 0.5*(DNB_Num+1) µL 在D2 enzyme管中
p8_aspirate({"Position":"M2_POS17", "Col":1, "Row":4,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":11.6 * (DNB_Num + 1),"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
# Step 2: 打入D2 enzyme源管 (big into small, 冲洗小体积enzyme)
p8_empty({"Position":"M2_POS17","Col":2,"Row":4,"EmptyOffsetOfZ":0.5,"EmptySpeed":10,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 0, "TipTouchSpeed": 100})
# Step 3: 在D2管中混合Enzyme + Buffer
p8_mix({"Position":"M2_POS17","Col":2,"Row":4,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":50,"MixAspirateOffsetOfZ":0.5,"MixVolume":10*DNB_Num,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":50,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})###关试剂盖板
ss.Wait()
###PCR开门
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0}) #开PCR盖板
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})###开试剂盖板
# [v7] 加入环化mix - Column布局: POS20 Col 7, Row 1-6
DNB_mix_cycling = tip_300.load(DNB_Num,1)
for x in range(DNB_Num):
	p8_load_modified(DNB_mix_cycling[x])
	# DNB Cycling Mix: 12.1 µL per reaction (从D2源管取, big-into-small后混合液在D2中)
	p8_aspirate({"Position":"M2_POS17", "Col":2, "Row":4,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":12.1,"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty({"Position":"M2_POS20","Col":7,"Row":1+x,"EmptyOffsetOfZ":0.5,"EmptySpeed":5,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 0, "TipTouchSpeed": 100})
	p8_mix({"Position":"M2_POS20","Col":7,"Row":1+x,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":30,"MixAspirateOffsetOfZ":0.5,"MixVolume":40,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":30,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS20","Col":7,"Row":1+x,"EmptyOffsetOfZ":0.5,"EmptySpeed":5,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 0, "TipTouchSpeed": 100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# [已移除] MakeDNB环节不添加矿物油（与CNVseq/PTseq Plus/NIFTY保持一致）

###PCR关门
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0}) #PCR盖板
pcr_close_door()
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})###关试剂盖板
###
lang=get_lang()
if lang==1: #
 report({"Phase": "单链环化", "Step": "环化反应程序", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Single-Strand Circularization", "Step": "Circularization Reaction Program", "TaskType": "library", "RemainingTime": None})
def blockC():
	pcr_run_method({"Methods": ["PTseq_DNB_cycling_2nd"]})
cycling_block = parallel_block(blockC)


cycling_block.Wait()

###PCR开门
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0}) #开PCR盖板


##################################################################################### DNB制备体系1 ############################################################################

transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})###开盖板

# [v7] 分装DNB制备缓冲液 - 10 µL per reaction → POS20 Col 8, Row 1-6
p8_load_modified(tip_50.load(1)[0])
for x in range(DNB_Num):
	p8_aspirate({"Position":"M2_POS17", "Col":3, "Row":5,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":10,"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty({"Position":"M2_POS20","Col":8,"Row":1+x,"EmptyOffsetOfZ":0.5,"EmptySpeed":3,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 0, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})


# [v7] 加样本（从环化反应孔Col 7转移到DNB制备孔Col 8）— 循环处理所有DNB组
DNB1_mix = tip_300.load(DNB_Num,1)
for x in range(DNB_Num):
	p8_load_modified(DNB1_mix[x])
	# 混合环化产物 (Col 7, Row 1+x)
	p8_mix({"Position":"M2_POS20","Col":7,"Row":1+x,"PreAirVolume":10,"MixTimes":10,"MixAspirateSpeed":30,"MixAspirateOffsetOfZ":0.5,"MixVolume":40,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":30,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 从环化孔吸取10µL样本 (Col 7, Row 1+x)
	p8_aspirate({"Position":"M2_POS20","Col":7,"Row":1+x,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":10,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 分装到DNB制备孔 (Col 8, Row 1+x)
	p8_empty({"Position":"M2_POS20","Col":8,"Row":1+x,"EmptyOffsetOfZ":0.8,"EmptySpeed":20,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 混合DNB制备体系 (Col 8, Row 1+x)
	p8_mix({"Position":"M2_POS20","Col":8,"Row":1+x,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":30,"MixAspirateOffsetOfZ":0.5,"MixVolume":15,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":30,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

###PCR关门
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0}) #PCR盖板
pcr_close_door()
###
lang=get_lang()
if lang==1: #
 report({"Phase": "DNB制备", "Step": "DNB制备程序1", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "DNB Preparation", "Step": "DNB Preparation Procedure 1", "TaskType": "library", "RemainingTime": None})
def blockD1():
	pcr_run_method({"Methods": ["PTseq_DNB_1st"]})
d1 = parallel_block(blockD1)

##################################################################################### DNB制备体系2 ############################################################################
#配置DNB制备体系2——E1 Mix I打入E2 Mix II源管混合（big-into-small, E5工作管保留但不使用）
#DNB Polymerase: E1 Mix I(大体积) → E2 Mix II tube → mix in E2 → 后续直接从E2分装
p8_load_modified(tip_300.load(1)[0])
# Step 1: 吸取E1 DNB聚合酶混合液I——手工配置DNB聚合酶混合液II = 2*(DNB_Num+0.5) µL 在E2 Mix II管中
p8_aspirate({"Position":"M2_POS17", "Col":1, "Row":5,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":20 * (DNB_Num + 0.5),"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
# Step 2: 打入E2 Mix II源管 (big into small, 冲洗小体积Mix II)
p8_empty({"Position":"M2_POS17","Col":2,"Row":5,"EmptyOffsetOfZ":0.5,"EmptySpeed":10,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 0, "TipTouchSpeed": 100})
# Step 3: 在E2管中混合Mix I + Mix II
p8_mix({"Position":"M2_POS17","Col":2,"Row":5,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":30,"MixAspirateOffsetOfZ":0.5,"MixVolume":20*DNB_Num,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":30,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})###关盖板
d1.Wait()
###PCR开门
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0}) #开PCR盖板
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})###开盖板
#加入聚合酶mix

##################################################################################### DNB制备体系2 ############################################################################

# [v7] 加入DNB聚合酶混合液mix（LC） → POS20 Col 8, Row 1-6 (从E2源管取, big-into-small后混合液在E2中)
DNB_mix_2 = tip_300.load(DNB_Num,1)
for x in range(DNB_Num):
	p8_load_modified(DNB_mix_2[x])
	p8_aspirate({"Position":"M2_POS17", "Col":2, "Row":5,"PreAirVolume":2,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":22,"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty({"Position":"M2_POS20","Col":8,"Row":1+x,"EmptyOffsetOfZ":0.5,"EmptySpeed":10,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 0, "TipTouchSpeed": 100})
	p8_mix({"Position":"M2_POS20","Col":8,"Row":1+x,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":30,"MixAspirateOffsetOfZ":0.5,"MixVolume":35,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":30,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})


transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})###关盖板

###PCR关门
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0}) #关PCR盖板
pcr_close_door()
###
lang=get_lang()
if lang==1: #
 report({"Phase": "DNB制备", "Step": "DNB制备程序2", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "DNB Preparation", "Step": "DNB Preparation Procedure 2", "TaskType": "library", "RemainingTime": None})


def blockD2():
	pcr_run_method({"Methods": ["PTseq_DNB_2nd"]})
d2 = parallel_block(blockD2)


# Removed: Hybridization product recovery artifact
# This step was unnecessary - library products remain at M2_POS13, Columns 7-12

d2.Wait()


###PCR开门
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0}) #开PCR盖板
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})###开盖板

# [v7] 加入DNB终止缓冲液 → POS20 Col 8, Row 1-6
DNB_temp1_300 = tip_300.load(DNB_Num,1)
for x in range(DNB_Num):
	p1_load_modified(DNB_temp1_300[x])
	p1_aspirate({"Position":"M2_POS17", "Col":4, "Row":5,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":10,"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS20","Col":8,"Row":1+x,"EmptyOffsetOfZ":0.5,"EmptySpeed":50,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 0, "TipTouchSpeed": 100})
	p1_mix({"Position":"M2_POS20","Col":8,"Row":1+x,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":0.5,"MixVolume":40,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# DNB定量已移除 - DNB为单链DNA，机上dsDNA_HS无法准确定量，改为手动ssDNA kit定量

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})###关盖板
###PCR关门
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0}) #PCR盖板
pcr_close_door()

def blockD3():
	pcr_run_method({"Methods": ["4keep"]})
d3 = parallel_block(blockD3)

d3.Wait()

# Home all axes at end of run to allow easy sample retrieval
home()
