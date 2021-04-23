'''
SPI testing script
entry of main func
v1.0 20210423 erkuo chen
'''



import os
import sys
import time
import traceback
import json

from dev_spi import *
from test_case_spi import *
from gpio import aceinna_gpio

def main(dev_type = 'OPEN300ZI', bcm_pin_list = [], com_type = 'SPI'): 
    start_time = time.time()   
    loc_time = '_'.join([str(x) for x in list(time.localtime())])
    with open('spi_attribute_' + dev_type + '.json') as json_data:
        dev_attribute = json.load(json_data)
    debug_main = True if dev_attribute['debug_mode'].upper() == 'TRUE' else False

    gpio_list = []
    bcm_pin_list.sort()
    for pin in bcm_pin_list: # created gpio instance based on pins, sorted the list firstly
        exec(f'gpio_{pin}=aceinna_gpio(pwr_pin = {pin})') # sequence is correspond to sequency indev_nodes.
        exec(f'gpio_list.append(gpio_{pin})')  

    dev = device_spi(attribute_json=dev_attribute,debug_mode=False, power_gpio=gpio_list[0],devtype=dev_type)




    # testitems = dev_attribute['test_items'] # testitems = ['3.6']    

    print(f'start testing device_src:{dev_type} device_sn:{dev.sn}')
    if debug_main: eval('input([k, i, j, m])', {'k':sys._getframe().f_code.co_name,'i':hex(i.sn_can), 'j':hex(i.src), 'm':'press enter:'})
    if  os.path.exists(os.path.join(os.getcwd(), 'data')) == False:
        os.mkdir(os.path.join(os.getcwd(), 'data'))
    test_file = my_csv(os.path.join(os.getcwd(), 'data','CAN-testing_result_{0:#X}_{1:#X}_{2}_FW{3}_{4}.csv'.format(i.src, i.sn_can, i.type_name, dev_attribute['predefine']['fwnum'], loc_time)))
    main_test = aceinna_test_case(test_file, debug_mode = debug_main)
    main_test.set_test_dev(i, fwnum=int(dev_attribute['predefine']['fwnum'], 16))  # need to be updated for each testing ----------input: 1        
    main_test.run_test_case(test_item = testitems, start_idx = dev_attribute['start_idx']) # do single/multi items test in testitems list if needed
    print(f'testing finished, {time.time()-start_time} seconds used')
    
    return True

if __name__ == "__main__":
    input('will start main(), press Enter:')
    try:
        print(time.time())
        # main(debug_main = False, dev_type = 'MTLT335')  # open debug mode
        main(dev_type = 'OPEN300ZI', bcm_pin_list=[4], com_type='SPI')  # dev_type of actual UUT need to be assigned, used for JSON_FILE_NAME AND DEVICE JUDGE. different with type in json.
    except Exception as e:
        print(e)
        traceback.print_exc()
  
    