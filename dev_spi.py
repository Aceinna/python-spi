'''
creat dev UUT based on OpenIMU_SPI.py
record parameters of UUT, do some operations related with HW unit. 
v1.0 20210423 erkuo chen
'''

import os
import sys
import time
import struct
import json
from OpenIMU_SPI import *

class device_spi(): 
    def __init__(self, attribute_json, debug_mode = False, power_gpio = None, devtype=None):
        # self.power_pin = pwr_pin # positve of power pin 
        self.auto_power = power_gpio
        self.dev_type = devtype
        self.sn  = None
        self.default_confi = {}
        self.reg_name = attribute_json["reg_name"]
        self.reg_id = attribute_json["reg_id_str"]
        self.driver =  SpiOpenIMU(target_module="300ZI",drdy_status=True, fw='4.1.2')
        self.debug = debug_mode

        self.update_sn()

    def update_sn(self):
        sn1_idx = self.reg_name.index('SN_1')
        sn2_idx = self.reg_name.index('SN_2')
        sn3_idx = self.reg_name.index('SN_3')
        self.sn = self.driver.single_read(sn1_idx)











