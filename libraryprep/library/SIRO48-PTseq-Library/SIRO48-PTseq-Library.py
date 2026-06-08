
# -*- coding: utf-8 -*-
#####################################################################
# GenSIRO48 G99 PTseq 建库流程脚本。
# 流程从 POS8 提取产物板开始，依次执行 cDNA 合成、靶向扩增、文库扩增、
# TA/LA 两轮磁珠纯化和 Qubit dsDNA HS 定量。
# 本脚本不执行 pooling 和 make DNB；流程状态通过 report(...) 输出到中台软件。
# 最终文库产物保存在 POS20 Col7-12；定量取样后 PCR 模块运行 4keep。
#####################################################################
# 共用头部包含平台初始化、枪头管理、移液封装和通用辅助函数。

from library import *
spxsiro = globals().get("library")
set_siro(spxsiro)
import math

home()
def blockA():
	temp_set({"Name":"M2_tempC","Temp": 6.00, "Duration": -1})#4度，POS17
	temp_set({"Name":"M2_tempB","Temp": 6.00, "Duration": -1})#4度，POS10

a = parallel_block(blockA)
# POS17/POS10 低温模块并行启动，后续液体处理立即继续执行。

'''==================================================================自动计算取枪头位置逻辑======================================================'''
# Tips 管理每种枪头的可用列、复用锁定列和备用枪头盒交换；reuse_index=1 表示该列枪头会放回原位等待后续复用。



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
		# 每列按 8 支枪头登记；列表元素为 [剩余枪头数, 枪头盒位置, 列号]。
		for i in range(1,13):
			self.tip_list.append([8,target,i])
	def refresh_tip_list(self):
		'''当前枪头盒耗尽时，切入一个备用枪头盒并刷新占用状态。'''
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
	'''取枪头逻辑：
		依次遍历已有的枪头列，返回可用枪头,返回顺序为板，列，行
		tip_num_per_time:单次取枪头个数，reuse_index：是否复用枪头，为0表示用枪头不复用，为1表示枪头会复用'''
	def load(self, tip_num, tip_num_per_time=8, reuse_index=0):
		result = []  # 用于存储结果的列表
		while tip_num > 0:
			found = 0
			cur_tip_num = min(8, tip_num, tip_num_per_time)
			for i, each in enumerate(self.tip_list):
				# x 为当前列剩余枪头数，y 为枪头盒板位，z 为列号。
				x, y, z = each
				# 复用列在归还前不能再次分配。
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

#===========================================================================取/放枪头封装=======================================================================
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

def p8_empty_waste_high(Position, Col, Row=1):
	p8_empty({"Position":Position,"Col":Col,"Row":Row,"EmptyOffsetOfZ":30,"EmptySpeed":30,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"TipTouchOffsetOfZ":30,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})


'''============================================================枪头位置=============================================================='''
# 枪头盒布局：300 uL、1000 uL、50 uL 枪头均在这里统一定义。
tip_300_loc = ['M2_POS5','M2_POS6']
backup_tip_300_loc = ['M2_POS28','M2_POS29']
tip_300 = Tips(tip_300_loc,backup_tip_300_loc)

tip_1000_loc = ['M2_POS18']
tip_1000 = Tips(tip_1000_loc)

# POS19 为 50 uL 备用枪头盒，deck.json 中 POS19 也必须定义为 50 uL 枪头盒。
tip_50_loc = ['M2_POS15','M2_POS12']
backup_tip_50_loc = ['M2_POS25','M2_POS19']
tip_50 = Tips(tip_50_loc,backup_tip_50_loc)

