# test_T23_mix.py - T2/T3 一链合成mix分装+转移测试 (8 samples)
# Step1: P1从POS15 1-1取50µL tip, 从POS17 Col1 Row1吸7µL, dispense 10µL到POS7 Col1 Row1-8
# Step2: P8从POS15 Col2取8个50µL tip, 从POS7 Col1吸4.6µL, 打到POS20 Col1

from library import *
spxsiro = globals().get("library")
set_siro(spxsiro)

# Step1: P1分装7µL到POS7中转板每孔
p1_load_tips({"Position":"M2_POS15","Col":1,"Row":1,"Tips":1})

for i in range(8):
    p1_aspirate({"Position":"M2_POS17","Col":1,"Row":1,"PreAirVolume":8,"AspirateOffsetOfZ":-0.2,"AspirateSpeed":10,"AspirateVolume":7,"PreAirSpeed":50,"DelayAfterAspirate":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
    p1_dispense({"Position":"M2_POS7","Col":1,"Row":i+1,"IsEmpty":False,"DispenseOffsetOfZ":-1,"DispenseSpeed":50,"DispenseVolume":10,"DelayAfterDispense":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})

p1_unload_tips2({"Position":"M2_POS15","Col":None,"Row":None})

# Step2: P8从POS7 Col1吸4.6µL转移到POS20 Col1
p8_load_tips({"Position":"M2_POS15","Col":2,"Row":1,"Tips":8})

p8_aspirate({"Position":"M2_POS7","Col":1,"Row":1,"PreAirVolume":4,"AspirateOffsetOfZ":-1,"AspirateSpeed":10,"AspirateVolume":4.6,"PreAirSpeed":50,"DelayAfterAspirate":1,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"IfTrack":False,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})
p8_empty({"Position":"M2_POS20","Col":1,"Row":1,"EmptyOffsetOfZ":3,"EmptySpeed":50,"DelayAfterEmpty":0.5,"TipTouchTimes":0,"PostAirSpeed":50,"PostAirVolume":0,"FirstSegmentSpeed":100,"SpeedChangeOffsetOfZ":0,"SecondSegmentSpeed":80})

p8_unload_tips({"Position":"M2_POS15","Col":2,"Row":1,"Tips":8})
