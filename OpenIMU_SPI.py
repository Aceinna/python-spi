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
import numpy
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

    def output_data_burst(self):
        # polling mode reading spi interface, with drdy pin detection
        try:
            while True:
                time.sleep(0.1)
                GPIO.output(cs_channel,GPIO.HIGH)
                if GPIO.event_detected(interrupt_channel):
                    time.sleep(0.1)
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

    def magnetic_align(self):
        try:
            time.sleep(0.1)
            GPIO.output(cs_channel,GPIO.HIGH)
            if GPIO.event_detected(interrupt_channel):
                time.sleep(0.1)
                GPIO.output(cs_channel,GPIO.LOW)
                # start mag align
                # change msb of 0x50 to do write operation
                spi.xfer2([0xd0,0x01])
                # cycle through CS high low before read operations
                GPIO.output(cs_channel,GPIO.HIGH)
                time.sleep(0.02)
                GPIO.output(cs_channel,GPIO.LOW)
                # read value for the unit
                resp = spi.xfer2([0x50,0x00,0x00,0x00,0x00,0x00])
                while resp[4] == 12 :
                    GPIO.output(cs_channel,GPIO.HIGH)
                    time.sleep(0.02)
                    GPIO.output(cs_channel,GPIO.LOW)
                    resp = spi.xfer2([0x50,0x00,0x00,0x00,0x00,0x00])
                    print('Mag align in progress')
                if resp[4] == 13:
                    # Status when mag align is complete
                    GPIO.output(cs_channel,GPIO.HIGH)
                    time.sleep(0.02)
                    GPIO.output(cs_channel,GPIO.LOW)
                    # get mag parameter's values from registers.
                    hardIron_x = spi.xfer2([0x48,0x00,0x00,0x00,0x00,0x00,0x00])
                    GPIO.output(cs_channel,GPIO.HIGH)
                    time.sleep(0.02)
                    GPIO.output(cs_channel,GPIO.LOW)
                    hardIron_y = spi.xfer2([0x4A,0x00,0x00,0x00,0x00,0x00,0x00,0x00])
                    GPIO.output(cs_channel,GPIO.HIGH)
                    time.sleep(0.02)
                    GPIO.output(cs_channel,GPIO.LOW)
                    softIron_angle = spi.xfer2([0x4E,0x00,0x00,0x00,0x00,0x00,0x00])
                    GPIO.output(cs_channel,GPIO.HIGH)
                    time.sleep(0.02)
                    GPIO.output(cs_channel,GPIO.LOW)
                    softIron_ratio = spi.xfer2([0x4C,0x00,0x00,0x00,0x00,0x00,0x00])
                    GPIO.output(cs_channel,GPIO.HIGH)
                    time.sleep(0.02)
                    GPIO.output(cs_channel,GPIO.LOW)

                    print('Hard Iron X:' + str((openimu_spi.combine_reg(hardIron_x[2],hardIron_x[3]) * 20) / 65536 ))
                    print('Hard Iron Y:' + str ((openimu_spi.combine_reg(hardIron_y[2],hardIron_y[3]) * 20) / 65536 ))
                    print('Soft Iron Angle:' + str ((openimu_spi.combine_reg(softIron_angle[2],softIron_angle[3]) * 3.14) / 32767 ))
                    print('Soft Iron Ratio:' + str ((openimu_spi.combine_reg(softIron_ratio[2],softIron_ratio[3]) * 2) / 65536 ))

                    data = input('Accept values?y/n: ')
                    if data == 'y':
                        resp = spi.xfer2([0xd0,0x05])
                        print('values saved')
                    else:
                        return

                GPIO.output(cs_channel,GPIO.HIGH)
                print ('mag algin completed')

        except KeyboardInterrupt:
            GPIO.cleanup()
            spi.close()



if __name__ == "__main__":
    openimu_spi = SpiOpenIMU()
    openimu_spi.gpio_setting()
    openimu_spi.spidev_setting()
    openimu_spi.check_settings()
    # Toggel between mag algin and burst mode
    # openimu_spi.output_data_burst()
    openimu_spi.magnetic_align()
