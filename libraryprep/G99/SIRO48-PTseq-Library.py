
# -*- coding: utf-8 -*-
#####################################################################
# SIRO48-PTseq-Library-G99 (仅建库+定量，无pooling/DNB)
#####################################################################
# 基于 working.py (full-process G99)
# 删除pooling和DNB部分，产物保留在POS20 Col 7-12
# 定量后POS20密封4度保存
#
# Current behavior summary (library prep + quantification only):
# - LA purification: oil and aspirations target POS20 Cols 1-6 (LA wells on the fresh plate after the POS9 swap).
# - PCR door management: pcr_close_door() runs after every lid replacement; pcr_open_door() runs before every lid opening.
# - LA mix aspirations: T7 PCR mix uses slowed FirstSegmentSpeed for gentle tip entry; UDG enzyme uses the same gentle entry profile.
# - TA/LA purification waste: p8_empty calls use TipTouch (3 touches) for cleaner waste disposal.
# - Dye dispensing: 217.8 µL × 1 with 2.2 µL sample (1:100 dilution ratio for Qubit dsDNA HS).
#
# Created: 2026-02-10
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
backup_tip_300_loc = ['M2_POS28','M2_POS29']
tip_300 = Tips(tip_300_loc,backup_tip_300_loc)

tip_1000_loc = ['M2_POS18']
tip_1000 = Tips(tip_1000_loc)

tip_50_loc = ['M2_POS15','M2_POS12']
backup_tip_50_loc = ['M2_POS25','M2_POS19']
tip_50 = Tips(tip_50_loc,backup_tip_50_loc)

'''============================================================Shaker Swap Logic=============================================================='''
# M2_POS16 and M2_POS23 act as shared hubs for orbital shaking and magnetization
# This function implements temporary "shaker swap" to move plates to shaker, mix, and return to home

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


# v12：POS7 反应体系预分装的逐孔死体积计算。
# 仅用于 POS7 Col9 cDNA mix、Col10 TA Master Mix、Col11 LA/PCR Master Mix。
#   active_cols      = 当前行实际需要服务的下游列数
#   extra_per_well   = clamp(单孔下游体积 * 0.2, min=10, max=30)
#   pos7_dispense    = active_cols * (单孔下游体积 + 单孔死体积)
# 不用于磁珠、乙醇、矿物油、T2/洗脱液、Qubit、DNB 等非反应体系预分装。
def clamp_value(value, lower, upper):
	return max(lower, min(value, upper))

def active_col_count_for_row(sample_count, row_index):
	full_cols = sample_count // 8
	remainder = sample_count % 8
	return full_cols + (1 if remainder != 0 and row_index < remainder else 0)

def pos7_reaction_mix_dispense_volume(p8_volume_per_column, sample_count, row_index, min_dead=10, ratio=0.2, max_dead=30):
	active_cols = active_col_count_for_row(sample_count, row_index)
	if active_cols <= 0 or p8_volume_per_column <= 0:
		return 0
	extra_per_well = clamp_value(p8_volume_per_column * ratio, min_dead, max_dead)
	return active_cols * (p8_volume_per_column + extra_per_well)

# v12 同步：POS17 2 mL 混合管分装到 POS7 后保留 15 uL 死体积。
MIX_TUBE_DEAD_VOLUME = 15

# 本分支低通量直接分装阈值：SampleCount <= 16 走 P1 50 uL 直接分装，>16 保持 POS7/P8。
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

# POS14/POS11 switched: original POS14 oil/waste plate now lives at POS11.
for i in range(min(8, SampleCount)):
	p1_aspirate({"Position":"M2_POS24","Col":3,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.8,"AspirateSpeed":30,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 3, "TipTouchSpeed": 100})
	p1_dispense({"Position":"M2_POS11","Col":8,"Row":i+1,"DispenseOffsetOfZ":8,"DispenseSpeed":20,"DispenseVolume":target_volume_list[i],"DelayAfterDispense":0.5,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":0,"IsEmpty":True,"EmptyOffsetOfZ":2,"EmptySpeed":30,"DelayAfterEmpty":0.5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# ===== STEP: Dispense T1 cDNA Primer to PCR Plate (POS20) =====
col_num = (sample_num+7)//8  # Number of sample columns

transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0}) #开试剂盖

