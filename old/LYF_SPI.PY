'''
OpenIMU SPI package version 0.0.1.
-pip install spidev3.4, 
-read package through SPI interface, OpenIMU330BI test on Pi3 board(Raspbian OS,Raspberry 3B+).
-Spi slave: OpenIMU 330 EVK
-Pins connection:
    Pi3                   330evk
	miso        <==>      miso
	mosi        <==>      mosi
	sck         <==>      sck
	gpio(bcm4)  <==>      cs
    gpio(bcm17) <==>      drdy
	gnd         <==>      gnd
'''

import os
import sys
import spidev
import time
import struct
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error import RPi.GPIO!")

spi = spidev.SpiDev()
cs_channel = 4
interrupt_channel = 17


class SpiOpenIMU:
    def __init__(self):
        self.burst_cmd_ahrs = 0x3f #11*2 bytes
        self.burst_cmd_std = 0x3e #8*2 bytes

    def gpio_setting(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(cs_channel,GPIO.OUT)
        GPIO.output(cs_channel,GPIO.HIGH) # used as CS line replace CS0 default in Pi3 board
        GPIO.setup(interrupt_channel,GPIO.IN) # channel used as IMU data ready detection
        GPIO.add_event_detect(interrupt_channel,GPIO.FALLING)
        return True

    def spidev_setting(self):
        bus = 0    #supporyed values:0,1
        device = 1   #supported values:0,1   default: 0
        spi.open(bus,device)    #connect to the device. /dev/spidev<bus>.<device>
        spi.max_speed_hz = 1000000
        spi.mode = 0b11
        #spi.bits_per_word = 0
        #spi.cshigh #default CS0 in pi3 board
        #spi.lsbfirst = False
        #spi.threewire = 0
        return True

    def check_settings(self):
        print(spi.mode)
        print(spi.threewire)
        print(spi.cshigh)
        print(spi.bits_per_word)
        print(spi.lsbfirst)
        return True

    def combine_reg(self,lsb,msb):
        lsb = struct.pack('B',lsb)
        msb = struct.pack('B',msb)
        return struct.unpack('h',msb+lsb)[0]

if __name__ == "__main__":
    openimu_spi = SpiOpenIMU()
    openimu_spi.gpio_setting()
    openimu_spi.spidev_setting()
    openimu_spi.check_settings()

    # polling mode reading spi interface, with drdy pin detection
    try:
        while True:
            # time.sleep(0.1)
            GPIO.output(cs_channel,GPIO.HIGH)
            if GPIO.event_detected(interrupt_channel):
            # if True:
                # time.sleep(0.02)
                GPIO.output(cs_channel,GPIO.LOW)
                # xfer2([value],speed_hz,delay_usec_cs), SPI bi-direction data transfer.
                # default 8 bits mode, if speed_hz set to zero means the maximun supported SPI clock.
                # delay_usec_cs is the cs hold delay
                resp = spi.xfer2([openimu_spi.burst_cmd_std,0x00,0x00,0x00,0x00,0x00,0x00,
                        0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],0,10)
                GPIO.output(cs_channel,GPIO.HIGH)
                #unit:degree per second
                x_rate = openimu_spi.combine_reg(resp[4],resp[5])/200
                y_rate = openimu_spi.combine_reg(resp[6],resp[7])/200
                z_rate = openimu_spi.combine_reg(resp[8],resp[8])/200
                #unit:mg
                x_acc = openimu_spi.combine_reg(resp[10],resp[11])/4
                y_acc = openimu_spi.combine_reg(resp[12],resp[13])/4
                z_acc = openimu_spi.combine_reg(resp[14],resp[15])/4
                print('g/a',x_rate,y_rate,z_rate,x_acc,y_acc,z_acc)

    except KeyboardInterrupt:
        GPIO.cleanup()
        spi.close()