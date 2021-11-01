import usb.core
import usb.util
import sys

dev = usb.core.find(find_all=True)

# get next item from the generator
dev = usb.core.find(find_all=True)
# loop through devices, printing vendor and product ids in decimal and hex
for cfg in dev:
    sys.stdout.write('Decimal VendorID=' + str(cfg.idVendor) + ' & ProductID=' + str(cfg.idProduct)+ '\n')
    sys.stdout.write(str(cfg.port_number))
    sys.stdout.write('Hexadecimal VendorID=' + hex(cfg.idVendor) + ' & ProductID=' + hex(cfg.idProduct) + '\n\n')
    #print(str(cfg.port_number))
    #try:
    #    print(str(cfg.manufacturer))
    #except:
    #    print("oops")


# Decimal VendorID=3405 & ProductID=59
# 2Hexadecimal VendorID=0xd4d & ProductID=0x3b


# find our device
dev_laser = usb.core.find(idVendor=0xd4d, idProduct=0x3b)

# was it found?
if dev_laser is None:
    raise ValueError('Laser not found')

# set the active configuration. With no arguments, the first
# configuration will be the active one
dev_laser.set_configuration()

# get an endpoint instance
cfg = dev_laser.get_active_configuration()
intf = cfg[(0,0)]







#laser has product id 59