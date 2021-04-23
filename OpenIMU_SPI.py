'''
OpenIMU SPI package version 0.2.0.
-pip install spidev3.4, 
-read package through SPI interface, OpenIMU330BI test on Pi3 board(Raspbian OS,Raspberry 3B+).
-Spi slave: OpenIMU 330 EVK
-Pins connection:
    Pi3                   330/300 evk
	miso        <==>      miso
	mosi        <==>      mosi
	sck         <==>      sck
<<<<<<< HEAD
	gpio(bcm4)  <==>      cs   black line
    gpio(bcm17) <==>      drdy red line
=======
	gpio(bcm4)  <==>      cs
        gpio(bcm17) <==>      drdy
>>>>>>> e1f00869bd4bbc361b7c7feebb8df015eb43b909
	gnd         <==>      gnd
@cek from Aceinna 2019.11.4
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

class SpiOpenIMU:
    def __init__(self, target_module = "300", fw='0.0', cs_pin = 4, interrupt_pin = 17, drdy_status = False):
        '''
        pin number use the BCM code
        '''        

        self.spi = spidev.SpiDev()
        self.cs_channel = cs_pin
        self.interrupt_channel = interrupt_pin
        self.drdy = drdy_status
        self.gpio_setting()
        self.spidev_setting()
        self.check_settings()
        time.sleep(0.1)

        self.module = target_module
        print("initialize based on: %s, with DRDY_usage: %s" % (self.module, self.drdy))

    def gpio_setting(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.cs_channel,GPIO.OUT)
        GPIO.output(self.cs_channel,GPIO.HIGH) # used as CS line replace CS0 default in Pi3 board        

        if self.drdy:
            GPIO.setup(self.interrupt_channel,GPIO.IN) # channel used as IMU data ready detection
            time.sleep(0.4)
            GPIO.add_event_detect(self.interrupt_channel,GPIO.FALLING)            
        return True

    def single_read(self, target_register):
        if self.drdy and self.module != "300":
            while not GPIO.event_detected(self.interrupt_channel):                
                pass 
        if self.module == "381":
            GPIO.output(self.cs_channel,GPIO.LOW) 
            self.spi.xfer2([target_register,0x00],900000,10)  #return data of 0000
            GPIO.output(self.cs_channel,GPIO.HIGH) 
            time.sleep(0.000010)
            GPIO.output(self.cs_channel,GPIO.LOW) 
            resp_single = self.spi.xfer2([0x00,0x00],900000,10)  #receive the back target data
            GPIO.output(self.cs_channel,GPIO.HIGH)             
            return self.combine_reg(resp_single[0],resp_single[1])
        else:
            GPIO.output(self.cs_channel,GPIO.LOW) 
            resp_single = self.spi.xfer2([target_register,0x00,0x00,0x00],900000,10)         
            GPIO.output(self.cs_channel,GPIO.HIGH)                   
            return self.combine_reg(resp_single[2],resp_single[3])
        
    def single_write(self, target_register, target_data):
        if self.drdy and self.module != "300":
            while not GPIO.event_detected(self.interrupt_channel):                
                pass    
        GPIO.output(self.cs_channel,GPIO.LOW)           
        self.spi.xfer2([target_register | 0x80, target_data],900000,10)  #write data, such as 0xF010, target address is 0x70, and data input is 0x10
        GPIO.output(self.cs_channel,GPIO.HIGH)
        return True 
    
    def burst_read(self, first_register, subregister_num):   
        rate, acc, deg, tmstp = [], [], [], []
        if self.drdy and self.module != "300":  # 300 no drdy now, so only not 300 will go next
            while not GPIO.event_detected(self.interrupt_channel):                
                pass 
        if self.module == "381":
            GPIO.output(self.cs_channel,GPIO.LOW)
            resp = self.spi.xfer2([first_register,0x00],900000,10)
            GPIO.output(self.cs_channel,GPIO.HIGH)
            for i_381 in range(subregister_num):
                time.sleep(0.000010)
                GPIO.output(self.cs_channel,GPIO.LOW)
                resp += self.spi.xfer2([0x00,0x00],900000,10)[:]
                GPIO.output(self.cs_channel,GPIO.HIGH)
            #unit:degree per second
            rate.append(self.combine_reg(resp[4],resp[5])/200)
            rate.append(self.combine_reg(resp[6],resp[7])/200)
            rate.append(self.combine_reg(resp[8],resp[9])/200)
            #unit:mg
            acc.append(self.combine_reg(resp[10],resp[11])/4)
            acc.append(self.combine_reg(resp[12],resp[13])/4)
            acc.append(self.combine_reg(resp[14],resp[15])/4)
        else:     #300,330 is here                   
            GPIO.output(self.cs_channel,GPIO.LOW)
            # xfer2([value],speed_hz,delay_usec_cs), SPI bi-direction data transfer.
            # default 8 bits mode, if speed_hz set to zero means the maximun supported SPI clock.
            # delay_usec_cs is the cs hold delay
            first_register_send = [first_register,0x00]
            for i_else in range(2*subregister_num):
                first_register_send.append(0x00)
            resp = self.spi.xfer2(first_register_send,900000,20)
            GPIO.output(self.cs_channel,GPIO.HIGH)
            #unit:degree per second
            rate.append(self.combine_reg(resp[4],resp[5])/64)
            rate.append(self.combine_reg(resp[6],resp[7])/64)
            rate.append(self.combine_reg(resp[8],resp[9])/64)
            #unit:mg
            acc.append(self.combine_reg(resp[10],resp[11])/4000)
            acc.append(self.combine_reg(resp[12],resp[13])/4000)
            acc.append(self.combine_reg(resp[14],resp[15])/4000)     
            #unit:deg
            if self.module == "330" and first_register == 0x3F:
                deg.append(self.combine_reg(resp[18],resp[19]) * 360/65536)
                deg.append(self.combine_reg(resp[20],resp[21]) * 360/65536)
                deg.append(self.combine_reg(resp[22],resp[23]) * 360/65536)
                return rate, acc, deg   
            if self.module == "330BA" and first_register == 0x3F:
                tmstp.append(self.combine_reg(resp[18],resp[19]) * 1)
                tmstp.append(self.combine_reg(resp[20],resp[21]) * 1)
                return rate, acc, tmstp         
        return rate, acc    

    def spidev_setting(self):
        bus = 0    #supporyed values:0,1
        device = 1   #supported values:0,1   default: 0
        self.spi.open(bus,device)    #connect to the device. /dev/spidev<bus>.<device>
        self.spi.max_speed_hz = 900000
        self.spi.mode = 0b11
        #spi.bits_per_word = 0
        #spi.cshigh #default CS0 in pi3 board
        #spi.lsbfirst = False
        #spi.threewire = 0
        return True

    def check_settings(self):
        print(self.spi.mode)
        print(self.spi.threewire)
        print(self.spi.cshigh)
        print(self.spi.bits_per_word)
        print(self.spi.lsbfirst)
        return True
    def combine_reg(self,msb,lsb):
        msb = struct.pack('B',msb)
        lsb = struct.pack('B',lsb)        
        return struct.unpack('>h',msb+lsb)[0]   #MSB firstly

    def __del__(self):
        GPIO.cleanup()
        self.spi.close()
        
if __name__ == "__main__":       
    openimu_spi = SpiOpenIMU(target_module="330BA",drdy_status=True, fw='26.0.7')   #set the module name and drdy status(enalbe or not)-----------------step: 1
    burst_read, single_read, single_write = True, False, False  # set the read style, burst or single------------step:2
    f = open("data_" + str(openimu_spi.module) + ".txt", "w")
    str_config = "module style:{0}; drdy:{1};   burst read:{2}; single read:{3} \n".format(openimu_spi.module, openimu_spi.drdy, burst_read, single_read)
    print(str_config)
    f.write(str_config) 
    input("Power on IMU !!!!!!!!")
    time.sleep(2)  
    try:        
        if openimu_spi.drdy == False:  # when no drdy, default SPI ODR is 100HZ 
            time.sleep(0.01)
        if single_read:
            read_name = [
                        "X_Rate", "Y_Rate", "Z_Rate", "X_Accel", "Y_Accel", "Z_Accel", "RATE_TEMP", "BOARD_TEMP", "DRDY_RATE", "ACCEL_LPF", "ACCEL_SCALE_FACTOR", "RATE_SCALE_FACTOR", 
                        "SN_1", "SN_2", "SN_3", "PRODUCT_ID", "MASTER_STATUS", "HW_STATUS", "SW_STATUS", "ACCEL_RANGE/RATE_RANGE", 
                        "ORIENTATION_MSB/ORIENTATION_LSB", "SAVE_CONFIG", "RATE_LPF", "HW_VERSION/SW_VERSION"
                        ]
            read_reg = [
                        0x04, 0x06, 0x08, 0x0A, 0x0C, 0x0E, 0x16, 0x18, 0x36, 0x38, 0x46, 0x47, 
                        0x52, 0x54, 0x58, 0x56, 0x5A, 0x5C, 0x5E, 0x70, 0x74, 0x76, 0x78, 0x7E
                        ]  
            for i in zip(read_name, read_reg):                
                read_value = openimu_spi.single_read(i[1])
                str_temp = "{0:_<40s}0x{1:<5X} read value: 0x{2:<10X}\n".format(i[0], i[1], read_value)
                print(str_temp)
                f.write(str_temp) 
            
        if single_write:    
            while input('need write? y/n?') != 'y':
                pass                                
            # write_name = ["ACCEL_RANGE", "RATE_RANGE", "ORIENTATION_MSB", "ORIENTATION_LSB", "RATE_LPF", "save config"] 
            # write_reg = [0x70, 0x71, 0x74, 0x75, 0x78, 0x76]
            # write_data = [0x08, 0x08, 0x00, 0x6B, 0x40, 0x00]
            write_name = ["packet rate", "orimsb", "orilsb", "save config"] 
            write_reg = [0x37, 0x74, 0x75, 0x76]
            write_data = [0x01, 0x00, 0x6B, 0x00]
            for j in zip(write_name, write_reg, write_data):    #start to write registers
                print("write_name:{0:<40s}, write address:0x{1:<5X}, wirte data:0x{2:<5X}".format(j[0], j[1], j[2]))            
                openimu_spi.single_write(j[1], j[2])
                time.sleep(0.5)
        # if single_read or single_write:
        #     break 
        while input('need burst read? y/n?') != 'y':
            pass  
        while burst_read: # not seting the ODR, if you use burst read, it will same with frequency of DRDY            
            if openimu_spi.module == "330" or openimu_spi.module == "330BA":
                # list_rate, list_acc = openimu_spi.burst_read(first_register=0x3E,subregister_num=8)     #input the read register and numbers of subregisters want to read together
                # str_burst = "time:{0:>10f};  gyro:{1:>25s};  accel:{2:>25s} \n".format(
                #     time.clock(), ", ".join([str(x) for x in list_rate]), ", ".join([str(x) for x in list_acc])
                #     )
                list_rate, list_acc, tmstamp = openimu_spi.burst_read(first_register=0x3F,subregister_num=10)     #input the read register and numbers of subregisters want to read together
                str_burst = "time:{0:>10f};  gyro:{1:>50s};  accel:{2:>50s}; timestamp:{3:>25s} \n".format(
                    time.clock(), ", ".join([str(x) for x in list_rate]), ", ".join([str(x) for x in list_acc]), ", ".join([str(x) for x in tmstamp])
                )
                
            else:
                list_rate, list_acc = openimu_spi.burst_read(first_register=0x3E,subregister_num=10)
                str_burst = "time:{0:>10f};  gyro:{1:>25s};  accel:{2:>25s} \n".format(
                    time.clock(), ", ".join([str(x) for x in list_rate]), ", ".join([str(x) for x in list_acc])
                    )
            print(str_burst)               
            f.write(str_burst)
    except KeyboardInterrupt:
        f.close()
        print("stoped by customer!")
        




















    # polling mode reading spi interface, with drdy pin detection
    # try:
    #     while True:
    #         # GPIO.output(cs_channel,GPIO.LOW)
    #         # product_id = spi.xfer2([0x56,0x00,0x00,0x00],0,10)
    #         # GPIO.output(cs_channel,GPIO.HIGH)                     
    #         # print('id',product_id)            
    #         time.sleep(0.1)
            
    #         # if GPIO.event_detected(interrupt_channel):
    #         if True:
    #             time.sleep(0.5)
    #             GPIO.output(cs_channel,GPIO.LOW)
    #             # xfer2([value],speed_hz,delay_usec_cs), SPI bi-direction data transfer.
    #             # default 8 bits mode, if speed_hz set to zero means the maximun supported SPI clock.
    #             # delay_usec_cs is the cs hold delay
    #             resp = spi.xfer2([openimu_spi.burst_cmd_std,0x00,0x00,0x00,0x00,0x00,0x00,
    #                     0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],0,10)
    #             GPIO.output(cs_channel,GPIO.HIGH)
    #             #unit:degree per second
    #             x_rate = openimu_spi.combine_reg(resp[4],resp[5])/200
    #             y_rate = openimu_spi.combine_reg(resp[6],resp[7])/200
    #             z_rate = openimu_spi.combine_reg(resp[8],resp[8])/200
    #             #unit:mg
    #             x_acc = openimu_spi.combine_reg(resp[10],resp[11])/4
    #             y_acc = openimu_spi.combine_reg(resp[12],resp[13])/4
    #             z_acc = openimu_spi.combine_reg(resp[14],resp[15])/4
    #             print('g/a',x_rate,y_rate,z_rate,x_acc,y_acc,z_acc)
            
            
            
    # #write to register
    # time.sleep(0.5)
    # GPIO.output(cs_channel,GPIO.LOW)             
    # resp1 = spi.xfer2([0x80|0x50,0x23],0,10)
    # time.sleep(0.5)
    # GPIO.output(cs_channel,GPIO.HIGH) 

    # 0x56 OPEN300 ID: 0x30(48) 0x00(0) 
    # 0x56 OPEN330 ID: 0x33(48) 0x00(0)
    # 0x56 IMU381 ID:  0X38(56) 0x10(16)  


<<<<<<< HEAD
=======
    except KeyboardInterrupt:
        GPIO.cleanup()
        spi.close()
>>>>>>> e1f00869bd4bbc361b7c7feebb8df015eb43b909
