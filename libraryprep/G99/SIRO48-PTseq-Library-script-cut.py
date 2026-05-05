'''=====================================定量=============================================================='''

#======================物料设置=============================================================
lang=get_lang()
if lang==1: #
 report({"Phase": "定量", "Step": "cDNA定量", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "quantification", "Step": "cDNA quantification", "TaskType": "library", "RemainingTime": None})

# 定量样本数
sample_num = SampleCount

# 样本定量阶段，只支持PCR，Extract，DNB
sample_stage = 'Extract'

# 染料位置,板位，列，行
dye_loc = ('M2_POS4',1,1)

# 分装染料取枪头位置，板位，列，行
dye_tip = tip_300.load(8,8,1)[0]

# 稀释样本取枪头位置，列表，内置位置，必须是整列，可多不可少
sample_dilute_tip_loc = tip_50.load(sample_num,8,1)

# 样本来源起始位置,板位，起始列，样本必须从上到下，从左到右，从第一个开始
source_plate = ['M2_POS20',1]

# 样本染料混合起始位置,必须是深孔板，板位，起始列，样本必须从上到下，从左到右，从第一个开始
dye_mix_plate = ['M2_POS16',1]

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
file_path = f"D:\\data\\PTplus_cDNA.xlsx"
quantification_fila_path = f"D:\\data\\quantification{current_datetime}.txt"




#=================================== 函数计算部分#===================================
col_num = (sample_num+7)//8
# 本部分为获取特定位置的浓度,pos为位置元组，板列行
def get_concentration_modified(pos):
	# 文档要求输入为板行列，所以对位置数组做一个预处理
	spx_concentration = find_sampling_concentration(pos[0],pos[2],pos[1])
	return spx_concentration.Consistence
