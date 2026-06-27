# -*- coding: utf-8 -*-
# Timestamp:2024/11/18 9:46:21
# Head - 共用头部，包含所有功能。
from extraction import *
spxsiro = globals().get("extraction")
set_siro(spxsiro)
import math
"""
不要修改HEAD
"""
home()
import sys
import math

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

	




#===========================================================================优化吸液逻辑=======================================================================


def p8_aspirate_modified(Position,Row,Col,AspirateVolume,FirstSegmentSpeed=100,SpeedChangeOffsetOfZ=5,PreAirSpeed=100,SecondSegmentSpeed = 50,\
						 PreAirVolume=10,AspirateSpeed=80,DelayAfterAspirate=0.5,AspirateOffsetOfZ=0.5,\
						 TipTouchTimes=0, TipTouchOffsetOfZ=45.5, TipTouchRangeOfX=1.5,TipTouchSpeed=10.0,PostAirSpeed=50.0, PostAirVolume=0,liquid=0,IfTrack=False):
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
						 TipTouchTimes=0, TipTouchOffsetOfZ=45.5, TipTouchRangeOfX=1.5,TipTouchSpeed=10.0,PostAirSpeed=50.0, PostAirVolume=0,liquid=0,IfTrack=False):
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
TipTouchTimes= 0, TipTouchOffsetOfZ= 10, TipTouchRangeOfX= 2, TipTouchSpeed= 100,
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



'''=====================================样本信息读取====================================='''
# 该代码用于读取样本信息文件，并将每一行数据存储为一个 Sample 对象
# 该代码使用了 Python 的内置库，不需要额外安装任何库
# 质控类型为 'N' 和 'P' 的样本孔可以被过滤掉，如果过滤掉，孔位会重新计算


# ================================输入部分=============================================

# 样本信息文件位置
sample_info_file_path = r'D:/Pathogens/PTseq.csv'
# 是否有样本孔需要过滤，默认值位True，即有样本孔需要过滤，反之则设为 False
is_filter = False
# 提取过滤的样本质控类型（仅在 is_filter 为 True 时生效）
filtered_sample_qc_type = {'N','P'}

sample_type_list = "产前绒毛，流产物绒毛，胎儿组织，脐带血，外周血".split("，")
volume_dict = {key:5 for key in sample_type_list}
default_volume = 40

# ================================以下内容为读取样本信息文件=============================================
class Sample:
	def __init__(self, sample_id, position, sample_type, sample_qc_type, barcode, target_position):
		sample_type_list = "产前绒毛，流产物绒毛，胎儿组织，脐带血，外周血，全血".split("，")
		volume_dict = {key:5 for key in sample_type_list}
		default_volume = 40
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
	except:

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
transport_go({"Position": "M1_T1"})

'''============================================================枪头位置=============================================================='''

#初始化枪头位
# ==================== 物理限制修改 ====================
# 300µL tips moved to POS7 due to physical constraints
tip_300_pos = ['M1_POS7']
tip_300 = Tips(tip_300_pos)

# 1000µL tips at POS11 and POS1
tip_1000_pos = ['M1_POS11', 'M1_POS1']
tip_1000 = Tips(tip_1000_pos)
# ====================================================

transport_go({"Position": "M1_T1"})

#=========================================混匀磁珠=====================================================
lang=get_lang()
if lang==1: #
 report({"Phase": "磁珠分装", "Step": "磁珠分装", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Magnetic Bead Aliquoting", "Step": "Magnetic Bead Aliquoting", "TaskType": "library", "RemainingTime": None})
 
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1200, "Duration": 60}})

#=========================================分装磁珠=====================================================

magnet_pos_list = ['M1_POS5','M1_POS9','M1_POS13']
target_col_list = [1,7]
target_row_list = [i+1 for i in range(8)]
total_col_num,rest_8 = divmod(sample_num,8)
if rest_8!=0:
	total_col_num += 1
