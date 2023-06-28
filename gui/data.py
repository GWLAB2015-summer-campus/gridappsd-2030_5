__all__ = [
    "get_end_device_list",
    "get_end_device",
    "update_end_device_list"
]

import collections
from pathlib import Path
from typing import Dict, Mapping
import ieee_2030_5.models as m
from ieee_2030_5.client import AdminClient
import config

admin_client = AdminClient(
                server_hostname=config.HOST_2030_5,
                server_ssl_port=config.PORT,
                cafile=Path(config.CA_CERT).expanduser(),
                certfile=Path(config.ADMIN_CERT).expanduser(),
                keyfile=Path(config.ADMIN_KEY).expanduser()
            )


def get_end_device_list() -> m.EndDeviceList:
    return __end_device_list

def get_end_device(index: int) -> m.EndDevice:
    return __end_device_list.EndDevice[index]

def update_end_device_list() -> None:
    global __end_device_list
    __end_device_list = admin_client.get_enddevice_list()
    
def update_ders_by_end_device() -> Dict[int, m.DERList]:
    global __ders_by_end_device
    
    for index, end_device in enumerate(__end_device_list.EndDevice):
        __ders_by_end_device[index] = admin_client.get_der_list(index)

def update_der_program_list() -> m.DERProgramList:
    global __der_program_list__
    admin_client.get_der_program_list()
        
def get_der_program_list(end_device_index: int, der_index: int) -> m.DERProgramList:
    pass
    
def add_der_control(der_control: m.DERControl) -> None:
    global __derc_by_der__
    __derc_by_der__[EndDeviceDerIndex(der_control.endDeviceIndex, der_control.derIndex)] = der_control
    
def get_usage_point_list() -> m.UsagePointList:
    return __usage_point_list__
       
# End devices in the system
__end_device_list: m.EndDeviceList = None
update_end_device_list()
# DERS exposed by each end device
__ders_by_end_device: Dict[int, m.DERList] = {}
update_ders_by_end_device()

# An immuntable index that can be used to hold both the end device index and the DER index.
EndDeviceDerIndex = collections.namedtuple("EndDeviceDerIndex", ["end_device_index", "der_index"])

# DERControl for each DER
__derc_by_der__: Dict[EndDeviceDerIndex, m.DERControl] = {}
# DERControl active for each DER
__derca_by_der__: Dict[EndDeviceDerIndex, m.DERControlBase] = {}
# DefaultDERControl active for each DER
__dderc_by_der__: Dict[EndDeviceDerIndex, m.DefaultDERControl] = {}

__der_program_list__: m.DERProgramList = update_der_program_list()

__usage_point_list__: m.UsagePointList = None
def update_usage_point_list():
    global __update_point_list__
    __update_point_list__ = admin_client.get_usage_point_list()
    
update_usage_point_list()

if __name__ == '__main__':
    #print("usage points", get_usage_point_list())
    print("mirror usage points", admin_client.get_mirror_usage_point_list())
    print("Usage point list", admin_client.get_usage_point_list())
    