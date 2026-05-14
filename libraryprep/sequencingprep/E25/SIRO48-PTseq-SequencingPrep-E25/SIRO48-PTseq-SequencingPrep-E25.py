# -*- coding: utf-8 -*-
#####################################################################
# SIRO48-PTseq SequencingPrep (上机前准备) for E25
#####################################################################
# 独立的Pooling + DNB脚本，通过CSV读取样本浓度信息
# 模仿PTseq Plus SequencingPrep的结构模式，使用PTseq自己的实验参数
#
# 前置条件：
#   1. 文库产物PCR plate已放置在POS11 Col 7-12
#   2. CSV文件已准备好（含浓度信息）
#   3. DNB试剂已放置在POS17 Row 4-5
#   4. T2 buffer在POS24 Col 1, Row 2
#   5. Pooling管在POS13 Col 7
#   6. 矿物油在POS24 Col 3, Row 1
#
# Created: 2026-03-11
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
# 温控只在后台启动，用于保护 POS17/POS10 试剂；程序不等待温度到达，避免开局空等。
import time

'''=====================================样本信息读取（CSV）====================================='''
# 样本信息CSV文件位置
# CSV格式: sample_id, position, plate_index, concentration, product_type, barcode, sample_type
# 第一行为表头，从第二行开始为数据
sample_info_file_path = r'D:/Pathogens/PTseq_concentration.csv'

# 样本质控浓度阈值 (ng/µL)
sample_qc_concentration = 10

class Sample:
	"""样本信息类 - 兼容全流程pooling代码的属性名"""
	def __init__(self, sample_id, position, plate_index, concentration, product_type, barcode, sample_type):
		self.sample_id = sample_id
		self.position = position
		self.plate_index = plate_index
		self.Concentration = float(concentration)  # 大写C，兼容全流程代码
		self.product_type = product_type
		self.barcode = barcode
		self.SampleType = sample_type  # 兼容全流程代码的属性名

		# 从孔位计算行列号 (e.g., "A1" → row=1, col=1)
		self.row = ord(position[0].upper()) - ord('A') + 1  # 行号（1-based）
		self.column = int(position[1:])  # 列号（1-based）

		# 初始化pooling相关属性
		self.NeedDilution = False
		self.DilutingSampleVolume = 0
		self.DilutingBufferVolume = 0
		self.sample_initial_index = 0

	def __repr__(self):
		return f"Sample(id={self.sample_id}, pos={self.position}, conc={self.Concentration})"

def get_sample_info(file_path):
	"""读取CSV样本信息文件"""
	samples = []
	try:
		with open(file_path, 'rb') as file:
			lines = file.readlines()
		for line in lines[1:]:  # 跳过表头
			parts = line.decode('utf-8').strip().split(',')
			if len(parts) != 7:
				continue
			sample_id, position, plate_index, concentration, product_type, barcode, sample_type = parts
			sample = Sample(sample_id, position, plate_index, concentration, product_type, barcode, sample_type)
			samples.append(sample)
	except Exception as e:
		print(f"Error reading sample info: {e}")
	return samples

# 读取样本信息
samples_from_csv = get_sample_info(sample_info_file_path)

if not samples_from_csv:
	a_dialog = dialog_textbox({"Title": "样本信息", "Timeout": "02:00:00","Parameters":[{"Name": "样本数量", "Value": "48", "Notes": "未检测到样本信息CSV文件，请确认"}]})
	raise Exception("未读取到有效样本信息，请检查CSV文件")

sample_num = len(samples_from_csv)
print(f"读取到 {sample_num} 个有效样本")

'''=====================================以上为样本信息读取====================================='''


'''==================================================================自动计算取枪头位置逻辑v6======================================================'''
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
# SequencingPrep枪头从全新开始（无文库制备消耗）
tip_300_loc = ['M2_POS5','M2_POS6']
backup_tip_300_loc = ['M2_POS28','M2_POS29']
tip_300 = Tips(tip_300_loc,backup_tip_300_loc)

