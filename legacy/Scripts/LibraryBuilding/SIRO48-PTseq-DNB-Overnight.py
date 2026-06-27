# -*- coding: utf-8 -*-
#####################################################################
# SIRO48-PTseq-DNB-Overnight
#####################################################################
# DNB过夜后恢复操作：打开PCR门和盖板，停止温控，停止PCR方法
# 用于第二天取出DNB产物前执行
#####################################################################
from library import *
spxsiro = globals().get("library")
set_siro(spxsiro)
import math
"""
不要修改HEAD
"""

pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0}) #PCR盖板

temp_stop({"Name":"M2_tempB"})
temp_stop({"Name":"M2_tempC"})
pcr_stop_method()
