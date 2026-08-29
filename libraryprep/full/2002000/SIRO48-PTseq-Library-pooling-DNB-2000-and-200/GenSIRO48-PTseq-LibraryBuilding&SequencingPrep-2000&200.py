
# -*- coding: utf-8 -*-
#####################################################################
# 脚本定位：GenSIRO48 200/2000 平台 PTseq 全流程脚本。
# 覆盖范围：从提取完成后的 cDNA 合成开始，依次完成建库、定量、pooling 和 200/2000 DNB 制备。
# 主要体系：T1 逆转录引物、T2/T3 cDNA 一链体系、T4/T5/T2/T6 TA 体系、
#           T7/T8/T2/T9 LA 体系、两轮磁珠纯化、Qubit dsDNA HS 定量、pooling、make DNB。
# 关键设计：
#   1. POS17 和 POS10 低温运行，但温控并行启动，不等待温度到达后才开始程序。
#   2. SampleCount <= 16 时，Col9/Col10/Col11 反应液使用 P1 50 uL 低通量直接分装；
#      SampleCount > 16 时保持原始 POS7 中转 + P8 分装流程。
#   3. POS7 只作为反应液、T2、磁珠、乙醇等中转深孔板；不同用途的死体积算法不可混用。
#   4. POS11/POS14 已对换：POS11 固定承担废液、矿物油、pooling/DNB 汇集相关功能；
#      POS14 为定量管 home，定量时通过 POS13 访问，结束后恢复。
#   5. POS16 是温控震荡位，POS23 是磁力架位；需要震荡时必须确认物理板位已经移动到 POS16。
#   6. 代码内保留的英文缩写如 POS、PCR、DNB、Qubit、PTseq 为平台或产品固定术语。
# 版本说明：本仓库已从传统 v 命名迁移到 git 分支管理；本文件所在分支代表当前开发版本。
# 创建时间：2026-02-10
#####################################################################
# 时间戳：2026-04-05
# 共用头部：包含平台初始化、枪头管理、移液封装和通用辅助函数。

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

# POS19 已随本分支从 300 uL 备用枪头位改为 50 uL 备用枪头位；deck.json 中 POS19 也必须是 50 uL 枪头盒。
tip_50_loc = ['M2_POS15','M2_POS12']
backup_tip_50_loc = ['M2_POS25','M2_POS19']
tip_50 = Tips(tip_50_loc,backup_tip_50_loc)

'''============================================================震荡位换板逻辑=============================================================='''
# POS16 是共享温控震荡位，POS23 是共享磁力架位；二者不是某一块板子的永久 home。
# 当某块板需要震荡但 POS16 已有板时，先把 POS16 上的板临时移到 POS30，再把目标板移入 POS16。
# 震荡结束后，目标板回到自己的原位置；如果原先 POS16 有板，再从 POS30 恢复到 POS16。
# POS30 只作为换板过程中的临时中转位，不能长期放置带液体的流程板。

def shaker_swap(target_plate_pos, operation_callback, current_shaker_occupant=None):
	"""
	执行一次“目标板进入 POS16 震荡、震荡后恢复原位”的换板操作。

	参数：
		target_plate_pos: 需要震荡的目标板当前所在位置，例如 M2_POS13 或 M2_POS14。
		operation_callback: 目标板到达 POS16 后要执行的震荡函数。
		current_shaker_occupant: 当前已经在 POS16 的板；如果没有则传 None。
	"""
	# 第一步：如果 POS16 已有板，先把这块板移到 POS30 暂存。
	if current_shaker_occupant:
		transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS30","LoosenOffsetOfZ":0})

	# 第二步：把目标板移动到 POS16 震荡位。
	transfer({"StartPosition":target_plate_pos,"EndPosition":"M2_POS16","LoosenOffsetOfZ":0})

	# 第三步：执行调用方传入的震荡/混匀动作。
	operation_callback()

	# 第四步：目标板回到原位置，确保后续移液仍然访问正确物理板位。
	transfer({"StartPosition":"M2_POS16","EndPosition":target_plate_pos,"LoosenOffsetOfZ":0})

	# 第五步：如果 POS16 原来有板，从 POS30 恢复回 POS16。
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


# POS7 反应体系预分装的逐孔死体积计算。
# 仅用于 POS7 Col9 cDNA 反应液、Col10 TA Master Mix、Col11 LA/PCR Master Mix。
#   active_cols      = 当前行实际需要服务的下游列数
#   pos7_dead_volume = 每个 POS7 中转孔保留的总冗余体积
#   pos7_dispense    = active_cols * 单次下游吸取体积 + pos7_dead_volume
# 不用于磁珠、乙醇、矿物油、T2/洗脱液、Qubit、DNB 等非反应体系预分装。
def active_col_count_for_row(sample_count, row_index):
	full_cols = sample_count // 8
	remainder = sample_count % 8
	return full_cols + (1 if remainder != 0 and row_index < remainder else 0)

def pos7_reaction_mix_dispense_volume(p8_volume_per_column, sample_count, row_index, pos7_dead_volume=20):
	active_cols = active_col_count_for_row(sample_count, row_index)
	if active_cols <= 0 or p8_volume_per_column <= 0:
		return 0
	return active_cols * p8_volume_per_column + pos7_dead_volume

# POS17 混合管分装完成后保留死体积。
MIX_TUBE_DEAD_VOLUME = 15
# TA 和 LA/PCR Master Mix 额外增加 10 uL 冗余，降低最后一枪不足的风险。
TA_LA_MIX_TUBE_EXTRA_DEAD_VOLUME = 10
TA_LA_MIX_TUBE_DEAD_VOLUME = MIX_TUBE_DEAD_VOLUME + TA_LA_MIX_TUBE_EXTRA_DEAD_VOLUME
LA_MIX_TUBE_DEAD_VOLUME = 30
# 高通量 POS7/P8 中转分装时，上游 mixing tube 额外保留两个完整 POS7 中转孔的体积。
# 额外体积只留在 mixing tube 内，不会分装到不存在的样本孔。
EXTRA_COLLECTION_WELL_COUNT = 2
# 2.0 mL LA mixing tube 的已验证工作上限；超过时，T2 改为直接加入 POS7 Col11。
LA_MIX_TUBE_MAX_WORKING_VOLUME = 1421

def mix_total_with_collection_reserve(pos7_volumes, base_dead_volume):
	active_volumes = [volume for volume in pos7_volumes if volume > 0]
	if not active_volumes:
		return base_dead_volume
	return sum(active_volumes) + base_dead_volume + EXTRA_COLLECTION_WELL_COUNT * max(active_volumes)

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

def report_low_throughput_branch(section_cn, section_en, direct_branch, sample_count):
	lang = get_lang()
	if lang == 1:
		branch_name = "P1 50 uL 直接分装" if direct_branch else "POS7/P8 中转分装"
		message = f"{section_cn}: 使用{branch_name}分支；样本数={sample_count}"
		print(f"[低通量P1直接分装] {message}")
		report({"Phase":"低通量P1直接分装","Step":message,"TaskType":"library","RemainingTime":None})
	elif lang == 2:
		branch_name = "P1 50 uL direct" if direct_branch else "POS7/P8 transfer"
		message = f"{section_en}: {branch_name} branch selected; SampleCount={sample_count}"
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
BLANK_QC_TYPE = 'B'
T12_BLANK_VOLUME = 14

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
		self.barcode = barcode      # 样本 barcode / index 信息
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
# 中台在启动任务前生成 D:/Pathogens/PTseq.csv；脚本开局读取后立即检查 barcode。
missing_barcode_sample_ids = [sample.sample_id for sample in filtered_samples if not sample.barcode.strip()]
if missing_barcode_sample_ids:
	missing_barcode_message = "以下样本缺少barcode，将忽略这些样本的barcode唯一性检查并继续运行：" + "、".join(missing_barcode_sample_ids)
	print(f"[WARNING] {missing_barcode_message}")
	report({"Phase":"样本信息检查","Step":missing_barcode_message,"TaskType":"library","RemainingTime":None})
blank_samples = [sample for sample in filtered_samples if sample.sample_qc_type.upper() == BLANK_QC_TYPE]
blank_positions = set()
for blank_sample in blank_samples:
	blank_position = blank_sample.position.upper()
	if blank_sample.target_position.strip().upper() != blank_position:
		raise Exception(f"空白对照 {blank_sample.sample_id} 的输入孔位 {blank_sample.target_position} 与流程孔位 {blank_position} 不一致，请按 A1-H1、A2-H2 顺序排列 PTseq.csv")
	if blank_position in blank_positions:
		raise Exception(f"空白对照孔位重复：{blank_position}")
	blank_positions.add(blank_position)
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

# POS14/POS11 已对换：原 POS14 的矿物油/废液/pooling 汇集板现在固定放在 POS11。
for i in range(min(8, SampleCount)):
	p1_aspirate({"Position":"M2_POS24","Col":3,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.8,"AspirateSpeed":30,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 3, "TipTouchSpeed": 100})
	p1_dispense({"Position":"M2_POS11","Col":8,"Row":i+1,"DispenseOffsetOfZ":8,"DispenseSpeed":20,"DispenseVolume":target_volume_list[i],"DelayAfterDispense":0.5,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":0,"IsEmpty":True,"EmptyOffsetOfZ":2,"EmptySpeed":30,"DelayAfterEmpty":0.5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# ===== 步骤：向 POS20 PCR 板分装 T1 cDNA 引物 =====
col_num = (sample_num+7)//8  # 样本占用的 PCR 板列数，每 8 个样本为 1 列

transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})  # 打开 POS17 试剂盖。

