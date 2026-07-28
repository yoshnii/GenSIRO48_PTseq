from library import *
spxsiro = globals().get("library")
set_siro(spxsiro)
import math
def blockA():
	temp_set({"Name":"M2_tempB","Temp": 6.00, "Duration": -1})
	temp_set({"Name":"M2_tempC","Temp": 6.00, "Duration": -1})
a = parallel_block(blockA)