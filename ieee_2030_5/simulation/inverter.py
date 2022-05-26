from argparse import ArgumentParser
import asyncio
from pathlib import Path
from typing import List, Optional, Dict
from threading import Thread

import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import pvlib
import math

from ieee_2030_5.certs import TLSRepository
from ieee_2030_5.client import IEEE2030_5_Client
from ieee_2030_5.models import MirrorUsagePoint, MirrorMeterReading


def run_inverter(client: IEEE2030_5_Client, capabilities_url: str = "/dcap"):

    cap = client.request_device_capability(capabilities_url)
    mups = client.request_mirror_usage_point_list(url=cap.MirrorUsagePointListLink.href)

    if not mups.results:
        # f"p_ac = {p_ac}, s_ac = {s_ac}, q_ac= {q_ac}, PF = {PF}, v_ac = {v_ac}, i_ac = {i_ac}"
        mup_readings = [MirrorMeterReading("p_ac"),
                        MirrorMeterReading("s_ac"),
                        MirrorMeterReading("q_ac"),
                        MirrorMeterReading("PF"),
                        MirrorMeterReading("v_ac"),
                        MirrorMeterReading("i_ac")]
        mup = MirrorUsagePoint(description=f"Inverter {client.hostname}",
                               status=1,
                               MirrorMeterReading=mup_readings)
        client.post_mirror_usage_point(cap.MirrorUsagePointListLink.href,
                                       mup)
    for pt in mups.results:
        print(pt)

    # PV module
    sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
    module = sandia_modules['Canadian_Solar_CS5P_220M___2009_']
    # Inverter model
    sapm_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
    inverter = sapm_inverters['ABB__MICRO_0_25_I_OUTD_US_208__208V_']
    irradiance = [900, 1000, 925]
    temperature = [25, 28, 20]
    # Assumed constant power factor
    PF = 0.99
    # Assumed constant AC voltage
    v_ac = 120
    latitude = 32
    longitude = -111.0
    weather = pvlib.iotools.get_pvgis_tmy(latitude, longitude, map_variables=True)[0]
    total_solar_radiance = weather['ghi']
    # assumed that the total solar radiance is equal to ghi(global horizontal irradiance)
    outdoor_temp = weather["temp_air"]
    # both the total_solar_radiace and outdoor_temp has 1hr sampling rate.
    # you should be able modify the sampling rate by resampling it
    for x, y in zip(total_solar_radiance, outdoor_temp):
        dc = pvlib.pvsystem.sapm(x, y, module)
        # print(dc)
        p_ac = pvlib.inverter.sandia(dc['v_mp'], dc['p_mp'], inverter)
        s_ac = p_ac / PF
        q_ac = math.sqrt(p_ac**2 + s_ac**2)
        i_ac = (s_ac / v_ac) * 1000

        print(f"p_ac = {p_ac}, s_ac = {s_ac}, q_ac= {q_ac}, PF = {PF}, v_ac = {v_ac}, i_ac = {i_ac}")
        yield p_ac, s_ac, PF, v_ac, i_ac
        # single phase circuit calculation


def main(clients: List[IEEE2030_5_Client], params: Optional[Dict[int, str]] = None):
    if not isinstance(clients, list):
        raise ValueError("clients must be a list")

    if params is None:
        params = {}

    for index, c in enumerate(clients):
        if params.get(index):
            print(f"Got inverter params for index {index} {params.get(index)}")
        else:
            print(f"No params for {index}")
        p_ac, s_ac, PF, v_ac, i_ac = run_inverter(c)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("hostname", help="Host of the invert to use.")
    parser.add_argument("--tls-repo", help="TLS repository directory to use, defaults to ~/tls", default="~/tls")
    parser.add_argument("--server-host", help="Reference to the utilities server for data.")
    parser.add_argument("--server-port", help="Port the server is listening on, default to 443", default=443)

    opts = parser.parse_args()

    path = Path(__file__).parent.parent.parent.joinpath("openssl.cnf")
    repo_dir = Path(opts.tls_repo).expanduser().resolve(strict=True)
    if not repo_dir.exists():
        raise ValueError(f"Invalid repo directory {str(repo_dir)}")
    tls_repo = TLSRepository(repo_dir=repo_dir, openssl_cnffile=path,
                             serverhost="gridappsd_dev_2004", clear=False)

    if opts.hostname not in tls_repo.client_list:
        raise ValueError(f"Hostname: ({opts.hostsname}) not in tls repository")


    # print(tls_repo.client_list)
    for p in tls_repo.client_list:
        IEEE2030_5_Client(cafile=tls_repo.ca_cert_file,
                          keyfile=tls_repo.__get_key_file__(opts.hostname),
                          certfile=tls_repo.__get_cert_file__(opts.hostname),
                          hostname=p,
                          server_hostname=opts.server_host,
                          server_ssl_port=opts.server_port)

    threads: List[Thread] = []

    for index, client in enumerate(IEEE2030_5_Client.clients):
        th = Thread(target=run_inverter, args=[client, client.device_capability])
        th.daemon = True
        th.start()

    while True:
        alive = False
        for t in threads:
            if t.is_alive():
                alive = True
                break
        if alive:
            break
