import time

from gridappsd import GridAPPSD


def on_message_callback(header, message):
    print(f"header: {header} message: {message}")

# Note these should be changed on the server in a cyber secure environment!
username = "app_user"
password = "1234App"

# Note: there are other parameters for connecting to
# systems other than localhost
gapps = GridAPPSD(username=username, password=password)

print(gapps.connected)
assert gapps.connected

#gapps.send('send.topic', {"foo": "bar"})

# Note we are sending the function not executing the function in the second parameter
gapps.subscribe('subscribe.topic', on_message_callback)
time.sleep(3)

for i in range(5):
    gapps.send('subcribe.topic', 'A message about subscription')

time.sleep(50)

gapps.disconnect()