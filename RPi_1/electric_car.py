'''
This emulates an electric car, mainly the charging and draining of the battery.

Setup in MQTTX for solo testing:
* Subscribe to the topic "car/battery/#" to see the current car info.

* Publish to the topic "car/request_info" to get the updated car info
* Publish to the topic "station/connection" with the msg 1 or 0 to tell the car if it is connected to the
* charging station or not.

In Mosquitto:
I'm running localhost as the broker.

Python script:
* You only need to start the run and then do the rest in MQTTX.
'''

from stmpy import Driver, Machine
from threading import Thread
import paho.mqtt.client as mqtt
import time
import json

class Car:
    def update_battery_percentage(self):
        while True:
            if(self.charging):
                self.battery_percentage += 1
                if(self.battery_percentage > 100): self.battery_percentage = 100 #Cap the percentage at 100%
                time.sleep(1)
            else:
                self.battery_percentage -= 1 
                if(self.battery_percentage < 0): self.battery_percentage = 0 #Min percentage is 0%
                time.sleep(3)
            print("Current charge:", self.battery_percentage)
            
    def on_init(self):
        self.battery_percentage = 100
        self.charging = False
        # MQTT client init
        self.QoS = 2 
        self.mqtt_client.publish("car/battery", "{}".format(self.battery_percentage), self.QoS)
        #Thread simulating the car battery
        self.battery_percentage_thread = Thread(target=self.update_battery_percentage)
        self.battery_percentage_thread.start()
        print("Car init done")

    def disconnecting_from_charger(self):
        self.charging = False
        print("Not connected, draining battery")
        
    def connecting_to_charger(self):
        self.charging = True
        print("Connected, charging battery")
        
    def on_information_request(self):
        # Someone is requesting car info through the MQTT broker
        print("Information requested")
        self.mqtt_client.publish("car/battery", "{}".format(self.battery_percentage), self.QoS)

# initial transition
t0 = {
    "source": "initial", 
    "target": "DRAINING",
    "effect": "on_init;"
    }
t1 = {
    "trigger": "info_requested",
    "source": "DRAINING",
    "target": "DRAINING",
    "effect": "on_information_request"
    }
t2 = {
    "trigger": "info_requested",
    "source": "CHARGING",
    "target": "CHARGING",
    "effect": "on_information_request"
    }
t3 = {
    "trigger": "car_connected_to_station",
    "source": "DRAINING",
    "target": "CHARGING",
    "effect": "connecting_to_charger"
    }

t4 = {
    "trigger": "car_disconnected_from_station",
    "source": "CHARGING",
    "target": "DRAINING",
    "effect": "disconnecting_from_charger"
    }

class MQTT_Client_1:
    
    def __init__(self):
        self.previous_time = time.time()
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1) # Running on windows
        # self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1) # Running on raspberry pi
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc):
        print("on_connect(): {}".format(mqtt.connack_string(rc)))

    def on_message(self, client, userdata, msg):
        
        print("on_message(): topic: {}".format(msg.topic))

        if(format(msg.topic) == "car/request_info"):
           self.stm_driver.send("info_requested", "stm_car")
        
        if(format(msg.topic) == "station/connection"):
            # Extracting info from the json-message
            json_payload = json.loads((msg.payload).decode('utf-8'))
            connection = int(json_payload['status']) #convert to a int
            print(connection)
            if(connection == 1):
               self.stm_driver.send("car_connected_to_station", "stm_car")
            else:
               self.stm_driver.send("car_disconnected_from_station", "stm_car")
        
        
        
    def start(self, broker, port):
        print("Connecting to {}:{}".format(broker, port))
        self.client.connect(broker, port)

        self.client.subscribe("station/connection")
        self.client.subscribe("car/request_info")
        try:
            # line below should not have the () after the function!
            thread = Thread(target=self.client.loop_forever)
            thread.start()
        except KeyboardInterrupt:
            print("Interrupted")
            self.client.disconnect()

broker, port = "localhost", 1883 # connecting to internal broker
#broker, port = "***.***.***.***", 1883 # connecting to external broker

car = Car()
car_machine = Machine(name="stm_car", transitions=[t0, t1, t2, t3, t4], obj=car)
car.stm = car_machine

driver = Driver()
driver.add_machine(car_machine)

myclient = MQTT_Client_1()
car.mqtt_client = myclient.client
myclient.stm_driver = driver

myclient.start(broker, port)
driver.start()