tip_1000_loc = ['M2_POS18']
tip_1000 = Tips(tip_1000_loc)

tip_50_loc = ['M2_POS15','M2_POS12']
backup_tip_50_loc = ['M2_POS25','M2_POS19']
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


'''=====================================Pooling配置参数====================================='''

# 样本来源板位 - 文库产物在 POS7 Col 7-12 (用户手动放置PCR plate)
source_plate = ('M2_POS7',7)

# 稀释板位 - 在 POS8 Col 7-12 做 library dilution
sample_dilution_place = ('M2_POS8',7)

# 样本取样体积临界值
min_sample_volume = 2
max_sample_volume = 20

# 单个DNB样本数 - E25: ≤32样本1个pool, >32样本2个pool
single_dnb_sample_num = 32
# 单个DNB投入量 (E25说明书: 1pmol ≈ 200ng for ~300bp fragments)
target_dna_ng = 200
# pooling总体积
target_pooling_volume = 48

# pooling取buffer使用1ml枪头
single_tip_loc = tip_1000.load(1)[0]
# pooling稀释buffer位置 - M2_POS24 B1 (Col 1, Row 2) contains T2 buffer
dilution_buffer_loc = ('M2_POS24',1,2)
# pooling产物位置 - M2_POS13 Column 7
target_tube_loc = [('M2_POS13',7,i) for i in range(1,9)]
# DNB反应位置 - Column布局: Col 7 Row 1-6 为 pooling 产物暂存, Col 8 Row 1-6 为DNB制备
# SIRO48最多48样本, 每8个一组, 最多6个pool
target_dnb_loc_list = [('M2_POS20',7,1+i) for i in range(6)]

# 混匀DNB的枪头位置
dilution_mix_tip_loc = None
dilution_transfer_tip_loc = None

# 空白样本是否pooling
Is_blank_pooling = False
# 浓度不合格样本是否pooling
Is_unqualified_pooling = False
# pooling信息输出文件
output_file_path = r"D:/data/PTseq_pooling_info.csv"


'''=====================================Pooling计算====================================='''

# 构建兼容全流程代码的 sample_concentration 列表。
# 样本来源孔位按 CSV 原始 position 映射，避免过滤低浓度样本后把后续样本前移。
for i, s in enumerate(samples_from_csv):
	s.SampleWellPosition = source_plate[0]
	s.SampleWellColumn = source_plate[1] + s.column - 1
	s.SampleWellRow = s.row
	s.DilutingWellPosition = sample_dilution_place[0]
	s.DilutingWellColumn = sample_dilution_place[1] + s.column - 1
	s.DilutingWellRow = s.row
	s.sample_initial_index = i

sample_concentration = samples_from_csv

# 浓度不合格样本是否进入 pooling；过滤发生在孔位映射之后，因此保留剩余样本的原始吸液孔位。
if not Is_unqualified_pooling:
	sample_concentration = [each for each in sample_concentration if each.Concentration >= sample_qc_concentration]

# 过滤空白样本
if not Is_blank_pooling:
	try:
		sample_concentration = [each for each in sample_concentration if each.SampleType != '空白对照']
	except:
		pass

# 按浓度计算pooling分组
sample_num = len(sample_concentration)
if sample_num == 0:
	raise Exception("过滤低浓度或空白样本后没有可 pooling 的有效样本，请检查CSV浓度和样本类型")
target_dnb_num = (sample_num+single_dnb_sample_num-1)//single_dnb_sample_num
Hybridization_num = target_dnb_num

x,y = divmod(sample_num,target_dnb_num)
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

initial_dnb_list = [group.copy() for group in dnb_list]

# 补水位置
water_loc_list = []

# 浓度均一化: max/min > 8 时高浓度样本8x稀释
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


temp = [(n,water_volume) for n,water_volume in [get_sample_volume(each) for each in dnb_list]]
water_volume_list = [each[1] for each in temp]

