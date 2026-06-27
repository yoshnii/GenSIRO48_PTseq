# -*- coding: utf-8 -*-
#Timestamp:2024/11/18 9:46:21
#Head - 共用头部,包含所有功能。
from library import *
spxsiro = globals().get("library")
set_siro(spxsiro)
import math
"""
不要修改HEAD
"""

#####################################################################
# 测试脚本: T1 cDNA Primer 分装到POS20全部48孔
# 目的: 验证P1从POS17 Col1 Row1分装到POS20 Col1-6 Row1-8
# 参数: 完全复制v8 G99全流程 L441-447
# 枪头: 50µL (M2_POS15)
#####################################################################

home()

# ===== 开试剂盖 =====
transfer({"StartPosition":"M2_POS17","EndPosition":"M2_POS27","LoosenOffsetOfZ":0})

# ===== 取50µL枪头 (P1单通道, 从POS15第1列取) =====
p1_load_tips({"Position":"M2_POS15","Col":1,"Row":1,"Tips":1})

# ===== 分装到POS20全部48孔 (6列 × 8行) =====
# 参数与v8 G99全流程完全一致
for i in range(6):
	for j in range(8):
		p1_aspirate({"Position":"M2_POS17","Col":1,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":-0.2,"AspirateSpeed":15,"AspirateVolume":2.3,"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100})
		p1_dispense({"Position":"M2_POS20","Col":i+1,"Row":j+1,"IsEmpty":False,"DispenseOffsetOfZ":0.5,"DispenseSpeed":50,"DispenseVolume":10,"DelayAfterDispense":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2,"TipTouchOffsetOfZ":5,"TipTouchRangeOfX":0,"TipTouchSpeed":100})

# ===== 丢枪头 =====
p1_unload_tips2({"Position":"M2_Trash","Col":None,"Row":None})

# ===== 盖试剂盖 =====
transfer({"StartPosition":"M2_POS27","EndPosition":"M2_POS17","LoosenOffsetOfZ":0})

home()
