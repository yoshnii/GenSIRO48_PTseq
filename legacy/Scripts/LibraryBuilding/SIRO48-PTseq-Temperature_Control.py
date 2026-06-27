# -*- coding: utf-8 -*-
#####################################################################
# SIRO48-PTseq-Temperature_Control
#####################################################################
# 开启温控：M2_tempB (POS17试剂区) 和 M2_tempC (POS20 PCR区) 设为6°C
# 用于DNB过夜保存前开启温控
#####################################################################
from library import *
spxsiro = globals().get("library")
set_siro(spxsiro)
import math

def blockA():
	temp_set({"Name":"M2_tempB","Temp": 6.00, "Duration": -1})
	temp_set({"Name":"M2_tempC","Temp": 6.00, "Duration": -1})
a = parallel_block(blockA)
