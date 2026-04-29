# test_T23_mix_v2.py - T2/T3 一链合成mix分装+转移测试 (优化参数版)
# 模拟8样本场景: 每管仅7µL, 验证优化后的dispense参数能否确保液体完全排空
#
# 优化要点 (参考T1单管分装):
#   P1 aspirate: 加PostAirVolume=3, TipTouch=2, DelayAfterAspirate=5
#   P1 dispense: DispenseVolume=21 (按≤20样本最大管量), 远大于实际7µL
#                PreAir+液体+PostAir全部被空气推出, 确保管壁无残留
#
# Step1: P1从POS17 Col1 Row1吸7µL → dispense 21µL到POS7 Col1 Row1-8
# Step2: P8从POS7 Col1吸4µL → 打到POS20 Col1

from library import *
spxsiro = globals().get("library")
set_siro(spxsiro)

# ==================== Step1: P1分装7µL到POS7中转管 (优化参数) ====================
p1_load_tips({"Position":"M2_POS15","Col":1,"Row":1,"Tips":1})

for i in range(8):
    # Aspirate: 参考T1参数, 加PostAir空气垫+TipTouch+长延迟
    p1_aspirate({
        "Position":"M2_POS17","Col":1,"Row":1,
        "PreAirVolume":5,
        "AspirateOffsetOfZ":-0.2,
        "AspirateSpeed":15,
        "AspirateVolume":7,
        "PreAirSpeed":30,
        "DelayAfterAspirate":0.5,
        "PostAirSpeed":50,
        "PostAirVolume":3,
        "IfTrack":False,
        "FirstSegmentSpeed":100,
        "SpeedChangeOffsetOfZ":0,
        "SecondSegmentSpeed":80,
        "TipTouchTimes":2,
        "TipTouchOffsetOfZ":3,
        "TipTouchRangeOfX":1.2,
        "TipTouchSpeed":100
    })
    # Dispense: DispenseVolume=21远大于实际7µL, 空气垫推出全部液体
    p1_dispense({
        "Position":"M2_POS7","Col":1,"Row":i+1,
        "IsEmpty":False,
        "DispenseOffsetOfZ":-1,
        "DispenseSpeed":50,
        "DispenseVolume":21,
        "DelayAfterDispense":0.5,
        "PostAirSpeed":50,
        "PostAirVolume":0,
        "FirstSegmentSpeed":100,
        "SpeedChangeOffsetOfZ":0,
        "SecondSegmentSpeed":80,
        "TipTouchTimes":2,
        "TipTouchOffsetOfZ":5,
        "TipTouchRangeOfX":1.2,
        "TipTouchSpeed":100
    })

p1_unload_tips2({"Position":"M2_POS15","Col":None,"Row":None})

# ==================== Step2: P8从POS7 Col1吸4µL → POS20 Col1 ====================
p8_load_tips({"Position":"M2_POS15","Col":2,"Row":1,"Tips":8})

p8_aspirate({
    "Position":"M2_POS7","Col":1,"Row":1,
    "PreAirVolume":4,
    "AspirateOffsetOfZ":-1,
    "AspirateSpeed":10,
    "AspirateVolume":4,
    "PreAirSpeed":50,
    "DelayAfterAspirate":1,
    "TipTouchTimes":0,
    "PostAirSpeed":50,
    "PostAirVolume":0,
    "IfTrack":False,
    "FirstSegmentSpeed":100,
    "SpeedChangeOffsetOfZ":0,
    "SecondSegmentSpeed":80
})
p8_empty({
    "Position":"M2_POS20","Col":1,"Row":1,
    "EmptyOffsetOfZ":3,
    "EmptySpeed":50,
    "DelayAfterEmpty":0.5,
    "TipTouchTimes":0,
    "PostAirSpeed":50,
    "PostAirVolume":0,
    "FirstSegmentSpeed":100,
    "SpeedChangeOffsetOfZ":0,
    "SecondSegmentSpeed":80
})

p8_unload_tips({"Position":"M2_POS15","Col":2,"Row":1,"Tips":8})
