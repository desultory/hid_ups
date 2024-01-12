
from hid import enumerate as hid_enumerate
from .cyberpowerups import CyberPowerUPS

HID_DEVICES = {1892: {1537: CyberPowerUPS}}


def get_hid_devices():
    for device in hid_enumerate():
        vendor_id = device['vendor_id']
        product_id = device['product_id']
        if vendor_id in HID_DEVICES and product_id in HID_DEVICES[vendor_id]:
            yield device, HID_DEVICES[vendor_id][product_id]


def get_hid_path_from_serial(serial):
    for device, cls in get_hid_devices():
        if device['serial_number'] == serial:
            return device['path']
    return None