'''=====================================中转位=============================================================='''
transposition = "M2_POS30"

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

	# 第五步：如果调用前 POS16 已有板，从 POS30 恢复回 POS16。
	if current_shaker_occupant:
		transfer({"StartPosition":"M2_POS30","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})

#===========================================================================吸液封装=======================================================================


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

#===========================================================================排空封装=======================================================================
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

def pos7_reaction_mix_dispense_volume(p8_volume_per_column, sample_count, row_index, pos7_dead_volume=10):
	active_cols = active_col_count_for_row(sample_count, row_index)
	if active_cols <= 0 or p8_volume_per_column <= 0:
		return 0
	return active_cols * p8_volume_per_column + pos7_dead_volume

# POS17 2 mL 混合管分装到 POS7 后保留 15 uL 死体积。
MIX_TUBE_DEAD_VOLUME = 15

# 低通量直接分装阈值：SampleCount <= 16 走 P1 50 uL 直接分装，>16 走 POS7/P8。
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


'''=====================================样本信息读取=============================================================='''
# 输入文件由中台写入 D:/Pathogens/PTseq.csv。脚本按 CSV 中的有效样本数量决定后续列数和枪头数量；
# 如果文件不存在或为空，则弹窗要求人工输入样本数。
sample_info_file_path = r'D:/Pathogens/PTseq.csv'
# is_filter=True 时会跳过 filtered_sample_qc_type 中定义的 QC 类型。
is_filter = False
filtered_sample_qc_type = {'N','P'}

sample_type_list = []
volume_dict = {key:5 for key in sample_type_list}
default_volume = 35

class Sample:
	def __init__(self, sample_id, position, sample_type, sample_qc_type, barcode, target_position):
		sample_type_list = "".split("，")
		volume_dict = {key:5 for key in sample_type_list}
		default_volume = 35
		self.sample_id = sample_id
		self.position = position
		self.target_position = target_position
		self.sample_type = sample_type
		self.sample_qc_type = sample_qc_type
		self.barcode = barcode
		# 行列号均为 1-based，直接对应自动化平台参数。
		self.row = ord(position[0].upper()) - ord('A') + 1
		self.column = int(position[1:])
		self.target_row = ord(self.target_position[0].upper()) - ord('A') + 1
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
		# 机器端运行时以二进制读取，再逐行按 UTF-8 解码，兼容 Windows 路径下的 CSV。
		with open(sample_info_file_path, 'rb') as file:
			lines = file.readlines()
	except IOError as e:

		return samples
	except Exception as e:

		return samples

	# 跳过表头；样本在自动化流程内按 A1-H1、A2-H2 的顺序重排到连续孔位。
	for line in lines[1:]:
		line = line.strip()

		if not line:
			continue

		decoded_str = line.decode('utf-8')
		columns = decoded_str.split(',')

		# 需要 sample_id、目标孔位、QC 类型、barcode、样本类型等列。
		if len(columns) < 7:

			continue

		# 可选过滤：过滤掉 N/P 等 QC 样本。
		sample_qc_type = columns[3].strip()
		if is_filter and sample_qc_type in filtered_sample_qc_type:
			continue

		position = u"{}{}".format(chr(ord('A') + cur_index % 8), cur_index // 8 + 1)
		target_position = columns[1]

		sample_id = columns[0].strip()
		sample_type = columns[6].strip()
		barcode = columns[5].strip()

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
'''=====================================以上为样本信息读取=============================================================='''
# 样本读取结束后，后续流程统一使用 sample_num / col_num / target_tip_num_list 作为通量控制参数。


def blockB():
	pcr_run_method({"Methods": ["PTseq_START"]})
	pcr_run_method({"Methods": ["25-4"]})
b = parallel_block(blockB)
'''===================================================cDNA合成==============================================================='''
# 计算样本占用列数。未满 8 个样本的最后一列只加载实际需要的枪头。
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

# POS11 固定放置矿物油/废液深孔板。
for i in range(min(8, SampleCount)):
	p1_aspirate({"Position":"M2_POS24","Col":3,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.8,"AspirateSpeed":30,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 3, "TipTouchSpeed": 100})
	p1_dispense({"Position":"M2_POS11","Col":8,"Row":i+1,"DispenseOffsetOfZ":8,"DispenseSpeed":20,"DispenseVolume":target_volume_list[i],"DelayAfterDispense":0.5,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":0,"IsEmpty":True,"EmptyOffsetOfZ":2,"EmptySpeed":30,"DelayAfterEmpty":0.5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# ===== 步骤：向 POS20 PCR 板分装 T1 cDNA 引物 =====
col_num = (sample_num+7)//8  # 样本占用的 PCR 板列数，每 8 个样本为 1 列

transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})  # 打开 POS17 试剂盖。

# RT 第一步转移 2 uL T1 引物，使用 P1 逐样本加入 POS20；每最多 3 列更换一次 50 uL 枪头。
for col_group_start in range(0, col_num, 3):
	p1_load_modified(tip_50.load(1)[0])
	for i in range(col_group_start, min(col_group_start + 3, col_num)):
		last_row = 8 if (i < col_num - 1 or sample_num % 8 == 0) else sample_num % 8
		for j in range(last_row):
			p1_aspirate_modified("M2_POS17", 1, 1, 2, AspirateSpeed=10)
			p1_empty_modified("M2_POS20", j+1, i+1, EmptyOffsetOfZ=0.5)
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})  # 关闭 POS17 试剂盖。

# 从 POS8 提取产物板转移 14 uL 样本到 POS20 Col1-6，并与 T1 在孔内混匀。
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

# RT 和 cDNA 共用同一孔内的矿物油保护。
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

# 合上 POS20 PCR 盖板后启动 RT 程序。
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})


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
 report({"Phase": "cDNA synthesis", "Step": "cDNA first-strand synthesis reaction system", "TaskType": "library", "RemainingTime": None})

# 配置一链反应试剂
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
low_throughput_p1_direct_col9 = use_low_throughput_p1_direct(SampleCount)
report_low_throughput_branch("第9列cDNA反应液", "Col9 cDNA mix", low_throughput_p1_direct_col9, SampleCount)
# 低通量分支直接从 POS17 混合管分装到反应孔，只计算 POS17 混合管死体积。
# 高通量分支使用 POS7 Col9 中转，并采用逐孔 10-30 uL 封顶死体积算法。
if low_throughput_p1_direct_col9:
	pos7_col9_volumes = [0] * 8
	mix_total_col9 = 4 * SampleCount + MIX_TUBE_DEAD_VOLUME
else:
	pos7_col9_volumes = [pos7_reaction_mix_dispense_volume(4, SampleCount, r) for r in range(8)]
	mix_total_col9 = sum(pos7_col9_volumes) + MIX_TUBE_DEAD_VOLUME  # POS17 2 mL 混合管保留 15 uL 死体积。
t23_vol = mix_total_col9 / 2  # T2 缓冲液和 T3 酶按 1:1 配制，各占总量一半。
# 将 T2 一链合成缓冲液加入 POS17 Col4 Row1 混合管。
p1_load_modified(tip_300.load(1)[0])
p1_aspirate({"Position":"M2_POS17","Col":2,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":t23_vol,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_empty({"Position":"M2_POS17","Col":4,"Row":1,"EmptyOffsetOfZ":0.1*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
# 将 T3 一链合成酶加入同一混合管，并完成 cDNA 一链反应液混匀。
p1_load_modified(tip_300.load(1)[0])
p1_aspirate({"Position":"M2_POS17","Col":3,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":t23_vol,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_empty({"Position":"M2_POS17","Col":4,"Row":1,"EmptyOffsetOfZ":0.2*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":"M2_POS17","Col":4,"Row":1,"PreAirVolume":8,"MixTimes":10,"MixAspirateSpeed":3*SampleCount,"MixAspirateOffsetOfZ":0.6,"MixVolume":4.9*SampleCount,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":2.5*SampleCount,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.5+0.3*SampleCount,"MixEmptySpeed":5,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":"M2_POS17","Col":4,"Row":1,"PreAirVolume":8,"MixTimes":10,"MixAspirateSpeed":3*SampleCount,"MixAspirateOffsetOfZ":0.6,"MixVolume":4.9*SampleCount,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":2.5*SampleCount,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.5+0.3*SampleCount,"MixEmptySpeed":5,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":"M2_POS17","Col":4,"Row":1,"PreAirVolume":8,"MixTimes":10,"MixAspirateSpeed":3*SampleCount,"MixAspirateOffsetOfZ":0.6,"MixVolume":4.9*SampleCount,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":2.5*SampleCount,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.5+0.3*SampleCount,"MixEmptySpeed":5,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_empty({"Position":"M2_POS17","Col":4,"Row":1,"EmptyOffsetOfZ":0.2*SampleCount,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

if not low_throughput_p1_direct_col9:
	# POS7 Col9 每行预分装体积来自上方逐孔封顶死体积算法。
	target_volume_list = pos7_col9_volumes

	# 将 cDNA 一链反应液预分装到 POS7 Col9 中转深孔板；POS7 无盖板，不需要开关盖动作。
	# 同一支 P1 枪头完成 8 行预分装；来源和目标均为干净试剂/空孔。
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

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})  # 关闭 POS17 试剂盖。
# POS7 无盖板，因此这里不需要任何开关盖动作。
spx_p0_v_0.Wait()

# RT 完成后打开 POS20，把 cDNA 一链反应液加入 RT 产物。
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})
# POS7 无盖板，不执行盖板转移动作。



