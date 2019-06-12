'''
	FlyScan for Sector 32 ID C

'''
import sys
import json
import time
from epics import PV
import h5py
import shutil
import os
import imp
import traceback

from tomo_scan_lib import *

variableDict = {
                'IOC_Prefix': '32idcPG3:',
                'FileWriteMode': 'Stream'
                }


global_PVs = {}
init_general_PVs(global_PVs, variableDict)

###### Beam Stop
def Beam_Stop_In():
    global_PVs['beam_stop_y'].put(0, wait=True)

def Beam_Stop_Out():
    global_PVs['beam_stop_y'].put(5, wait=True)

###### Condenser
def Condenser_In():
# Zeiss condenser:
    global_PVs['condenser_x'].put(0) # capillary --> -13.05 compared to BSC
    global_PVs['condenser_y'].put(0) # capillary --> ?? compared to BSC

def Condenser_Out():
    global_PVs['condenser_y'].put(10)       # Capillary and High Energy BSC
#    global_PVs['condenser_y'].put(-13)       # BSC

###### Pinhole
def Pinhole_In():
    global_PVs['pin_hole_y'].put(0)

def Pinhole_Out():
    global_PVs['pin_hole_y'].put(5)

###### Zone plate
def Zone_Plate_In():
## 50 nm ZP:
    global_PVs['zone_plate_y'].put(0.0000)
# 60 nm ZP:
#    global_PVs['zone_plate_x'].put(-7.5)
#    global_PVs['zone_plate_y'].put(0.055)
# 16 nm ZP:
#    global_PVs['zone_plate_x'].put(-3.684300)
#    global_PVs['zone_plate_y'].put(0.0000)
# 40 nm ZP:
#    global_PVs['zone_plate_x'].put(0)
#    global_PVs['zone_plate_y'].put(0)
    pass

def Zone_Plate_Out():
## 50 nm ZP:
    global_PVs['zone_plate_x'].put(0.0)
    global_PVs['zone_plate_y'].put(4.6)
# 60 nm ZP:
#    global_PVs['zone_plate_x'].put(-7.5)
#    global_PVs['zone_plate_y'].put(5.0)
# 16 nm ZP:
#    global_PVs['zone_plate_x'].put(-3.684300)
#    global_PVs['zone_plate_y'].put(4.415)
## 40 nm ZP:
#    global_PVs['zone_plate_x'].put()
#    global_PVs['zone_plate_y'].put()
    pass

###### diffuser:
def Diffuser_In():
#    pv.diffuser_x.put(-6.2)
#    global_PVs['diffuser_x'].put(0) # foam diffuser
    global_PVs['diffuser_x'].put(16) # nylon diffuser

def Diffuser_Out():
    global_PVs['diffuser_x'].put(7)

###### CRL's:
def crl_out():
    global_PVs['crl_actuators_0'].put(0, wait=True, timeout=1)
    global_PVs['crl_actuators_1'].put(0, wait=True, timeout=1)
    global_PVs['crl_actuators_2'].put(0, wait=True, timeout=1)
    global_PVs['crl_actuators_3'].put(0, wait=True, timeout=1)
    global_PVs['crl_actuators_4'].put(0, wait=True, timeout=1)
    global_PVs['crl_actuators_5'].put(0, wait=True, timeout=1)
    global_PVs['crl_actuators_6'].put(0, wait=True, timeout=1)
    global_PVs['crl_actuators_7'].put(0, wait=True, timeout=1)

def crl_in():
#    global_PVs['crl_actuators_0'].put(1, wait=True, timeout=1)
    global_PVs['crl_actuators_1'].put(1, wait=True, timeout=1)
    global_PVs['crl_actuators_2'].put(1, wait=True, timeout=1)
    #global_PVs['crl_actuators_3'].put(1, wait=True, timeout=1)
    global_PVs['crl_actuators_4'].put(1, wait=True, timeout=1)
#    global_PVs['crl_actuators_5'].put(1, wait=True, timeout=1)
#    global_PVs['crl_actuators_6'].put(1, wait=True, timeout=1)
#    global_PVs['crl_actuators_7'].put(1, wait=True, timeout=1)

def change_ccd_exposure_in():
    exposure = 1
    global_PVs['Cam1_SoftwareTrigger'].put(0, wait=True)
    time.sleep(0.5)
    global_PVs['Cam1_FrameRateOnOff'].put(0, wait=True, timeout=1) # turn off
    global_PVs['Cam1_AcquireTime'].put(exposure, wait=True, timeout=1)
    time.sleep(0.5)
    global_PVs['Cam1_AcquireTime'].put(exposure, wait=True, timeout=1) # Do it twice to force the acqu period without going back to frame_rate_enable on
    #pv.ccd_acquire_period.put(exposure, wait=True, timeout=1)

    global_PVs['Cam1_ImageMode'].put(2, wait=True, timeout=1) # continuous
    time.sleep(1)
    global_PVs['Cam1_SoftwareTrigger'].put(1, wait=True, timeout=1)
    time.sleep(1.5)

def change_ccd_exposure_out():
    exposure = 0.005
    acquire_period = 0.2
    global_PVs['Cam1_SoftwareTrigger'].put(0, wait=True)
    global_PVs['Cam1_FrameRateOnOff'].put(1, wait=True)
    global_PVs['Cam1_AcquireTime'].put(exposure, wait=True, timeout=1)
    global_PVs['Cam1_AcquirePeriod'].put(acquire_period, wait=True, timeout=1)
    global_PVs['Cam1_ImageMode'].put(2, wait=True, timeout=1) # continuous
    time.sleep(2)
    global_PVs['Cam1_SoftwareTrigger'].put(1, wait=True, timeout=1)

