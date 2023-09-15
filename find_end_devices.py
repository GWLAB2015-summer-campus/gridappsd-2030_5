import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# ieee_dir = Path(__file__).parent.parent
# sys.path.insert(0, str(ieee_dir))
import ieee_2030_5.models as m

session = requests.Session()
session.cert = ('/home/os2004/tls/certs/admin.pem', '/home/os2004/tls/private/admin.pem')
session.verify = "/home/os2004/tls/certs/ca.pem"

def get_url(endpoint) -> str:
    if endpoint.startswith('/'):
        endpoint = endpoint[1:]
    return f"https://127.0.0.1:7443/admin/{endpoint}"


current_time = int(time.mktime(datetime.utcnow().timetuple()))

print(session.get(get_url("edev")).text)
print(f'Fetching: {get_url("edev/0/der")}')
print(session.get(get_url("edev/0/der")).text)