# -*- coding: utf-8 -*-
#####################################################################
# SIRO48-PTseq-Turn_Off_Temperature_Control
#####################################################################
# 关闭温控：停止M2_tempB和M2_tempC
#####################################################################
from library import *
spxsiro = globals().get("library")
set_siro(spxsiro)
import math

def blockT():
	temp_stop({"Name": "M2_tempB"})
	temp_stop({"Name": "M2_tempC"})
t = parallel_block(blockT)
