from pathlib import Path

import ieee_2030_5.models as m
from ieee_2030_5.client import IEEE2030_5_Client


def test_starting_server_using_fixture(server_startup):
    tls_repo, server_config = server_startup

    assert tls_repo
    assert server_config

    ed_config = server_config.devices[0]

    server_host, server_port = server_config.server_hostname.split(":")
    cert_file, key_file = tls_repo.get_file_pair(ed_config.id)
    client = IEEE2030_5_Client(cafile=tls_repo.ca_cert_file,
                               server_hostname=server_host,
                               server_ssl_port=server_port,
                               keyfile=Path(key_file),
                               certfile=Path(cert_file))

    dcap = client.device_capability()
    assert dcap.pollRate > 0
    client.disconnect()


def test_first_enddevice_using_fixture(first_client: IEEE2030_5_Client):
    assert first_client
