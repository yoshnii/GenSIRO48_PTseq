
# -*- coding: utf-8 -*-
#####################################################################
# 定量测量最小测试脚本 v4
# Minimal Quantification Measurement Test
#####################################################################
# 用途: 仅测试 quantity_run_sample 系统函数行为
#   - 不做任何液体处理（不分染料、不加样本、不转移）
#   - 直接拾取定量管 -> 执行测量 -> 读取结果
#   - 用于验证系统级 "sample information" 的获取机制
#
# 前提: POS11 Col1 已经放好8个定量管（空管即可）
#
# ======================== 耗材摆放 ========================
#
# POS11: 定量管架
#        Col1: 8个定量管 (可以是空管)
#
# 其他板位: 无需任何耗材
#
#####################################################################

#Timestamp:2026/02/21
#Head
from library import *
spxsiro = globals().get("library")
set_siro(spxsiro)
"""
不要修改HEAD
"""

home()

'''========================== 配置 =========================='''
# 定量管位置 (POS11, Col1)
quantification_tube_loc = ['M2_POS11', 1]

# 样本类型
sample_stage = 'PCR'

'''========================== 浓度获取函数 =========================='''
def get_concentration_modified(pos):
	"""获取浓度，空channel返回None而不是崩溃"""
	try:
		spx_concentration = find_sampling_concentration(pos[0], pos[2], pos[1])
		if spx_concentration is None:
			return None
		return spx_concentration.Consistence
	except Exception as e:
		print(f"  [WARNING] get_concentration error at {pos}: {e}")
		return None

'''========================== 定量测量 =========================='''
lang=get_lang()
if lang==1:
	report({"Phase": "定量测试", "Step": "拾取定量管并测量", "TaskType": "library", "RemainingTime": None})
elif lang==2:
	report({"Phase": "Quant Test", "Step": "Load tubes and measure", "TaskType": "library", "RemainingTime": None})

print("=" * 60)
print("定量测量最小测试 Minimal Quant Test")
print(f"  仅执行: 拾取定量管 -> quantity_run_sample -> 读取结果")
print(f"  定量管位置: {quantification_tube_loc[0]} Col{quantification_tube_loc[1]}")
print("=" * 60)

concentration_list = []

# Step 1: 拾取定量管
print(f"\n[Step 1] 拾取定量管: {quantification_tube_loc[0]}, Col {quantification_tube_loc[1]}")
p8_load_quantification_tube({"Position": quantification_tube_loc[0], "Row": 1, "Col": quantification_tube_loc[1], "Tips":8})
print("  [OK] 定量管已拾取")

# Step 2: 执行定量
print(f"\n[Step 2] 执行 quantity_run_sample ...")
quantity_error = False
try:
	spx_quantity_result = quantity_run_sample({
		"Name": "",
		"SampleType": "dsDNA_HS",
		"ProductType": sample_stage,
		"StandardToSampleRatio": 5,
		"DilutionRatio": 1,
		"Label": "",
		"DilutionAssessment": 60
	})
	print(f"  返回类型: {type(spx_quantity_result)}")
	print(f"  返回值: {spx_quantity_result}")
except Exception as e:
	print(f"  [ERROR] quantity_run_sample 异常: {e}")
	quantity_error = True

# Step 3: 逐channel读取浓度
print(f"\n[Step 3] 逐channel读取浓度:")
for j in range(1, 9):
	well = chr(ord('A') + j - 1)
	conc = get_concentration_modified((quantification_tube_loc[0], quantification_tube_loc[1], j))
	concentration_list.append(conc)
	status = f"{conc:.4f} ng/uL" if conc is not None else "None (无数据)"
	print(f"  {well}1 (Channel {j}): {status}")

# Step 4: 放回定量管
print(f"\n[Step 4] 放回定量管: {quantification_tube_loc[0]}, Col {quantification_tube_loc[1]}")
p8_unload_quantification_tube({"Position": quantification_tube_loc[0], "Row": 1, "Col": quantification_tube_loc[1], "Tips":8})
print("  [OK] 定量管已放回")

# Step 5: 导出定量报告
file_path = f"D:\\data\\PTseq_Library.xlsx"
print(f"\n[Step 5] 导出定量报告到: {file_path}")
try:
	output_quantitative_data({"ProductType": sample_stage, "FilePath": file_path})
	print(f"  [OK] 报告已生成，请到 D:\\data\\PTseq_Library.xlsx 查看")
except Exception as e:
	print(f"  [ERROR] 导出报告失败: {e}")

'''========================== 结果总结 =========================='''
print("\n" + "=" * 60)
print("结果总结 Result Summary")
print("=" * 60)

valid_count = sum(1 for c in concentration_list if c is not None)
none_count = sum(1 for c in concentration_list if c is None)
print(f"  有效读数: {valid_count} / 8")
print(f"  空channel: {none_count} / 8")

if valid_count > 0:
	valid_concs = [c for c in concentration_list if c is not None]
	print(f"  浓度范围: {min(valid_concs):.4f} - {max(valid_concs):.4f} ng/uL")
	print(f"  平均浓度: {sum(valid_concs)/len(valid_concs):.4f} ng/uL")

print(f"\n  quantity_run_sample: {'ERROR' if quantity_error else 'OK'}")
print(f"  浓度读取: {valid_count}/8 valid, {none_count}/8 empty")
print("=" * 60)

if lang==1:
	report({"Phase": "定量测试", "Step": "测试完成", "TaskType": "library", "RemainingTime": None})
elif lang==2:
	report({"Phase": "Quant Test", "Step": "Test complete", "TaskType": "library", "RemainingTime": None})

home()