# 低通量直接从 POS17 混合管加样；高通量从 POS7 Col9 中转加样。
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
	# POS7 反应 mix 中转吸液高度为 0.5 mm，用于降低低液位/死体积风险。
	for i in range(col_num):
		p8_load_modified(tip_50.load(target_tip_num_list[i])[0])
		if SampleCount <= 20:
			p8_aspirate({"Position":"M2_POS7","Col":9,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":15,"AspirateVolume":4,"PreAirSpeed":30,"DelayAfterAspirate":5,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		else:
			p8_aspirate({"Position":"M2_POS7","Col":9,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":15,"AspirateVolume":4,"PreAirSpeed":30,"DelayAfterAspirate":5,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS20","Col":i+1,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":30,"DelayAfterEmpty":2,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_mix({"Position":"M2_POS20","Col":i+1,"Row":1,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":0.5,"MixVolume":16,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 矿物油在 PTseq_RT 前加到 POS20 Col1-6，cDNA 复用同孔矿物油。

# 合上 POS20 PCR 盖板后启动 PTseq_cDNA。
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})



pcr_close_door()
def spx_p2_f_0():
	pcr_run_method({"Methods":["PTseq_cDNA"]})
spx_p2_v_0 = parallel_block(spx_p2_f_0)

# PTseq_cDNA 后等待 30 min 再配置 TA Master Mix，避免 T4/T5/T2 混合液提前放置太久。
delay({"Duration": 1800})

# POS7 无盖板，不执行盖板转移动作。

'''===================================================靶向扩增反应试剂==============================================================='''
lang=get_lang()
if lang==1: #
 report({"Phase": "cDNA合成", "Step": "靶向扩增反应体系", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "cDNA synthesis", "Step": "Targeted amplification reaction system", "TaskType": "library", "RemainingTime": None})


# 配置靶向扩增反应试剂
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
c = 1.4  # T2 缓冲液预分装到 POS7 Col7 的安全系数；该位置不使用 10-30 uL 逐孔封顶死体积算法。
low_throughput_p1_direct_col10 = use_low_throughput_p1_direct(SampleCount)
report_low_throughput_branch("第10列靶向扩增反应液", "Col10 targeted amplification mix", low_throughput_p1_direct_col10, SampleCount)
# 低通量分支直接从 POS17 混合管分装到反应孔，只计算 POS17 混合管死体积。
# 高通量分支使用 POS7 Col10 中转，并采用逐孔 10-30 uL 封顶死体积算法。
if low_throughput_p1_direct_col10:
	pos7_col10_volumes = [0] * 8
	mix_total_col10 = 15 * SampleCount + MIX_TUBE_DEAD_VOLUME
else:
	pos7_col10_volumes = [pos7_reaction_mix_dispense_volume(15, SampleCount, r) for r in range(8)]
	mix_total_col10 = sum(pos7_col10_volumes) + MIX_TUBE_DEAD_VOLUME  # POS17 2 mL 混合管保留 15 uL 死体积。
ta_t2_vol = mix_total_col10 * 7 / 15
ta_t4_vol = mix_total_col10 * 5 / 15
ta_t5_vol = mix_total_col10 * 3 / 15

# 将 T2 溶解液加入 POS17 Col4 Row2 TA 混合管；总量按两次等体积分段转移。
p1_load_modified(tip_1000.load(1)[0])
p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":10,"AspirateOffsetOfZ":0.8,"AspirateSpeed":10,"AspirateVolume":ta_t2_vol/2,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_empty({"Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.1*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":10,"AspirateOffsetOfZ":0.8,"AspirateSpeed":10,"AspirateVolume":ta_t2_vol/2,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_empty({"Position":"M2_POS17","Col":4,"Row":2,"EmptyOffsetOfZ":0.1*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# 将 T4 靶向扩增缓冲液加入 TA 混合管；超过 300 uL 枪头保守上限时分两次转移。
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
	# 高通量时 T4 总体积较大，P1 分两次等体积分段吸取，避免 300 uL 枪头过满。
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
	# POS7 Col10 每行预分装体积来自上方逐孔封顶死体积算法。
	target_volume_list = pos7_col10_volumes
	# 8 行预分装共用 1 支 P1 枪头。
	# 使用 300 uL 枪头：该混合管最大需求体积超过 50 uL 枪头范围。
	p1_load_modified(tip_300.load(1)[0])
	for i in range(8):
		p1_aspirate({"Position":"M2_POS17","Col":4,"Row":2,"PreAirVolume":8,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p1_empty({"Position":"M2_POS7","Col":10,"Row":i+1,"EmptyOffsetOfZ":0.5,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 8 行全部分装完成后再丢弃枪头。
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})

# =============================================
# 向 POS7 Col7 预分装 T2 缓冲液。
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

# cDNA 程序完成后打开 POS20，向 Col7-12 配置 TA 反应体系。
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
		p1_aspirate_modified("M2_POS20", row, col_index+1, 5, PreAirVolume=5, AspirateSpeed=10, AspirateOffsetOfZ=0.7, DelayAfterAspirate=1, PostAirVolume=0, IfTrack=False)
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
		p8_aspirate({"Position":"M2_POS20","Col":i+1,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.7,"AspirateSpeed":10,"AspirateVolume":5,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS20","Col":i+7,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_mix({"Position":"M2_POS20","Col":i+7,"Row":1,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":50,"MixAspirateOffsetOfZ":0.5,"MixVolume":22,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":50,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":3,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

	# TA PCR 前向 POS20 Col7-12 加矿物油；这里是新反应孔。
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

# 合上 POS20 PCR 盖板并启动 PTseq_TA。
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})
# 高通量 TA 分支在前面统一打开 POS10 盖板；低通量分支每个样本吸完 primer 后已经关闭 POS10。
if not low_throughput_p1_direct_col10:
	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS10","LoosenOffsetOfZ":0})

'''================================================== 二链反应==============================================================='''

pcr_close_door()
def spx_p2_f_1():
	pcr_run_method({"Methods":["PTseq_TA"]})

spx_p2_v_1 = parallel_block(spx_p2_f_1)

# PTseq_TA 运行期间延后准备 TA 纯化试剂，避免磁珠和乙醇过早暴露。
delay({"Duration": 5400})

#####################################################T1 磁珠分装##############################################
# TA 产物磁珠纯化。

p1_load_modified(tip_1000.load(1)[0])
# 混匀 T1 磁珠后预分装到 POS7 Col12。
p1_mix({"Position":"M2_POS24", "Col": 1, "Row": 1,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":0.8,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":2,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":"M2_POS24", "Col": 1, "Row": 1,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":1,"MixVolume":900,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":30,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":15,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})

# 计算磁珠分装体积：第一轮 TA 纯化每个样本使用 50 uL 磁珠，对 25 uL TA 产物为 2:1 比例，并使用 1.4 倍安全系数。
target_volume_list = [50*1.4*(SampleCount//8+1)]*(SampleCount%8)+[50*1.4*(SampleCount//8)]*(8-SampleCount%8)
for i in range(8):
	p1_aspirate({"Position":"M2_POS24", "Col": 1, "Row": 1,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":50,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 50, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS7","Col":12,"Row":i+1,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":1,"TipTouchOffsetOfZ":5,"TipTouchRangeOfX":2,"TipTouchSpeed":50,"PostAirSpeed":100,"PostAirVolume":5,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	if i == 3:
		p1_mix({"Position":"M2_POS24", "Col": 1, "Row": 1,"PreAirVolume":10,"MixTimes":10,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":0.8,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":2,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
		p1_mix({"Position":"M2_POS24", "Col": 1, "Row": 1,"PreAirVolume":10,"MixTimes":10,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":1,"MixVolume":900,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":30,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":15,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})


# 从 POS7 Col12 将 T1 磁珠分装到 POS16 Col7-12，作为 TA 纯化结合孔。
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

# TA PCR 结束后，POS20 Col7-12 的 TA 产物与 POS16 Col7-12 的磁珠结合。
lang=get_lang()
if lang==1: #
 report({"Phase": "靶向扩增反应后纯化", "Step": "样本与磁珠结合", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Targeted amplification purification", "Step": "Sample binding to magnetic beads", "TaskType": "library", "RemainingTime": None})

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
	# POS3 → POS7 乙醇预分装：5 次循环 ×195 uL = 975 uL/孔，分层高度 0.5 + 4*tt。
	# 该动作与 POS23 磁吸等待并行执行，确保 TA 弃上清后可以立即加乙醇，降低磁珠过早干燥风险。
	Alcohol_1 = tip_1000.load(8,8)
	p8_load_modified(Alcohol_1[0])
	for x in range(col_num):
		for tt in range(5):
			p8_aspirate({"Position":"M2_POS3","Col":1,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":1.0,"AspirateSpeed":80,"AspirateVolume":195,"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":0})
			p8_empty({"Position":"M2_POS7","Col":1+x,"Row":1,"EmptyOffsetOfZ":0.5+4*tt,"EmptySpeed":50,"DelayAfterEmpty":0.8,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})


# TA 结合完成后，把 POS16 纯化板转移到 POS23 磁力架磁吸。
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})
TA_ethanol_predispense_wait = parallel_block(predispense_TA_ethanol_to_POS7)
delay({"Duration": 180})
TA_ethanol_predispense_wait.Wait()

# POS11 deepwell 1.3 mL 板 Col1-6 作为 TA/LA 废液回收列，与样本列 1:1 映射。
# 单孔累计废液约 1020 uL，低于 1.3 mL 深孔容量。
waste_col_start = 1

Ligation_purification_tips2 = tip_300.load(sample_num,8,0)  # reuse_index=0：TA 乙醇洗涤/弃液枪头用完直接丢弃。
# T2 在磁吸前加入，用于提供 DNA 结合 SPRI 磁珠所需的 PEG/盐环境。

# TA 纯化乙醇清洗。
lang=get_lang()
if lang==1: #
 report({"Phase": "靶向扩增反应后纯化", "Step": "乙醇清洗", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Targeted amplification purification", "Step": "Ethanol wash", "TaskType": "library", "RemainingTime": None})

# 移除上清：结合体系约 100 uL（50 uL 磁珠 + 25 uL TA + 25 uL T2），吸走 110 uL 用于“弃多于打”的余量策略。
# 废液按样本列 1:1 回收到 POS11 Col1-6。
for i in range(col_num):
	p8_load_modified_BubblePurge(TA_purification_tips[i])
	p8_aspirate({"Position":"M2_POS23","Col":7+i,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":30,"AspirateVolume":110,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	# 将废液打入 POS11 废液板，列映射与样本列保持 1:1。
	p8_empty({"Position":"M2_POS11","Col":waste_col_start+i,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"TipTouchOffsetOfZ":15,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 乙醇洗涤继续使用前面分配好的 Ligation_purification_tips2。

# TA 乙醇洗涤流程：加乙醇后不移板、不吹打，磁吸沉降 120 s 后弃乙醇。
for i in range(2):
	# 第一步：加乙醇，板保持在 POS23 磁力架位。
	for x in range(col_num):
		p8_load_modified_BubblePurge(Ligation_purification_tips2[x])
		p8_aspirate({"Position":"M2_POS7","Col":1+x,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":1.0,"AspirateSpeed":50,"AspirateVolume":200,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS23","Col":7+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":2,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.4, "TipTouchSpeed": 100})
		p8_unload_modified(Ligation_purification_tips2[x])

	# 第二步：静置磁吸沉降，板始终保持在 POS23 磁力架位。
	delay({"Duration": 120})

	# 第三步：弃乙醇，板仍在 POS23；吸液体积 220 uL，用 +20 uL 余量减少残液。
	for x in range(col_num):
		p8_load_modified_BubblePurge(Ligation_purification_tips2[x])
		p8_aspirate({"Position":"M2_POS23","Col":7+x,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0,"AspirateSpeed":10,"AspirateVolume":220,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS11","Col":waste_col_start+x,"Row":1,"EmptyOffsetOfZ":10,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"TipTouchOffsetOfZ":15,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty_waste_high("M2_POS11", waste_col_start+x)
		# 只在最后一轮丢弃枪头，第一轮放回原位
		if i == 1:
			p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
		else:
			p8_unload_modified(Ligation_purification_tips2[x])

def wait_for_magnetic_beads():
	# TA 纯化晾干延时 5 min。
	delay({"Duration": 300})

magetic_wait = parallel_block(wait_for_magnetic_beads)

lang=get_lang()
if lang==1: #
 report({"Phase": "文库扩增准备", "Step": "配置文库扩增反应液", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Library amplification preparation", "Step": "Preparing library amplification reaction mixture", "TaskType": "library", "RemainingTime": None})

'''===================================================文库扩增反应液==============================================================='''
# LA/PCR Master Mix 配置。
# T8 UDG 体积：小体积酶液按分段系数补偿 300 uL 枪头低体积死体积。
# 样本数 <16：系数 1.6 且最低 7 uL；样本数 >=16：系数 1.3。
def _t8_vol(n):
	return max(1 * 1.6 * n, 7) if n < 16 else 1 * 1.3 * n

low_throughput_p1_direct_col11 = use_low_throughput_p1_direct(SampleCount)
report_low_throughput_branch("第11列文库扩增PCR反应液", "Col11 library amplification PCR mix", low_throughput_p1_direct_col11, SampleCount)
# 低通量分支直接从 POS17 混合管分装到反应孔，只计算 POS17 混合管死体积。
# 高通量分支使用 POS7 Col11 中转，并采用逐孔 10-30 uL 封顶死体积算法。
if low_throughput_p1_direct_col11:
	pos7_col11_volumes = [0] * 8
	mix_total_col11 = 30 * SampleCount + MIX_TUBE_DEAD_VOLUME
else:
	pos7_col11_volumes = [pos7_reaction_mix_dispense_volume(30, SampleCount, r) for r in range(8)]
	mix_total_col11 = sum(pos7_col11_volumes) + MIX_TUBE_DEAD_VOLUME  # POS17 2 mL 混合管保留 15 uL 死体积。
la_t7_vol = mix_total_col11 * 20 / 30
la_t8_vol = max(_t8_vol(SampleCount), mix_total_col11 * 1 / 30)  # _t8_vol acts as min-floor for T8
la_t2_vol = mix_total_col11 * 9 / 30

transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
if SampleCount > 20:
	p1_load_modified(tip_1000.load(1)[0])
	# 吸取 T7 PCR mix：降低第一段进液速度，减少枪头进入液面时扰动。
	p1_aspirate({"Position":"M2_POS17","Col":1,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t7_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	delay({"Duration": 10})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":10,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	p1_load_modified(tip_1000.load(1)[0])
	p1_aspirate({"Position":"M2_POS17","Col":1,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t7_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	# 吸取 T8 UDG 酶：每孔 1 uL，用于 30 uL LA Master Mix；这是第二次吸液，使用正常速度。
	p1_load_modified(tip_300.load(1)[0])
	p1_aspirate({"Position":"M2_POS17","Col":2,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t8_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	p1_load_modified(tip_300.load(1)[0])
	p1_aspirate({"Position":"M2_POS17","Col":2,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t8_vol/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

	# 吸取 T2 溶解液：每孔 9 uL，用于 30 uL LA Master Mix。
	# POS24 Row2 存放 T2 缓冲液；Row1 保留给磁珠，不能混用。
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
	# 吸取 T7 PCR mix：每孔 20 uL，并降低第一段进液速度。
	p1_aspirate({"Position":"M2_POS17","Col":1,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t7_vol,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	delay({"Duration": 10})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	# 吸取 T8 UDG 酶：每孔 1 uL，用于 30 uL LA Master Mix。
	p1_load_modified(tip_300.load(1)[0])
	p1_aspirate({"Position":"M2_POS17","Col":2,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":la_t8_vol,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
	# 吸取 T2 溶解液：每孔 9 uL，用于 30 uL LA Master Mix。
	# POS24 Row2 存放 T2 缓冲液；Row1 保留给磁珠，不能混用。
	p1_load_modified(tip_1000.load(1)[0])
	p1_aspirate({"Position":"M2_POS24","Col":1,"Row":2,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":150,"AspirateVolume":la_t2_vol,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
# POS17 盖处于打开状态，无需关盖再开盖。
# 混匀 LA/PCR Master Mix。
if SampleCount <=20:
	if SampleCount <=5:
		p1_load_modified(tip_300.load(1)[0])
	else:
		p1_load_modified(tip_1000.load(1)[0])
	p1_mix({"Position":"M2_POS17", "Col": 4, "Row": 3,"PreAirVolume":80,"MixTimes":10,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":30*SampleCount,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_mix({"Position":"M2_POS17", "Col": 4, "Row": 3,"PreAirVolume":80,"MixTimes":10,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":30*SampleCount,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_mix({"Position":"M2_POS17", "Col": 4, "Row": 3,"PreAirVolume":80,"MixTimes":10,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":30*SampleCount,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":15,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":3, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
else:
	p1_load_modified(tip_1000.load(1)[0])
	# 样本数 >20 时使用 900 uL 混匀体积，覆盖更大的 LA/PCR Master Mix 总量。
	p1_mix({"Position":"M2_POS17", "Col": 4, "Row": 3,"PreAirVolume":80,"MixTimes":15,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":900,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_mix({"Position":"M2_POS17", "Col": 4, "Row": 3,"PreAirVolume":80,"MixTimes":15,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":900,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_mix({"Position":"M2_POS17", "Col": 4, "Row": 3,"PreAirVolume":80,"MixTimes":15,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":900,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":15,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":3, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})

'''===================================================靶向扩增反应纯化PCR反应液回溶==============================================================='''

# ============ POS20/POS9 PCR 板交换 ============
# TA 结束后，POS9 的新 PCR 板换到 POS20，用于 LA 和最终文库保存。
# 新 PCR 板用于 LA 反应 Col1-6 和最终文库保存 Col7-12。
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})
transfer({"StartPosition":"M2_POS20","EndPosition":transposition,"LoosenOffsetOfZ":0})
transfer({"StartPosition":"M2_POS9","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})
transfer({"StartPosition":transposition,"EndPosition":"M2_POS9","LoosenOffsetOfZ":0})
# ============ PCR 板交换完成 ============

lang=get_lang()
if lang==1: #
 report({"Phase": "PCR前准备", "Step": "添加PCR反应液", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Pre-PCR", "Step": "Adding PCR mix", "TaskType": "library", "RemainingTime": None})

# 计算 LA Master Mix 预分装体积：每个样本最终加入 30 uL。
# 分段策略：样本数 <=15 用基数 35（每孔死体积约 5 uL）；样本数 >=16 用基数 33（所有孔至少被吸 2 次，约 6 uL 死体积已足够）。
if not low_throughput_p1_direct_col11:
	# POS7 Col11 每行预分装体积来自上方逐孔封顶死体积算法。
	target_volume_list_pre_PCR = pos7_col11_volumes
	transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})


	p1_load_modified(tip_1000.load(1)[0])
	for i in range(8):
		# LA/PCR Master Mix 在 POS17 Col4 Row3 混匀后直接预分装到 POS7 Col11。
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
		p8_aspirate({"Position":"M2_POS7","Col":11,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":30,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		# 打入 POS23 磁架上的干燥磁珠产物孔。
		p8_empty({"Position":"M2_POS23","Col":7+i,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_unload_modified(LA_dispense_tips[i])

# 第二步：把 POS23 磁架上的板转到 POS16 振荡位进行回溶。
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})
# 用交替双向振荡回溶干燥磁珠产物；总时长 6 min。
temp_shaker_set({"TempParameters":{"IsEnable":False,"Duration":-1},"ShakerParameters":{"IsEnable":True,"Direction":0,"Speed":1200,"Duration":90}})
temp_shaker_set({"TempParameters":{"IsEnable":False,"Duration":-1},"ShakerParameters":{"IsEnable":True,"Direction":1,"Speed":1200,"Duration":90}})
temp_shaker_set({"TempParameters":{"IsEnable":False,"Duration":-1},"ShakerParameters":{"IsEnable":True,"Direction":0,"Speed":1200,"Duration":90}})
temp_shaker_set({"TempParameters":{"IsEnable":False,"Duration":-1},"ShakerParameters":{"IsEnable":True,"Direction":1,"Speed":1200,"Duration":90}})

# 第三步：把 POS16 Col7-12 的 30 uL 磁珠悬液转移到新 PCR 板 POS20 Col1-6。
# 高通量分支使用 LA_dispense_tips；低通量直接分装分支使用新的 300 uL P8 枪头。
# 这一步是 LA_dispense_tips 的最后一次使用，转移完成后直接丢弃到垃圾桶，不再放回枪头盒。
def reshake_la_slurry_on_pos16():
	# 每转移一列后短暂双向震荡 POS16，减少剩余磁珠悬液再次沉降。
	temp_shaker_set({"TempParameters":{"IsEnable":False,"Duration":-1},"ShakerParameters":{"IsEnable":True,"Direction":0,"Speed":1200,"Duration":30}})
	temp_shaker_set({"TempParameters":{"IsEnable":False,"Duration":-1},"ShakerParameters":{"IsEnable":True,"Direction":1,"Speed":1200,"Duration":30}})

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
	reshake_la_slurry_on_pos16()

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

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS10","LoosenOffsetOfZ":0})  # 关闭 POS10 盖板。

# PTseq_LA 前向新 PCR 板 POS20 Col1-6 加 20 uL 矿物油，防止 LA PCR 蒸发。
if SampleCount%8 == 0:
	last_row =1
else:
	last_row = 9-SampleCount%8
oil_3 = tip_300.load(8,8,0)  # reuse_index=0：LA 矿物油枪头用完直接丢弃，不跨 PCR 阶段复用。

p8_load_tips({"Position":oil_3[0][0],"Col":oil_3[0][1],"Row":last_row,"Tips":8})
for i in range(col_num-1,-1,-1):
	p8_aspirate({"Position":"M2_POS11","Col":8,"Row":1,"PreAirVolume":20,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":20,"PreAirSpeed":50,"DelayAfterAspirate":1,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 1.5, "TipTouchSpeed": 100})
	# LA PCR 矿物油加到新板 Col1-6。
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

'''===================================================文库扩增反应后纯化准备==============================================================='''
# PTseq_LA 运行期间延后准备 LA 纯化磁珠，避免磁珠长时间暴露。
lang=get_lang()
if lang==1: #
 report({"Phase": "文库扩增", "Step": "文库扩增后纯化准备", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Library amplification", "Step": "Preparation for library amplification purification", "TaskType": "library", "RemainingTime": None})


delay({"Duration": 1800})

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

# 废液统一回收到 POS11 深孔板 Col1-6。
# waste_col_start 用于 TA 和 LA 两轮纯化的废液列映射。

# 乙醇位置：POS7 Col1-6 为 80% 乙醇中转孔，支持多轮洗涤。
ethanol_pos = {"Position":"M2_POS7","Col":1,"Row":1}

# 最终文库产物回收到 POS20 Col7-12。
# 产物定量后 POS20 密封并由 PCR 模块 4keep 保存。
product_pos = {"Position":"M2_POS20","Col":7,"Row":1}



p1_load_modified(tip_1000.load(1)[0])
# 分装 LA 磁珠前充分混匀源磁珠。
p1_mix({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":0.8,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":2,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":10,"MixTimes":30,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":30,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":15,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})


for i in range(8):
	p1_aspirate({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":50,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 50, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p1_empty({"Position":magetic_beads_pre_dispense_pos["Position"], "Col":magetic_beads_pre_dispense_pos["Col"], "Row":magetic_beads_pre_dispense_pos["Row"]+i,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":2,"PostAirSpeed":50,"PostAirVolume":25,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	if i == 3:
		p1_mix({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":10,"MixTimes":12,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":0.8,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":2,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
		p1_mix({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":10,"MixTimes":12,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":30,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":15,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
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
	# LA 产物磁珠转移体积为 32 uL；低速吸液和 10 uL 后吸用于减少枪头中段气泡。
	p8_aspirate({"Position":magetic_beads_pre_dispense_pos["Position"], "Col":magetic_beads_pre_dispense_pos["Col"], "Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.9,"AspirateSpeed":30,"AspirateVolume":magetic_beads_volume1,"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX":1.2, "TipTouchSpeed": 100})
	p8_dispense({"Position":magetic_beads_dispense_pos1["Position"], "Col":magetic_beads_dispense_pos1["Col"]+i, "Row":1,"FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "DispenseOffsetOfZ": 0.8, "DispenseSpeed": 30, "DispenseVolume":magetic_beads_volume1,"DelayAfterDispense": 1, "IsEmpty": True, "EmptyOffsetOfZ": 0.8, "EmptySpeed": 50, "DelayAfterEmpty": 0.5, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})

	if i == col_num-1 and target_tip_num_list[i] != 8:
		p8_unload_modified((temp[0],temp[1],temp[2]+8-sample_num%8))
		p8_load_modified(temp)
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

Pre_PCR_wait.Wait()
pcr_open_door()
# PTseq_LA 结束后，将 POS20 Col1-6 的 LA PCR 产物加入 POS16 Col1-6 的磁珠孔。
lang=get_lang()
if lang==1: #
 report({"Phase": "文库扩增反应", "Step": "文库扩增反应后纯化", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Library amplification", "Step": "Library amplification purification", "TaskType": "library", "RemainingTime": None})
 
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})

temp = tip_300.load(sample_num,8,1)
for i in range(col_num):
	p8_load_modified(temp[i])
	# 从 POS20 Col1-6 转移 40 uL LA PCR 产物。
	p8_aspirate({"Position":"M2_POS20","Col":1+i,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":30,"AspirateVolume":40,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":magetic_beads_dispense_pos1["Position"], "Col":magetic_beads_dispense_pos1["Col"]+i, "Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ":15, "TipTouchRangeOfX": 1.3, "TipTouchSpeed": 100})
	p8_unload_modified(temp[i])


temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1000, "Duration": 60}})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 0, "Speed": 1000, "Duration": 60}})


delay({"Duration": 300})


transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})  # 关闭 POS20 PCR 盖板。
pcr_close_door()

# LA 结合完成后，把 POS16 纯化板转移到 POS23 磁力架磁吸。
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})
delay({"Duration": 120})

# LA 纯化板位追踪：LA 使用 dispense_pos1，不使用 TA 的 dispense_pos2。
if magetic_beads_dispense_pos1["Position"] == "M2_POS16":
	magetic_beads_dispense_pos1["Position"] = "M2_POS23"

# 逐列去除废液到 POS11 废液板
for i in range(col_num):
	p8_load_modified_BubblePurge(temp[i])
	# 移除 85 uL 废液上清；对应 40 uL LA 产物 + 32 uL 磁珠体系。
	# 吸液高度为 0.5 mm，与 TA 弃上清一致，避免贴底吸入磁珠。
	p8_aspirate({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+i,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":85,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS11","Col":waste_col_start+i,"Row":1,"EmptyOffsetOfZ":10,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"TipTouchOffsetOfZ":15,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_modified(temp[i])  # 将弃上清枪头放回原位，后续同列乙醇洗涤继续使用。

# LA 纯化乙醇清洗。
lang=get_lang()
if lang==1: #
 report({"Phase": "PCR前准备", "Step": "乙醇清洗", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Pre-PCR", "Step": "Ethanol wash", "TaskType": "library", "RemainingTime": None})

# LA 乙醇洗涤继续使用同列弃上清枪头。

# LA 乙醇洗涤流程：加乙醇后不移板、不吹打，磁吸沉降 120 s 后弃乙醇。
for i in range(2):
	# 第一步：加乙醇，板保持在 POS23 磁力架位。
	for x in range(col_num):
		p8_load_modified_BubblePurge(temp[x])
		p8_aspirate({"Position":ethanol_pos["Position"], "Col":ethanol_pos["Col"]+x, "Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":1.0,"AspirateSpeed":50,"AspirateVolume":200,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x, "Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
		p8_unload_modified(temp[x])

	# 第二步：静置磁吸沉降，板始终保持在 POS23 磁力架位。
	delay({"Duration": 120})

	# 第三步：弃乙醇，板仍在 POS23；吸液体积 220 uL，用 +20 uL 余量减少残液。
	for x in range(col_num):
		p8_load_modified_BubblePurge(temp[x])
		p8_aspirate({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x, "Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0,"AspirateSpeed":10,"AspirateVolume":220,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M2_POS11","Col":waste_col_start+x,"Row":1,"EmptyOffsetOfZ":10,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"TipTouchOffsetOfZ":15,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty_waste_high("M2_POS11", waste_col_start+x)
		# 只在最后一轮丢弃枪头，第一轮放回原位
		if i == 1:
			p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
		else:
			p8_unload_modified(temp[x])

# LA 纯化晾干延时 5 min，从最后一次乙醇弃液完成后起计时。
def wait_for_LA_beads_dry():
	delay({"Duration": 300})

LA_dry_wait = parallel_block(wait_for_LA_beads_dry)

LA_dry_wait.Wait()
# LA 纯化回溶：23 uL T2 洗脱液回溶；使用 50 uL 枪头以减少 300 uL 枪头消耗。

Product = tip_50.load(SampleCount,8,1)


for x in range(col_num):
	p8_load_modified(Product[x])
	# 从 POS7 预分装的 T2 洗脱液中吸取 23 uL，打入 POS23 磁珠孔。
	p8_aspirate({"Position":elution_buffer_pre_dispense_pos["Position"],"Col":elution_buffer_pre_dispense_pos["Col"],"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":23,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_mix({"Position":"M2_POS23","Col":magetic_beads_dispense_pos1["Col"]+x,"Row":1,"PreAirVolume":5,"MixTimes":6,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":18,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":40,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":8,"MixEmptySpeed":30,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_modified(Product[x])

# 纯化板从磁力架转到 POS16 振荡位，使干燥磁珠充分回溶。
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1200, "Duration": 150}})

temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 0, "Speed": 1200, "Duration": 150}})
delay({"Duration": 300})

# 回溶后转回 POS23 磁吸，准备回收最终文库产物。
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})
delay({"Duration": 300})

# 回收建库产物到 POS20 Col7-12，产物保存在该 PCR 板中。
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})  # 开PCR盖板

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

'''=====================================定量=============================================================='''

#======================物料设置=============================================================
lang=get_lang()
if lang==1: #
 report({"Phase": "定量", "Step": "定量", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Quantification", "Step": "Quantification", "TaskType": "library", "RemainingTime": None})

sample_num = SampleCount

# 定量模块按 PCR 产品类型输出浓度。
sample_stage = 'PCR'

# Qubit 染液来源位置。
dye_loc = ('M2_POS4',1,1)

# 染液分装枪头在同一染液步骤内复用。
dye_tip = tip_300.load(8,8,1)[0]  # reuse_index=1：定量染液分装枪头在同一染液步骤内复用。

# 样本稀释枪头按样本列分配并在混合/转移阶段复用。
sample_dilute_tip_loc = tip_50.load(sample_num,8,1)

# 样本来源起始位置：从 POS20 Col7-12 取最终文库产物。
source_plate = ['M2_POS20',7]

# 样本与染液的混合起始位置：POS13 Col1-6，按样本列映射。
dye_mix_plate = ['M2_POS13',1]

# POS14/POS11 对换后，定量管 home 在 POS14；实际读数/移液时临时换到 POS13 访问。
quantification_tube_home_pos = 'M2_POS14'
quantification_tube_operating_pos = 'M2_POS13'
quantification_tube_loc = [quantification_tube_operating_pos,1]

#=====================定量浓度输出文件位置======================================
# 定量结果输出：平台原始表格和辅助 txt 均写到 D:/data。
import time
current_datetime = time.strftime("%Y%m%d_%H%M%S")
file_path = f"D:\\data\\PTseq_Library.xlsx"
quantification_fila_path = f"D:\\data\\quantification{current_datetime}.txt"




#=================================== 函数计算部分#===================================
col_num = (sample_num+7)//8
def get_concentration_modified(pos):
	# 平台接口输入顺序为板位、行、列；pos 参数在脚本内部统一保存为板位、列、行。
	try:
		spx_concentration = find_sampling_concentration(pos[0],pos[2],pos[1])
		if spx_concentration is None:
			print(f"  [WARNING] No concentration data at {pos}")
			return 0.0
		return spx_concentration.Consistence
	except Exception as e:
		print(f"  [WARNING] get_concentration error at {pos}: {e}")
		return 0.0
quantification_tubes = [(quantification_tube_loc[0],quantification_tube_loc[1]+i//8,1 + i%8) for i in range(sample_num)]

concentration_list = []


#=================================== 样本稀释部分#===================================
# 定量流程先在染液混合板中混合样本和染液，再移到 POS16 震荡，随后把定量管换到 POS13 并转移读数。

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
	p8_aspirate_modified(dye_loc[0], Row=dye_loc[2], Col=dye_loc[1], AspirateVolume=217.8, PreAirVolume=10, AspirateOffsetOfZ=1.0)
	p8_empty_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i, EmptyOffsetOfZ=3, TipTouchTimes=1)
	# 处理最后一列不足 8 个样本时的枪头放回/重取。
	if i == col_num - 1 and sample_num%8!=0:
		p8_unload_tips({"Position":dye_tip[0],"Col":dye_tip[1],"Row":last_row,"Tips":8})
		p8_load_tips({"Position":dye_tip[0],"Col":dye_tip[1],"Row":1,"Tips":8})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 第二步：向染液混合板加入样本并在孔内混匀。
for i in range(col_num):
	p8_load_modified(sample_dilute_tip_loc[i])
	p8_aspirate_modified(source_plate[0], 1, source_plate[1]+i, 2.2, AspirateSpeed=2, AspirateOffsetOfZ=2, IfTrack=True)
	p8_empty_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i, EmptyOffsetOfZ=12)
	# 在染液混合板中混匀样本和染液。
	p8_mix({"Position":dye_mix_plate[0],"Col":dye_mix_plate[1]+i,"Row":1,"PreAirVolume":10,"MixTimes":2,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":1,"MixVolume":40,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_modified(sample_dilute_tip_loc[i])

# 定量取样完成后关闭 POS20 盖板，并启动 PCR 模块 4 度过夜保存。
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})  # 关PCR盖板
pcr_close_door()

lang=get_lang()
if lang==1:
 report({"Phase": "建库产物保存", "Step": "4度保存", "TaskType": "library", "RemainingTime": None})
elif lang==2:
 report({"Phase": "Library product storage", "Step": "4C Hold", "TaskType": "library", "RemainingTime": None})

# 启动PCR 4keep保存（并行执行，不阻塞后续定量流程）
def block_pcr_4keep():
	pcr_run_method({"Methods": ["4keep"]})
keep = parallel_block(block_pcr_4keep)

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

# 按样本列依次装载定量管并运行 dsDNA HS 读数。
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
# 额外输出一个按 8 行布局排列的 txt，便于快速核对浓度矩阵。
column_size = 8
try:
	float_array = concentration_list
	with open(quantification_fila_path, "w") as file:
		num_columns = (len(float_array) + column_size - 1) // column_size

		for row in range(column_size):
			for col in range(num_columns):
				index = col * column_size + row
				if index < len(float_array):
					file.write(f"{float_array[index]:<10}")
				else:
					file.write(" " * 10)
			file.write("\n")
except:
	pass


# 等待 PCR 模块 4keep 进入保持状态后结束脚本。
keep.Wait()

# 产物保存位置：POS20 Col7-12。
# 定量结果输出路径：D:\data\PTseq_Library.xlsx
