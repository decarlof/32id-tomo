from epics import PV
import time

shaker_status = PV('32idcMC:shaker:run')
shaking = 1
while shaking:
    shaker_check = shaker_status.get()
    if shaker_check == 0:
        shaker_status.put(1)
    time.sleep(0.2) # checking every 200 ms
    
