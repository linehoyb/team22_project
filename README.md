# team22_project

Some things you need to know to be able to set up the system.
It was hard to find the right documentation on this and took unecessaty long time to figure out.
(This should really be included in the project description/tips next year :))

For running on RaspberryPi these packages needs to be installed exactly this way:
* $ python3.11 -m pip install stmpy
* $ pip install paho-mqtt

To be able to receive external connections you need to do the following on the unit thats running the broker:
-  In mosquitto.conf add (without a hash (#) infront):
listener 1883
allow_anonymous true

You might also need to create a rule in your pc-firewall that allows inbound and outbound connections on
port 1883

The rasberrypis needs mosquitto downloaded aswell:
sudo apt-get install -y mosquitto mosquitto-clients

To send test messages from raspberrypi to broker running on pc:
mosquitto_pub -h your_pc_ip_address -t test_channel -m “Hello im Raspberry Pi”

If you get socket error when running the broker on windows telling you that the port 1883 is already taken:
- run the command: netstat -ano | findstr1883
- then kill the process: taskkill /F /PID 4464