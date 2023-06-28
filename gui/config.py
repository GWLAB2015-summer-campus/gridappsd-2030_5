from pathlib import Path
 
HOST_2030_5 = "full20305"
PORT = 8443
CA_CERT = str(Path("~/tls/certs/ca.pem").expanduser())
ADMIN_CERT = str(Path("~/tls/certs/admin.pem").expanduser())
ADMIN_KEY = str(Path("~/tls/private/admin.pem").expanduser())
