This Raspberry Pi simulates an electric car.

Its battery will drain or charge depending if it's conneceted to the charging station or not. 
This is decided from the last received message from the
MQTT-topic: "station/connection" where 'msg' == true/false.   

The battery charges 1% every 500ms.
The battery drains 1% every 2000ms.

If someone needs the cars info, then they can get it by publishing 
to "car/request_info" (the message doesnt matter), 
the car will then publish its current battery-level to "car/battery".

It will then return to either charging or draining depending on the last received message from "station/connection".