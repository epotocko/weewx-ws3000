# weewx-ws3000

## Description
This is a driver for weewx that collects data from Ambient Weather WS-3000 
temperature/humidity sensors. The WS-3000 is a small console that receives data 
wirelessly from up to 8 temperature/humidity sensors.

## Installation

Install weewx (http://www.weewx.com/docs/usersguide.htm#installation_methods)

```bash
# Download extension
wget -O weewx-ws3000.zip https://github.com/epotocko/weewx-ws3000/archive/master.zip

# Install extension
wee_extension --install weewx-ws3000.zip

# Configure the driver
wee_config --reconfigure --driver=user.ws3000

# Start/restart weewx
```

## Credits
Original code is from here: https://groups.google.com/d/msg/weewx-user/qDe-El03C2k/YpqEmI-iBgAJ

Which is based off the HP3000 driver from here: https://github.com/matthewwall/weewx-hp3000/

Instructions for complete setup available here: https://etherpad.net/p/weewx_raspi
