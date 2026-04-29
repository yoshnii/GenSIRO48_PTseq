# test_T1_direct.py - T1直接分装测试
# P1 取50µL tip from POS15, 从POS17 Col1 Row1 吸液(3µL, PostAir 3µL)
# dispense 10µL(over-dispense)到POS20 Col1全孔

from library import *
spxsiro = globals().get("library")
set_siro(spxsiro)

p1_load_tips({"Position":"M2_POS15","Col":1,"Row":1,"Tips":1})

for row in range(1, 9):
    p1_aspirate({"Position":"M2_POS17","Col":1,"Row":1,"PreAirVolume":5,"AspirateOffsetOfZ":0.6,"AspirateSpeed":15,"AspirateVolume":2.3,"PreAirSpeed":30,"DelayAfterAspirate":5,"PostAirSpeed":50,"PostAirVolume":3,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2,"TipTouchOffsetOfZ":3,"TipTouchRangeOfX":1.2,"TipTouchSpeed":100})
    p1_dispense({"Position":"M2_POS20","Col":1,"Row":row,"IsEmpty":False,"DispenseOffsetOfZ":0.5,"DispenseSpeed":50,"DispenseVolume":10,"DelayAfterDispense":0.5,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80,"TipTouchTimes":2,"TipTouchOffsetOfZ":5,"TipTouchRangeOfX":0,"TipTouchSpeed":100})

p1_unload_tips2({"Position":"M2_POS15","Col":None,"Row":None})
