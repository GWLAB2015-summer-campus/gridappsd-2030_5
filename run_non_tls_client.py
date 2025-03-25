import atexit
import ssl
import sys
from http.client import HTTPConnection, HTTPSConnection
from pathlib import Path
from pprint import pprint
import argparse

import OpenSSL

from ieee_2030_5.client import IEEE2030_5_Client_Non_Tls


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--server", required=True,
                        help="The 2030.5 server to connect to")
    parser.add_argument("--port", default=443, type=int,
                        help="The port to connect to the 2030.5 server on. (Default 443)")
    parser.add_argument("--pin", required=True, type=int,
                        help="PIN to validate that the client is registered with the server.")

    opts = parser.parse_args()

    print(f"Connecting to: {opts.server}:{opts.port}")

    client = IEEE2030_5_Client_Non_Tls(
                               server_hostname=opts.server,
                               server_port=int(opts.port))

    dcap = client.device_capability()
    # There should be only a single device, unless this is an aggregator, which this
    # would give the first response in the list.
    end_device = client.end_device()

    # Check the first end device in the list to see if it is the same as the pin
    # passed to the client script.  If not then exit the program with a note to
    # check the pin.
    if not client.is_end_device_registered(end_device, opts.pin):
        print(f"End device not registered on server.  Check pin.")
        sys.exit(0)

    fsa = client.function_set_assignment()
    print(fsa)

    client.get("/tm")