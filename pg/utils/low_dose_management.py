
from tomo_scan_lib import *
from epics import PV
import time

global_PVs = {}


enable_button = PV('32idcTXM:st1:AllTrigEnable') # disable = 0, enable = 1
shutter_control = PV('32idcTXM:shutCam:ShutterCtrl') #   0 = manual, 1 = Auto
shutter_manual = PV('32idcTXM:shutCam:ShutterManual') # 0 = closed, 1 = open
shutter_triggered = PV('32idcTXM:shutCam:Triggered') # 0 = manual, 1 = Triggered
start_ccd_acq = PV('32idcPG3:cam1:Acquire')

# disable the low dose mode:
if enable_button.get() == 1:
    print('*** Disabling low dose mode')
    enable_button.put(0, wait=True) # --> disable low dose mode
    shutter_control.put(0, wait=True) # --> switch to manual mode
    shutter_manual.put(1, wait=True) # --> making sure the shutter is open
    start_ccd_acq.put(1, wait=True)

# else, enable the low dose mode:
else:
    print('*** Enabling low dose mode')
    enable_button.put(1, wait=True) # --> enable low dose mode
    shutter_triggered.put(0, wait=True)
    shutter_control.put(1, wait=True) # --> Auto
    
    
    