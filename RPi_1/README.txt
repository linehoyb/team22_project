This Raspberry Pi emulates an electric car.

Its battery will drain or charge depending if it's conneceted to the charging station or not. 
This is decided from the last received message from the
MQTT-topic: "station/connection" where 'msg' == '0' / '1'.   

The battery charges 1% every 1 sec.
The battery drains 1% every 2 sec.

If some other node wants the car's info, then they can get it by publishing to "car/request_info" (the message doesn't matter). 

The car will then publish its current battery-level to "car/battery".

In the background it will continue to either charge or drain the battery depending on the last received message received from "station/connection".