def change_rot_speed():
    rot_speed = 40.0
    global_PVs['Motor_SampleRot_Speed'].put(rot_speed, wait=True, timeout=1)

#############################
#############################
def All_In():
    
    crl_in()
#    global_PVs['BPM_vert_readback'].put(-1.4) # @ 7.7 keV CRL 0,4,5
#    global_PVs['BPM_horiz_readback'].put(3.8) # @ 7.7 keV CRL 0,4,5
    global_PVs['BPM_vert_readback'].put(-2.0) # @ 8 keV CRL 1,2,4
    global_PVs['BPM_horiz_readback'].put(5.0) # @ 8 keV CRL 1,2,4
#    global_PVs['BPM_vert_readback'].put(-1.6) # @ 8.3 keV CRL 0,1,4,5
#    global_PVs['BPM_horiz_readback'].put(3.9) # @ 8.3 keV CRL 0,1,4,5
#    global_PVs['BPM_vert_readback'].put(-2.0) # @ 8.5 keV CRL 1,4,5
#    global_PVs['BPM_horiz_readback'].put(3.5) # @ 8.5 keV CRL 1,4,5
#    global_PVs['BPM_vert_readback'].put(-2.0) # @ 9.1 keV CRL 1,4,5
#    global_PVs['BPM_horiz_readback'].put(3.7) # @ 9.1 keV CRL 1,4,5
#    global_PVs['BPM_vert_readback'].put(1.0) # @ 11.2 keV CRL 1,4,5
#    global_PVs['BPM_horiz_readback'].put(5.5) # @ 11.2 keV CRL 1,2,3,4,5
    
    Beam_Stop_In()
    Condenser_In()
    Pinhole_In()
#    Zone_Plate_In() # it is better not moving the ZP if possible
    Diffuser_In()
    change_rot_speed()
    global_PVs['BPM_DCM_Vert_FBL'].put(1, wait=True, timeout=1) # Turn ON DCM / BMP vertical feedback
    global_PVs['BPM_DCM_Horiz_FBL'].put(1, wait=True, timeout=1) # Turn ON DCM / BMP horizontal feedback

    # CCD management:
    if 1:
        change_ccd_exposure_in()
        global_PVs['Cam1_TriggerMode'].put(0, wait=True, timeout=1)
        global_PVs['Cam1_FrameRateOnOff'].put(0)
    else:
        global_PVs['Cam1_AcquireTime'].put(1, wait=True, timeout=1)
        global_PVs['Cam1_AcquirePeriod'].put(1, wait=True, timeout=1)
        
    global_PVs['Cam1_FF_norm'].put(0, wait=True, timeout=1)
    global_PVs['Cam1_Trans_Port'].put('PROC1')
    global_PVs['Cam1_OverLay_Port'].put('TRANS1')
    global_PVs['Cam1_Image1_Port'].put('OVER1')


def All_Out():

    crl_out()
#    global_PVs['BPM_vert_readback'].put(-2.0) # 6.53 keV
#    global_PVs['BPM_horiz_readback'].put(4.2) # 6.53 keV
#    global_PVs['BPM_vert_readback'].put(1.0) # 8 keV
#    global_PVs['BPM_horiz_readback'].put(7.5) # 8 keV
#    global_PVs['BPM_vert_readback'].put(-1.7) # 8.3 keV
#    global_PVs['BPM_horiz_readback'].put(4.2) # 8.3 keV
#    global_PVs['BPM_vert_readback'].put(0.7) # 8.5 keV
#    global_PVs['BPM_horiz_readback'].put(5.7) # 8.5 keV
#    global_PVs['BPM_vert_readback'].put(0.5) # 9.1 keV
#    global_PVs['BPM_horiz_readback'].put(5.0) # 9.1 keV
    global_PVs['BPM_vert_readback'].put(-0.9) # 11.2 keV
    global_PVs['BPM_horiz_readback'].put(6.3) # 11.2 keV

    global_PVs['Cam1_TriggerMode'].put(0, wait=True, timeout=1)
    global_PVs['Cam1_FF_norm'].put(0, wait=True, timeout=1)
    wait_pv(global_PVs['Cam1_FF_norm'], 0, max_timeout_sec=3)
    Beam_Stop_Out()
    Condenser_Out()
    Pinhole_Out()
    change_rot_speed()
#    Zone_Plate_Out()
    #Zone_Plate_2_Out()
    Diffuser_Out()
#    pv.fast_shutter.put(1, wait=True)
    global_PVs['Cam1_Recursive_Filter'].put(0, wait=True, timeout=1)

    # CCD management:
    if 1:
        change_ccd_exposure_out()
        global_PVs['Cam1_TriggerMode'].put(0, wait=True, timeout=1)
    else:
        pv.ccd_dwell_time.put(0.005, wait=True, timeout=1)
        global_PVs['Cam1_AcquirePeriod'].put(0.2, wait=True, timeout=1)

    global_PVs['Cam1_FF_norm'].put(0, wait=True, timeout=1)
    global_PVs['Cam1_Trans_Port'].put('PROC1')
    global_PVs['Cam1_OverLay_Port'].put('PROC1')
    global_PVs['Cam1_Image1_Port'].put('OVER1')
    time.sleep(1)

#############################
#############################


if __name__ == '__main__': # FOR THE OLD CODE
    eval(sys.argv[1])

