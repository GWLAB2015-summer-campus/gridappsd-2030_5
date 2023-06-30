import yaml
from pydantic.tools import parse_obj_as
import json
from ieee_2030_5.config import ServerConfiguration

valid_config = """
---
server: full20305
https_port: 8443
tls_repository: "~/tls"
openssl_cnf: "openssl.cnf"
server_mode: enddevices_create_on_start
lfdi_mode: lfdi_mode_from_file
generate_admin_cert: True
log_event_list_poll_rate: 60
device_capability_poll_rate: 60
devices:
  - id: dev1
    deviceCategory: FUEL_CELL
    pin: 111115
    ders:
      - capabilities:
        modesSupported: "1110000000000000"
        type: 83
        program: Program 1

      - capabilities:
        modesSupported: "1110000000000000"
        type: 83
        rtgMaxW: 600
        rtgMaxVA: 600
        rtgNormalCategory: 1
        rtgAbnormalCategory: 1
        rtgMaxVar: 600
        rtgMaxVarNeg: 600
        rtgMaxChargeRateW: 600
        rtgMaxChargeRateVA: 600
        rtgVNom: 120
        rtgMaxV: 128
        rtgMinV: 116

programs:
  - description: Program 1
    default_control: Control 1
    controls:
      - Control 2
      - Control 3
    curves:
      - Curve 1
    primacy: 89

  - description: Program 2
    default_control: Control 3
    primacy: 20
  
controls:
  - description: Control 1
    setESDelay: 30
    base:
      opModConnect: True
      opModMaxLimW: 9500
  - description: Control 2
  - description: Control 3

curves:
  - description: Curve 1
    curveType: opModVoltVar
    CurveData:
      - xvalue: 5
        yvalue: 5

  - description: Curve 2
    curveType: opModFreqWatt
    CurveData:
      - exitation: 10
        xvalue: 5
        yvalue: 5
"""

def test_load_config_properly():
    server_dict = yaml.safe_load(valid_config)
    server_config = parse_obj_as(ServerConfiguration, server_dict)
    
    assert server_dict['server'] == server_config.server
    assert server_dict['https_port'] == server_config.https_port
    assert server_dict['tls_repository'] == server_config.tls_repository
    assert server_dict['openssl_cnf'] == server_config.openssl_cnf
    