# v12 sync: RT first-step 2 µL T1 primer 转移 — 参数对齐 PTplus 16+2 system 的 2 µL 模式
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
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
b.Wait()

# v12 sync: 添加矿物油 (BEFORE PTseq_RT — 保护 RT, cDNA 复用同孔无需再加)
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
	# v12 sync: POS7 Col 9 per-row dispense list comes from the capped dead-volume curve above.
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
	# v12 sync: AspirateOffsetOfZ 0.1→0.5 (POS7 reaction-mix intermediate dead-volume safety)
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

# v12 sync: 矿物油已在 PTseq_RT 前添加 (POS20 Cols 1-6), cDNA 复用同孔无需再加

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
c = 1.4  # legacy safety coefficient retained for T2 buffer pre-dispense at POS7 Col 7 below, out of capped-curve scope
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
	# v12 sync: POS7 Col 10 per-row dispense list comes from the capped dead-volume curve above.
	target_volume_list = pos7_col10_volumes
	# Optimization: Load ONE tip for all 8 dispenses (reduces 8 tips to 1 tip)
	# Use 300 µL tips because the maximum required volume per tube exceeds the 50 µL tip range.
	p1_load_modified(tip_300.load(1)[0])
	for i in range(8):
		p1_aspirate({"Position":"M2_POS17","Col":4,"Row":2,"PreAirVolume":8,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p1_empty({"Position":"M2_POS7","Col":10,"Row":i+1,"EmptyOffsetOfZ":0.5,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# Unload tip after all 8 dispenses
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

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

# 盖上试剂盖
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})
spx_p2_v_0.Wait()

#Block begin:将靶向扩增反应液与样本混合
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})

