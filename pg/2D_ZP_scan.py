from epics import PV
import numpy as np
import time

# INPUT-----------------------------
X_start = -0.000030; X_end = 0.000035
Y_start = -0.000030; Y_end = 0.000035
step = 0.000005 # mm
X_start = -0.000030; X_end = 0.000035
Y_start = -0.000030; Y_end = 0.000040
step = 0.000010 # mm
exposure = 2 # s
#-----------------------------------


FrameTypeData = 0
FrameTypeDark = 1
FrameTypeWhite = 2
DetectorIdle = 0
DetectorAcquire = 1
EPSILON = 0.1

# PV names:
FrameType = PV('32idcPG3:cam1:FrameType')
SoftwareTrigger = PV('32idcPG3:cam1:SoftwareTrigger')
NumImages = PV('32idcPG3:cam1:NumImages')
ImageMode = PV('32idcPG3:cam1:ImageMode')
AcquireTime = PV('32idcPG3:cam1:AcquireTime')
AcquirePeriod = PV('32idcPG3:cam1:AcquirePeriod')
Acquire = PV('32idcPG3:cam1:Acquire')
FrameType = PV('32idcPG3:cam1:FrameType')
HDF1_Capture = PV('32idcPG3:HDF1:Capture')
HDF1_NumCapture = PV('32idcPG3:HDF1:NumCapture')

Motor_Sample_Top_X = PV('32idcTXM:mcs:c3:m7.VAL')
Motor_Sample_Top_Z = PV('32idcTXM:mcs:c3:m8.VAL')
Motor_SampleRot = PV('32idcTXM:ens:c1:m1.VAL')

ZP_2_x = PV('32idcTXM:mcs:c0:m3.VAL')
ZP_2_y = PV('32idcTXM:mcs:c0:m1.VAL')

Fly_Taxi = PV('32idcTXM:PSOFly3:taxi')
Fly_Run = PV('32idcTXM:PSOFly3:fly')
#####################################################

def wait_pv(pv, wait_val, max_timeout_sec=-1):
	print 'wait_pv(', pv.pvname, wait_val, max_timeout_sec, ')'
	#delay for pv to change
	time.sleep(.01)
	startTime = time.time()
	while(True):
		pv_val = pv.get()
		if type(pv_val) == float:
			if abs(pv_val - wait_val) < EPSILON:
				return True
		if (pv_val != wait_val):
			if max_timeout_sec > -1:
				curTime = time.time()
				diffTime = curTime - startTime
				if diffTime >= max_timeout_sec:
					print 'wait_pv(', pv.pvname, wait_val, max_timeout_sec, ') reached max timeout. Return False'
					return False
			time.sleep(.01)
		else:
			return True

X_vect = np.arange(X_start, X_end, step)
Y_vect = np.arange(Y_start, Y_end, step)
nIm = X_vect.shape[0] * Y_vect.shape[0] * 2 # x2 for flat and data

print('\n*** reset # of images')
NumImages.put(nIm, wait=True); time.sleep(1)
print('\n*** Push acquire button')
Acquire.put(1); time.sleep(1) # start acquisition
print('\n*** Push Trigger button')
SoftwareTrigger.put(1, wait=True); time.sleep(1.5)
print('\n*** reset acquire period')
AcquireTime.put(exposure); time.sleep(1)
print('\n*** reset exposure')
AcquirePeriod.put(exposure, wait=True); time.sleep(1)
print('\n*** Push Trigger button again')
SoftwareTrigger.put(1, wait=True); time.sleep(1)
print('\n*** reset # of images')
NumImages.put(nIm, wait=True); time.sleep(1)
print('\n*** Reset number of images to be captured')
HDF1_NumCapture.put(nIm, wait=True); time.sleep(1)
print('\n*** Start hdf capture')
HDF1_Capture.put(1); time.sleep(1) # start capture

print('\n*** Change frame type to data')
FrameType.put(FrameTypeData, wait=True)
print('\n*** Moving sample IN')
Motor_Sample_Top_Z.put(0.0, wait=True); time.sleep(1.0) # move sample out
Motor_SampleRot.put(0.0, wait=True); time.sleep(1.0)

print('\n*** Start scanning the ZP')
for y in(Y_vect):
    ZP_2_y.put(y, wait=True)
    time.sleep(exposure+0.5)
    for x in(X_vect):
        print('ZP position: y = %f, x = %f' % (y, x))
        ZP_2_x.put(x, wait=True)
        time.sleep(exposure+0.5)
        
        # Acquire image:
        SoftwareTrigger.put(1, wait=True)
        #wait_pv(Detector_State_RBV, DetectorIdle, 5)
        time.sleep(exposure+0.5)
        
print('\n*** Change frame type to flat field')
FrameType.put(FrameTypeWhite, wait=True)
print('\n*** Moving sample OUT')
Motor_SampleRot.put(90.0, wait=True); time.sleep(1.0)
Motor_Sample_Top_Z.put(2.0, wait=True); time.sleep(1.0) # move sample out

print('\n*** Start scanning the ZP for Flat-field acqu.')
for y in(Y_vect):
    ZP_2_y.put(y, wait=True)
    time.sleep(exposure)
    for x in(X_vect):
        print('ZP position: y = %f, x = %f' % (y, x))
        ZP_2_x.put(x, wait=True)
        time.sleep(exposure+0.2)

        # Acquire image:
        SoftwareTrigger.put(1, wait=True)
        #wait_pv(Acquire, DetectorIdle, 60)
        time.sleep(exposure+0.5)
