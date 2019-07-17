# goodwemqtt2domo
Converts mqtt data received from the GoodWeUSBLogger to mqtt understood by Domoticz

Subscribes to the mqtt messages submitted by the goodwe usb logger (https://github.com/sircuri/GoodWeUSBLogger) and maps these to mqtt messages for Domoticz.

## TODO ##
To be added

## Python version
This converter can be used on either python 2 or pyton 3. Use whatever version you prefer or have available.

## Required python modules
To be added

## Configuration
Install the _goodwe2domoticz.conf_ in _/etc_. It shall look like:

TBA

## Usage
Enable and start the service in systemd as described below. 

## Systemd integration
A sample systemd service unit file is included in the _deploy_ directory.
It looks as follows:
```
[Unit]
Description=Goodwe USB Logger
After=basic.target

[Service]
Type=simple
User=goodwe
Group=goodwe
ExecStart=/opt/goodwemqtt2domo/GoodWeMQTTToDomo.py
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```
This assumes that the service runs as user _goodwe_, group _goodwe_.
Use the following command to create the user and group:
```
useradd --system goodwe
The service unit assumes that the software is installed under _/opt/goodwemqtt2domo/_.

Use the standard commands to activate the service:
```
systemctl daemon-reload
systemctl enable goodwemqttconverter.service
systemctl start goodwemqttconverter.service
```
The first command is only required when you just installed the service unit. You could also reboot instead.
The second command enables start of the service after a fresh boot.
The third command activates the service.