# 单个定量管位置，板列行
quantification_tubes = [(quantification_tube_loc[0],quantification_tube_loc[1]+i//8,1 + i%8) for i in range(sample_num)]

# 用于存储当前定量结果
concentration_list = []


# 单个定量管位置，板列行
quantification_tubes = [(quantification_tube_loc[0],quantification_tube_loc[1]+i//8,1 + i%8) for i in range(sample_num)]

# Move quantification tubes from home POS14 to operating POS13.
# Park the current POS13 plate in POS30 during quantification access.
transfer({"StartPosition":"M2_POS13","EndPosition":"M2_POS30","LoosenOffsetOfZ":0})
transfer({"StartPosition":quantification_tube_home_pos,"EndPosition":quantification_tube_operating_pos,"LoosenOffsetOfZ":0})

#=================================== 样本稀释部分#===================================
#分装染液
if sample_num%8 == 0:
	last_row = 1
else:
	last_row = 9-(sample_num%8)

for i in range(col_num-1,-1,-1):
	# 最后一列有余数时，打回分染液枪头并重新取
	if i == col_num - 1:
		p8_load_tips({"Position":dye_tip[0],"Col":dye_tip[1],"Row":last_row,"Tips":8})
	for j in range(1):
		p8_aspirate_modified(dye_loc[0], Row=dye_loc[2], Col=dye_loc[1], AspirateVolume=217.8,PreAirVolume=10)
		p8_empty_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i,EmptyOffsetOfZ=3+2*j,TipTouchTimes=1)
	if i == col_num - 1 and sample_num%8!=0:
		p8_unload_tips({"Position":dye_tip[0],"Col":dye_tip[1],"Row":last_row,"Tips":8})
		p8_load_tips({"Position":dye_tip[0],"Col":dye_tip[1],"Row":1,"Tips":8})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
# 添加样本
if dye_mix_plate[0] == 'M2_POS16':
	for i in range(col_num):
		p8_load_modified(sample_dilute_tip_loc[i])
		p8_aspirate_modified(source_plate[0], 1, source_plate[1]+i, 2.2,AspirateSpeed=2,IfTrack=True)
		p8_empty_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i,EmptyOffsetOfZ=10)
		p8_mix({"Position":dye_mix_plate[0],"Col":dye_mix_plate[1]+i,"Row":1,"PreAirVolume":10,"MixTimes":2,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":1,"MixVolume":50,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
		p8_unload_modified(sample_dilute_tip_loc[i])
	temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": 60}, "ShakerParameters": {"IsEnable": True,"Direction": 0,"Speed": 1200,"Duration": 60}})
	temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": 60}, "ShakerParameters": {"IsEnable": True,"Direction": 1,"Speed": 1200,"Duration": 60}})
	for i in range(col_num):
		p8_load_modified(sample_dilute_tip_loc[i])
		for x in range(4):
			p8_aspirate_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i,PreAirVolume= 5,AspirateVolume=50,AspirateOffsetOfZ=1,PostAirVolume=3,IfTrack=True)
			p8_empty_modified(quantification_tube_loc[0], Row=1, Col=quantification_tube_loc[1]+i,EmptyOffsetOfZ=10)
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
else:
	for i in range(col_num):
		p8_load_modified(sample_dilute_tip_loc[i])
		p8_aspirate_modified(source_plate[0], 1, source_plate[1]+i, 2 ,AspirateSpeed=2,IfTrack=True)
		p8_empty_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i,EmptyOffsetOfZ=10)
		# 如果染液混匀板位在震荡板位，就开启震荡，同时少混匀两次
		if dye_mix_plate[0] != 'M2_POS16':
			p8_mix({"Position":dye_mix_plate[0],"Col":dye_mix_plate[1]+i,"Row":1,"PreAirVolume":10,"MixTimes":5,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":1,"MixVolume":230,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
		else:
			temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 30.00, "Duration": 90}, "ShakerParameters": {"IsEnable": True,"Direction": 0,"Speed": 1200,"Duration": 90}})
			p8_mix({"Position":dye_mix_plate[0],"Col":dye_mix_plate[1]+i,"Row":1,"PreAirVolume":10,"MixTimes":2,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":1,"MixVolume":50,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":20,"MixEmptySpeed":50,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
			temp_shaker_stop({"IsStopTemp": True, "IsStopShaker": True})
		p8_aspirate_modified(dye_mix_plate[0], Row=1, Col=dye_mix_plate[1]+i,AspirateVolume=200,IfTrack=True)
		p8_empty_modified(quantification_tube_loc[0], Row=1, Col=quantification_tube_loc[1]+i,EmptyOffsetOfZ=14,EmptySpeed=500)
		p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
# 依次定量
for i in range(col_num):
	p8_load_quantification_tube({"Position": quantification_tube_loc[0], "Row": 1, "Col": quantification_tube_loc[1]+i, "Tips":8})
	spx_quantity_result = quantity_run_sample({"Name":"","SampleType": "dsDNA_HS", "ProductType": sample_stage, "StandardToSampleRatio": 5, "DilutionRatio":1,"Label":"","DilutionAssessment": 60})
	cur_concentration_list = [get_concentration_modified((quantification_tube_loc[0],quantification_tube_loc[1]+i,j)) for j in range(1,9)]
	concentration_list += cur_concentration_list

	p8_unload_quantification_tube({"Position": quantification_tube_loc[0], "Row": 1, "Col": quantification_tube_loc[1]+i, "Tips":8})
output_quantitative_data({"ProductType":sample_stage,"FilePath":file_path})

# Restore quantification tubes to POS14 and the parked POS13 plate to POS13.
transfer({"StartPosition":quantification_tube_operating_pos,"EndPosition":quantification_tube_home_pos,"LoosenOffsetOfZ":0})
transfer({"StartPosition":"M2_POS30","EndPosition":"M2_POS13","LoosenOffsetOfZ":0})

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





'''=====================================均一化（不带混匀）=============================================================='''
lang=get_lang()
if lang==1: #
 report({"Phase": "cDNA均一化", "Step": "cDNA均一化", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "cDNA normalization", "Step": "cDNA normalization", "TaskType": "library", "RemainingTime": None})


#======================物料设置=============================================================
# 定量样本数
sample_num = SampleCount
#稀释后目标浓度（ng/ul）
target_concentration = 6.7
# 样本最大取样体积
sample_volume = 30
#稀释总体积
target_volume = 30
# 样本稀释液位置,板位，列，行
water_loc = ('M2_POS24',1,1)

# 分装稀释液取枪头位置，板位，列，行
water_tip = tip_1000.load(1,8,0)[0]

# 稀释样本取枪头位置，列表，内置位置，必须是单个
sample_dilute_tip_loc = tip_50.load(sample_num,1)

# 样本来源起始位置,板位，起始列，样本必须从上到下，从左到右，从第一个开始
source_plate = ['M2_POS20',1]

# 均一化最低取样体积
min_diluting_volume = 4

# 样本稀释后目标位置,板位，起始列，样本必须从上到下，从左到右，从第一个开始
target_plate = ['M2_POS23',5]

#=====================均一化方案输出文件位置======================================
file_path = f"D:\\data\\samplingvolume{current_datetime}.xlsx"
# 浓度不合格样本是否一起均一化，默认均，True为均，False为不均
Is_unqualified_diluting = True





#===================本部分依据体积计算所有的样本均一化方案和体积=========================
class Sample:
	def __init__(self, SampleWellPosition,SampleWellColumn ,SampleWellRow , Concentration,DilutingWellPosition,DilutingWellColumn,DilutingWellRow,DilutingSampleVolume=0, DilutingBufferVolume=0):
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




#=============================== 函数计算部分#===================================
col_num = (sample_num+7)//8
#根据板位计算孔位，板-列-行
source_hole = [(source_plate[0],source_plate[1]+i//8,1+i%8) for i in range(sample_num)]
dilute_hole = [(target_plate[0],target_plate[1]+i//8,1+i%8) for i in range(sample_num)]
concentration_list = concentration_list
#此部分为浓度读取，暂时手工录入
# concentration_list = list(map(float,'''13.96 	14.18 	12.42 	11.33 	15.25 	20.87 	13.89 	13.46
# 14.24 	16.25 	8.83 	9.72 	15.61 	11.68 	13.88 	7.57
# 17.28 	13.51 	11.80 	8.64 	17.30 	16.52 	13.61 	13.20
# 12.77 	18.15 	19.52 	16.29 	14.95 	14.52 	11.77 	8.80
# 14.29 	11.91 	18.60 	13.75 	14.59 	12.48 	10.72 	11.04
# 19.67 	25.29 	20.23 	21.21 	22.34 	18.48 	24.63 	12.31
# '''.split()))


sample_concentration = [Sample(*source_hole[i], concentration_list[i], *dilute_hole[i], DilutingSampleVolume=0, DilutingBufferVolume=0) for i in range(sample_num)]
if not Is_unqualified_diluting:
	sample_concentration = [each for each in sample_concentration if each.Concentration >= target_concentration]


for item in sample_concentration:
	cur_concentration = item.Concentration
	if cur_concentration < target_concentration:
		item.DilutingSampleVolume = sample_volume
		item.DilutingBufferVolume = max(0,target_volume-sample_volume)
	# 目标取样体积
	else:
		item.DilutingSampleVolume = round(target_concentration / cur_concentration* target_volume,2)
		# 稀释液体积
		if item.DilutingSampleVolume<min_diluting_volume:
			item.DilutingSampleVolume = min_diluting_volume
		item.DilutingBufferVolume = target_volume-item.DilutingSampleVolume

# 取吸水枪头
p1_load_modified(water_tip)
# 根据稀释液体积在目标孔位中添加稀释液，如果为0则不添加
for i in range(sample_num):
	if sample_concentration[i].DilutingBufferVolume != 0:
		p1_aspirate_modified(water_loc[0], Row=water_loc[2], Col=water_loc[1], AspirateOffsetOfZ=0.8,AspirateVolume=sample_concentration[i].DilutingBufferVolume,AspirateSpeed=10)
		p1_empty_modified(dilute_hole[i][0], Row=dilute_hole[i][2], Col=dilute_hole[i][1],EmptyOffsetOfZ=0.5,EmptySpeed=10)
	else:
		pass
# 推掉枪头
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

#悬空添加矿物油
# 计算最后一列去枪头的行
if SampleCount%8 == 0:
	last_row =1
else:
	last_row = 9-SampleCount%8
#oil_1 = tip_300.load(8,8,1)
transfer({"StartPosition":"M2_POS10","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})#开盖
p8_load_tips({"Position":oil_1[0][0],"Col":oil_1[0][1],"Row":last_row,"Tips":8})
for i in range(col_num-1,-1,-1):
	p8_aspirate({"Position":"M2_POS10","Col":10,"Row":1,"PreAirVolume":20,"AspirateOffsetOfZ":1,"AspirateSpeed":10,"AspirateVolume":20,"PreAirSpeed":50,"DelayAfterAspirate":1,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 2, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})
	p8_empty({"Position":"M2_POS23","Col":i+5,"Row":1,"EmptyOffsetOfZ":8,"EmptySpeed":30,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	if i == col_num-1 and SampleCount%8 != 0:
		p8_unload_tips({"Position":oil_1[0][0],"Col":oil_1[0][1],"Row":last_row,"Tips":8})
		p8_load_modified(oil_1[0])
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})	
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS10","LoosenOffsetOfZ":0})#关盖

# 根据样本体积在目标孔位中添加样本，如果为0则不添加，每次都打掉枪头
for i in range(sample_num):
	p8_load_modified(sample_dilute_tip_loc[i])
	if sample_concentration[i].DilutingSampleVolume != 0:
		p8_aspirate_modified(source_hole[i][0], Row=source_hole[i][2], Col=source_hole[i][1], AspirateVolume=sample_concentration[i].DilutingSampleVolume,AspirateSpeed=10)
		p8_empty_modified(dilute_hole[i][0], Row=dilute_hole[i][2], Col=dilute_hole[i][1],EmptyOffsetOfZ=0.5,EmptySpeed=10)
	else:
		pass
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS9","LoosenOffsetOfZ":0})
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})




'''=========================================================建库==================================================='''
'''=========================================================建库==================================================='''

#SampleCount= 48#int(get_variable({"Name":"SampleCount"}))
#取8的商和余数,计算行列数
Quotient8= SampleCount//8
Remainder8= SampleCount%8
if Remainder8 == 0:
	add8 = 0
else:
	add8 = 1
ColNum =Quotient8+add8

#取16的商和余数,计算行列数#管子数
Quotient16= SampleCount//16
Remainder16= SampleCount%16
if Remainder16 == 0:
	add16 = 0
else:
	add16 = 1
TubeNum =Quotient16+add16



######################################################################末端修复和分装#####################################################


lang=get_lang()
if lang==1: #
 report({"Phase": "片段化&末修&加A", "Step": "片段化&末修&加A", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "DNA Fragmentation, End Repair and A-Tailing", "Step": "DNA Fragmentation, End Repair and A-Tailing", "TaskType": "library", "RemainingTime": None})
 
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})###开试剂盖板
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})###开试剂盖板

# 配置末端修复反应液
if SampleCount <= 20:
	c = 1.4
else:
	c = 1.3

#分装C23
p1_load_modified(tip_1000.load(1)[0])
for i in range(1):
	p1_aspirate({"Position":"M2_POS24","Col":1,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.8,"AspirateSpeed":50,"AspirateVolume":20*SampleCount,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":20,"IfTrack":False,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_empty({"Position":"M2_POS17","Col":5,"Row":4,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":1,"TipTouchOffsetOfZ":5,"TipTouchRangeOfX":2,"TipTouchSpeed":50,"PostAirSpeed":100,"PostAirVolume":5,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
# 添加C23 4ul
p8_load_modified(tip_300.load(1)[0])
p8_aspirate({"Position":"M2_POS17","Col":5,"Row":4,"PreAirVolume":0,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":4*c*SampleCount,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_empty({"Position":"M2_POS17","Col":3,"Row":4,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

# 添加C9酶切反应液
p1_load_modified(tip_1000.load(1)[0])
#p1_mix({"Position":"M2_POS17","Col":3,"Row":1,"PreAirVolume":5,"MixTimes":10,"MixAspirateSpeed":200,"MixAspirateOffsetOfZ":0.6,"MixVolume":7*c*SampleCount,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":200,"DelayAfterMixLoop":0,"MixEmptyOffsetOfZ":1,"MixEmptySpeed":300,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_aspirate({"Position":"M2_POS17","Col":3,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":20,"AspirateVolume":9.2*c*SampleCount,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"PostAirSpeed":100,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":2, "TipTouchOffsetOfZ": 20, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_empty({"Position":"M2_POS17","Col":3,"Row":4,"EmptyOffsetOfZ":0.8,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchTimes": 3, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
# 添加C10
p8_load_modified(tip_50.load(1)[0])
p8_aspirate({"Position":"M2_POS17","Col":3,"Row":2,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":0.8*c*SampleCount,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS17","Col":3,"Row":4,"EmptyOffsetOfZ":0.8,"EmptySpeed":10,"DelayAfterEmpty":0.5,"TipTouchTimes":1,"TipTouchOffsetOfZ":10,"TipTouchRangeOfX":3,"TipTouchSpeed":50,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
# 添加C11后混匀
p1_load_modified(tip_1000.load(1)[0])
p1_aspirate({"Position":"M2_POS17","Col":3,"Row":3,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":3*SampleCount,"AspirateVolume":6*c*SampleCount,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_empty({"Position":"M2_POS17","Col":3,"Row":4,"EmptyOffsetOfZ":0.8,"LiquidLevelDetection":"None","EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
#p1_mix({"Position":"M2_POS17","Col":3,"Row":4,"PreAirVolume":8,"MixTimes":15,"MixAspirateSpeed":8*n,"MixAspirateOffsetOfZ":2,"MixVolume":16*n,"MixDispenseOffsetOfZ":2+0.4*n,"MixDispenseSpeed":100,"DelayAfterMixLoop":5,"MixEmptyOffsetOfZ":0.5+0.3*n,"MixEmptySpeed":50,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":2, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_mix({"Position":"M2_POS17", "Col": 3, "Row": 4,"PreAirVolume":80,"MixTimes":10,"MixAspirateSpeed":8*SampleCount,"MixAspirateOffsetOfZ":0.6,"MixVolume":16*SampleCount,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":70,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.5+0.3*SampleCount,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":3,"DelayAfterMixDispense":5,"DelayAfterMixEmpty":5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_mix({"Position":"M2_POS17", "Col": 3, "Row": 4,"PreAirVolume":80,"MixTimes":10,"MixAspirateSpeed":8*SampleCount,"MixAspirateOffsetOfZ":0.6,"MixVolume":16*SampleCount,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":70,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.5+0.3*SampleCount,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":3,"DelayAfterMixDispense":5,"DelayAfterMixEmpty":10,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":5, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
#p1_empty({"Position":"M2_POS17","Col":3,"Row":4,"EmptyOffsetOfZ":1,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})


p1_load_modified(tip_300.load(1)[0])
transfer({"StartPosition":"M2_POS10","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})###开试剂盖板
# 计算每列的分装体积
if SampleCount <= 20:
	target_volume_list = [20*(c-0.25)*(SampleCount//8+1)]*(SampleCount%8)+[20*(c-0.25)*(SampleCount//8)]*(8-SampleCount%8)
else:
	target_volume_list = [20*(c-0.2)*(SampleCount//8+1)]*(SampleCount%8)+[20*(c-0.2)*(SampleCount//8)]*(8-SampleCount%8)
	
for i in range(8):
	p1_aspirate({"Position":"M2_POS17","Col":3,"Row":4,"PreAirVolume":8,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS10","Col":7,"Row":i+1,"EmptyOffsetOfZ":6,"EmptySpeed":20,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
# 盖上试剂盖
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})
# 打开PCR盖板
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})
col_num = math.ceil(SampleCount/8)


# 添加末修酶切反应液
for i in range(col_num):
	p8_load_modified(tip_300.load(target_tip_num_list[i])[0])
	p8_aspirate({"Position":"M2_POS10","Col":7,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":20,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS20","Col":i+5,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_mix({"Position":"M2_POS20","Col":i+5,"Row":1,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.6,"MixVolume":40,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":100,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS20","Col":i+5,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

	
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})#PCR盖板

def spx_p5_f_0():
	pcr_close_door()
	pcr_run_method({"Methods":["PTplus_Frag_ER"]})
PTplus_Frag_ER = parallel_block(spx_p5_f_0)
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS10","LoosenOffsetOfZ":0})#八连管盖板



######################################################################连接缓冲液配置和分装#####################################################

lang=get_lang()
if lang==1: #
 report({"Phase": "接头连接", "Step": "接头连接", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Adapter Ligation", "Step": "Adapter Ligation", "TaskType": "library", "RemainingTime": None})


transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})#试剂盖板



if SampleCount <= 20:
	c = 1.4
	c_3 = 0.25
else:
	c = 1.3
	c_3 = 0.15

# 吸取c13连接酶
p8_load_modified(tip_50.load(1)[0])
p8_aspirate({"Position":"M2_POS17","Col":4,"Row":2,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":1*c*SampleCount,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":0.1*SampleCount,"EmptySpeed":10,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3,"TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.5, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})


#吸取c12连接缓冲液
if SampleCount <=8:
	p1_load_modified(tip_300.load(1)[0])
else:
	p1_load_modified(tip_1000.load(1)[0])
#p1_load_modified(tip_1000.load(1)[0])
#p1_mix({"Position":"M2_POS17","Col":4,"Row":1,"PreAirVolume":0,"MixTimes":15,"MixAspirateSpeed":200,"MixAspirateOffsetOfZ":0.6,"MixVolume":25*SampleCount,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":200,"DelayAfterMixLoop":0,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":200,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
for x in range(2):
	p1_aspirate({"Position":"M2_POS17","Col":4,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":27*c*SampleCount/2,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"PostAirSpeed":100,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes": 3, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS17","Col":4,"Row":3,"EmptyOffsetOfZ":0.7*SampleCount,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes": 3, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
#p1_mix({"Position":"M2_POS17","Col":4,"Row":3,"PreAirVolume":10,"MixTimes":15,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":2,"MixVolume":22*SampleCount,"MixDispenseOffsetOfZ":0.6+0.4*SampleCount,"MixDispenseSpeed":100,"DelayAfterMixLoop":7,"MixEmptyOffsetOfZ":2+0.7*SampleCount,"MixEmptySpeed":10,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes": 3, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
p1_mix({"Position":"M2_POS17", "Col": 4, "Row": 3,"PreAirVolume":80,"MixTimes":10,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.6,"MixVolume":25*SampleCount,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":50,"DelayAfterMixLoop":10,"MixEmptyOffsetOfZ":30,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":3,"DelayAfterMixDispense":5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":2, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
p1_mix({"Position":"M2_POS17", "Col": 4, "Row": 3,"PreAirVolume":80,"MixTimes":20,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.6,"MixVolume":25*SampleCount,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":50,"DelayAfterMixLoop":10,"MixEmptyOffsetOfZ":2+0.7*SampleCount,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":3,"DelayAfterMixDispense":5,"DelayAfterMixEmpty":15,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":5, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})


transfer({"StartPosition":"M2_POS10","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})#八连管盖板

# 分装连接缓冲液
if SampleCount <=8:
	p1_load_modified(tip_50.load(1)[0])
else:
	p1_load_modified(tip_300.load(1)[0])

# 计算每列的分装体积
target_volume_list = [28*(c-c_3)*(SampleCount//8+1)]*(SampleCount%8)+[28*(c-c_3)*(SampleCount//8)]*(8-SampleCount%8)

for i in range(8):
	if SampleCount <=8:
		p1_aspirate({"Position":"M2_POS17","Col":4,"Row":3,"PreAirVolume":8,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	else:
		p1_aspirate({"Position":"M2_POS17","Col":4,"Row":3,"PreAirVolume":8,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 3.5, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS10","Col":8,"Row":i+1,"EmptyOffsetOfZ":1.7,"EmptySpeed":20,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 14, "TipTouchRangeOfX":1.2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})###关试剂盖板
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS10","LoosenOffsetOfZ":0})#八连管盖板


PTplus_Frag_ER.Wait()
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})###开PCR盖板
transfer({"StartPosition":"M2_POS10","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})###开试剂盖板


for i in range(col_num):
	p8_load_modified(tip_50.load(target_tip_num_list[i])[0])
	p8_aspirate({"Position":"M2_POS10","Col":8,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":28,"PreAirSpeed":10,"DelayAfterAspirate":0.5,"TipTouchTimes":5,"PostAirSpeed":10,"PostAirVolume":2,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.5, "TipTouchSpeed": 100})
	p8_aspirate_modified("M2_POS10",1,i+1,2,PreAirVolume=0)
	p8_empty_modified("M2_POS20",1,i+5,EmptySpeed=10)
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
	p8_load_modified(tip_300.load(target_tip_num_list[i])[0])
	p8_mix({"Position":"M2_POS20","Col":i+5,"Row":1,"PreAirVolume":10,"MixTimes":10,"MixAspirateSpeed":50,"MixAspirateOffsetOfZ":0.6,"MixVolume":50,"MixDispenseOffsetOfZ":3,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":100,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty_modified("M2_POS20",1,i+5)
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})###关PCR盖板

def spx_p6_f_0():
	pcr_close_door()
	pcr_run_method({"Methods":["PTplus_Ligation"]})

Ligation = parallel_block(spx_p6_f_0)
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS10","LoosenOffsetOfZ":0})###关试剂盖板

lang=get_lang()
if lang==1: #
 report({"Phase": "接头连接", "Step": "连接反应及磁珠分装", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Adapter Ligation", "Step": "Ligation reaction and magnetic bead aliquoting", "TaskType": "library", "RemainingTime": None})


# 分装C23
p1_load_modified(tip_1000.load(1)[0])
target_volume_list = [90*(SampleCount//8+1)+25]*(SampleCount%8)+[90*(SampleCount//8)+25]*(8-SampleCount%8)
for i in range(8):
	p1_aspirate({"Position":"M2_POS24","Col":1,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.8,"AspirateSpeed":50,"AspirateVolume":target_volume_list[i],"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":20,"IfTrack":False,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p1_empty({"Position":"M2_POS7","Col":11,"Row":i+1,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":1,"TipTouchOffsetOfZ":5,"TipTouchRangeOfX":2,"TipTouchSpeed":50,"PostAirSpeed":100,"PostAirVolume":5,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})

p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
#####################################################磁珠分装##############################################

p1_load_modified(tip_1000.load(1)[0])
#C21增加混匀
p1_mix({"Position":"M2_POS24", "Col": 2, "Row": 1,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":0.8,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":2,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":"M2_POS24", "Col": 2, "Row": 1,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":1,"MixVolume":900,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":30,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":15,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})

# 计算磁珠分装体积，每个样本第一轮纯化使用48+40磁珠，最多四列
target_volume_list = [88*1.2*(SampleCount//8+1)]*(SampleCount%8)+[88*1.2*(SampleCount//8)]*(8-SampleCount%8)
for i in range(8):
	#p1_aspirate({"Position":"M2_POS24","Col":2,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.8,"AspirateSpeed":50,"AspirateVolume":target_volume_list[i],"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":30,"IfTrack":False,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100, "TipTouchOffsetOfZ": 14, "TipTouchRangeOfX": 1.5, "TipTouchSpeed": 100})
	p1_aspirate({"Position":"M2_POS24", "Col": 2, "Row": 1,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":50,"AspirateVolume":target_volume_list[i],"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 50, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
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
	p8_aspirate({"Position":"M2_POS7","Col":12,"Row":1,"PreAirVolume":35,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":48,"PreAirSpeed":50,"DelayAfterAspirate":1,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.4, "TipTouchSpeed": 100})
	p8_dispense({"Position": "M2_POS16","Col":5+i,"Row":1,"FirstSegmentSpeed": 100, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 80, "DispenseOffsetOfZ": 0.8, "DispenseSpeed": 30, "DispenseVolume":48,"DelayAfterDispense": 1, "IsEmpty": True, "EmptyOffsetOfZ": 2, "EmptySpeed": 30, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	if i == col_num-1 and target_tip_num_list[i] != 8:
		p8_unload_modified((temp[0],temp[1],temp[2]+8-sample_num%8))
		p8_load_modified(temp)
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

Ligation.Wait()
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0})###开PCR盖板













'''=====================================杂洗（带混匀）=============================================================='''

lang=get_lang()
if lang==1: #
 report({"Phase": "杂交捕获", "Step": "文库pooling", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Hybridization Capture", "Step": "Library pooling", "TaskType": "library", "RemainingTime": None})

#==========================输入部分=============================

# 单产品pooling方案

#样本来源板,板位，起始列
source_plate = ['M2_POS13',5]

#样本稀释位置,板位，起始列
sample_dilution_place = ['M2_POS8',9]

# 样本取样体积临界值
min_sample_volume = 2
max_sample_volume = 20


#单个DNB样本数
single_dnb_sample_num = 4
# 单个DNB投入量
target_dna_ng = 2000
#pooling总体积
target_pooling_volume = 80
# 质控浓度
sample_qc_concentration = 25
#pooling取buffer使用1ml枪头
single_tip_loc = tip_1000.load(1)[0]
#pooling稀释buffer位置，板-列-行
dilution_buffer_loc = ('M2_POS24',1,1)
#pooling产物位置列表，板位，列，行
target_tube_loc = [('M2_POS7',1,i) for i in range(1,9)]



#pooing取样本枪头位置，要求位置数组，板位，列，行
sample_pooling_tip_loc = tip_50.load(sample_num,1) # sample_pooling_tip_loc = [('M2_POS15',i//8 + 1,8-i%8) for i in range(sample_num)]
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
# 浓度不合格样本是否一起pooling，默认pooling，True为pooling，False为不pooling
Is_unqualified_pooling = True
output_file_path = r"D:/data/PTplus_Hybridization_info.csv"



'''==========================================以下为执行部分，禁止修改====================================================='''
#===================本部分依据体积计算所有的样本pooling方案和体积=========================
class Sample:
	def __init__(self, SampleWellPosition,SampleWellColumn ,SampleWellRow , Concentration,DilutingWellPosition,DilutingWellColumn,DilutingWellRow,DilutingSampleVolume=0, DilutingBufferVolume=0):
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




#=============================== 函数计算部分#===================================
col_num = (sample_num+7)//8
#根据板位计算孔位,板-列-行
sample_list = [(source_plate[0],source_plate[1]+i//8,1+i%8) for i in range(sample_num)]
dilute_hole = [(sample_dilution_place[0],sample_dilution_place[1]+i//8,1+i%8) for i in range(sample_num)]

# 此部分为浓度读取,暂时手工录入
# concentration_list = list(map(float,'''11.62     11.05     10.70     10.10     12.27     4.95     8.09     5.29
# 15.18     10.26     14.29     22.22     0.60     16.29     14.53     0.70
# '''.split()))





sample_concentration = [Sample(*sample_list[i], concentration_list[i], *dilute_hole[i], DilutingSampleVolume=0, DilutingBufferVolume=0) for i in range(sample_num)]
if filtered_samples:
	for i in range(sample_num):
		sample_concentration[i].sample_id = filtered_samples[i].sample_id
		sample_concentration[i].sample_initial_index = i+1
initial_samples = [each for each in filtered_samples]


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

x,y = divmod(sample_num,target_dnb_num)

# 把sorted_volume分成target_dnb_num组,分组后每组的样本数为x+1或x,以下位代码实现分组
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


# 补水的位置
water_loc_list = []

# 计算每组样本浓度最大值和最小值是否差10倍,如果出现了,就需要将浓度高于最小值10倍的样本标记为需要预稀释,最小值设置为sample_qc_concentration
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

def output_pooling_info(samples, temp, output_file_path):
	"""
	将每个样本的 pooling 组、取样体积、稀释倍数和放大倍数输出到文件中
	:param samples: 样本列表，每个样本包含属性：sample_id（样本编号）、group_idx（pooling 组）、DilutingSampleVolume（取样体积）、dilution_type（稀释倍数）
	:param temp: 包含放大倍数的列表，格式为 [(放大倍数, 水体积), ...]
	:param output_file_path: 输出文件路径
	"""
	with open(output_file_path, 'w', encoding='utf-8') as f:
		# 写入表头
		f.write("样本编号,Pooling组,取样体积(ul),稀释倍数,放大倍数\n")
		# 遍历每个样本并写入信息
		# 获取当前日期时间
		current_time = time.localtime()
		# 格式化为年P月日时分秒
		formatted_time = time.strftime("%yH%m%d%H%M%S", current_time)
		cur_output_index = 0
		for i, group in enumerate(samples):
			cur_pooling_id = f"{formatted_time}{i+1}"
			for sample in group:
				cur_output_index +=1
				# 获取当前样本的放大倍数
				while sample.sample_initial_index != cur_output_index:
					f.write(f"{initial_samples[cur_output_index-1].sample_id},,,,\n")
					cur_output_index += 1
					if cur_output_index>=100:
						break
				concentrate_times = temp[i][0]  # temp[i][0] 是放大倍数
				if sample.NeedDilution:
					dilution_type = 8
				else:
					dilution_type = 1
				formated_DilutingSampleVolume = "%.2f" % sample.DilutingSampleVolume
				f.write(f"{sample.sample_id},{cur_pooling_id},{formated_DilutingSampleVolume},{dilution_type},{concentrate_times}\n")


# 调用函数输出信息
output_pooling_info(dnb_list, temp, output_file_path)
print(f"样本的 pooling 组、取样体积、稀释倍数和放大倍数已输出到文件：{output_file_path}")














#分水（暂不考虑超体积）
p1_load_tips({"Position":single_tip_loc[0],'Col':single_tip_loc[1],'Row':single_tip_loc[2]})

if water_loc_list:
	for i in range(len(water_loc_list)):
		p1_aspirate({"Position": dilution_buffer_loc[0], "Row": dilution_buffer_loc[2], "Col":  dilution_buffer_loc[1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "PreAirSpeed": 100, "PreAirVolume": 10, "SecondSegmentSpeed": 100, "AspirateoffsetOfZ": 1.0, "AspirateSpeed": 20, "AspirateVolume": 14, "DelayAfterAspirate": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100, "PostAirSpeed": 100, "PostAirVolume": 0})
		p1_empty({"Position": water_loc_list[i][0], "Row": water_loc_list[i][1], "Col":  water_loc_list[i][2], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100, "EmptyOffsetOfZ": 1, "EmptySpeed": 190, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})
if target_tube_loc[0][0]=='M2_POS17':
	transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})
for i in range(len(water_volume_list)):
	if temp[i][0]>=8:
		new_water_volume = target_pooling_volume-target_pooling_volume/(temp[i][0]/8)
		p1_aspirate({"Position": dilution_buffer_loc[0], "Row": dilution_buffer_loc[2], "Col":  dilution_buffer_loc[1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "PreAirSpeed": 100, "PreAirVolume": 10, "SecondSegmentSpeed": 100, "AspirateoffsetOfZ": 1.0, "AspirateSpeed": 20, "AspirateVolume": new_water_volume, "DelayAfterAspirate": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100, "PostAirSpeed": 100, "PostAirVolume": 0})
		p1_empty({"Position": target_dnb_loc_list[i][0], "Row": target_dnb_loc_list[i][2], "Col": target_dnb_loc_list[i][1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100, "EmptyOffsetOfZ": 2, "EmptySpeed": 190, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})
	p1_aspirate({"Position": dilution_buffer_loc[0], "Row": dilution_buffer_loc[2], "Col":  dilution_buffer_loc[1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "PreAirSpeed": 100, "PreAirVolume": 10, "SecondSegmentSpeed": 100, "AspirateoffsetOfZ": 1.0, "AspirateSpeed": 100, "AspirateVolume": water_volume_list[i], "DelayAfterAspirate": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100, "PostAirSpeed": 100, "PostAirVolume": 0})
	p1_empty({"Position": target_tube_loc[i][0], "Row": target_tube_loc[i][2], "Col": target_tube_loc[i][1], "FirstSegmentSpeed": 150, "SpeedChangeOffsetOfZ": 0, "SecondSegmentSpeed": 100, "EmptyOffsetOfZ": 5, "EmptySpeed": 190, "DelayAfterEmpty": 0.5, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 2, "TipTouchSpeed": 100})

p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

j = 0
for i,poolings in enumerate(temp):
	samples = dnb_list[i]
	for sample in samples:
		p8_load_modified(sample_pooling_tip_loc[j])
		j += 1
		if not sample.NeedDilution:
			sample_volume = sample.DilutingSampleVolume
			sample_pos = sample.SampleWellPosition
			sample_col = sample.SampleWellColumn
			sample_row = sample.SampleWellRow
			p8_aspirate_modified(sample_pos,sample_row,sample_col,sample_volume,PreAirVolume=10)
			p8_empty_modified(target_tube_loc[i][0],target_tube_loc[i][2],target_tube_loc[i][1])
			p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
		else:
			sample_volume = sample.DilutingSampleVolume
			sample_pos = sample.SampleWellPosition
			sample_col = sample.SampleWellColumn
			sample_row = sample.SampleWellRow
			sample_diluting_pos = sample.DilutingWellPosition
			sample_diluting_col = sample.DilutingWellColumn
			sample_diluting_row = sample.DilutingWellRow
			p8_aspirate_modified(sample_pos,sample_row,sample_col,2,PreAirVolume=5,PostAirVolume=0)
			p8_empty_modified(sample_diluting_pos,sample_diluting_row,sample_diluting_col,EmptyOffsetOfZ=0.5,EmptySpeed=10)
			p8_mix({"Position":sample_diluting_pos,"Col":sample_diluting_col,"Row":sample_diluting_row,"PreAirVolume":10,"MixTimes":5,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.5,"MixVolume":30,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":100,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 5, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
			p8_aspirate_modified(sample_diluting_pos,sample_diluting_row,sample_diluting_col,sample_volume,PreAirVolume=0,PostAirVolume=0)
			p8_empty_modified(target_tube_loc[i][0],target_tube_loc[i][2],target_tube_loc[i][1])
			p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})


if target_tube_loc[0][0]=='M2_POS17':
	transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})
'''==========================================以上为执行部分，禁止修改====================================================='''
'''===========================================单产品pooling模板v1=============================================================='''

lang=get_lang()
if lang==1: #
 report({"Phase": "杂交捕获", "Step": "纯化", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Hybridization Capture", "Step": "Purification", "TaskType": "library", "RemainingTime": None})
 
# 杂交pooling后转板
transfer({"StartPosition":"M2_POS16","EndPosition":transposition,"LoosenOffsetOfZ":0})#转移深孔板4
transfer({"StartPosition":"M2_POS7","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})#转移深孔板3
transfer({"StartPosition":transposition,"EndPosition":"M2_POS7","LoosenOffsetOfZ":0})#转移深孔板4

# 样本数量

Hyb_Quotient= SampleCount//4
Hyb_Remainder= SampleCount%4
if Hyb_Remainder == 0:
	Hyb_Add = 0
else:
	Hyb_Add = 1
Hybridization_num = Hyb_Quotient + Hyb_Add
# c21纯化磁珠分装
# 磁珠位置(板，列，行)
magetic_beads_pos = {"Position":"M2_POS24","Col":3,"Row":2}
# 磁珠预分位置（板，列）
magetic_beads_dispense_pos = {"Position":"M2_POS16","Col":2,"Row":1}

# 乙醇位置
ethanol_pos = {"Position":"M2_POS3","Col":2,"Row":1}





p1_load_modified(tip_1000.load(1)[0])
#增加混匀
p1_mix({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":0.8,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":2,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":300,"MixAspirateOffsetOfZ":0.8,"MixVolume":900,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":400,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":30,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":15,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

p1_load_modified(tip_1000.load(1)[0])
for i in range(Hybridization_num):
	p1_aspirate({"Position":magetic_beads_pos["Position"], "Col":magetic_beads_pos["Col"], "Row":magetic_beads_pos["Row"],"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":50,"AspirateVolume":144,"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 50, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p1_empty({"Position":magetic_beads_dispense_pos["Position"], "Col":magetic_beads_dispense_pos["Col"], "Row":magetic_beads_dispense_pos["Row"]+i,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":2,"PostAirSpeed":50,"PostAirVolume":25,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	#p1_empty({"Position":magetic_beads_dispense_pos["Position"], "Col":magetic_beads_dispense_pos["Col"], "Row":magetic_beads_dispense_pos["Row"]+i,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":2,"PostAirSpeed":50,"PostAirVolume":25,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})



# 转移样本到磁珠1位置
temp = tip_300.load(Hybridization_num,Hybridization_num,1)
p8_load_modified(temp[0])
p8_mix({"Position":"M2_POS16","Col":1,"Row":1,"PreAirVolume":0,"MixTimes":5,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":1,"MixVolume":70,"MixDispenseOffsetOfZ":1,"MixDispenseSpeed":100,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":1,"MixEmptySpeed":100,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_aspirate({"Position":"M2_POS16","Col":1,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":30,"AspirateVolume":90,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":10,"IfTrack":True,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":magetic_beads_dispense_pos["Position"], "Col":magetic_beads_dispense_pos["Col"], "Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(temp[0])

# transfer({"StartPosition":"M2_POS7","EndPosition":"M2_POS16","LoosenOffsetOfZ":0}) #转移深孔板4
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1000, "Duration": 30}})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 0, "Speed": 1000, "Duration": 30}})
delay({"Duration": 300})
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0}) #转移深孔板4
delay({"Duration": 120})






###去废液
p8_load_modified_BubblePurge(temp[0])
p8_aspirate({"Position":"M2_POS23","Col":2,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0,"AspirateSpeed":10,"AspirateVolume":230,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS23","Col":1,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

#乙醇洗2次
for tt in range(2):
	temp = tip_300.load(Hybridization_num)[0]
	p8_load_modified(temp)
	p8_aspirate({"Position":ethanol_pos["Position"],"Col":ethanol_pos["Col"],"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":1,"AspirateSpeed":50,"AspirateVolume":180,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS23","Col":2,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_modified(temp)
	delay({"Duration": 60})
###去废液,到POS23前半板
	p8_load_modified_BubblePurge(temp)
	p8_aspirate({"Position":"M2_POS23","Col":2,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0,"AspirateSpeed":10,"AspirateVolume":190,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS23","Col":1,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
	
def wait_for_magnetic_beads2():
	# 等待磁珠吸附
	delay({"Duration": 300})#5-10min

magetic_wait2 = parallel_block(wait_for_magnetic_beads2)

transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0}) #开盖
lang=get_lang()
if lang==1: #
 report({"Phase": "杂交捕获", "Step": "配置杂交反应液", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Hybridization Capture", "Step": "Preparing hybridization reaction mixture", "TaskType": "library", "RemainingTime": None})
 
#配置杂交反应液
#C17
p8_load_modified(tip_300.load(1)[0])
p8_aspirate({"Position":"M2_POS2","Col":4,"Row":2,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":13*1.3*Hybridization_num,"PreAirSpeed":50,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS17","Col":6,"Row":4,"EmptyOffsetOfZ":0.5,"EmptySpeed":3,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
#C18
p8_load_modified(tip_300.load(1)[0])
p8_aspirate({"Position":"M2_POS17","Col":6,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":5*1.3*Hybridization_num,"PreAirSpeed":50,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS17","Col":6,"Row":4,"EmptyOffsetOfZ":0.5,"EmptySpeed":3,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
#c19
p8_load_modified(tip_50.load(1)[0])
p8_aspirate({"Position":"M2_POS17","Col":6,"Row":2,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":2*1.3*Hybridization_num,"PreAirSpeed":50,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS17","Col":6,"Row":4,"EmptyOffsetOfZ":0.5,"EmptySpeed":3,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
#C20
p8_load_modified(tip_50.load(1)[0])
p8_aspirate({"Position":"M2_POS17","Col":6,"Row":3,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":10,"AspirateVolume":2*1.3*Hybridization_num,"PreAirSpeed":50,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS17","Col":6,"Row":4,"EmptyOffsetOfZ":0.5,"EmptySpeed":3,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
#C23
p8_load_modified(tip_300.load(1)[0])
p8_aspirate({"Position":"M2_POS17","Col":5,"Row":4,"PreAirVolume":10,"AspirateOffsetOfZ":0.6,"AspirateSpeed":50,"AspirateVolume":8*1.3*Hybridization_num,"PreAirSpeed":50,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS17","Col":6,"Row":4,"EmptyOffsetOfZ":0.5,"EmptySpeed":3,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_mix({"Position":"M2_POS17","Col":6,"Row":4,"PreAirVolume":5,"MixTimes":10,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":0.6,"MixVolume":30*Hybridization_num,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":20,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":5,"MixEmptySpeed":30,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_mix({"Position":"M2_POS17","Col":6,"Row":4,"PreAirVolume":5,"MixTimes":15,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":0.6,"MixVolume":30*Hybridization_num,"MixDispenseOffsetOfZ":10,"MixDispenseSpeed":20,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":1,"MixEmptySpeed":30,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchTimes": 5, "TipTouchOffsetOfZ": 20, "TipTouchRangeOfX": 2.5, "TipTouchSpeed": 100})
#p8_empty({"Position":"M2_POS17","Col":6,"Row":4,"EmptyOffsetOfZ":3,"EmptySpeed":3,"DelayAfterEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0}) #关盖

magetic_wait2.Wait()

transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0}) #开盖
#添加杂交反应液
for x in range(Hybridization_num):
	p8_load_modified(tip_50.load(1)[0])
	p8_aspirate({"Position":"M2_POS17","Col":6,"Row":4,"PreAirVolume":0,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":30,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS23","Col":2,"Row":1+x,"EmptyOffsetOfZ":0.5,"EmptySpeed":20,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0}) #关盖

transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})#震荡深孔板4
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1200, "Duration": 60}})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 0, "Speed": 1200, "Duration": 60}})
delay({"Duration": 180})
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})#磁力架深孔板4
delay({"Duration": 180})

pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0}) #PCR盖板
#添加矿物油
p1_load_modified(tip_1000.load(1)[0])
for i in range(Hybridization_num):
	target_pos = 'M2_POS20'
	target_col_1 = 1
	target_col_2 = 2
	target_row = i%8+1
	p1_aspirate_modified("M2_POS24", 1, 3, 20,AspirateOffsetOfZ=0.8,AspirateSpeed=10)
	p1_dispense({"Position":target_pos,"Col":target_col_1,"Row":target_row,"DispenseOffsetOfZ":2,"DispenseSpeed":10,"DispenseVolume":10,"DelayAfterDispense":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IsEmpty":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p1_empty_modified(target_pos, target_row, target_col_2,EmptyOffsetOfZ=2)
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

p8_load_modified(tip_300.load(Hybridization_num)[0])
p8_aspirate({"Position":"M2_POS23","Col":2,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":28,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_dispense({"Position":"M2_POS20","Col":2,"Row":1,"DispenseOffsetOfZ":0.5,"DispenseSpeed":20,"DispenseVolume":14,"DelayAfterDispense":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IsEmpty":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS20","Col":1,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":20,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
# p8_mix({"Position":"M2_POS20","Col":1,"Row":1,"PreAirVolume":20,"MixTimes":5,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":10,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":1, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

lang=get_lang()
if lang==1: #
 report({"Phase": "杂交捕获", "Step": "杂交反应&洗脱准备", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Hybridization Capture", "Step": "Hybridization Reaction & Elution Preparation", "TaskType": "library", "RemainingTime": None})
 
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0}) #PCR盖板
pcr_close_door()

# 杂交反应转板
transfer({"StartPosition":"M2_POS7","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})

def blockHyb():
	pcr_run_method({"Methods": ["PTplus_hybrid"]})
hybrid = parallel_block(blockHyb)

delay({"Duration": 1800})

#Block begin:配置PCR反应液
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})#开试剂盖板
p1_load_modified(tip_1000.load(1)[0])
p1_aspirate({"Position":"M2_POS17","Col":5,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":25*1.2*Hybridization_num,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_empty({"Position":"M2_POS17","Col":5,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
p8_load_modified(tip_50.load(1)[0])
p8_aspirate({"Position":"M2_POS17","Col":5,"Row":2,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":4*1.2*Hybridization_num,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_empty({"Position":"M2_POS17","Col":5,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
p1_load_modified(tip_1000.load(1)[0])
p1_aspirate({"Position":"M2_POS17","Col":5,"Row":4,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":150,"AspirateVolume":21*1.2*Hybridization_num,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_empty({"Position":"M2_POS17","Col":5,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":3, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
#p1_mix({"Position":"M2_POS17","Col":5,"Row":3,"PreAirVolume":5,"MixTimes":10,"MixAspirateSpeed":200,"MixAspirateOffsetOfZ":2+0.5*Hybridization_num,"MixVolume":25*sample_num,"MixDispenseOffsetOfZ":2+0.6*sample_num,"MixDispenseSpeed":200,"DelayAfterMixLoop":0.5,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":50,"LiquidLevelDetection":"None","PreAirSpeed":100,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
# p1_mix({"Position":"M2_POS17", "Col": 5, "Row": 3,"PreAirVolume":80,"MixTimes":10,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":45*Hybridization_num,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":20,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
# p1_mix({"Position":"M2_POS17", "Col": 5, "Row": 3,"PreAirVolume":80,"MixTimes":15,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":45*Hybridization_num,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":10,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":3, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})#关试剂盖板

#洗脱
#C25 清洗液分装
p1_load_modified(tip_1000.load(1)[0])
for x in range(Hybridization_num):
	if x >= 4:
		p1_aspirate({"Position":"M2_POS24", "Col":2, "Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":100,"AspirateVolume":850,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	else:
		p1_aspirate({"Position":"M2_POS24", "Col":2, "Row":2,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":100,"AspirateVolume":850,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p1_empty({"Position":"M2_POS16","Col":1,"Row":1+x,"EmptyOffsetOfZ":10,"EmptySpeed":100,"DelayAfterEmpty":2,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

def blockTemp_set():
	temp_shaker_set({"TempParameters": {"IsEnable": True, "Temp": 60.00, "Duration": -1}, "ShakerParameters": {"IsEnable": False, "Direction": 1, "Speed": 1200, "Duration": 60}})
Temp_set = parallel_block(blockTemp_set)

lang=get_lang()
if lang==1: #
 report({"Phase": "杂交捕获", "Step": "捕获磁珠纯化", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Hybridization Capture", "Step": "Capture Bead Purification", "TaskType": "library", "RemainingTime": None})
#C22 捕获磁珠
p1_load_modified(tip_1000.load(1)[0])

#增加混匀
p1_mix({"Position":"M2_POS2", "Col":4, "Row":1,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":80,"MixAspirateOffsetOfZ":0.6,"MixVolume":Hybridization_num*40,"MixDispenseOffsetOfZ":0.6,"MixDispenseSpeed":100,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":2,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":"M2_POS2", "Col":4, "Row":1,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":80,"MixAspirateOffsetOfZ":0.6,"MixVolume":Hybridization_num*40,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":100,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":15,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":15,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_empty({"Position":"M2_POS2","Col":4,"Row":1,"EmptyOffsetOfZ":0.6,"EmptySpeed":100,"DelayAfterEmpty":2,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

p1_load_modified(tip_300.load(1)[0])
for x in range(Hybridization_num):
	p1_aspirate({"Position":"M2_POS2", "Col":4, "Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":50,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p1_empty({"Position":"M2_POS23","Col":3,"Row":1+x,"EmptyOffsetOfZ":0.6,"EmptySpeed":100,"DelayAfterEmpty":2,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
#C24 磁珠清洗剂
p1_load_modified(tip_1000.load(1)[0])
for x in range(Hybridization_num):
	target_row = x//4	# 前四个第一管，后四个另一管
	p1_aspirate({"Position":"M2_POS24", "Col":1, "Row":2+target_row,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":100,"AspirateVolume":4*180+20,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p1_empty({"Position":"M2_POS23","Col":4,"Row":1+x,"EmptyOffsetOfZ":0.6,"EmptySpeed":100,"DelayAfterEmpty":2,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

#磁珠纯化弃上清
Capture = tip_300.load(Hybridization_num,Hybridization_num,1)
p8_load_modified(Capture[0])
p8_aspirate({"Position":"M2_POS23","Col":3,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":60,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS23","Col":9,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(Capture[0])

for i in range(3):
	transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS7","LoosenOffsetOfZ":0})
#加C24 磁珠清洗剂
	p8_load_modified_BubblePurge(Capture[0])
	p8_aspirate({"Position":"M2_POS7","Col":4,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":180,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS7","Col":3,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_mix({"Position":"M2_POS7","Col":3,"Row":1,"PreAirVolume":20,"MixTimes":15,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":150,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_empty({"Position":"M2_POS7","Col":3,"Row":1,"EmptyOffsetOfZ":1,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_modified(Capture[0])
	transfer({"StartPosition":"M2_POS7","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})#磁力架
	delay({"Duration":60})
#弃上清
	p8_load_modified_BubblePurge(Capture[0])
	p8_aspirate({"Position":"M2_POS23","Col":3,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":190,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS23","Col":9,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_modified(Capture[0])

transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS7","LoosenOffsetOfZ":0})#磁力架
#C24 磁珠清洗剂重悬（等待时间不超过10min）
p8_load_modified_BubblePurge(Capture[0])
p8_aspirate({"Position":"M2_POS7","Col":4,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":180,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS7","Col":3,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_mix({"Position":"M2_POS7","Col":3,"Row":1,"PreAirVolume":20,"MixTimes":15,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":150,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS7","Col":3,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})

p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})



hybrid.Wait()
Temp_set.Wait()
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0}) #PCR盖板

lang=get_lang()
if lang==1: #
 report({"Phase": "杂交捕获", "Step": "靶标捕获", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Hybridization Capture", "Step": "Target Capture", "TaskType": "library", "RemainingTime": None})
 
# # 将杂交产物分成两份
# p8_load_modified(tip_300.load(Hybridization_num)[0])
# p8_mix({"Position":"M2_POS20","Col":1,"Row":1,"PreAirVolume":20,"MixTimes":8,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":25,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":1, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
# p8_aspirate({"Position":"M2_POS20","Col":1,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":14,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
# p8_empty({"Position":"M2_POS20","Col":2,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
# p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
#转移C22 捕获磁珠至POS20温控
Hyb_2 = tip_300.load(Hybridization_num,Hybridization_num,1)
p8_load_modified(Hyb_2[0])
p8_aspirate({"Position":"M2_POS7","Col":3,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":90,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS20","Col":1,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_mix({"Position":"M2_POS20","Col":1,"Row":1,"PreAirVolume":20,"MixTimes":10,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":90,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS20","Col":1,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_aspirate({"Position":"M2_POS7","Col":3,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":90,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS20","Col":2,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_mix({"Position":"M2_POS20","Col":2,"Row":1,"PreAirVolume":20,"MixTimes":10,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":90,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS20","Col":2,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS20","Col":2,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(Hyb_2[0])

#转移杂交产物至POS7
#Capture_mix = tip_300.load(Hybridization_num,Hybridization_num,1)

p8_load_modified(Hyb_2[0])
p8_aspirate({"Position":"M2_POS20","Col":1,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":105,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_aspirate({"Position":"M2_POS20","Col":2,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":105,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS7","Col":3,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(Hyb_2[0])
for x in range(5):
	delay({"Duration":120})
	#p8_load_modified_BubblePurge(Hyb_2[0])
	if x == 4:
		#最后一次混匀后，将产物从POS7常温转至POS16温控
		transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})#深孔板4磁力架
		p8_load_modified_BubblePurge(Hyb_2[0])
		p8_mix({"Position":"M2_POS7","Col":3,"Row":1,"PreAirVolume":20,"MixTimes":15,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":180,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
		for tt in range(2):
			p8_aspirate({"Position":"M2_POS7","Col":3,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":110,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
			p8_empty({"Position":"M2_POS23","Col":5,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	else:
		p8_load_modified_BubblePurge(Hyb_2[0])
		p8_mix({"Position":"M2_POS7","Col":3,"Row":1,"PreAirVolume":20,"MixTimes":15,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":180,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_modified(Hyb_2[0])

# 弃上清
delay({"Duration":60})
p8_load_modified_BubblePurge(Hyb_2[0])
p8_aspirate({"Position":"M2_POS23","Col":5,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.5,"AspirateSpeed":30,"AspirateVolume":220,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS7","Col":3,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})


transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})#深孔板4温控

wash_1 = tip_300.load(Hybridization_num,Hybridization_num,1)
#第1次清洗
#加C25洗液
p8_load_modified(wash_1[0])
p8_aspirate({"Position":"M2_POS16","Col":1,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.8,"AspirateSpeed":100,"AspirateVolume":150,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS16","Col":5,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":2,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_mix({"Position":"M2_POS16","Col":5,"Row":1,"PreAirVolume":20,"MixTimes":12,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":1,"MixVolume":130,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS16","Col":5,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(wash_1[0])
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})#深孔板4温控

delay({"Duration":60})
#去废液
p8_load_modified_BubblePurge(wash_1[0])
p8_aspirate({"Position":"M2_POS23","Col":5,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0,"AspirateSpeed":100,"AspirateVolume":160,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS23","Col":4,"Row":1,"EmptyOffsetOfZ":10,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(wash_1[0])
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})#深孔板5
#第2次清洗
#加C25洗液
p8_load_modified_BubblePurge(wash_1[0])
p8_aspirate({"Position":"M2_POS16","Col":1,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.8,"AspirateSpeed":100,"AspirateVolume":150,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS16","Col":5,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_mix({"Position":"M2_POS16","Col":5,"Row":1,"PreAirVolume":20,"MixTimes":12,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":1,"MixVolume":130,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS16","Col":5,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(wash_1[0])
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})#深孔板5磁力架
delay({"Duration":60})
#去废液
p8_load_modified_BubblePurge(wash_1[0])
p8_aspirate({"Position":"M2_POS23","Col":5,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0,"AspirateSpeed":100,"AspirateVolume":160,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS23","Col":4,"Row":1,"EmptyOffsetOfZ":10,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
wash_2 = tip_300.load(Hybridization_num,Hybridization_num,1)
#第3次清洗换管，深孔板5第4列转移至深孔板4第6列
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})#深孔板5
p8_load_modified(wash_2[0])
p8_aspirate({"Position":"M2_POS16","Col":1,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.8,"AspirateSpeed":100,"AspirateVolume":150,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS16","Col":5,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_mix({"Position":"M2_POS16","Col":5,"Row":1,"PreAirVolume":20,"MixTimes":12,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":1,"MixVolume":130,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_aspirate({"Position":"M2_POS16","Col":5,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.8,"AspirateSpeed":100,"AspirateVolume":150,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS16","Col":6,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":4,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(wash_2[0])
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})#深孔板4磁力架
delay({"Duration":60})
#弃上清
p8_load_modified_BubblePurge(wash_2[0])
p8_aspirate({"Position":"M2_POS23","Col":6,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0,"AspirateSpeed":100,"AspirateVolume":160,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS23","Col":7,"Row":1,"EmptyOffsetOfZ":10,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":4,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(wash_2[0])
#转移至温控
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})#深孔板4温控
#第4次清洗
p8_load_modified_BubblePurge(wash_2[0])
p8_aspirate({"Position":"M2_POS16","Col":1,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.8,"AspirateSpeed":100,"AspirateVolume":150,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS16","Col":6,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_mix({"Position":"M2_POS16","Col":6,"Row":1,"PreAirVolume":20,"MixTimes":12,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":1,"MixVolume":130,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS16","Col":6,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":4,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(wash_2[0])
delay({"Duration":180})
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})#深孔板4磁力架
#弃上清
p8_load_modified_BubblePurge(wash_2[0])
p8_aspirate({"Position":"M2_POS23","Col":6,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0,"AspirateSpeed":100,"AspirateVolume":160,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS23","Col":7,"Row":1,"EmptyOffsetOfZ":10,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(wash_2[0])
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})#深孔板4磁力架
#第5次清洗
p8_load_modified_BubblePurge(wash_2[0])
p8_aspirate({"Position":"M2_POS16","Col":1,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.8,"AspirateSpeed":100,"AspirateVolume":150,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS16","Col":6,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_mix({"Position":"M2_POS16","Col":6,"Row":1,"PreAirVolume":20,"MixTimes":12,"MixAspirateSpeed":20,"MixAspirateOffsetOfZ":1,"MixVolume":130,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS16","Col":6,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(wash_2[0])
delay({"Duration":180})
#将产物从POS16第6列转移至POS16第2列
p8_load_modified_BubblePurge(wash_2[0])
p8_aspirate({"Position":"M2_POS16","Col":6,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.8,"AspirateSpeed":100,"AspirateVolume":150,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS16","Col":2,"Row":1,"EmptyOffsetOfZ":0.5,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(wash_2[0])
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})#深孔板5磁力架
def spx_p5_f_0():
	spx_flp_avoidBodyEmpty = 1
	#Block begin:Block
	pcr_run_method({"Methods":["PTplus_60-4"]})
	temp_shaker_stop({"Name":"spx_p5_f_0","IsStopTemp":True,"IsStopShaker":True})


cool_down = parallel_block(spx_p5_f_0)
delay({"Duration":60})
#弃上清
p8_load_modified_BubblePurge(wash_2[0])
p8_aspirate({"Position":"M2_POS23","Col":2,"Row":1,"PreAirVolume":0,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":160,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS23","Col":3,"Row":1,"EmptyOffsetOfZ":10,"EmptySpeed":100,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

#洗酒精1次
EtOH_2 = tip_300.load(Hybridization_num,Hybridization_num,0)
p8_load_modified(EtOH_2[0])
p8_aspirate({"Position":"M2_POS3","Col":2,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":1,"AspirateSpeed":50,"AspirateVolume":200,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS23","Col":2,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(EtOH_2[0])
delay({"Duration": 120})
###去废液
p8_load_modified(EtOH_2[0])
p8_aspirate({"Position":"M2_POS23","Col":2,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0,"AspirateSpeed":10,"AspirateVolume":210,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS23","Col":3,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":2, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
def post_PCR_delay():
	delay({"Duration": 180})
P_PCR_mix = parallel_block(post_PCR_delay)

lang=get_lang()
if lang==1: #
 report({"Phase": "Post-PCR", "Step": "配置PCR反应液", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Post-PCR", "Step": "Preparing PCR reaction mixture", "TaskType": "library", "RemainingTime": None})

#Block begin:配置PCR反应液
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})#开试剂盖板
# p1_load_modified(tip_1000.load(1)[0])
# p1_aspirate({"Position":"M2_POS17","Col":5,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":25*1.2*Hybridization_num,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
# p1_empty({"Position":"M2_POS17","Col":5,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
# p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
# p8_load_modified(tip_50.load(1)[0])
# p8_aspirate({"Position":"M2_POS17","Col":5,"Row":2,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":4*1.2*Hybridization_num,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
# p8_empty({"Position":"M2_POS17","Col":5,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
# p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
p1_load_modified(tip_1000.load(1)[0])
# p1_aspirate({"Position":"M2_POS24","Col":1,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":150,"AspirateVolume":21*1.2*Hybridization_num,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
# p1_empty({"Position":"M2_POS17","Col":5,"Row":3,"EmptyOffsetOfZ":2,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":"M2_POS17", "Col": 5, "Row": 3,"PreAirVolume":80,"MixTimes":10,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":45*Hybridization_num,"MixDispenseOffsetOfZ":5,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":20,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":0, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_mix({"Position":"M2_POS17", "Col": 5, "Row": 3,"PreAirVolume":80,"MixTimes":15,"MixAspirateSpeed":120,"MixAspirateOffsetOfZ":0.6,"MixVolume":45*Hybridization_num,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":100,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":0.6*sample_num,"MixEmptySpeed":10,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchTimes":3, "TipTouchOffsetOfZ": 35, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

P_PCR_mix.Wait()
cool_down.Wait()
#加PCR mix
for x in range(Hybridization_num):
	p8_load_modified(tip_300.load(1)[0])
	p8_aspirate({"Position":"M2_POS17","Col":5,"Row":3,"PreAirVolume":5,"AspirateOffsetOfZ":0.5,"AspirateSpeed":100,"AspirateVolume":50,"PreAirSpeed":100,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":5,"IfTrack":True,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p8_empty({"Position":"M2_POS23","Col":2,"Row":x+1,"EmptyOffsetOfZ":0.5,"LiquidLevelDetection":"None","EmptySpeed":100,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})#关试剂盖板
transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})#深孔板4转至震荡
delay({"Duration": 120})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1200, "Duration": 120}})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": -1, "Speed": 1200, "Duration": 120}})
#添加矿物油
p1_load_modified(tip_1000.load(1)[0])
for i in range(Hybridization_num):
	target_pos = 'M2_POS20'
	target_col = i//8+3
	target_row = i%8+1
	p1_aspirate_modified("M2_POS24", 1, 3, 30,AspirateOffsetOfZ=0.8,AspirateSpeed=10)
	p1_empty_modified(target_pos, target_row, target_col,EmptyOffsetOfZ=0.5)
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})
#转至PCR板反应
p8_load_modified(tip_300.load(Hybridization_num)[0])
p8_aspirate({"Position":"M2_POS16","Col":2,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":60,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS20","Col":3,"Row":1,"EmptyOffsetOfZ":0.6,"EmptySpeed":10,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})
transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0})#PCR盖板

lang=get_lang()
if lang==1: #
 report({"Phase": "Post-PCR", "Step": "PCR反应程序&杂交文库纯化准备", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Post-PCR", "Step": "Preparation for Hybridized library purification", "TaskType": "library", "RemainingTime": None})
 
def blockPost_PCR():
	pcr_close_door()
	pcr_run_method({"Methods": ["PTplus_Post_PCR"]})
Post_PCR = parallel_block(blockPost_PCR)

#C21纯化磁珠

# 磁珠分装
# 磁珠位置(板，列，行)
# magetic_beads_pos = {"Position":"M2_POS24","Col":2,"Row":1}
# 磁珠预分位置（板，列）
# magetic_beads_dispense_pos = {"Position":"M2_POS16","Col":8,"Row":1}
# 磁珠分装位置1（板，列，行）
# magetic_beads_dispense_pos1 = {"Position":"M2_POS16","Col":1,"Row":1}
# magetic_beads_volume1 = 144

# 磁珠分装位置2（板，列，行）
# magetic_beads_dispense_pos2 = {"Position":"M2_POS16","Col":2,"Row":1}
# magetic_beads_volume2 = 144

# 计算磁珠分装体积
# target_volume_list = [154*(Hybridization_num//8+1)]*(Hybridization_num%8)+[154*(Hybridization_num//8)]*(8-Hybridization_num%8)
# target_volume_list = 144
# 废液板
# waste_board = {"Position":"M2_POS7","Col":3,"Row":1}

# 乙醇位置
# ethanol_pos = {"Position":"M2_POS12","Col":7,"Row":1}


p1_load_modified(tip_1000.load(1)[0])
#增加混匀

p1_mix({"Position":"M2_POS24","Col":3,"Row":2,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.8,"MixVolume":500,"MixDispenseOffsetOfZ":0.8,"MixDispenseSpeed":100,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":2,"TipTouchTimes":0,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100})
p1_mix({"Position":"M2_POS24","Col":3,"Row":2,"PreAirVolume":10,"MixTimes":20,"MixAspirateSpeed":100,"MixAspirateOffsetOfZ":0.8,"MixVolume":500,"MixDispenseOffsetOfZ":30,"MixDispenseSpeed":100,"DelayAfterMixLoop":1,"MixEmptyOffsetOfZ":30,"MixEmptySpeed":50,"PreAirSpeed":100,"DelayAfterMixAspirate":0,"DelayAfterMixDispense":0,"DelayAfterMixEmpty":15,"TipTouchTimes":3,"PostAirSpeed":100,"PostAirVolume":0,"FirstSegmentSpeed":190,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":100,"TipTouchOffsetOfZ": 30, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_empty({"Position":"M2_POS24","Col":3,"Row":2,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":2,"PostAirSpeed":50,"PostAirVolume":25,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})

p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

p1_load_modified(tip_1000.load(1)[0])
for i in range(Hybridization_num):	
	p1_aspirate({"Position":"M2_POS24","Col":3,"Row":2,"PreAirVolume":5,"AspirateOffsetOfZ":0.8,"AspirateSpeed":50,"AspirateVolume":55,"PreAirSpeed":50,"DelayAfterAspirate":2,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 50, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p1_empty({"Position":"M2_POS16","Col":8,"Row":1+i,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":2,"PostAirSpeed":50,"PostAirVolume":25,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":3, "TipTouchOffsetOfZ": 10, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

Post_PCR.Wait()
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0}) #PCR盖板

lang=get_lang()
if lang==1: #
 report({"Phase": "Post-PCR后纯化", "Step": "Post-PCR后纯化", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Post-PCR purification", "Step": "Post-PCR purification", "TaskType": "library", "RemainingTime": None})
 
#结合磁珠
postPCR_tips = tip_300.load(Hybridization_num,Hybridization_num,1)
p8_load_modified(postPCR_tips[0])
p8_mix({"Position":"M2_POS20","Col":3,"Row":1,"PreAirVolume":20,"MixTimes":5,"MixAspirateSpeed":50,"MixAspirateOffsetOfZ":0.5,"MixVolume":40,"MixDispenseOffsetOfZ":15,"MixDispenseSpeed":50,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":15,"MixEmptySpeed":10,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_aspirate({"Position":"M2_POS20","Col":3,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":60,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS16","Col":8,"Row":1,"EmptyOffsetOfZ":0.6,"EmptySpeed":10,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS16","Col":8,"Row":1,"EmptyOffsetOfZ":0.6,"EmptySpeed":10,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_modified(postPCR_tips[0])
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1200, "Duration": 60}})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": -1, "Speed": 1200, "Duration": 60}})
delay({"Duration": 300})
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})#深孔板5转至磁力架
delay({"Duration": 120})
#弃上清
p8_load_modified_BubblePurge(postPCR_tips[0])
p8_aspirate({"Position":"M2_POS23","Col":8,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0.5,"AspirateSpeed":10,"AspirateVolume":110,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS23","Col":9,"Row":1,"EmptyOffsetOfZ":0.6,"EmptySpeed":10,"DelayAfterEmpty":0.8,"TipTouchTimes":3,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})

#洗酒精2次
# EtOH_2 = tip_300.load(Hybridization_num,Hybridization_num,1)
for x in range(2):
	postPCR_wash_tips = tip_300.load(Hybridization_num,Hybridization_num,1)
	p8_load_modified_BubblePurge(postPCR_wash_tips[0])
	p8_aspirate({"Position":"M2_POS3","Col":2,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":1,"AspirateSpeed":50,"AspirateVolume":180,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS23","Col":8,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_modified(postPCR_wash_tips[0])
	delay({"Duration": 120})
###去废液
	p8_load_modified_BubblePurge(postPCR_wash_tips[0])
	p8_aspirate({"Position":"M2_POS23","Col":8,"Row":1,"PreAirVolume":2,"AspirateOffsetOfZ":0,"AspirateSpeed":10,"AspirateVolume":190,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
	p8_empty({"Position":"M2_POS23","Col":9,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":50,"DelayAfterEmpty":0.8,"TipTouchTimes":3, "PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80, "TipTouchOffsetOfZ": 15, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
	p8_unload_tips({"Position":"M2_Trash","Col":None,"Row":None})


def close_PCR():
	delay({"Duration": 300})#5-10Min
Close_door = parallel_block(close_PCR)

transfer({"StartPosition":"M2_POS26","EndPosition":"M2_POS20","LoosenOffsetOfZ":0}) #PCR盖板
pcr_close_door()

Close_door.Wait()
# 加C23

Hyb_3 = tip_50.load(Hybridization_num,Hybridization_num,1)
p8_load_modified(Hyb_3[0])
p8_aspirate({"Position":"M2_POS7","Col":11,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":23,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS23","Col":8,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_unload_modified(Hyb_3[0])

transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})#深孔板5转至震荡
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": 1, "Speed": 1200, "Duration": 60}})
temp_shaker_set({"TempParameters": {"IsEnable": False, "Temp": 25.00, "Duration": -1}, "ShakerParameters": {"IsEnable": True, "Direction": -1, "Speed": 1200, "Duration": 60}})
delay({"Duration": 300})
transfer({"StartPosition":"M2_POS16","EndPosition":"M2_POS23","LoosenOffsetOfZ":0})#深孔板5转至磁力架
delay({"Duration": 180})

lang=get_lang()
if lang==1: #
 report({"Phase": "Post-PCR后纯化", "Step": "转移产物", "TaskType": "library", "RemainingTime": None})
elif lang==2: #
 report({"Phase": "Post-PCR purification", "Step": "Transfer the product", "TaskType": "library", "RemainingTime": None})
 
#转移产物
p8_load_modified(Hyb_3[0])
p8_aspirate({"Position":"M2_POS23","Col":8,"Row":1,"PreAirVolume":10,"AspirateOffsetOfZ":0.5,"AspirateSpeed":50,"AspirateVolume":21,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":1,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS13","Col":9,"Row":1,"EmptyOffsetOfZ":0.8,"EmptySpeed":80,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_mix({"Position":"M2_POS13","Col":9,"Row":1,"PreAirVolume":20,"MixTimes":5,"MixAspirateSpeed":40,"MixAspirateOffsetOfZ":0.5,"MixVolume":10,"MixDispenseOffsetOfZ":8,"MixDispenseSpeed":20,"DelayAfterMixLoop":2,"MixEmptyOffsetOfZ":10,"MixEmptySpeed":20,"PreAirSpeed":50,"DelayAfterMixAspirate":0.5,"DelayAfterMixDispense":0.5,"DelayAfterMixEmpty":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":1, "TipTouchOffsetOfZ": 3, "TipTouchRangeOfX": 1.2, "TipTouchSpeed": 100})
p8_empty({"Position":"M2_POS13","Col":9,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":10,"DelayAfterEmpty":0.8,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":5,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_unload_modified(Hyb_3[0])

transfer({"StartPosition":"M2_POS23","EndPosition":"M2_POS16","LoosenOffsetOfZ":0})#深孔板5转至磁力架
