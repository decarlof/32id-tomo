from epics import PV
import time

file_path = '/local/data/DMagic/2019-07/Zhu/tiff_serie_1'
exposure = 3.9
sleep_min = 5/60
sample_x_in = 0.0
sample_x_out = 0.5
sample_z_in = 0.0
sample_z_out = 0.0
sample_rot_in = 0.0
sample_rot_out = 0.0

##################################################
# PV list:
Motor_Sample_Top_X = PV('32idcTXM:mcs:c3:m7.VAL')
Motor_Sample_Top_Z = PV('32idcTXM:mcs:c3:m8.VAL')
Motor_SampleRot = PV('32idcTXM:ens:c1:m1.VAL')
Trigger = PV('32idcTXM:shutCam:go')
manual_trigger = PV('32idcTXM:shutCam:Triggered') # 0 = manual, 1 = triggered
CCD_acqu = PV('32idcPG3:cam1:Acquire')
CCD_mode = PV('32idcPG3:cam1:ImageMode')
CCD_trigger_mode = PV('32idcPG3:cam1:TriggerMode')
nIm = PV('32idcPG3:cam1:NumImages')
enable_low_dose = PV('32idcTXM:st1:AllTrigEnable')
shutter_control = PV('32idcTXM:shutCam:ShutterCtrl') # 0 = manual, 1 = auto
exposure_shutter = PV('32idcTXM:shutCam:tExpose')
path_pv = PV('32idcPG3:TIFF1:FilePath')
file_name_pv = PV('32idcPG3:TIFF1:FileName')
next_file_pv = PV('32idcPG3:TIFF1:FileNumber')
start_tiff_capture_pv = PV('32idcPG3:TIFF1:Capture')
###################################################


# Start scan:
#############
exposure_shutter.put(exposure, wait=True)
enable_low_dose.put(1, wait = True)
#manual_trigger.put(0, wait=True)
#shutter_control.put(1, wait=True)
#CCD_acqu.put(0, wait=True) # stop acq
#CCD_trigger_mode.put(1, wait=True)
#nIm.put(1000000)
#CCD_mode.put(1, wait=True) # Multiple
#time.sleep(1)
#CCD_acqu.put(1, wait=True) # start acq
path_pv.put(file_path, wait = True) 
start_tiff_capture_pv.put(1, wait = True)
time.sleep(2)

cpt = 0
while 1:
    # ACQUIRING THE FLAT:
    # move sample out:
    print('--> proj # %i' % cpt)

    # change tiff file name for flat:
    file_name_pv.put('flat', wait = True)
    next_file_pv.put(cpt)

    print('*** Move sample out')
    Motor_Sample_Top_Z.put(sample_z_out, wait = True)
    Motor_SampleRot.put(sample_rot_out, wait = True)
    Motor_Sample_Top_X.put(sample_x_out, wait = True)
    time.sleep(exposure+1)
    # Trigger the CCD to acquire a flat:
#    print('*** Acquiring the flat')
#    Trigger.put(1, wait=True)
    
    # ACQUIRING THE PROJ:
    # move sample in:
    print(' ')
    # change tiff file name for proj:
    file_name_pv.put('proj', wait = True)
    next_file_pv.put(cpt)

    print('*** Move sample in')
    Motor_Sample_Top_Z.put(sample_z_in, wait = True)
    Motor_SampleRot.put(sample_rot_in, wait = True)
    Motor_Sample_Top_X.put(sample_x_in, wait = True)
    time.sleep(exposure+1)

    # Trigger the CCD to acquire a flat:
#    print('*** Acquiring the proj')
#    Trigger.put(1, wait=True)

    cpt = cpt + 1
    time.sleep(sleep_min * 60) # pause in min
    print('*** Waiting for %i minutes' % sleep_min)
    print(' ')
    
    