def output_pooling_info(samples, temp, output_file_path):
	"""输出pooling信息到CSV"""
	with open(output_file_path, 'w', encoding='utf-8') as f:
		f.write("样本编号,Pooling组,浓度,取样体积(ul),稀释倍数,放大倍数\n")
		current_time = time.localtime()
		formatted_time = time.strftime("%yP%m%d%H%M%S", current_time)
		for i, group in enumerate(samples):
			cur_pooling_id = f"{formatted_time}{i+1}"
			for sample in group:
				concentrate_times = temp[i][0]
				if sample.NeedDilution:
					dilution_type = 8
				else:
					dilution_type = 1
				formated_DilutingSampleVolume = "%.2f" % sample.DilutingSampleVolume
				f.write(f"{sample.sample_id},{cur_pooling_id},{sample.Concentration},{formated_DilutingSampleVolume},{dilution_type},{concentrate_times}\n")

output_pooling_info(dnb_list, temp, output_file_path)
print(f"Pooling信息已输出到：{output_file_path}")


'''=====================================Pooling物理操作====================================='''

lang=get_lang()
if lang==1:
 report({"Phase": "上机前准备", "Step": "Pooling", "TaskType": "library", "RemainingTime": None})
elif lang==2:
 report({"Phase": "Sequencing Prep", "Step": "Pooling", "TaskType": "library", "RemainingTime": None})

pooling_tube_pos = 'M2_POS13'
pooling_tube_col = 7

# Step 2: Normalization - 稀释高浓度样本 (p1加T2 buffer到POS8 Col 7-12)
p1_load_tips({"Position":single_tip_loc[0],'Col':single_tip_loc[1],'Row':single_tip_loc[2]})

