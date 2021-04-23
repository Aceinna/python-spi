import time
import random
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error import RPi.GPIO!")


class aceinna_gpio(): 
    '''
    for Raspberry cannot supply full power for 305D, so gpio pin can only suply 3.3v, i need another chip to control 5-32V power supply
    the chip can accept 0/3.3v input contrl, still under preparation.
    so self.enabled set to faulse firstly.
    '''
    def __init__(self, pwr_pin = 4, use_gpio = False):
        self.power_pin = pwr_pin # positve of power pin 
        self.gpio_setting()
        self.enabled = use_gpio # only if enabled, it will power on and off by gpio automaticaly.  default will not use auto-power, need manual power on and off

    def gpio_setting(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.power_pin,GPIO.OUT)
        GPIO.output(self.power_pin,GPIO.HIGH) # used as power positive line  in Pi3 board 


    def power_on(self, prt=True):
        GPIO.output(self.power_pin,GPIO.HIGH) 
        if prt:
            print('power on now of pin_BCM: ', self.power_pin)

    def power_off(self, prt=True):    
        GPIO.output(self.power_pin,GPIO.LOW) 
        if prt:
            print('power off now of pin_BCM: ', self.power_pin)
    
    def mkpwm(self, lw_time, hi_time):
        while True:
            GPIO.output(self.power_pin,GPIO.LOW) 
            time.sleep(lw_time)
            GPIO.output(self.power_pin,GPIO.HIGH) 
            time.sleep(hi_time)

if __name__ == "__main__":
    a = aceinna_gpio(use_gpio=True)
    # freq = 1000
    # dl_time = 1/1000 # make 1k hz pwm
    # a.mkpwm(dl_time/2, dl_time/2)
    dl_time = 0.00038 # 0.00038--1k; 0.00015--2k hz; 0.000075--3k hz; 0.000035--4k hz; 0.000012--5k hz; 0.000002--5.5k hz;
    while True:
        # dl_time = random.uniform(0, 0.001) # create one float data between [0,1] randomly
        a.power_off(prt=False)
        time.sleep(dl_time)
        a.power_on(prt=False)
        time.sleep(dl_time)
