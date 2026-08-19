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

pcr_stop_method()
pcr_open_door()
transfer({"StartPosition":"M2_POS20","EndPosition":"M2_POS26","LoosenOffsetOfZ":0}) #PCR盖板

temp_stop({"Name":"M2_tempB"})
temp_stop({"Name":"M2_tempC"})