if water_loc_list:
	for i in range(len(water_loc_list)):
		# 加入35µL T2 buffer到POS8 PCR板稀释孔 (5µL sample + 35µL buffer = 40µL, 8x dilution)
		p1_aspirate({"Position": dilution_buffer_loc[0], "Row": dilution_buffer_loc[2], "Col": dilution_buffer_loc[1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "PreAirSpeed": 100, "PreAirVolume": 10, "SecondSegmentSpeed": 100, "AspirateOffsetOfZ": 1.0, "AspirateSpeed": 20, "AspirateVolume": 35, "DelayAfterAspirate": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100, "PostAirSpeed": 100, "PostAirVolume": 10})
		p1_empty({"Position": water_loc_list[i][0], "Row": water_loc_list[i][1], "Col": water_loc_list[i][2], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100, "EmptyOffsetOfZ": 1, "EmptySpeed": 190, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})

# Step 3 mix 并入 Step 5：sample 进入 POS8 稀释孔后再混匀。

# Step 4: p1 加补水到pooling管 (POS13 Col 7) 和 DNB反应孔 (POS20)
for i in range(len(water_volume_list)):
	if temp[i][0]>=8:
		new_water_volume = target_pooling_volume-target_pooling_volume/(temp[i][0]/8)
		p1_aspirate({"Position": dilution_buffer_loc[0], "Row": dilution_buffer_loc[2], "Col": dilution_buffer_loc[1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "PreAirSpeed": 100, "PreAirVolume": 10, "SecondSegmentSpeed": 100, "AspirateOffsetOfZ": 1.0, "AspirateSpeed": 20, "AspirateVolume": new_water_volume, "DelayAfterAspirate": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100, "PostAirSpeed": 100, "PostAirVolume": 10})
		p1_empty({"Position": target_dnb_loc_list[i][0], "Row": target_dnb_loc_list[i][2], "Col": target_dnb_loc_list[i][1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100, "EmptyOffsetOfZ": 2, "EmptySpeed": 190, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})
	p1_aspirate({"Position": dilution_buffer_loc[0], "Row": dilution_buffer_loc[2], "Col": dilution_buffer_loc[1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "PreAirSpeed": 100, "PreAirVolume": 10, "SecondSegmentSpeed": 100, "AspirateOffsetOfZ": 1.0, "AspirateSpeed": 100, "AspirateVolume": water_volume_list[i], "DelayAfterAspirate": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100, "PostAirSpeed": 100, "PostAirVolume": 10})
	p1_empty({"Position": pooling_tube_pos, "Row": i+1, "Col": pooling_tube_col, "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100, "EmptyOffsetOfZ": 5, "EmptySpeed": 190, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})

p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# Step 5: p8 pool 转移（非稀释直转 POS7→POS13；稀释分支 POS7→POS8 mix→POS8→POS13）
for i,poolings in enumerate(temp):
	samples = dnb_list[i]
	for sample in samples:
		sample_volume = sample.DilutingSampleVolume
		if not sample.NeedDilution:
			p8_load_modified(tip_50.load(1)[0])
			p8_aspirate_modified(sample.SampleWellPosition, sample.SampleWellRow, sample.SampleWellColumn, sample_volume, PreAirVolume=10)
			p8_empty_modified(pooling_tube_pos, i+1, pooling_tube_col)
			p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
		else:
			p1_load_modified(tip_50.load(1)[0])
			p1_aspirate_modified(sample.SampleWellPosition, sample.SampleWellRow, sample.SampleWellColumn, 5, PreAirVolume=5, AspirateSpeed=10, AspirateOffsetOfZ=0.5, DelayAfterAspirate=1, PostAirVolume=0)
			p1_empty_modified(sample.DilutingWellPosition, sample.DilutingWellRow, sample.DilutingWellColumn, EmptyOffsetOfZ=0.5, EmptySpeed=10, PostAirVolume=0)
			p1_mix({"Position":sample.DilutingWellPosition,"Col":sample.DilutingWellColumn,"Row":sample.DilutingWellRow,"PreAirVolume":10,"MixTimes":5,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.5,"MixVolume":30,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":100,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":0,"TipTouchOffsetOfZ":5,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100})
			p1_aspirate_modified(sample.DilutingWellPosition, sample.DilutingWellRow, sample.DilutingWellColumn, sample_volume, PreAirVolume=0, PostAirVolume=0)
			p1_empty_modified(pooling_tube_pos, i+1, pooling_tube_col)
			p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# Step 6: 混匀pooling管并转移到POS20 Col 7 Row 1-6 (DNB反应位)
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

'''#######################################################make DNB (E25) - 无单链环化步骤#########################################'''
DNB_Num = target_dnb_num

##################################################################################### 样本转移 Col7→Col8 #######################################################################

# 混匀Col7 pooling产物并转移20µL到Col8 (DNB反应位)
DNB_transfer = tip_300.load(DNB_Num,1)
for x in range(DNB_Num):
	p8_load_modified(DNB_transfer[x])
	# 混匀Col7 pooling产物 (48µL)
	p8_mix({"Position":"M2_POS20","Col":7,"Row":1+x,"PreAirVolume":10,"MixTimes":10,"MixAspirateSpeed":30,"MixAspirateOffsetOfZ":0.5,"MixVolume":40,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":30,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 吸取20µL
	p8_aspirate({"Position":"M2_POS20","Col":7,"Row":1+x,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":20,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 排到Col8
	p8_empty({"Position":"M2_POS20","Col":8,"Row":1+x,"EmptyOffsetOfZ":0.8,"EmptySpeed":20,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

##################################################################################### DNB制备体系1 ############################################################################

transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})###开盖板

# 50 uL tip 只负责分装 20 uL DNB 制备缓冲液(SB)；POS17 Row5 Col1 为 SB。
DNB1_buffer = tip_50.load(DNB_Num,1)
for x in range(DNB_Num):
	p8_load_modified(DNB1_buffer[x])
	p8_aspirate({"Position":"M2_POS17", "Col":1, "Row":5,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":5,"AspirateVolume":20,"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty({"Position":"M2_POS20","Col":8,"Row":1+x,"EmptyOffsetOfZ":0.5,"EmptySpeed":3,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 0, "TipTouchSpeed": 100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 参考 PTplus E25：SB 加完后用 300 uL tip 单独混匀 40 uL DNB 制备体系1。
DNB1_mix = tip_300.load(DNB_Num,1)
for x in range(DNB_Num):
	p8_load_modified(DNB1_mix[x])
	p8_mix({"Position":"M2_POS20","Col":8,"Row":1+x,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":10,"MixAspirateOffsetOfZ":0.5,"MixVolume":35,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":10,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
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
	pcr_run_method({"Methods": ["PTseq_DNB_E25_1st"]})
d1 = parallel_block(blockD1)

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})###关盖板
d1.Wait()
###PCR开门
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0}) #开PCR盖板
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})###开盖板

##################################################################################### DNB制备体系2 ############################################################################
# DNB聚合酶体系：先将 Mix I 大体积加入 Mix II 小体积源管，再从源管分装到 POS20 Col8。
# POS17 Row5 Col2 为 DNB聚合酶混合液I，Row5 Col3 为 DNB聚合酶混合液II。
DNB_polymerase_source_mix = tip_300.load(1)[0]
p8_load_modified(DNB_polymerase_source_mix)
p8_aspirate({"Position":"M2_POS17", "Col":2, "Row":5,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":40 * (DNB_Num + 0.5),"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS17","Col":3,"Row":5,"EmptyOffsetOfZ":0.5,"EmptySpeed":10,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2,"TipTouchOffsetOfZ":5,"TipTouchRangeOfX":0,"TipTouchSpeed":100})
p8_mix({"Position":"M2_POS17","Col":3,"Row":5,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":30,"MixAspirateOffsetOfZ":0.5,"MixVolume":40 * DNB_Num,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":30,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 分装混匀后的 DNB聚合酶体系 44 uL → POS20 Col8；44 uL 接近 50 uL tip 上限，改用 300 uL tip 留足气隙余量。
DNB_polymerase_mix = tip_300.load(DNB_Num,1)
for x in range(DNB_Num):
	p8_load_modified(DNB_polymerase_mix[x])
	p8_aspirate({"Position":"M2_POS17", "Col":3, "Row":5,"PreAirVolume":3,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":44,"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":1,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p8_empty({"Position":"M2_POS20","Col":8,"Row":1+x,"EmptyOffsetOfZ":0.5,"EmptySpeed":20,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2,"TipTouchOffsetOfZ":5,"TipTouchRangeOfX":0,"TipTouchSpeed":100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 聚合酶体系加完后，用 300 uL tip 混匀 POS20 Col8。
DNB_polymerase_reaction_mix = tip_300.load(DNB_Num,1)
for x in range(DNB_Num):
	p8_load_modified(DNB_polymerase_reaction_mix[x])
	p8_mix({"Position":"M2_POS20","Col":8,"Row":1+x,"PreAirVolume":10,"MixTimes":10,"MixAspirateSpeed":50,"MixAspirateOffsetOfZ":0.5,"MixVolume":60,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":50,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
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
	pcr_run_method({"Methods": ["PTseq_DNB_E25_2nd"]})
d2 = parallel_block(blockD2)


d2.Wait()


###PCR开门
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0}) #开PCR盖板
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})###开盖板

#加入DNB终止缓冲液 20µL → POS20 Col8 Row 1+x
DNB_temp1_1000 = tip_1000.load(DNB_Num,1)
for x in range(DNB_Num):
	p1_load_modified(DNB_temp1_1000[x])
	p1_aspirate({"Position":"M2_POS17", "Col":4, "Row":5,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":20,"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS20","Col":8,"Row":1+x,"EmptyOffsetOfZ":0.5,"EmptySpeed":50,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 0, "TipTouchSpeed": 100})
	p1_mix({"Position":"M2_POS20","Col":8,"Row":1+x,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":0.5,"MixVolume":80,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

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