# 添加靶向扩增反应液到样本中：15 uL TA Master Mix + 5 uL T6/index 引物 + 5 uL cDNA/product。
if low_throughput_p1_direct_col10:
	# 低通量直接分装按来源分阶段执行，避免每个样本反复开关 POS10 盖板。
	# 第一套 50 uL 单枪头复用两次：先加 15 uL TA Master Mix，暂存回原位，再加 5 uL T6/index 引物。
	# 该复用只接触空 TA 目标孔和一次性使用的 T6 引物孔；sample/product 使用第二套新枪头，避免样本回带到 POS10。
	transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
	ta_direct_reagent_tips = tip_50.load(sample_num, 1)
	for tip_index, (col_index, row) in enumerate(active_sample_wells(SampleCount)):
		p1_load_modified(ta_direct_reagent_tips[tip_index])
		p1_aspirate_modified("M2_POS17", 2, 4, 15, PreAirVolume=5, AspirateSpeed=10, AspirateOffsetOfZ=0.6, DelayAfterAspirate=0.5, PostAirVolume=0, IfTrack=False)
		p1_empty_modified("M2_POS20", row, col_index+7, EmptyOffsetOfZ=3, EmptySpeed=50, DelayAfterEmpty=0.5, TipTouchTimes=0, PostAirVolume=0)
		p1_unload_modified(ta_direct_reagent_tips[tip_index])
	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})
	# 同一套枪头从原位取回，POS10 T6/index 引物一次开盖处理完全部样本，处理完立即关盖。
	transfer({"StartPosition":"M2_POS10","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
	for tip_index, (col_index, row) in enumerate(active_sample_wells(SampleCount)):
		p1_load_modified(ta_direct_reagent_tips[tip_index])
		p1_aspirate_modified("M2_POS10", row, col_index+1, 5, PreAirVolume=5, AspirateSpeed=10, AspirateOffsetOfZ=0.5, DelayAfterAspirate=1, PostAirVolume=0, IfTrack=False)
		p1_empty_modified("M2_POS20", row, col_index+7, EmptyOffsetOfZ=3, EmptySpeed=50, DelayAfterEmpty=0.5, TipTouchTimes=0, PostAirVolume=0)
		p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS10","LoosenOffsetOfZ":0})
	# 第二套 50 uL 单枪头：从 POS20 cDNA/product 来源孔加入 5 uL 到对应 TA 目标孔。
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
		p8_aspirate({"Position":"M2_POS10","Col":i+1,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":5,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS20","Col":i+7,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
	for i in range(col_num):
		p8_load_modified(tip_50.load(target_tip_num_list[i])[0])
		p8_aspirate({"Position":"M2_POS20","Col":i+1,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":5,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS20","Col":i+7,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_mix({"Position":"M2_POS20","Col":i+7,"Row":1,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":50,"MixAspirateOffsetOfZ":0.5,"MixVolume":22,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":50,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

	# v12：TA PCR 前向 POS20 Col7-12 加矿物油。这里是新反应孔，不存在上一轮残留矿物油。
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
# 高通量 TA 分支在前面统一打开 POS10 盖板；低通量分支每个样本吸完 primer 后已经关闭 POS10。
if not low_throughput_p1_direct_col10:
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


###48μL磁珠1振荡位置转移到磁吸位置
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})
delay({"Duration": 180})

# === 废液回收设置 ===
# POS14/POS11 switched: original POS14 deepwell plate now lives at POS11.
# POS11 deepwell 1.3mL 板 Col 1-6 用于回收废液（1:1 列映射）
# 累计废液量: 95 + 420 + 85 + 420 = 1020 µL/孔 (容量 1300 µL)
waste_col_start = 1

# 移除上清 (after adding T2 buffer: 50 beads + 25 TA + 25 T2 = 100 µL total, remove 110 µL for "弃多于打" safety margin)
# Waste recovered to POS11 plate Col 1-6
for i in range(col_num):
	p8_load_modified_BubblePurge(TA_purification_tips[i])
	p8_aspirate({"Position":"M2_POS23","Col":7+i,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":30,"AspirateVolume":110,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# Empty waste to POS11 waste plate, Col 1:1 mapping
	p8_empty({"Position":"M2_POS11","Col":waste_col_start+i,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"TipTouchOffsetOfZ":15,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

MB_mix = tip_300.load(8,8,0)  # reuse_index=0: tips discarded to trash, not returned to rack
p8_load_modified(MB_mix[0])
#if SampleCount < 16: 
	#p8_mix({"Position":"M2_POS7","Col":12,"Row":1,"PreAirVolume":20,"MixTimes":10,"MixAspirateSpeed":200,"MixAspirateOffsetOfZ":0.5,"MixVolume":90,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":200,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_mix({"Position":"M2_POS7","Col":12,"Row":1,"PreAirVolume":20,"MixTimes":10,"MixAspirateSpeed":200,"MixAspirateOffsetOfZ":0.5,"MixVolume":180,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":200,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
#else: #更换300ul吸头后可改体积
	#p8_mix({"Position":"M2_POS7","Col":12,"Row":1,"PreAirVolume":20,"MixTimes":10,"MixAspirateSpeed":200,"MixAspirateOffsetOfZ":0.5,"MixVolume":180,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":200,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})


Ligation_purification_tips2 = tip_300.load(sample_num,8,0)  # reuse_index=0: tips discarded after the LA wash supernatant-removal block
# NOTE: T2 Buffer is now added BEFORE magnetic separation (see line ~875-880)
# The previous step here that added T2 after supernatant removal was INCORRECT
# and caused DNA loss (DNA needs PEG/salt buffer to bind to SPRI beads)

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
# POS17盖已处于打开状态(L868), 无需关再开
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

# v12: POS3 → POS7 ethanol pre-dispense, PTplus-style (5 cycles × 195 µL = 975 µL/well; staged height 0.5 + 4*tt). Capped at range(5) so 48-sample demand stays under 50 mL POS3 reservoir.
Alcohol_1 = tip_1000.load(8,8)
p8_load_modified(Alcohol_1[0])
for x in range(col_num):
	for tt in range(5):
		p8_aspirate({"Position":"M2_POS3","Col":1,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":1.0,"AspirateSpeed":80,"AspirateVolume":195,"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":0})
		p8_empty({"Position":"M2_POS7","Col":1+x,"Row":1,"EmptyOffsetOfZ":0.5+4*tt,"EmptySpeed":50,"DelayAfterEmpty":0.8,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 连接后纯化乙醇清洗
lang=get_lang()
if lang==1: #
 report({"Phase": "靶向扩增反应后纯化", "Step": "乙醇清洗", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Targeted Amplification Purification", "Step": "Ethanol Wash", "TaskType": "library", "RemainingTime": None})

# Reuse Ligation_purification_tips2 from waste removal for ethanol wash (saves 48 tips)

# v12 sync: TA 乙醇洗涤流程 - 静置等待方案, 加乙醇后不移板/不吹打, 仅做 120 s 磁吸沉降后弃乙醇
for i in range(2):
	# Step 1a: 加乙醇 (板在 POS23 磁铁位)
	for x in range(col_num):
		p8_load_modified_BubblePurge(Ligation_purification_tips2[x])
		p8_aspirate({"Position":"M2_POS7","Col":1+x,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":200,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
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
	# v12 sync: TA 纯化晾干延时 5 min (8→5 min, 回退至 SOP 允许下限)
	delay({"Duration": 300})

magetic_wait = parallel_block(wait_for_magnetic_beads)
# 等待磁珠吸附

# 靶向扩增反应纯化PCR反应液回溶

# ============ SWAP POS20 (used plate) with POS9 (fresh plate) ============
# After TA, POS20 has used wells. Swap with fresh plate from POS9.
# Fresh plate will be used for LA (Cols 1-6) and product recovery (Cols 7-12)
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

# 逐个分装PCR反应液到每个样本
# 计算每行的分装体积
# 计算LA Master Mix预分装体积 (Updated to 30 µL per well)
# 分段策略: n≤15 用基数35 (每孔dead=5µL), n≥16 用基数33 (所有孔被吸≥2次, dead=6µL 已足够)
if not low_throughput_p1_direct_col11:
	# v12 sync: POS7 Col 11 per-row dispense list comes from the capped dead-volume curve above.
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

# LA 建库反应前处理：先把 LA/PCR Master Mix 加到 POS23 磁架上的干燥磁珠产物，再转到 POS16 振荡回溶形成磁珠悬液。
# 第一步：向 POS23 Col7-12 的干燥磁珠产物中加入 30 uL LA/PCR Master Mix。
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
	LA_dispense_tips = tip_300.load(sample_num,8,1)
	for i in range(col_num):
		p8_load_modified(LA_dispense_tips[i])
		# 从 POS7 Col11 预分装槽吸取 30 uL LA/PCR Master Mix。
		# 参数与 PTplus 同类 20-30 uL 深孔板分装动作对照；当前数值沿用本 PTseq 分支已验证的小体积 POS7 -> POS23 参数，本分支仅把枪头改为 300 uL 以节省 50 uL 枪头。
		p8_aspirate({"Position":"M2_POS7","Col":11,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":30,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		# 打入 POS23 磁架上的干燥磁珠产物孔。
		p8_empty({"Position":"M2_POS23","Col":7+i,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_modified(LA_dispense_tips[i])

# 第二步：把 POS23 磁架上的板转到 POS16 振荡位进行回溶。
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})
# 用振荡回溶干燥磁珠产物，保持 v12 行为，不新增枪头混匀。
temp_shaker_set({"TempParameters":{"IsEnable":False,"Duration":-1},"ShakerParameters":{"IsEnable":True,"Direction":0,"Speed":1200,"Duration":60}})

# 第三步：把 POS16 Col7-12 的 30 uL 磁珠悬液转移到新 PCR 板 POS20 Col1-6。
# 高通量分支复用上一套 LA_dispense_tips；低通量 P1 直接分装分支不跨振荡复用单枪头，改用新的 300 uL P8 枪头。
# 这一步是 LA_dispense_tips 的最后一次使用，转移完成后直接丢弃到垃圾桶，不再放回枪头盒。
if low_throughput_p1_direct_col11:
	LA_slurry_tips = tip_300.load(sample_num,8,0)
else:
	LA_slurry_tips = LA_dispense_tips
for i in range(col_num):
	p8_load_modified(LA_slurry_tips[i])
	# 从 POS16 吸取整列 30 uL 磁珠悬液。
	p8_aspirate({"Position":"M2_POS16","Col":7+i,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0.5,"AspirateSpeed":20,"AspirateVolume":30,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 转移到新 PCR 板 POS20 Col1-6。
	p8_empty({"Position":"M2_POS20","Col":1+i,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":20,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 向 POS20 Col1-6 加入 10 uL T9 index 引物。
transfer({"StartPosition":"M2_POS10","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})# 打开 POS10 盖板，暴露 T9 index 引物
T9_primer_tips = tip_50.load(sample_num,8,1)
for i in range(col_num):
	p8_load_modified(T9_primer_tips[i])
	# 从 POS10 Col7-12 吸取 10 uL T9 index 引物，来源列不变。
	p8_aspirate({"Position":"M2_POS10","Col":7+i,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":10,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":2,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 打入 POS20 Col1-6，与 30 uL 磁珠悬液组成 40 uL LA PCR 反应体系。
	p8_empty({"Position":"M2_POS20","Col":1+i,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 混匀最终 40 uL 反应体系。
	p8_mix({"Position":"M2_POS20","Col":1+i,"Row":1,"PreAirVolume":5,"MixTimes":5,"MixAspirateSpeed":50,"MixAspirateOffsetOfZ":0.5,"MixVolume":35,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":50,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":2,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS10","LoosenOffsetOfZ":0})# 关闭 POS10 盖板

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
- 动态使用: 当Plate 3或Plate 4需要高速混合时，临时移动到此位置

Plate 3: M2_POS13 - 库存和测量板(Stock & Measurement Plate) [固定位置]
此板用于高价值存储和测量准备。物理上与珠废物和大容量试剂区域隔离。
- Columns 1-6 (Quantification Mix): 用于等分和混合文库样品与HS dsDNA染料
- Columns 7-12 (Concentrated Library): 最终洗脱的目的地（Library-only: 产物在POS20）
- 震荡器交换: 当需要定量染料混合均质化时，临时移动到POS16震荡

Plate 4 home moved: M2_POS11 - 废液/矿物油板(Waste & Mineral Oil Plate) [固定位置]
此板原位为POS14，现常驻POS11以减少高频POS14访问。
- Columns 1-6: 废液回收（1:1 列映射）
- Column 8: 矿物油中间储层

Quantification tubes home: M2_POS14 [固定位置]
定量阶段临时释放POS13访问位：POS13 product/dye mix整板到空闲POS23，
POS14定量管到POS13执行加液/混匀/读数；定量后POS13定量管回POS14，POS23整板回POS13。

M2_POS30 - 中转点(Transit Spot)
临时存储位置，用于板交换操作和震荡器交换

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

# 双选产物位置 - Library-only: 产物回收到POS20 Col 7-12（LA后Col 1-6已清空）
# 产物定量后POS20密封4度保存
product_pos = {"Position":"M2_POS20","Col":7,"Row":1}



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
	# v12: Conservative PTplus second-bead-transfer style for the LA-product 32 µL aliquot (avoids middle-of-tip air bubble seen in production).
	p8_aspirate({"Position":magetic_beads_pre_dispense_pos["Position"], "Col":magetic_beads_pre_dispense_pos["Col"], "Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.9,"AspirateSpeed":30,"AspirateVolume":magetic_beads_volume1,"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX":1.2, "TipTouchSpeed": 100})
	p8_dispense({"Position":magetic_beads_dispense_pos1["Position"], "Col":magetic_beads_dispense_pos1["Col"]+i, "Row":1,"FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "DispenseOffsetOfZ": 0.8, "DispenseSpeed": 30, "DispenseVolume":magetic_beads_volume1,"DelayAfterDispense": 1, "IsEmpty": True, "EmptyOffsetOfZ": 0.8, "EmptySpeed": 50, "DelayAfterEmpty": 0.5, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})

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
	# Transfer 40 µL LA PCR product from Cols 1-6
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

# v12 sync: LA 乙醇洗涤流程 - 静置等待方案, 加乙醇后不移板/不吹打, 仅做 120 s 磁吸沉降后弃乙醇
for i in range(2):
	# Step 1a: 加乙醇 (板在 POS23 磁铁位)
	for x in range(col_num):
		p8_load_modified_BubblePurge(temp[x])
		p8_aspirate({"Position":ethanol_pos["Position"], "Col":ethanol_pos["Col"]+x, "Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":200,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
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

# v12 sync: LA 纯化晾干延时 5 min — 在最后一次乙醇弃液完成后立即起计时
def wait_for_LA_beads_dry():
	delay({"Duration": 300})

LA_dry_wait = parallel_block(wait_for_LA_beads_dry)

LA_dry_wait.Wait()



####回溶
### 23 uL T2 洗脱液回溶；使用 50 uL 枪头以减少 300 uL 枪头消耗。

Product = tip_50.load(SampleCount,8,1)


for x in range(col_num):
	p8_load_modified(Product[x])
	# 从 POS7 预分装的 T2 洗脱液中吸取 23 uL，打入 POS23 磁珠孔。
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

###回收建库产物 → POS20 Col 7-12
# Library-only: 需要打开PCR门才能往POS20放产物（LA后PCR门已关闭）
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})  # 开PCR盖板

for x in range(col_num):
	p8_load_modified_BubblePurge(Product[x])
	# Recover 21 µL final library product (SOP: 23 µL elution → 21 µL recovery)
	p8_aspirate({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0,"AspirateSpeed":10,"AspirateVolume":21,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":product_pos["Position"],"Col":product_pos["Col"]+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":10,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_mix({"Position":product_pos["Position"],"Col":product_pos["Col"]+x,"Row":1,"PreAirVolume":20,"MixTimes":10,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":10,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":1, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty({"Position":product_pos["Position"],"Col":product_pos["Col"]+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":10,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# Move purification plate back from magnet to shaker position
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})

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

# 样本来源起始位置 - Library-only: 从POS20 Col 7-12取样（产物在POS20上）
source_plate = ['M2_POS20',7]

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
	p8_aspirate_modified(dye_loc[0], Row=dye_loc[2], Col=dye_loc[1], AspirateVolume=217.8, PreAirVolume=10, AspirateOffsetOfZ=1.0)
	p8_empty_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i, EmptyOffsetOfZ=3, TipTouchTimes=1)
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

# Library-only: 定量取样完成，关闭POS20盖板并启动PCR模块4度过夜保存
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})  # 关PCR盖板
pcr_close_door()

# 启动PCR 4keep保存（并行执行，不阻塞后续定量流程）
def block_pcr_4keep():
	pcr_run_method({"Methods": ["4keep"]})
keep = parallel_block(block_pcr_4keep)

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


# ===== Library-only: 等待PCR 4keep过夜保存完成 =====
keep.Wait()

# ===== 脚本结束 =====
# 产物保留在POS20 Col 7-12，已密封4度保存
# 定量结果已输出到 D:\data\PTseq_Library.xlsx