# T12 空白对照放在 POS17 F1（0.5 mL 管；API 坐标 Col1 Row6）。
# 根据 PTseq.csv 中所有 QcType=B 的动态孔位，逐孔向 POS8 提取产物板加入 14 uL T12。
for blank_sample in blank_samples:
	blank_tip = tip_50.load(1)[0]
	p8_load_modified(blank_tip)
	p8_aspirate({"Position":"M2_POS17","Col":1,"Row":6,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":T12_BLANK_VOLUME,"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100})
	p8_empty({"Position":"M2_POS8","Col":blank_sample.column,"Row":blank_sample.row,"EmptyOffsetOfZ":1,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":3,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# RT 第一步转移 2 uL T1 引物，使用 P1 逐样本加入 POS20；每最多 3 列更换一次 50 uL 枪头。
for col_group_start in range(0, col_num, 3):
	p1_load_modified(tip_50.load(1)[0])
	for i in range(col_group_start, min(col_group_start + 3, col_num)):
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

# v12：PTseq_RT 前添加矿物油，保护 RT/cDNA 同一孔反应；cDNA 阶段复用同孔，不再额外加油。
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

# PTseq_RT 运行期间立即配置 T2/T3；后续 spx_p0_v_0.Wait() 会等待 RT 完成后再开盖加样。

'''===================================================cDNA一链合成反应体系==============================================================='''
lang=get_lang()
if lang==1: #
 report({"Phase": "cDNA合成", "Step": "cDNA一链合成反应体系", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "cDNA synthesis", "Step": "cDNAFirst-strand synthesis reaction system", "TaskType": "library", "RemainingTime": None})

# 配置一链反应试剂
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
low_throughput_p1_direct_col9 = use_low_throughput_p1_direct(SampleCount)
report_low_throughput_branch("第9列cDNA反应液", "Col9 cDNA mix", low_throughput_p1_direct_col9, SampleCount)
# 低通量分支直接从 POS17 混合管分装到反应孔，只计算 POS17 混合管死体积。
# 高通量分支使用 POS7 Col9 中转，每个 POS7 中转孔保留 20 uL 总冗余。
if low_throughput_p1_direct_col9:
	pos7_col9_volumes = [0] * 8
	mix_total_col9 = 4 * SampleCount + MIX_TUBE_DEAD_VOLUME
else:
	pos7_col9_volumes = [pos7_reaction_mix_dispense_volume(4, SampleCount, r) for r in range(8)]
	mix_total_col9 = mix_total_with_collection_reserve(pos7_col9_volumes, MIX_TUBE_DEAD_VOLUME)
t23_vol = mix_total_col9 / 2  # T2 缓冲液和 T3 酶按 1:1 配制，各占总量一半。
# 吸T2 一链合成缓冲液
p1_load_modified(tip_300.load(1)[0])
p1_aspirate({"Position":"M2_POS17","Col":2,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":t23_vol,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_empty({"Position":"M2_POS17","Col":4,"Row":1,"EmptyOffsetOfZ":0.1*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
# 吸T3 一链合成酶
p1_load_modified(tip_300.load(1)[0])
p1_aspirate({"Position":"M2_POS17","Col":3,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":t23_vol,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_empty({"Position":"M2_POS17","Col":4,"Row":1,"EmptyOffsetOfZ":0.2*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":"M2_POS17","Col":4,"Row":1,"PreAirVolume":8,"MixTimes":10,"MixAspirateSpeed":3*SampleCount,"MixAspirateOffsetOfZ":0.6,"MixVolume":4.9*SampleCount,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":2.5*SampleCount,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.5+0.3*SampleCount,"MixEmptySpeed":5,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":"M2_POS17","Col":4,"Row":1,"PreAirVolume":8,"MixTimes":10,"MixAspirateSpeed":3*SampleCount,"MixAspirateOffsetOfZ":0.6,"MixVolume":4.9*SampleCount,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":2.5*SampleCount,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.5+0.3*SampleCount,"MixEmptySpeed":5,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":"M2_POS17","Col":4,"Row":1,"PreAirVolume":8,"MixTimes":10,"MixAspirateSpeed":3*SampleCount,"MixAspirateOffsetOfZ":0.6,"MixVolume":4.9*SampleCount,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":2.5*SampleCount,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.5+0.3*SampleCount,"MixEmptySpeed":5,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_empty({"Position":"M2_POS17","Col":4,"Row":1,"EmptyOffsetOfZ":0.2*SampleCount,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

if not low_throughput_p1_direct_col9:
	# POS7 Col9 每行预分装体积来自上方中转孔总冗余算法。
	target_volume_list = pos7_col9_volumes

	# 将 cDNA 一链反应液预分装到 POS7 Col9 中转深孔板；POS7 无盖板，不需要开关盖动作。
	# 优化点：同一支 P1 枪头完成 8 行预分装；来源和目标均为干净试剂/空孔，不引入样本污染。
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
# POS7 无盖板，因此这里不需要任何开关盖动作。
spx_p0_v_0.Wait()

#Block begin:将cDNA合成反应液与样本混合
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})#PCR盖板
# POS7 无盖板，已移除旧逻辑中不必要的 POS10 盖板动作。



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
		p8_mix({"Position":"M2_POS20","Col":i+1,"Row":1,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":0.5,"MixVolume":16,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
else:
	# v12：POS7 反应 mix 中转吸液高度由 0.1 调到 0.5，用于降低低液位/死体积风险。
	for i in range(col_num):
		p8_load_modified(tip_50.load(target_tip_num_list[i])[0])
		if SampleCount <= 20:
			p8_aspirate({"Position":"M2_POS7","Col":9,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":15,"AspirateVolume":4,"PreAirSpeed":30,"DelayAfterAspirate":5,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		else:
			p8_aspirate({"Position":"M2_POS7","Col":9,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":15,"AspirateVolume":4,"PreAirSpeed":30,"DelayAfterAspirate":5,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS20","Col":i+1,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":30,"DelayAfterEmpty":2,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_mix({"Position":"M2_POS20","Col":i+1,"Row":1,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":0.5,"MixVolume":16,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# v12：矿物油已在 PTseq_RT 前加到 POS20 Col1-6，cDNA 复用同孔无需再加。

# 盖上PCR盖板
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0}) #PCR盖板



'''==================================================cDNA一链合成反应==============================================================='''
pcr_close_door()
def spx_p2_f_0():
	pcr_run_method({"Methods":["PTseq_cDNA"]})
spx_p2_v_0 = parallel_block(spx_p2_f_0)

# PTseq_cDNA 后等待 30 min，再配置 TA Master Mix，避免 T4/T5/T2 混合液提前放置太久。
delay({"Duration": 1800})

# POS7 无盖板，已移除旧逻辑中不必要的 POS10 盖板动作。

'''===================================================靶向扩增反应试剂==============================================================='''
lang=get_lang()
if lang==1: #
 report({"Phase": "cDNA合成", "Step": "靶向扩增反应体系", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "cDNA synthesis", "Step": "Targeted Amplification reaction system", "TaskType": "library", "RemainingTime": None})
 

# 配置靶向扩增反应试剂
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
c = 1.4  # T2 缓冲液预分装到 POS7 Col7 的历史安全系数；该位置不使用 10-30 uL 逐孔封顶死体积算法。
low_throughput_p1_direct_col10 = use_low_throughput_p1_direct(SampleCount)
report_low_throughput_branch("第10列靶向扩增反应液", "Col10 targeted amplification mix", low_throughput_p1_direct_col10, SampleCount)
# 低通量分支直接从 POS17 混合管分装到反应孔，只计算 POS17 混合管死体积。
# 高通量分支使用 POS7 Col10 中转，每个 POS7 中转孔保留 20 uL 总冗余。
if low_throughput_p1_direct_col10:
	pos7_col10_volumes = [0] * 8
	mix_total_col10 = 15 * SampleCount + TA_LA_MIX_TUBE_DEAD_VOLUME
else:
	pos7_col10_volumes = [pos7_reaction_mix_dispense_volume(15, SampleCount, r) for r in range(8)]
	mix_total_col10 = mix_total_with_collection_reserve(pos7_col10_volumes, TA_LA_MIX_TUBE_DEAD_VOLUME)
ta_t2_vol = mix_total_col10 * 7 / 15
ta_t4_vol = mix_total_col10 * 5 / 15
ta_t5_vol = mix_total_col10 * 3 / 15

# 吸取 T2 溶解液：分成两次等体积 P1 转移，保留原脚本“两次吸取”的保守模式。
p1_load_modified(tip_1000.load(1)[0])
p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":10,"AspirateOffsetOfZ":0.8,"AspirateSpeed":10,"AspirateVolume":ta_t2_vol/2,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_empty({"Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.1*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":10,"AspirateOffsetOfZ":0.8,"AspirateSpeed":10,"AspirateVolume":ta_t2_vol/2,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_empty({"Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.1*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# 吸取 T4 靶向扩增缓冲液：T4 来源和 TA mixing tube 都是 POS17 单孔位，改用 P1 单枪头更符合机械动作。
total_ta_buffer_vol = ta_t4_vol
max_tip_capacity = 240  # P1 使用 300 uL 枪头时的保守上限；扣除 10 uL 前吸空气后，约 34 个样本以内可一次吸完 T4。

p1_load_modified(tip_300.load(1)[0])

if total_ta_buffer_vol <= max_tip_capacity:
	# T4 体积未超过 P1 300 uL 枪头保守上限时，一次吸取即可。
	p1_aspirate({
		"Position":"M2_POS17","Col":1,"Row":2,"PreAirVolume":10,
		"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,
		"AspirateVolume":total_ta_buffer_vol,
		"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,
		"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,
		"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80
	})
	p1_empty({
		"Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.1*SampleCount,
		"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,
		"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,
		"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80
	})

else:
	# 高通量时 T4 总体积较大，P1 仍按两次等体积分段吸取，避免 300 uL 枪头过满。
	split_vol = total_ta_buffer_vol / 2

	print(f"[INFO] T4 volume {total_ta_buffer_vol}uL exceeds P1 limit. Splitting into 2x {split_vol}uL.")

	for _ in range(2):
		p1_aspirate({
			"Position":"M2_POS17","Col":1,"Row":2,"PreAirVolume":10,
			"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,
			"AspirateVolume":split_vol,
			"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,
			"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,
			"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80
		})
		p1_empty({
			"Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.1*SampleCount,
			"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,
			"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,
			"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80
		})

p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# 加入 T5 靶向扩增酶，并完成 TA Master Mix 混匀。
p1_load_modified(tip_300.load(1)[0])
p1_aspirate({"Position":"M2_POS17","Col":2,"Row":2,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":ta_t5_vol,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_empty({"Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.2*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
ta_master_mix_volume = min(900, 12 * SampleCount)
if ta_master_mix_volume > 240:
	p1_load_modified(tip_1000.load(1)[0])
else:
	p1_load_modified(tip_300.load(1)[0])
ta_mix_dispense_plan = [(10, 5), (10, 15), (10, 30)] if mix_total_col10 >= 700 else [(10, 5), (10, 10), (10, 15)]
for ta_mix_times, ta_mix_dispense_offset in ta_mix_dispense_plan:
	p1_mix({"Position":"M2_POS17","Col":4,"Row":2,"PreAirVolume":8,"MixTimes":ta_mix_times,"MixAspirateSpeed":3*SampleCount,"MixAspirateOffsetOfZ":0.6,"MixVolume":ta_master_mix_volume,"MixDispenseOffsetOfZ":ta_mix_dispense_offset,"MixDispenseSpeed":2.5*SampleCount,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.5+0.3*SampleCount,"MixEmptySpeed":5,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_empty({"Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.2*SampleCount,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

if not low_throughput_p1_direct_col10:
	# POS7 Col10 每行预分装体积来自上方中转孔总冗余算法。
	target_volume_list = pos7_col10_volumes
	# if SampleCount <= 20:
	# 优化点：8 行预分装共用 1 支 P1 枪头，减少枪头消耗。
	# 使用 300 uL 枪头：该混合管最大需求体积超过 50 uL 枪头范围。
	p1_load_modified(tip_300.load(1)[0])
	for i in range(8):
		p1_aspirate({"Position":"M2_POS17","Col":4,"Row":2,"PreAirVolume":8,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p1_empty({"Position":"M2_POS7","Col":10,"Row":i+1,"EmptyOffsetOfZ":0.5,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 8 行全部分装完成后再丢弃枪头。
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})

# =============================================
# 关键步骤：向 POS7 Col7 预分装 T2 缓冲液。
# =============================================
# POS7 Col7 的 T2 后续会用两次：
# 1. TA 纯化结合阶段，每个样本加入 25 uL T2。
# 2. LA 纯化最终洗脱阶段，每个样本加入 23 uL T2。
# 总需求按每行 (25 + 23) uL 再乘安全系数计算。

# 计算每行目标体积：基础需求 48 uL/活跃列，再乘安全系数。
target_volume_list = [48*c*(SampleCount//8+1)]*(SampleCount%8)+[48*c*(SampleCount//8)]*(8-SampleCount%8)

# 8 行预分装共用 1 支 P1 枪头，减少枪头消耗。
# 使用 1000 uL 枪头：该预分装总量可能超过 300 uL 枪头安全范围。
p1_load_modified(tip_1000.load(1)[0])
for i in range(8):
	p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":8,"AspirateOffsetOfZ":0.8,"AspirateSpeed":30,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p1_empty({"Position":"M2_POS7","Col":7,"Row":i+1,"EmptyOffsetOfZ":0.5,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
# 8 行全部分装完成后再丢弃枪头。
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

spx_p2_v_0.Wait()

#Block begin:将靶向扩增反应液与样本混合
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})

# 添加靶向扩增反应液到样本中：15 uL TA Master Mix + 5 uL T6/index 引物 + 5 uL cDNA 产物。
if low_throughput_p1_direct_col10:
	# 低通量直接分装按来源分阶段执行，避免每个样本反复开关 POS10 盖板。
	# TA Master Mix 只接触同一混合液和空 TA 目标孔，每个样本列复用 1 支 50 uL 枪头。
	# T6/index 按列使用 P8 排枪转移；cDNA 产物仍使用逐样本独立枪头，避免样本回带。
	transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
	ta_direct_mix_tips = tip_50.load(col_num, 1)
	for col_index in range(col_num):
		p1_load_modified(ta_direct_mix_tips[col_index])
		last_row = 8 if (col_index < col_num - 1 or SampleCount % 8 == 0) else SampleCount % 8
		for row in range(1, last_row + 1):
			p1_aspirate_modified("M2_POS17", 2, 4, 15, PreAirVolume=5, AspirateSpeed=10, AspirateOffsetOfZ=0.6, DelayAfterAspirate=1, PostAirVolume=0, IfTrack=False)
			p1_empty_modified("M2_POS20", row, col_index+7, EmptyOffsetOfZ=3, EmptySpeed=50, DelayAfterEmpty=0.5, TipTouchTimes=0, PostAirVolume=0)
		p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})
	# POS10 T6/index 引物一次开盖处理完全部样本，处理完立即关盖。
	transfer({"StartPosition":"M2_POS10","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
	ta_direct_reagent_tips = tip_50.load(sample_num, 8, 1)
	for col_index in range(col_num):
		p8_load_modified(ta_direct_reagent_tips[col_index])
		p8_aspirate({"Position":"M2_POS10","Col":col_index+1,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":5,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS20","Col":col_index+7,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS10","LoosenOffsetOfZ":0})
	# 第二套 50 uL 单枪头：从 POS20 cDNA 产物来源孔加入 5 uL 到对应 TA 目标孔。
	ta_direct_sample_tips = tip_50.load(sample_num, 1)
	for tip_index, (col_index, row) in enumerate(active_sample_wells(SampleCount)):
		p1_load_modified(ta_direct_sample_tips[tip_index])
		p1_aspirate_modified("M2_POS20", row, col_index+1, 5, PreAirVolume=0, AspirateSpeed=5, AspirateOffsetOfZ=1.0, DelayAfterAspirate=3, PostAirVolume=1, IfTrack=False)
		p1_dispense({"Position":"M2_POS20","Col":col_index+7,"Row":row,"IsEmpty":False,"DispenseOffsetOfZ":0.5,"DispenseSpeed":50,"DispenseVolume":30,"DelayAfterDispense":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	for i in range(col_num):
		p8_load_modified(tip_50.load(target_tip_num_list[i])[0])
		p8_mix({"Position":"M2_POS20","Col":i+7,"Row":1,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":50,"MixAspirateOffsetOfZ":0.5,"MixVolume":22,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":50,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":50,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
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
		p8_aspirate({"Position":"M2_POS20","Col":i+1,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":1.0,"AspirateSpeed":5,"AspirateVolume":5,"PreAirSpeed":50,"DelayAfterAspirate":3,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":1,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_dispense({"Position":"M2_POS20","Col":i+7,"Row":1,"IsEmpty":False,"DispenseOffsetOfZ":0.5,"DispenseSpeed":50,"DispenseVolume":30,"DelayAfterDispense":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_mix({"Position":"M2_POS20","Col":i+7,"Row":1,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":50,"MixAspirateOffsetOfZ":0.5,"MixVolume":22,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":50,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":50,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
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

# PTseq_TA 启动后先等待 80 min，再依次准备 TA 纯化磁珠和 LA/PCR Master Mix。
delay({"Duration": 4800})

#####################################################T1 磁珠分装##############################################

p1_load_modified(tip_1000.load(1)[0])
#T1 磁珠混匀
p1_mix({"Position":"M2_POS24", "Col": 1, "Row": 1,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":0.8,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":2,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":"M2_POS24", "Col": 1, "Row": 1,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":1,"MixVolume":900,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":30,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":15,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})

# 计算磁珠分装体积：第一轮 TA 纯化每个样本使用 50 uL 磁珠，对 25 uL TA 产物为 2:1 比例，并使用 1.4 倍安全系数。
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



# TA PCR 等待结束前完成 LA/PCR Master Mix 的配制和长混匀；完成后关闭 POS17 盖板并在 6 C 冷位保存。
lang=get_lang()
if lang==1: #
 report({"Phase": "文库扩增准备", "Step": "配置文库扩增反应液", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Library Amplification preparation", "Step": "Preparing Library Amplification reaction mixture", "TaskType": "library", "RemainingTime": None})

#Block begin:配置文库扩增反应液
# T8 UDG 体积：小体积酶液按分段系数补偿 300 uL 枪头低体积死体积。
# 样本数 <16：系数 1.6 且最低 7 uL；样本数 >=16：系数 1.3。
def _t8_vol(n):
	return max(1 * 1.6 * n, 7) if n < 16 else 1 * 1.3 * n

low_throughput_p1_direct_col11 = use_low_throughput_p1_direct(SampleCount)
report_low_throughput_branch("第11列文库扩增PCR反应液", "Col11 library amplification PCR mix", low_throughput_p1_direct_col11, SampleCount)
# 低通量分支直接从 POS17 C2R3 mixing tube 分装到反应孔，只计算 mixing tube 冗余。
# 高通量分支使用 POS7 Col11 中转，每个 POS7 中转孔保留 20 uL 总冗余，再叠加 mixing tube 冗余。
# LA mixing tube 冗余使用 LA_MIX_TUBE_DEAD_VOLUME（独立于 TA），冗余计入总体系后按 20:1:9 分摊。
if low_throughput_p1_direct_col11:
	pos7_col11_volumes = [0] * 8
	mix_total_col11 = 30 * SampleCount + LA_MIX_TUBE_DEAD_VOLUME
else:
	pos7_col11_volumes = [pos7_reaction_mix_dispense_volume(30, SampleCount, r) for r in range(8)]
	mix_total_col11 = mix_total_with_collection_reserve(pos7_col11_volumes, LA_MIX_TUBE_DEAD_VOLUME)
# T7:T8:T2 严格 20:1:9。T8 手工预置在 C2R3，la_t8_vol 仅用于总量记账/分装表，机器不吸取。
la_t7_vol = mix_total_col11 * 20 / 30
la_t8_vol = mix_total_col11 * 1 / 30
la_t2_vol = mix_total_col11 * 9 / 30
la_split_t2_to_pos7 = not low_throughput_p1_direct_col11 and mix_total_col11 > LA_MIX_TUBE_MAX_WORKING_VOLUME
la_t7_t8_pos7_volumes = [volume * 21 / 30 for volume in pos7_col11_volumes]
la_t2_pos7_volumes = [volume * 9 / 30 for volume in pos7_col11_volumes]

transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
# T8 已手工预置在 POS17 C2R3 的 2.0 mL mixing tube 内，机器不再单独吸取 T8。
# 机器只把 T7（POS17 C1R3）和 T2（POS24 C1R2）加入 C2R3，再原地混匀。
if SampleCount > 20:
	p1_load_modified(tip_1000.load(1)[0])
	# 吸取 T7 PCR mix：降低第一段进液速度，减少枪头进入液面时扰动。分两次，避免超过 1000 uL 枪头容量。
	p1_aspirate({"Position":"M2_POS17","Col":1,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t7_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":2,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	delay({"Duration": 10})
	p1_empty({"Position":"M2_POS17","Col":2,"Row":3,"EmptyOffsetOfZ":10,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	p1_load_modified(tip_1000.load(1)[0])
	p1_aspirate({"Position":"M2_POS17","Col":1,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t7_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":2,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

	if not la_split_t2_to_pos7:
		# 总体积不超过 2.0 mL 管工作上限时，T2 在 C2R3 内完成配制。分两次转移。
		p1_load_modified(tip_1000.load(1)[0])
		p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":150,"AspirateVolume":la_t2_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
		p1_empty({"Position":"M2_POS17","Col":2,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
		p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
		p1_load_modified(tip_1000.load(1)[0])
		p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":150,"AspirateVolume":la_t2_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
		p1_empty({"Position":"M2_POS17","Col":2,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
		p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
else:
	p1_load_modified(tip_1000.load(1)[0])
	# 吸取 T7 PCR mix：每孔 20 uL，并降低第一段进液速度。
	p1_aspirate({"Position":"M2_POS17","Col":1,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t7_vol,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":2,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	delay({"Duration": 10})
	p1_empty({"Position":"M2_POS17","Col":2,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	if not la_split_t2_to_pos7:
		# 低体积体系在 C2R3 内完成 T2 配制。
		p1_load_modified(tip_1000.load(1)[0])
		p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":150,"AspirateVolume":la_t2_vol,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
		p1_empty({"Position":"M2_POS17","Col":2,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
		p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
# POS17 盖处于打开状态，无需关盖再开盖。
# 混匀 LA/PCR Master Mix。
if SampleCount <=20:
	if SampleCount <=5:
		p1_load_modified(tip_300.load(1)[0])
	else:
		p1_load_modified(tip_1000.load(1)[0])
	p1_mix({"Position":"M2_POS17", "Col": 2, "Row": 3,"PreAirVolume":80,"MixTimes":10,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":30*SampleCount,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_mix({"Position":"M2_POS17", "Col": 2, "Row": 3,"PreAirVolume":80,"MixTimes":10,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":30*SampleCount,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_mix({"Position":"M2_POS17", "Col": 2, "Row": 3,"PreAirVolume":80,"MixTimes":10,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":30*SampleCount,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":15,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":3, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":2,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
else:
	p1_load_modified(tip_1000.load(1)[0])
	# 样本数 >20 时使用 900 uL 混匀体积，覆盖更大的 LA/PCR Master Mix 总量。
	p1_mix({"Position":"M2_POS17", "Col": 2, "Row": 3,"PreAirVolume":80,"MixTimes":15,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":900,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_mix({"Position":"M2_POS17", "Col": 2, "Row": 3,"PreAirVolume":80,"MixTimes":15,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":900,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_mix({"Position":"M2_POS17", "Col": 2, "Row": 3,"PreAirVolume":80,"MixTimes":15,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":900,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":15,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":3, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":2,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})

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
	# 第一步：先吸取 25 uL T2，干净枪头先接触 T2，避免样本回带污染 POS7 T2 条。
	p8_aspirate({"Position":"M2_POS7","Col":7,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":30,"AspirateVolume":25,"PreAirSpeed":50,"DelayAfterAspirate":2,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 第二步：同一批枪头继续吸取 25 uL TA 产物。
	p8_aspirate({"Position":"M2_POS20","Col":7+i,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0.5,"AspirateSpeed":40,"AspirateVolume":25,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 第三步：把 50 uL 混合液（T2 + TA 产物）打入 POS16 的磁珠孔。
	p8_empty({"Position":"M2_POS16","Col":7+i,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":40,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.3, "TipTouchSpeed": 100})
	# 第四步：混匀 50 uL 磁珠 + 25 uL TA 产物 + 25 uL T2，总体积约 100 uL，混匀体积设为 95 uL。
	p8_mix({"Position":"M2_POS16","Col":7+i,"Row":1,"PreAirVolume":20,"MixTimes":5,"MixAspirateSpeed":80,"MixAspirateOffsetOfZ":0.5,"MixVolume":95,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":50,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":10,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":0, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty({"Position":"M2_POS16","Col":7+i,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":20,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.3, "TipTouchSpeed": 100})
	p8_unload_modified(TA_purification_tips[i])
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1000, "Duration": 30}})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 0, "Speed": 1000, "Duration": 30}})

delay({"Duration": 300})

transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})#关PCR盖板
pcr_close_door()  # PCR 盖板放回后立即关闭 PCR 门。

def predispense_TA_ethanol_to_POS7():
	# v12：POS3 → POS7 乙醇预分装参考 PTplus 风格；5 次循环 ×195 uL = 975 uL/孔，分层高度 0.5 + 4*tt。
	# 该动作与 POS23 磁吸等待并行执行，确保 TA 弃上清后可以立即加乙醇，降低磁珠过早干燥风险。
	Alcohol_1 = tip_1000.load(8,8)
	p8_load_modified(Alcohol_1[0])
	for tt in range(5):
		target_columns = range(col_num) if tt % 2 == 0 else range(col_num - 1, -1, -1)
		for x in target_columns:
			p8_aspirate({"Position":"M2_POS3","Col":1,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":1.0,"AspirateSpeed":80,"AspirateVolume":195,"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":0})
			p8_empty({"Position":"M2_POS7","Col":1+x,"Row":1,"EmptyOffsetOfZ":0.5+4*tt,"EmptySpeed":50,"DelayAfterEmpty":0.8,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})


###48μL磁珠1振荡位置转移到磁吸位置
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})
TA_ethanol_predispense_wait = parallel_block(predispense_TA_ethanol_to_POS7)
delay({"Duration": 180})
TA_ethanol_predispense_wait.Wait()

# === 废液回收设置 ===
# POS14/POS11 已对换：原 POS14 深孔废液板现在固定放在 POS11。
# POS11 1.3 mL 深孔板 Col1-6 用于回收废液（与样本列 1:1 映射）。
# 累计废液量: 95 + 420 + 85 + 420 = 1020 µL/孔 (容量 1300 µL)
waste_col_start = 1

Ligation_purification_tips2 = tip_300.load(sample_num,8,0)  # reuse_index=0：TA 乙醇洗涤/弃液枪头用完直接丢弃。
# 注意：T2 现在在磁吸前加入，用于帮助 DNA 结合到 SPRI 磁珠。
# 旧逻辑曾在弃上清后再加 T2，这与结合机理不符。
# DNA 需要 PEG/盐环境才能有效结合 SPRI 磁珠，因此不能把 T2 放到弃上清之后。

# 连接后纯化乙醇清洗
lang=get_lang()
if lang==1: #
 report({"Phase": "靶向扩增反应后纯化", "Step": "乙醇清洗", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Targeted Amplification Purification", "Step": "Ethanol Wash", "TaskType": "library", "RemainingTime": None})

# 移除上清：结合体系约 100 uL（50 uL 磁珠 + 25 uL TA + 25 uL T2），吸走 110 uL 用于“弃多于打”的余量策略。
# 废液按样本列 1:1 回收到 POS11 Col1-6。
for i in range(col_num):
	p8_load_modified_BubblePurge(TA_purification_tips[i])
	p8_aspirate({"Position":"M2_POS23","Col":7+i,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":30,"AspirateVolume":110,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 将废液打入 POS11 废液板，列映射与样本列保持 1:1。
	p8_empty({"Position":"M2_POS11","Col":waste_col_start+i,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"TipTouchOffsetOfZ":15,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 乙醇洗涤继续使用前面分配好的 Ligation_purification_tips2。

# v12: TA 乙醇洗涤流程 - 静置等待方案, 加乙醇后不移板/不吹打, 仅做 120 s 磁吸沉降后弃乙醇
for i in range(2):
	# 第一步：加乙醇，板保持在 POS23 磁力架位。
	for x in range(col_num):
		p8_load_modified_BubblePurge(Ligation_purification_tips2[x])
		p8_aspirate({"Position":"M2_POS7","Col":1+x,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":1.0,"AspirateSpeed":50,"AspirateVolume":200,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS23","Col":7+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":2,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.4, "TipTouchSpeed": 100})
		p8_unload_modified(Ligation_purification_tips2[x])

	# 第二步：静置磁吸沉降，板始终保持在 POS23 磁力架位。
	delay({"Duration": 120})

	# 第三步：弃乙醇，板仍在 POS23；吸液体积从 210 uL 提到 220 uL，用 +20 uL 余量减少残液。
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
	# TA 纯化至少晾干 5 min；计时期间并行执行 PCR 板交换和高通量 POS7 预分装。
	delay({"Duration": 300})

magetic_wait = parallel_block(wait_for_magnetic_beads)

# 靶向扩增反应纯化PCR反应液回溶

# ============ 将 POS20 已用 PCR 板与 POS9 新 PCR 板对换 ============
# TA 结束后 POS20 已有使用过的孔；这里将 POS9 的新 PCR 板换到 POS20，用于 LA 和后续 DNB。
# 新板的 Col1-6 用于 LA，Col7-12 预留给 DNB 相关反应。
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})#开PCR盖板
transfer({"StartPosition":"M2_POS20","EndPosition":transposition,"LoosenOffsetOfZ":0})#POS20 (used) → POS30 (temp)
transfer({"StartPosition":"M2_POS9","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})#POS9 (fresh) → POS20
transfer({"StartPosition":transposition,"EndPosition":"M2_POS9","LoosenOffsetOfZ":0})# POS30 → POS9，存放已经用过的 PCR 板。
# ============ END SWAP ============
# State: door OPEN (line 1003), lid at POS26 (line 1004), fresh plate at POS20

lang=get_lang()
if lang==1: #
 report({"Phase": "Pre-PCR", "Step": "添加PCR mix", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Pre-PCR", "Step": "Adding PCR mix", "TaskType": "library", "RemainingTime": None})

# 已移除旧的除油步骤：此处 POS20 已经换成新 PCR 板，不存在上一轮矿物油残留。
# 旧代码曾从 Col7-12 除去 TA 矿物油；换新板后该动作不再需要。

if not low_throughput_p1_direct_col11:
	# v12：POS7 Col11 每行预分装体积来自上方逐孔封顶死体积算法。
	target_volume_list_pre_PCR = pos7_col11_volumes
	transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})


	p1_load_modified(tip_1000.load(1)[0])
	for i in range(8):
		pos17_dispense_volume = la_t7_t8_pos7_volumes[i] if la_split_t2_to_pos7 else target_volume_list_pre_PCR[i]
		p1_aspirate({"Position":"M2_POS17","Col":2,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":pos17_dispense_volume,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
		p1_empty({"Position":"M2_POS7","Col":11,"Row":i+1,"EmptyOffsetOfZ":0.5,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	if la_split_t2_to_pos7:
		# C2R3 只保留 T7+T8；T2 按 9/30 比例直接补入 POS7 Col11，避免 2.0 mL 管溢出。
		p1_load_modified(tip_1000.load(1)[0])
		for i in range(8):
			p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":150,"AspirateVolume":la_t2_pos7_volumes[i],"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
			p1_empty({"Position":"M2_POS7","Col":11,"Row":i+1,"EmptyOffsetOfZ":0.5,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
		p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})
	LA_dispense_tips = tip_300.load(sample_num,8,1)
	p8_load_modified(LA_dispense_tips[0])
	p8_mix({"Position":"M2_POS7","Col":11,"Row":1,"PreAirVolume":20,"MixTimes":10,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.5,"MixVolume":150,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":15,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2,"TipTouchOffsetOfZ":14,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100})
	p8_unload_modified(LA_dispense_tips[0])
	transfer({"StartPosition":"M2_POS7","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})
	temp_shaker_set({"TempParameters":{"IsEnable":False,"Duration":-1},"ShakerParameters":{"IsEnable":True,"Direction":0,"Speed":1000,"Duration":30}})
	temp_shaker_set({"TempParameters":{"IsEnable":False,"Duration":-1},"ShakerParameters":{"IsEnable":True,"Direction":1,"Speed":1000,"Duration":30}})
	transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS7","LoosenOffsetOfZ":0})

# 上述机械动作完成后，仅补足尚未达到的 5 min；若动作已超过 5 min，则立即继续加 LA Mix。
magetic_wait.Wait()

# LA 建库反应前处理：先把 LA/PCR Master Mix 加到 POS23 磁架上的干燥磁珠产物，再转到 POS16 振荡回溶形成磁珠悬液。
# 第一步：向 POS23 Col7-12 的干燥磁珠产物中加入 30 uL LA/PCR Master Mix。
if low_throughput_p1_direct_col11:
	transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
	LA_direct_tips = tip_50.load(sample_num, 1)
	for tip_index, (col_index, row) in enumerate(active_sample_wells(SampleCount)):
		p1_load_modified(LA_direct_tips[tip_index])
		p1_aspirate_modified("M2_POS17", 3, 2, 30, PreAirVolume=5, AspirateSpeed=50, AspirateOffsetOfZ=0.5, DelayAfterAspirate=0.5, TipTouchTimes=3, TipTouchOffsetOfZ=35, TipTouchRangeOfX=3.5, TipTouchSpeed=100, PostAirVolume=0, IfTrack=True)
		p1_empty_modified("M2_POS23", row, col_index+7, EmptyOffsetOfZ=0.5, EmptySpeed=20, DelayAfterEmpty=0.5, TipTouchTimes=0, PostAirVolume=5)
		p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})
else:
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
# 用双向振荡回溶干燥磁珠产物；总时长 2 min，改善靠后列干团未完全重悬的问题。
temp_shaker_set({"TempParameters":{"IsEnable":False,"Duration":-1},"ShakerParameters":{"IsEnable":True,"Direction":0,"Speed":1200,"Duration":60}})
temp_shaker_set({"TempParameters":{"IsEnable":False,"Duration":-1},"ShakerParameters":{"IsEnable":True,"Direction":1,"Speed":1200,"Duration":60}})

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
	p8_mix({"Position":"M2_POS20","Col":1+i,"Row":1,"PreAirVolume":5,"MixTimes":8,"MixAspirateSpeed":50,"MixAspirateOffsetOfZ":0.6,"MixVolume":35,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":50,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":2,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS10","LoosenOffsetOfZ":0})# 关闭 POS10 盖板

# v12：PTseq_LA 前向新 PCR 板 POS20 Col1-6 加 20 uL 矿物油，防止 LA PCR 蒸发。
if SampleCount%8 == 0:
	last_row =1
else:
	last_row = 9-SampleCount%8
oil_3 = tip_300.load(8,8,0)  # reuse_index=0：LA 矿物油枪头用完直接丢弃，不跨 PCR 阶段复用。

p8_load_tips({"Position":oil_3[0][0],"Col":oil_3[0][1],"Row":last_row,"Tips":8})
for i in range(col_num-1,-1,-1):
	p8_aspirate({"Position":"M2_POS11","Col":8,"Row":1,"PreAirVolume":20,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":20,"PreAirSpeed":50,"DelayAfterAspirate":1,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 1.5, "TipTouchSpeed": 100})
	# LA PCR 矿物油加到新板 Col1-6；这里已从旧版 Col7-12 修正。
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
- Column 8 (LA Beads): LA 纯化磁珠中转孔
- Column 12 (TA Beads): TA 纯化磁珠中转孔

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
# 磁珠位置（板、列、行）：T1 磁珠来源，同时用于 TA 和 LA 两轮纯化。
magetic_beads_pos = {"Position":"M2_POS24","Col":1,"Row":1}
# LA 磁珠预分位置：POS7 Col8，避免复用 TA 磁珠的 POS7 Col12 中转孔。
magetic_beads_pre_dispense_pos = {"Position":"M2_POS7","Col":8,"Row":1}
# 回溶液预分位置：POS7 Col7，用于 T2 缓冲液中转。
elution_buffer_pre_dispense_pos = {"Position":"M2_POS7","Col":7,"Row":1}
# 磁珠分装位置 1：LA 纯化使用 M2_POS16 Col1-6。
magetic_beads_dispense_pos1 = {"Position":"M2_POS16","Col":1,"Row":1}
magetic_beads_volume1 = 32  # LA 产物 40 uL，对应 0.8× 磁珠纯化，磁珠量为 32 uL。

# 磁珠分装位置 2：TA 纯化使用 M2_POS16 Col7-12。
magetic_beads_dispense_pos2 = {"Position":"M2_POS16","Col":7,"Row":1}
magetic_beads_volume2 = 20

# 计算磁珠分装体积
target_volume_list = [55*(SampleCount//8+1)]*(SampleCount%8)+[55*(SampleCount//8)]*(8-SampleCount%8)

# POS14/POS11 对换后，废液统一回收到 POS11 深孔板 Col1-6。
# waste_col_start defined at line ~808, shared by TA and LA purification

# 乙醇位置：POS7 Col1-6 为 80% 乙醇中转孔，支持多轮洗涤。
ethanol_pos = {"Position":"M2_POS7","Col":1,"Row":1}

# 双选产物位置 - Concentrated Library destination at POS13 Col 7-12
# 最终文库直接分装到 POS13，不分装到 POS16。
product_pos = {"Position":"M2_POS13","Col":7,"Row":1}



p1_load_modified(tip_1000.load(1)[0])
#增加混匀
p1_mix({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":0.8,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":2,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":10,"MixTimes":30,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":30,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":15,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})


for i in range(8):
	p1_aspirate({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":50,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 50, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p1_empty({"Position":magetic_beads_pre_dispense_pos["Position"], "Col":magetic_beads_pre_dispense_pos["Col"], "Row":magetic_beads_pre_dispense_pos["Row"]+i,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":2,"PostAirSpeed":50,"PostAirVolume":25,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

target_tip_num_list = [8]*(sample_num//8) + [sample_num%8]
temp = tip_300.load(8)[0]
p8_load_modified(temp)
p8_mix({"Position":magetic_beads_pre_dispense_pos["Position"], "Col":magetic_beads_pre_dispense_pos["Col"], "Row":1,"PreAirVolume":20,"MixTimes":15,"MixAspirateSpeed":150,"MixAspirateOffsetOfZ":0.5,"MixVolume":220,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":150,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(temp)
for i in range(col_num-1,-1,-1):
	if i == col_num-1 and target_tip_num_list[i] != 8:
		p8_load_modified((temp[0],temp[1],temp[2]+8-sample_num%8))
	elif i == col_num-1:
		p8_load_modified(temp)
	# v12：LA 产物磁珠 32 uL 转移使用保守 PTplus 第二次磁珠转移风格，用于避免生产中观察到的枪头中段气泡。
	p8_aspirate({"Position":magetic_beads_pre_dispense_pos["Position"], "Col":magetic_beads_pre_dispense_pos["Col"], "Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.9,"AspirateSpeed":30,"AspirateVolume":magetic_beads_volume1,"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX":1.2, "TipTouchSpeed": 100})
	p8_dispense({"Position":magetic_beads_dispense_pos1["Position"], "Col":magetic_beads_dispense_pos1["Col"]+i, "Row":1,"FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "DispenseOffsetOfZ": 0.8, "DispenseSpeed": 30, "DispenseVolume":magetic_beads_volume1,"DelayAfterDispense": 1, "IsEmpty": True, "EmptyOffsetOfZ": 0.8, "EmptySpeed": 50, "DelayAfterEmpty": 0.5, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})

	# 已移除无用途的 20 uL 磁珠转移到 dispense_pos2；TA 纯化磁珠已在前面完成。

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
	# 从 POS20 Col1-6 转移 40 uL LA PCR 产物；该位置已从旧版 Col7-12 修正。
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

# 更新 LA 纯化板位追踪：LA 使用 dispense_pos1，不使用 TA 的 dispense_pos2。
if magetic_beads_dispense_pos1["Position"] == "M2_POS16":
	magetic_beads_dispense_pos1["Position"] = "M2_POS23"

# 已移除多余的磁吸-振荡-磁吸循环（原 1385-1396 行）。
# 正常流程：磁吸分离 → 弃上清，无需再回振荡位重新磁吸

# 逐列去除废液到 POS11 废液板
for i in range(col_num):
	p8_load_modified_BubblePurge(temp[i])
	# 移除 85 uL 废液上清；对应 40 uL LA 产物 + 32 uL 磁珠体系，已从旧版 110 uL 调整。
	# 吸液高度从 0 调到 0.5 mm，与 TA 弃上清一致，避免贴底吸入磁珠。
	p8_aspirate({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+i,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":85,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS11","Col":waste_col_start+i,"Row":1,"EmptyOffsetOfZ":10,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"TipTouchOffsetOfZ":15,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_modified(temp[i])  # 将弃上清枪头放回原位，后续同列乙醇洗涤继续使用。

# 乙醇洗2次
lang=get_lang()
if lang==1: #
 report({"Phase": "Pre-PCR", "Step": "乙醇清洗", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Pre-PCR", "Step": "Ethanol Wash", "TaskType": "library", "RemainingTime": None})

# LA 乙醇洗涤复用弃上清时放回原位的 temp 枪头，可节省最多 48 个 300 uL 枪头。

# v12: LA 乙醇洗涤流程 - 静置等待方案, 加乙醇后不移板/不吹打, 仅做 120 s 磁吸沉降后弃乙醇
for i in range(2):
	# 第一步：加乙醇，板保持在 POS23 磁力架位。
	for x in range(col_num):
		p8_load_modified_BubblePurge(temp[x])
		p8_aspirate({"Position":ethanol_pos["Position"], "Col":ethanol_pos["Col"]+x, "Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":1.0,"AspirateSpeed":50,"AspirateVolume":200,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x, "Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
		p8_unload_modified(temp[x])

	# 第二步：静置磁吸沉降，板始终保持在 POS23 磁力架位。
	delay({"Duration": 120})

	# 第三步：弃乙醇，板仍在 POS23；吸液体积从 210 uL 提到 220 uL，用 +20 uL 余量减少残液。
	for x in range(col_num):
		p8_load_modified_BubblePurge(temp[x])
		p8_aspirate({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x, "Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0,"AspirateSpeed":10,"AspirateVolume":220,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS11","Col":waste_col_start+x,"Row":1,"EmptyOffsetOfZ":10,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"TipTouchOffsetOfZ":15,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
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
### 23 uL T2 洗脱液回溶；使用 50 uL 枪头以减少 300 uL 枪头消耗。

Product = tip_50.load(SampleCount,8,1)


for x in range(col_num):
	p8_load_modified(Product[x])
		# 从 POS7 预分装的 T2 洗脱液中吸取 23 uL，打入 POS23 磁珠孔。
	p8_aspirate({"Position":elution_buffer_pre_dispense_pos["Position"],"Col":elution_buffer_pre_dispense_pos["Col"],"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":23,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_mix({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x,"Row":1,"PreAirVolume":5,"MixTimes":6,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":18,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":40,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":8,"MixEmptySpeed":30,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_modified(Product[x])

###磁吸位置转移到振荡位置
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1200, "Duration": 150}})

#delay({"Duration": 30})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 0, "Speed": 1200, "Duration": 150}})
delay({"Duration": 300})

###振荡位置转移到磁吸位置
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})
delay({"Duration": 300})

###回收建库产物
# 最终文库目标位置已设为 M2_POS13 Col7，回收产物会直接打入该位置。
# 无需更新位置变量：浓缩后文库的固定目标位置就是 POS13。
# HIGH RISK：下方 P8 将在 POS13 深孔板打液和混匀，运行前必须确认 POS13/POS14 相邻区域无机械干涉。
for x in range(col_num):
	p8_load_modified_BubblePurge(Product[x])
	# 回收 21 uL 最终文库产物；对应 SOP 中 23 uL 洗脱、21 uL 回收。
	p8_aspirate({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0,"AspirateSpeed":10,"AspirateVolume":21,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":product_pos["Position"],"Col":product_pos["Col"]+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":10,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_mix({"Position":product_pos["Position"],"Col":product_pos["Col"]+x,"Row":1,"PreAirVolume":20,"MixTimes":10,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":10,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":1, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty({"Position":product_pos["Position"],"Col":product_pos["Col"]+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":10,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 将纯化板从磁力架位移回震荡位，便于后续取板或保存。
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})

# 已移除旧转板动作：最终文库已经直接分装到 POS13，无需再把整板转到 POS13。

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
dye_tip = tip_300.load(8,8,1)[0]  # reuse_index=1：定量染液分装枪头按 PTseq Plus 方式在同一染液步骤内复用。

# 稀释样本取枪头位置，列表，内置位置，必须是整列，可多不可少
sample_dilute_tip_loc = tip_50.load(sample_num,8,1)

# 样本来源起始位置,板位，起始列，样本必须从上到下，从左到右，从第一个开始
source_plate = ['M2_POS13',7]

# 样本与染液的混合起始位置：POS13 Col1-6，按样本列映射。
# 必须是深孔板，板位，起始列，样本必须从上到下，从左到右，从第一个开始
dye_mix_plate = ['M2_POS13',1]

# POS14/POS11 对换后，定量管 home 在 POS14；实际读数/移液时临时换到 POS13 访问。
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
# 定量流程模板：先在染液混合板中混合样本和染液，再移到 POS16 震荡，随后把定量管换到 POS13 并转移读数。

# 第一步：向染液混合板 POS13 Col1-6 分装 Qubit 染液。
if sample_num%8 == 0:
	last_row = 1
else:
	last_row = 9-(sample_num%8)

for i in range(col_num-1,-1,-1):
	# 如果最后一列样本不足 8 个，只装载对应数量的枪头。
	if i == col_num - 1:
		p8_load_tips({"Position":dye_tip[0],"Col":dye_tip[1],"Row":last_row,"Tips":8})
	# 每孔加入 217.8 uL 染液；后续加入 2.2 uL 样本，对应 Qubit 1:100 稀释比例。
	for j in range(1):
		p8_aspirate_modified(dye_loc[0], Row=dye_loc[2], Col=dye_loc[1], AspirateVolume=217.8, PreAirVolume=10, AspirateOffsetOfZ=1.0)
		p8_empty_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i, EmptyOffsetOfZ=3+2*j, TipTouchTimes=1)
	# 处理最后一列不足 8 个样本时的枪头放回/重取。
	if i == col_num - 1 and sample_num%8!=0:
		p8_unload_tips({"Position":dye_tip[0],"Col":dye_tip[1],"Row":last_row,"Tips":8})
		p8_load_tips({"Position":dye_tip[0],"Col":dye_tip[1],"Row":1,"Tips":8})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 第二步：向染液混合板加入样本并在孔内混匀。
# HIGH RISK：P8 在 POS13 深孔板吸取 2.2 uL 文库；该位置邻近 POS14，必须确认板架无干涉。
for i in range(col_num):
	p8_load_modified(sample_dilute_tip_loc[i])
	p8_aspirate_modified(source_plate[0], 1, source_plate[1]+i, 2.2, AspirateSpeed=2, AspirateOffsetOfZ=0.5, IfTrack=True)
	p8_empty_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i, EmptyOffsetOfZ=12)
	# 在染液混合板中混匀样本和染液。
	p8_mix({"Position":dye_mix_plate[0],"Col":dye_mix_plate[1]+i,"Row":1,"PreAirVolume":10,"MixTimes":2,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":1,"MixVolume":40,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_modified(sample_dilute_tip_loc[i])

# 第三步：执行定量混合板震荡换位；先腾空 POS16，再把 POS13 混合板移入 POS16 震荡，震荡后恢复。
# 先把当前 POS16 上的板移到 POS23 暂存，腾出震荡位。
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})
# 把染液混合板从 POS13 移到 POS16 震荡位。
transfer({"StartPosition":"M2_POS13","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})
# 双方向震荡，提高染液和样本混匀均一性。
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": 60}, "ShakerParameters": {"IsEnable": True,"Direction": 0,"Speed": 1200,"Duration": 60}})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": 60}, "ShakerParameters": {"IsEnable": True,"Direction": 1,"Speed": 1200,"Duration": 60}})
# 震荡完成后，把染液混合板移回 POS13。
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS13","LoosenOffsetOfZ":0})
# 将原先暂存在 POS23 的板恢复到 POS16。
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})

# 第四步：把 POS13 的样本/染液混合板临时停放到空闲 POS23，再把 POS14 定量管换到 POS13。
transfer({"StartPosition":"M2_POS13","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})
dye_mix_plate[0] = "M2_POS23"
transfer({"StartPosition":quantification_tube_home_pos,"EndPosition":quantification_tube_operating_pos,"LoosenOffsetOfZ":0})

# 第五步：从当前停在 POS23 的同一块混合板转移到 POS13 定量管。
for i in range(col_num):
	p8_load_modified(sample_dilute_tip_loc[i])
	# 每孔分 4 次各 50 uL 从混合板转移到定量管。
	for x in range(4):
		p8_aspirate_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i, PreAirVolume=5, AspirateVolume=50, AspirateOffsetOfZ=1, PostAirVolume=3, IfTrack=True)
		p8_empty_modified(quantification_tube_loc[0], Row=1, Col=quantification_tube_loc[1]+i, EmptyOffsetOfZ=5, EmptySpeed=80)
	# 在定量管中再次混匀，保证读数前液体均一。
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

# 定量结束后，定量管从 POS13 回 POS14；样本/染液混合板从 POS23 回 POS13，恢复 deck 状态。
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





# [v7] 不再交换 POS13 和 POS14；library 产物保留在 POS13 Col7-12 原位。
# 最终文库位置保持 M2_POS13 不变。














# [v7] 删除了原本在此处的错位"第二次定量(DNB)"段落（原v6第1595-1760行）
# 该段在pooling和make DNB之前就尝试定量DNB产物，逻辑错误
# 正确的DNB定量将在make DNB完成后执行（见脚本末尾）

# Hybridization_num 会在 pooling 段根据 SampleCount 重新计算，此处不再需要沿用旧值。

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

# [v7] 原位稀释：直接在POS13 Col 7-12的library产物孔内加T2 buffer，不再使用POS14 Col 1-6
sample_dilution_place = ('M2_POS13',7)  # 稀释位置 = 样本来源位置（原位）

# 样本取样体积临界值
min_sample_volume = 2
max_sample_volume = 20


#单个DNB样本数 - 200/2000: 所有样本归入1个pool
single_dnb_sample_num = SampleCount
# 单个DNB投入量 (G99说明书: 1pmol ≈ 200ng for ~300bp fragments)
target_dna_ng = 200
#pooling总体积
target_pooling_volume = 48
# 质控浓度
sample_qc_concentration = 1

#pooling取buffer使用1ml枪头
single_tip_loc = tip_1000.load(1)[0]
#pooling稀释buffer位置，板-列-行 - M2_POS24 B1 (Col 1, Row 2) contains T2 buffer
dilution_buffer_loc = ('M2_POS24',1,2)
#pooling产物位置，板位，列，行 - Pooling Product at M2_POS11 Column 7
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
# 浓度不合格样本是否一起 pooling；False 表示剔除浓度低于质控阈值的样本。
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
		self.barcode = ""
		self.group_idx = None
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
		sample_concentration[i].barcode = filtered_samples[i].barcode
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
if sample_num == 0:
	raise Exception("过滤低浓度或空白样本后没有可 pooling 的有效样本，请检查定量结果和样本类型")

def get_barcode_key(sample):
	raw_barcode = sample.barcode.strip()
	if not raw_barcode:
		return ("MISSING_BARCODE", getattr(sample, "sample_initial_index", sample.sample_id))
	try:
		barcode_value = 0
		for part in raw_barcode.split('-'):
			barcode_value += 1 << int(part)
		return barcode_value
	except ValueError:
		raise Exception(f"样本 {sample.sample_id} 的 barcode '{sample.barcode}' 格式不合法，应为数字或数字-数字组合")

def validate_barcode_uniqueness(groups):
	for i, group in enumerate(groups):
		seen = {}
		for sample in group:
			barcode_key = get_barcode_key(sample)
			if barcode_key in seen:
				raise Exception(f"DNB组 {i+1} 内 barcode 重复: {sample.barcode}; 样本 {seen[barcode_key]} 和 {sample.sample_id}")
			seen[barcode_key] = sample.sample_id

def group_samples_single_pool(samples):
	for sample in samples:
		sample.group_idx = 1
	if len(target_dnb_loc_list) < 1:
		raise Exception("2000&200全流程没有配置DNB反应位")
	if len(target_tube_loc) < 1:
		raise Exception("Pooling暂存位不足：当前未配置pooling暂存位")
	groups = [samples]
	validate_barcode_uniqueness(groups)
	return groups

dnb_list = group_samples_single_pool(sample_concentration)
target_dnb_num = len(dnb_list)
# Update Hybridization_num to match calculated DNB count
Hybridization_num = target_dnb_num

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
		f.write("样本编号,Pooling组,取样体积(ul),稀释倍数,放大倍数,杂交浓度\n")
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
				f.write(f"{sample.sample_id},{cur_pooling_id},{formated_vol},{dilution_type},{concentrate_times},{conc}\n")
		# 输出被过滤掉的样本（不在任何pool中），标记为'-'
		for idx in range(len(concentration_list)):
			if idx not in pooled_indices:
				sid = filtered_samples[idx].sample_id if (filtered_samples and idx < len(filtered_samples)) else f"Sample_{idx+1}"
				f.write(f"{sid},'-',,,,{concentration_list[idx]}\n")
# 调用函数输出信息
output_hybrid_pooling_info(dnb_list, temp, output_file_path)
print(f"样本的 pooling 组、取样体积、稀释倍数和放大倍数已输出到文件：{output_file_path}")


# [v7] ===== Normalization + Pooling 重写 =====
# 流程: POS11→POS23 → 原位稀释(POS13) → pooling(POS13→POS23) → 转移到POS20 → POS23→POS11

# Step 1: 移动POS11 (pooling深孔板) 到POS23 (空闲, p1/p8均可达)
transfer({"StartPosition":"M2_POS11","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})  # POS11 → POS23

# 操作时pooling管在POS23 Col 7
pooling_tube_pos = 'M2_POS23'
pooling_tube_col = 7

# Step 2: Normalization - 原位稀释高浓度样本 (p1加T2 buffer到POS13 Col 7-12)
p1_load_tips({"Position":single_tip_loc[0],'Col':single_tip_loc[1],'Row':single_tip_loc[2]})

if water_loc_list:
	for i in range(len(water_loc_list)):
		# 加入147µL T2 buffer实现8倍原位稀释 (21µL library + 147µL buffer = 168µL, 8x dilution)
		p1_aspirate({"Position": dilution_buffer_loc[0], "Row": dilution_buffer_loc[2], "Col": dilution_buffer_loc[1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "PreAirSpeed": 100, "PreAirVolume": 10, "SecondSegmentSpeed": 100, "AspirateOffsetOfZ": 1.0, "AspirateSpeed": 20, "AspirateVolume": 147, "DelayAfterAspirate": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100, "PostAirSpeed": 100, "PostAirVolume": 10})
		p1_empty({"Position": water_loc_list[i][0], "Row": water_loc_list[i][1], "Col": water_loc_list[i][2], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100, "EmptyOffsetOfZ": 1, "EmptySpeed": 190, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})

# HIGH RISK：下方 P8 将首次访问 POS13 深孔板。先把 POS14 定量管架移到 POS30，避免机械干涉。
transfer({"StartPosition":"M2_POS14","EndPosition":"M2_POS30","LoosenOffsetOfZ":0})

# Step 3: p8 吹吸混匀已稀释的孔 (POS13 Col 7-12 原位)
if water_loc_list:
	for i in range(len(water_loc_list)):
		p8_load_modified(tip_50.load(1)[0])
		p8_mix({"Position":water_loc_list[i][0],"Col":water_loc_list[i][2],"Row":water_loc_list[i][1],"PreAirVolume":10,"MixTimes":10,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.5,"MixVolume":100,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":100,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# Step 4: p1 加补水到pooling管 (POS23 Col 7) 和 DNB反应孔 (POS20)
for i in range(len(water_volume_list)):
	if temp[i][0]>=8:
		new_water_volume = target_pooling_volume-target_pooling_volume/(temp[i][0]/8)
		p1_aspirate({"Position": dilution_buffer_loc[0], "Row": dilution_buffer_loc[2], "Col": dilution_buffer_loc[1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "PreAirSpeed": 100, "PreAirVolume": 10, "SecondSegmentSpeed": 100, "AspirateOffsetOfZ": 1.0, "AspirateSpeed": 20, "AspirateVolume": new_water_volume, "DelayAfterAspirate": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100, "PostAirSpeed": 100, "PostAirVolume": 10})
		p1_empty({"Position": target_dnb_loc_list[i][0], "Row": target_dnb_loc_list[i][2], "Col": target_dnb_loc_list[i][1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100, "EmptyOffsetOfZ": 2, "EmptySpeed": 190, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})
	p1_aspirate({"Position": dilution_buffer_loc[0], "Row": dilution_buffer_loc[2], "Col": dilution_buffer_loc[1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "PreAirSpeed": 100, "PreAirVolume": 10, "SecondSegmentSpeed": 100, "AspirateOffsetOfZ": 1.0, "AspirateSpeed": 100, "AspirateVolume": water_volume_list[i], "DelayAfterAspirate": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100, "PostAirSpeed": 100, "PostAirVolume": 10})
	p1_empty({"Position": pooling_tube_pos, "Row": i+1, "Col": pooling_tube_col, "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100, "EmptyOffsetOfZ": 5, "EmptySpeed": 190, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})

p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# Step 5: p8 从POS13 Col 7-12取样 → POS23 Col 7 pooling管 (所有样本统一流程，不再区分稀释/非稀释)
# POS14 定量管架已在首次 P8 访问 POS13 前移到 POS30，此处保持 POS14 为空。
for i,poolings in enumerate(temp):
	samples = dnb_list[i]
	for sample in samples:
		p8_load_modified(tip_50.load(1)[0])
		sample_volume = sample.DilutingSampleVolume
		sample_col = sample.SampleWellColumn
		sample_row = sample.SampleWellRow
		# HIGH RISK：从 POS13 深孔板直接吸取文库到 pooling 孔。
		p8_aspirate_modified(source_plate[0],sample_row,sample_col,sample_volume,PreAirVolume=10,AspirateSpeed=80,AspirateOffsetOfZ=0.5,DelayAfterAspirate=0.5,PostAirVolume=0)
		p8_empty_modified(pooling_tube_pos,i+1,pooling_tube_col)
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# POS13 pooling 取样完成后立即恢复 POS14，释放 POS30，避免后续板位交换发生碰撞。
transfer({"StartPosition":"M2_POS30","EndPosition":"M2_POS14","LoosenOffsetOfZ":0})

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
### FIX F-01: Removed pcr_open_door() — door already closed at pcr_close_door() above.
### blockSS needs door CLOSED to run PTseq_2000_SSR.
lang=get_lang()
if lang==1: #
 report({"Phase": "单链环化", "Step": "单链反应程序", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Single-Strand Cyclization", "Step": "Single-Strand Reaction Program", "TaskType": "library", "RemainingTime": None})

def blockSS():
	pcr_run_method({"Methods": ["PTseq_2000_SSR"]})
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
	pcr_run_method({"Methods": ["PTseq_2000_CR_30min"]})
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
	p8_aspirate({"Position":"M2_POS17", "Col":3, "Row":5,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":20,"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty({"Position":"M2_POS20","Col":8,"Row":1+x,"EmptyOffsetOfZ":0.5,"EmptySpeed":3,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 0, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})


# [v7] 加样本（从环化反应孔Col 7转移到DNB制备孔Col 8）— 循环处理所有DNB组
DNB1_mix = tip_300.load(DNB_Num,1)
for x in range(DNB_Num):
	p8_load_modified(DNB1_mix[x])
	# 混合环化产物 (Col 7, Row 1+x)
	p8_mix({"Position":"M2_POS20","Col":7,"Row":1+x,"PreAirVolume":10,"MixTimes":10,"MixAspirateSpeed":30,"MixAspirateOffsetOfZ":0.5,"MixVolume":40,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":30,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 从环化孔吸取20µL样本 (Col 7, Row 1+x)
	p8_aspirate({"Position":"M2_POS20","Col":7,"Row":1+x,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":20,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 分装到DNB制备孔 (Col 8, Row 1+x)
	p8_empty({"Position":"M2_POS20","Col":8,"Row":1+x,"EmptyOffsetOfZ":0.8,"EmptySpeed":20,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 混合DNB制备体系 (Col 8, Row 1+x)
	p8_mix({"Position":"M2_POS20","Col":8,"Row":1+x,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":30,"MixAspirateOffsetOfZ":0.5,"MixVolume":35,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":30,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
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
	pcr_run_method({"Methods": ["PTseq_2000_DNB1"]})
d1 = parallel_block(blockD1)

##################################################################################### DNB制备体系2 ############################################################################
#配置DNB制备体系2——E1 Mix I打入E2 Mix II源管混合（big-into-small, E5工作管保留但不使用）
#DNB Polymerase: E1 Mix I(大体积) → E2 Mix II tube → mix in E2 → 后续直接从E2分装
p8_load_modified(tip_300.load(1)[0])
# Step 1: 吸取E1 DNB聚合酶混合液I——手工配置DNB聚合酶混合液II(LC) = 2*(DNB_Num+0.5) µL 在E2 Mix II管中
p8_aspirate({"Position":"M2_POS17", "Col":1, "Row":5,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":40 * (DNB_Num + 0.5),"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
# Step 2: 打入E2 Mix II源管 (big into small, 冲洗小体积Mix II)
p8_empty({"Position":"M2_POS17","Col":2,"Row":5,"EmptyOffsetOfZ":0.5,"EmptySpeed":10,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 0, "TipTouchSpeed": 100})
# Step 3: 在E2管中混合Mix I + Mix II
p8_mix({"Position":"M2_POS17","Col":2,"Row":5,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":30,"MixAspirateOffsetOfZ":0.5,"MixVolume":40*DNB_Num+15,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":30,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
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
	p8_aspirate({"Position":"M2_POS17", "Col":2, "Row":5,"PreAirVolume":2,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":44,"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty({"Position":"M2_POS20","Col":8,"Row":1+x,"EmptyOffsetOfZ":0.5,"EmptySpeed":10,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 0, "TipTouchSpeed": 100})
	p8_mix({"Position":"M2_POS20","Col":8,"Row":1+x,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":30,"MixAspirateOffsetOfZ":0.5,"MixVolume":70,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":30,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
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
	pcr_run_method({"Methods": ["PTseq_2000_RCA_25min"]})
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
	p1_aspirate({"Position":"M2_POS17", "Col":4, "Row":5,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":20,"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS20","Col":8,"Row":1+x,"EmptyOffsetOfZ":0.5,"EmptySpeed":50,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 0, "TipTouchSpeed": 100})
	p1_mix({"Position":"M2_POS20","Col":8,"Row":1+x,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":0.5,"MixVolume":90,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":2,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# DNB定量已移除 - DNB为单链DNA，机上dsDNA_HS无法准确定量，改为手动ssDNA kit定量

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})###关盖板
###PCR关门
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0}) #PCR盖板
pcr_close_door()

def blockD3():
	pcr_run_method({"Methods": ["Keep4_8h"]})
d3 = parallel_block(blockD3)

d3.Wait()

# Home all axes at end of run to allow easy sample retrieval
home()