target_tip_num_list = [8]*(sample_num//8) + [sample_num%8]

#8样本以下时单枪分液=========================
if (sample_num) < 9:
	p8_load_modified(tip_1000.load(1)[0])
	for i in range(sample_num):
	#第五次分液前重新震荡磁珠
		if i == 4:
			temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1200, "Duration": 30}})
		target_pos_index,rest_num = divmod(i,16)
		target_col_index,target_rows_index = divmod(rest_num,8)
		#计算目标位置
		target_pos = magnet_pos_list[target_pos_index]
		target_col = target_col_list[target_col_index]
		target_row = target_row_list[target_rows_index]
		p8_aspirate({"Position":"M1_POS10","Col":1,"Row":1,"PreAirVolume":20,"AspirateOffsetOfZ":2,"AspirateSpeed":100,"AspirateVolume":20,"PreAirSpeed":10,"DelayAfterAspirate":2,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":f"{target_pos}","Col":target_col,"Row":target_row, "FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "EmptyOffsetOfZ": 5, "EmptySpeed": 80, "DelayAfterEmpty": 0.5,"TipTouchTimes": 3, "TipTouchOffsetOfZ":3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_tips({"Position":"M1_Trash","Col":1,"Row":1})
#8样本以上时先分一列再排枪加液========================
if (sample_num)  >8:
	p8_load_modified(tip_1000.load(1)[0])
	# 先将需要分的体积计算好存储到列表中
	target_volume_list = [(sample_num//8 + 1)*20*1.3]*rest_8 + [(sample_num//8)*20*1.3]*(8-rest_8)
	for i in range(8):
	#第五次分液前重新震荡磁珠
		if i == 4:
			temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1200, "Duration": 30}})
		p8_aspirate({"Position":"M1_POS10","Col":1,"Row":1,"PreAirVolume":20,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":target_volume_list[i],"PreAirSpeed":10,"DelayAfterAspirate":2,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
		p8_empty({"Position":"M1_POS2","Col":10,"Row":i+1, "FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "EmptyOffsetOfZ": 5, "EmptySpeed": 80, "DelayAfterEmpty": 0.5, "TipTouchTimes": 3, "TipTouchOffsetOfZ":3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_tips({"Position":"M1_Trash","Col":1,"Row":1})
	######按列分
	target_col_list = [1,7]
	target_tip_loc = tip_300.load(8)
	target_tip_pos,target_tip_col,target_tip_row = target_tip_loc[0]
	p8_load_tips({"Position": f"{target_tip_pos}", "Row": target_tip_row, "Col": target_tip_col})
	for i in range(total_col_num):
		target_pos_index,target_col_index = divmod(i,2)
		target_pos = magnet_pos_list[target_pos_index]
		target_col = target_col_list[target_col_index]
		target_row = 1
		p8_aspirate({"Position":"M1_POS2","Col":10,"Row":1,"PreAirVolume":20,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":20,"PreAirSpeed":10,"DelayAfterAspirate":2,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ":3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
		p8_empty({"Position":f"{target_pos}","Col":target_col,"Row":1, "FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "EmptyOffsetOfZ": 5, "EmptySpeed": 80, "DelayAfterEmpty": 0.5, "TipTouchTimes": 3, "TipTouchOffsetOfZ":3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_tips({"Position": "M1_Trash", "Col": 1, "Row": 1})


#================================添加异丙醇=====================================================
lang=get_lang()
if lang==1: #
 report({"Phase": "添加异丙醇", "Step": "添加异丙醇", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Add Isopropanol", "Step": "Add Isopropanol", "TaskType": "library", "RemainingTime": None})
 
cur_target_tip_num = target_tip_num_list[0]
p8_load_modified(tip_1000.load(cur_target_tip_num,8,1)[0])
for i in range(total_col_num):
	target_pos_index,target_col_index = divmod(i,2)
	target_pos = magnet_pos_list[target_pos_index]
	target_col = target_col_list[target_col_index]
	target_row = 1
	p8_aspirate_modified('M1_POS4',1,2,230,PostAirVolume=30)
	p8_empty_modified(f'{target_pos}',target_row,target_col,PostAirVolume=30,EmptyOffsetOfZ= 20,EmptySpeed=200)
p8_unload_tips({"Position": "M1_Trash", "Col": 1, "Row": 1})



#=========================================分装回溶液=====================================================
lang=get_lang()
if lang==1: #
 report({"Phase": "分装回溶液", "Step": "分装回溶液", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Aliquoting Elution Buffer", "Step": "Aliquoting Elution Buffer", "TaskType": "library", "RemainingTime": None})
 
magnet_pos_list = ['M1_POS5','M1_POS9','M1_POS13']
target_col_list = [6,12]
target_row_list = [i+1 for i in range(8)]
total_col_num,rest_8 = divmod(sample_num,8)
if rest_8!= 0:
	total_col_num += 1
	
if sample_num <= 9:
	temp = tip_1000.load(1)[0]
	p8_load_modified(temp)
	for i in range(sample_num):
		target_pos_index,rest_num = divmod(i,16)
		target_col_index,target_rows_index = divmod(rest_num,8)
		#计算目标位置
		target_pos = magnet_pos_list[target_pos_index]
		target_col = target_col_list[target_col_index]
		target_row = target_row_list[target_rows_index]

		p8_aspirate_modified('M1_POS14',1+i//4,1,45,PreAirVolume=0,AspirateOffsetOfZ=0.5)
		p8_empty_modified(f'{target_pos}',target_row,target_col)
	p8_unload_tips({"Position": "M1_Trash", "Col": 1, "Row": 1})

else:
	target_volume_list = [50*(sample_num//8 + 1)]*rest_8 + [50*(sample_num//8)]*(8-rest_8)
	#分装回溶液到POS3第11列
	temp = tip_1000.load(1)[0]
	p8_load_modified(temp)
	for i in range(8):
		p8_aspirate_modified('M1_POS14',1+i//4,1,target_volume_list[i],PreAirVolume=0,AspirateOffsetOfZ=0.5)
		p8_empty_modified(f'M1_POS2',i+1,11,EmptyOffsetOfZ=2)
	p8_unload_tips({"Position": "M1_Trash", "Col": 1, "Row": 1})
	# 添加回溶液到样本
	cur_target_tip_num=8
	target_tip_loc = tip_300.load(cur_target_tip_num)
	target_tip_pos,target_tip_col,target_tip_row = target_tip_loc[0]
	p8_load_tips({"Position": f"{target_tip_pos}", "Row": target_tip_row, "Col": target_tip_col})
	for i in range(total_col_num):
		# 计算目标位置
		magnet_pos_list = ['M1_POS5','M1_POS9','M1_POS13']
		target_col_list = [6,12]
		target_pos_index,target_col_index = divmod(i,2)
		target_pos = magnet_pos_list[target_pos_index]
		target_col = target_col_list[target_col_index]
		target_row = 1
		p8_aspirate_modified('M1_POS2',1,11,45)
		p8_empty_modified(f'{target_pos}',target_row,target_col,EmptyOffsetOfZ=2)
	p8_unload_tips({"Position": "M1_Trash", "Col": 1, "Row": 1})

target_col_list = [1,7]
target_row_list = [i+1 for i in range(8)]
#=========================================预分样本=====================================================
laneArr = ["M1_Lane1","M1_Lane2"]
lane_rows = list(range(1,25))
sample_tips = tip_1000.load(sample_num,1)

for i in range(sample_num):
	start_lane_index = i//24
	start_row_index = i%24
	target_pos_index,rest_num = divmod(i,16)
	target_col_index,target_rows_index = divmod(i,8)
	#计算目标位置
	target_pos = 'M1_POS2'
	target_col = target_col_index+1
	target_row = target_row_list[target_rows_index]
	p8_load_modified(sample_tips[i])
	p8_aspirate_modified(laneArr[start_lane_index],lane_rows[start_row_index],1,425)
	p8_empty({"Position":f"{target_pos}","Col":target_col,"Row":target_row, "FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "EmptyOffsetOfZ": 5, "EmptySpeed": 200, "DelayAfterEmpty": 0.5,
	"TipTouchTimes": 2, "TipTouchOffsetOfZ":15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_tips({"Position": "M1_Trash", "Col": 1, "Row": 1})


#=========================================分装洗液1=====================================================
lang=get_lang()
if lang==1: #
 report({"Phase": "分装洗液A", "Step": "分装洗液A", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Aliquoting Wash Buffer A", "Step": "Aliquoting Wash Buffer A", "TaskType": "library", "RemainingTime": None})

if SampleCount%8 == 0:
	last_row =1
else:
	last_row = 9-SampleCount%8
Wash_Buffer_A = tip_1000.load(8,8,1)
target_col_list = [3,9]
p8_load_tips({"Position":Wash_Buffer_A[0][0],"Col":Wash_Buffer_A[0][1],"Row":last_row,"Tips":8})
for i in range(total_col_num-1,-1,-1):
	target_pos_index,target_col_index = divmod(i,2)
	target_pos = magnet_pos_list[target_pos_index]
	target_col = target_col_list[target_col_index]
	target_row = 1
	p8_aspirate_modified('M1_POS4',1,3,500,PostAirVolume=10,AspirateSpeed=300)
	p8_empty_modified(f'{target_pos}',target_row,target_col,TipTouchTimes=1,EmptySpeed=200)
	if i == total_col_num-1 and SampleCount%8 != 0:
		p8_unload_tips({"Position":Wash_Buffer_A[0][0],"Col":Wash_Buffer_A[0][1],"Row":last_row,"Tips":8})
		p8_load_modified(Wash_Buffer_A[0])
p8_unload_tips({"Position": "M1_Trash", "Col": 1, "Row": 1})

#=========================================分装洗液2=====================================================
lang=get_lang()
if lang==1: #
 report({"Phase": "分装洗液B", "Step": "分装洗液B", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Aliquoting Wash Buffer B", "Step": "Aliquoting Wash Buffer B", "TaskType": "library", "RemainingTime": None})

if SampleCount%8 == 0:
	last_row =1
else:
	last_row = 9-SampleCount%8
Wash_Buffer_B = tip_1000.load(8,8,1)
target_col_list = [4,10]
p8_load_tips({"Position":Wash_Buffer_B[0][0],"Col":Wash_Buffer_B[0][1],"Row":last_row,"Tips":8})
for i in range(total_col_num-1,-1,-1):
	target_pos_index,target_col_index = divmod(i,2)
	target_pos = magnet_pos_list[target_pos_index]
	target_col = target_col_list[target_col_index]
	target_row = 1
	p8_aspirate_modified('M1_POS4',1,4,600,PostAirVolume=10,AspirateSpeed=300)
	p8_empty_modified(f'{target_pos}',target_row,target_col,TipTouchTimes=1,EmptySpeed=200)
	p8_aspirate_modified('M1_POS4',1,5,600,PostAirVolume=10)
	p8_empty_modified(f'{target_pos}',target_row,target_col+1,TipTouchTimes=1,EmptySpeed=200)
	if i == total_col_num-1 and SampleCount%8 != 0:
		p8_unload_tips({"Position":Wash_Buffer_B[0][0],"Col":Wash_Buffer_B[0][1],"Row":last_row,"Tips":8})
		p8_load_modified(Wash_Buffer_B[0])
p8_unload_tips({"Position": "M1_Trash", "Col": 1, "Row": 1})	

#=========================================添加样本到深孔板=====================================================

target_col_list = [1,7]
sample_tips2 = tip_1000.load(sample_num,8)
for i in range(total_col_num):
	p8_load_modified(sample_tips2[i])
	target_pos_index,target_col_index = divmod(i,2)
	target_pos = magnet_pos_list[target_pos_index]
	target_col = target_col_list[target_col_index]
	target_row = 1
	p8_aspirate_modified('M1_POS2',1,i+1,425,PostAirVolume=10)
	p8_empty_modified(f'{target_pos}',target_row,target_col,TipTouchTimes=1,TipTouchOffsetOfZ=15)
	p8_unload_tips({"Position": "M1_Trash", "Col": 1, "Row": 1})


#==========================================磁棒提取===============================================
lang=get_lang()
if lang==1: #
 report({"Phase": "磁棒提取", "Step": "磁棒提取", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Magnetic Rod Extraction", "Step": "Magnetic Rod Extraction", "TaskType": "library", "RemainingTime": None})


magnetic_rod_slide_in()
magnetic_rod_mix({"Col": 1,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "SecondSpeedOfZ": 10.00, "LiftingSpeed":50,"Cycles": 1, "MixParams":{"MixStartOffsetOfZ": 1, "MixFrequency": 5, "MixDuration": 600.00, "MixEndOffsetOfZ": 10, "DelayAfterMixLoopOffsetOfZ": 40.0, "DelayAfterMixLoop": 2.00}, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})
for x in range(3):
	magnetic_rod_beads_collection({"Col": 1,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "SecondSpeedOfZ": 10.00, "LiftingSpeed":50,"CollectionStartOffsetOfZ": 1, "CollectionSteppingSpeed": 5.00, "CollectionStep": 1.0, "DelayAfterStepping": 1.00, "CollectionEndOffsetOfZ": 12.0, "CollectionDuration": 60.00, "DelayAtSpeedChange": 0.50, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})
###将磁珠从第1列转移至第3列
magnetic_rod_beads_release({"Col": 3,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "SecondSpeedOfZ": 10.00, "LiftingSpeed":50,"ReleaseOffsetOfZ": 8.0, "ReleaseDuration": 0.50, "DelayAtSpeedChange": 0.50, "IsMix": True, "MixParams":{"MixStartOffsetOfZ": 8.0, "MixFrequency": 5, "MixDuration": 6, "MixEndOffsetOfZ":1, "DelayAfterMixLoopOffsetOfZ": 40.0, "DelayAfterMixLoop": 2.00}, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})
magnetic_rod_mix({"Col": 3,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "SecondSpeedOfZ": 10.00, "LiftingSpeed":50,"Cycles": 1, "MixParams":{"MixStartOffsetOfZ": 1, "MixFrequency": 4, "MixDuration": 120, "MixEndOffsetOfZ": 8.0, "DelayAfterMixLoopOffsetOfZ": 40.0, "DelayAfterMixLoop": 2.00}, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})
for x in range(3):
	magnetic_rod_beads_collection({"Col": 3,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "LiftingSpeed":50,"SecondSpeedOfZ": 10.00, "CollectionStartOffsetOfZ": 1, "CollectionSteppingSpeed": 5.00, "CollectionStep": 1.0, "DelayAfterStepping": 1.00, "CollectionEndOffsetOfZ": 8.0, "CollectionDuration": 60.00, "DelayAtSpeedChange": 0.50, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})
###将磁珠从第3列转移至第4列
magnetic_rod_beads_release({"Col": 4,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "SecondSpeedOfZ": 10.00, "LiftingSpeed":50,"ReleaseOffsetOfZ": 8.0, "ReleaseDuration": 0.50, "DelayAtSpeedChange": 0.50, "IsMix": True, "MixParams":{"MixStartOffsetOfZ": 8.0, "MixFrequency": 5, "MixDuration": 6, "MixEndOffsetOfZ":1, "DelayAfterMixLoopOffsetOfZ": 40.0, "DelayAfterMixLoop": 2.00}, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})
magnetic_rod_mix({"Col": 4,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "SecondSpeedOfZ": 10.00, "LiftingSpeed":50,"Cycles": 1, "MixParams":{"MixStartOffsetOfZ": 1, "MixFrequency": 4, "MixDuration": 120, "MixEndOffsetOfZ": 8.0, "DelayAfterMixLoopOffsetOfZ": 40.0, "DelayAfterMixLoop": 2.00}, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})
for x in range(3):
	magnetic_rod_beads_collection({"Col": 4,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "LiftingSpeed":50,"SecondSpeedOfZ": 10.00, "CollectionStartOffsetOfZ": 1, "CollectionSteppingSpeed": 5.00, "CollectionStep": 1.0, "DelayAfterStepping": 1.00, "CollectionEndOffsetOfZ": 8.0, "CollectionDuration": 60.00, "DelayAtSpeedChange": 0.50, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})
###将磁珠从第4列转移至第5列
magnetic_rod_beads_release({"Col": 5,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "LiftingSpeed":50,"SecondSpeedOfZ": 10.00, "ReleaseOffsetOfZ": 8.0, "ReleaseDuration": 0.50, "DelayAtSpeedChange": 0.50, "IsMix": True, "MixParams":{"MixStartOffsetOfZ": 8.0, "MixFrequency": 5, "MixDuration": 6, "MixEndOffsetOfZ":1, "DelayAfterMixLoopOffsetOfZ": 40.0, "DelayAfterMixLoop": 2.00}, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})
magnetic_rod_mix({"Col": 5,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "SecondSpeedOfZ": 10.00,"LiftingSpeed":50, "Cycles": 1, "MixParams":{"MixStartOffsetOfZ": 1, "MixFrequency": 4, "MixDuration": 120, "MixEndOffsetOfZ": 8.0, "DelayAfterMixLoopOffsetOfZ": 40.0, "DelayAfterMixLoop": 2.00}, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})
for x in range(3):
	magnetic_rod_beads_collection({"Col": 5,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "LiftingSpeed":50,"SecondSpeedOfZ": 10.00, "CollectionStartOffsetOfZ": 1, "CollectionSteppingSpeed": 5.00, "CollectionStep": 1.0, "DelayAfterStepping": 1.00, "CollectionEndOffsetOfZ": 8.0, "CollectionDuration": 60.00, "DelayAtSpeedChange": 0.50, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})
delay({"Duration":300})
##将磁珠从第5列转移至第6列
magnetic_rod_beads_release({"Col": 6,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "SecondSpeedOfZ": 10.00, "LiftingSpeed":50,"ReleaseOffsetOfZ": 8.0, "ReleaseDuration": 0.50, "DelayAtSpeedChange": 0.50, "IsMix": True, "MixParams":{"MixStartOffsetOfZ": 8.0, "MixFrequency": 5, "MixDuration": 6, "MixEndOffsetOfZ":1, "DelayAfterMixLoopOffsetOfZ": 40.0, "DelayAfterMixLoop": 2.00}, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})

magnetic_rod_mix({"Col": 6,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "SecondSpeedOfZ": 10.00,"LiftingSpeed":50, "Cycles": 1, "MixParams":{"MixStartOffsetOfZ": 1, "MixFrequency": 3, "MixDuration": 60.00, "MixEndOffsetOfZ": 4.0, "DelayAfterMixLoopOffsetOfZ": 40.0, "DelayAfterMixLoop": 2.00}, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})
for x in range(3):
	magnetic_rod_beads_collection({"Col": 6,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "SecondSpeedOfZ": 10.00,"LiftingSpeed":100, "CollectionStartOffsetOfZ": 1, "CollectionSteppingSpeed": 1, "CollectionStep": 0.1, "DelayAfterStepping": 2.00, "CollectionEndOffsetOfZ": 4.0, "CollectionDuration": 60.00, "DelayAtSpeedChange": 0.50, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})

##将磁珠从第6列转移至第3列,高度调整
magnetic_rod_beads_release({"Col": 3,"FirstSpeedOfZ": 58.00, "SpeedChangeOffsetOfZ": 38.0, "SecondSpeedOfZ": 10.00,"LiftingSpeed":50, "ReleaseOffsetOfZ": 8.0, "ReleaseDuration": 0.50, "DelayAtSpeedChange": 0.50, "IsMix": True, "MixParams":{"MixStartOffsetOfZ": 8.0, "MixFrequency": 6, "MixDuration": 10, "MixEndOffsetOfZ":1, "DelayAfterMixLoopOffsetOfZ": 40.0, "DelayAfterMixLoop": 2.00}, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 45.5, "TipTouchOffsetOfX": 1.5, "TipTouchSpeed": 10.0})
magnetic_rod_slide_out()
#==========================================转移产物===============================================
lang=get_lang()
if lang==1: #
 report({"Phase": "回收产物", "Step": "回收产物", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Recover the product", "Step": "Recover the nucleic acid product", "TaskType": "library", "RemainingTime": None})
 
target_col_list = [6,12]
for i in range(total_col_num):
	cur_target_tip_num = target_tip_num_list[i]
	start_pos_index,start_col_index = divmod(i,2)
	start_pos = magnet_pos_list[start_pos_index]
	start_col = target_col_list[start_col_index]
	start_row = 1
	target_tip_loc = tip_300.load(cur_target_tip_num)
	target_tip_pos,target_tip_col,target_tip_row = target_tip_loc[0]
	p8_load_tips({"Position": f"{target_tip_pos}", "Row": target_tip_row, "Col": target_tip_col})
	p8_aspirate_modified(f'{start_pos}',start_row,start_col,45)
	p8_empty_modified('M1_T1',1,i+1)
	p8_mix({"Position": 'M1_T1', "Col": i+1, "Row": 1, "PreAirVolume": 0, "MixTimes": 2, "MixAspirateSpeed": 50, "MixAspirateOffsetOfZ": 0.5, "MixVolume": 45, "MixDispenseOffsetOfZ": 5, "MixDispenseSpeed": 100, "DelayAfterMixLoop": 0.5, "MixEmptyOffsetOfZ": 5, "MixEmptySpeed": 100, "PreAirSpeed": 50, "DelayAfterMixAspirate": 0.5, "DelayAfterMixDispense": 0.5, "DelayAfterMixEmpty": 0.5, "PostAirSpeed": 50, "PostAirVolume": 0})
	p8_empty_modified('M1_T1',1,i+1)
	p8_unload_tips({"Position": "M1_Trash", "Col": 1, "Row": 1})
	
transport_go({"Position": "M1_T3"})
#磁棒浸没
magnetic_rod_slide_in()
magnetic_sleeve_down({"Speed": 50.00, "OffsetOfZ": 5.0})