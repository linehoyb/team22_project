'''
This webserver keeps track of users in queue for a charging station, and which charging stations are avaliable and reserved. 

Setup in MQTTX:
* Subscribe to the topic "car/battery/#" to see the current car info.

* Publish to the topic "car/request_info" to get the updated car info
* Publish to the topic "station/connection" with the msg 1 or 0 to tell the car if it is connected to the
* charging station or not.

In Mosquitto:
I'm running localhost as the broker.

Python script:
* You only need to start the run and then do the rest in MQTTX.

'''
from threading import Thread
import paho.mqtt.client as mqtt
import json

class Webserver:
    def __init__(self):
        # Webserver stuff
        self.user_queue_lst = []
        self.avaliable_stations_lst = []
        self.stations_reserved_lst = []

        # MQTT client init
        self.QoS = 2 
        print("Webserver init done")


    def car_disconnecting_from_station(self, station_id):
        print("Car disconnected from station {}".format(station_id))
        # Assign the station if there are users currently in queue
        if (len(self.user_queue_lst) != 0):
            print("There are users in the queue, reserve station")
            
            # Tell the station that it is reserved
            self.message = {"station_id" : "{}".format(station_id), "status:": "1"}
            self.mqtt_client.publish("server/station_reserved", json.dumps(self.message), self.QoS)
        
            # Get user first in line and remove them from the queue
            self.user_id = self.user_queue_lst.pop(0)
            # Put the user in the reserved list
            self.stations_reserved_lst.append([self.user_id, station_id])

            # Assign the station to the user 
            self.message = {"user_id" : "{}".format(self.user_id), "station_id" : "{}".format(station_id) } 
            self.mqtt_client.publish("server/assigned_station", json.dumps(self.message), self.QoS)
            
            # Tell the user that it's avaliable at once
            self.message = {"user_id" : "{}".format(self.user_id), "status:": "0"}
            self.mqtt_client.publish("server/wait_time", json.dumps(self.message), self.QoS)

            # Give a placement update for the others still in the queue if any
            if  (len(self.user_queue_lst) != 0):
                for placement in self.user_queue_lst:
                    self.message = {"user_id" : "{}".format(self.user_queue_lst[placement]), "status" : "{}".format(placement+1) }
                    self.mqtt_client.publish("server/wait_time", json.dumps(self.message), self.QoS)
        
        else:
            # Tell the station that it is now avaliable
            print("No users in queue, station is now avaliable")
            self.avaliable_stations_lst.append(station_id)
            self.message = {"station_id" : "{}".format(station_id), "status:": "0"}
            self.mqtt_client.publish("server/station_reserved", json.dumps(self.message), self.QoS)

        
    def car_connecting_to_station(self, user_id, station_id): # TODO: Få station til å sende hit hvilken user som kobler til station
        # Check if the station is avaliable
        if (station_id in self.avaliable_stations_lst):
            print("The user has connected to an avaliable station {}".format(station_id))
            self.avaliable_stations_lst.remove(station_id)

         # Or the user trying to connect has reserved this station
        elif (([user_id, station_id] in self.stations_reserved_lst)):
            print("The user {} has connected to the correct reserved station {}".format(user_id, station_id))
            self.reserved_stations_lst.remove([user_id, station_id])

        # The user is trying to connect to an unavaliable station
        else:
            print("The user {} is trying to connect to the unavalible station {}".format(user_id, station_id))
            
        
    def book_station(self, user_id):
        # Check if there are any avaliable stations
        if (len(self.avaliable_stations_lst) != 0):
            # Reserve the first station in the avaliable list
            self.station_id = self.avaliable_stations_lst.pop(0) 
            self.stations_reserved_lst.add([user_id, self.station_id])

            # Assign the station to the user
            self.message = {"user_id" : "{}".format(user_id), "station_id" : "{}".format(self.station_id) } 
            self.mqtt_client.publish("server/assigned_station", json.dumps(self.message), self.QoS)
            
            #  Tell the user that it's avaliable at once
            self.message = {"user_id" : "{}".format(user_id), "status:": "0"}
            self.mqtt_client.publish("server/wait_time", json.dumps(self.message), self.QoS)
    
        else:
            # There are no stations avaliable, get placed in the queue
            self.user_queue_lst.append(user_id)
            
            # Tell the user its placement in the queue
            self.placement = self.user_queue_lst.index(user_id) + 1
            self.message = {"user_id" : "{}".format(user_id), "status" : "{}".format(self.placement+1) }
            self.mqtt_client.publish("server/wait_time", json.dumps(self.message), self.QoS)
    
    
    def cancel_booking(self, user_id, station_id): # TODO: Få phone til å lagre station den har fått assigned og send det tilbake
        # Remove user from queue
        if(user_id in self.user_queue_lst):
            print("User {} was removed from the queue".format(user_id))
            self.user_queue_lst.remove(user_id)

        # Or remove the user from the reserved lst and give it to the next person in line if any
        if (([user_id, station_id] in self.stations_reserved_lst)):
            print("The user {} has no longer reserved the station {}".format(user_id, station_id))
            self.reserved_stations_lst.remove([user_id, station_id])
            
            self.car_disconnecting_from_station(station_id)
        
        else:
            print("User {} had no booking to cancel".format(user_id))
            
class MQTT_Client_1:
    
    def __init__(self):
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc):
        print("on_connect(): {}".format(mqtt.connack_string(rc)))

    def on_message(self, client, userdata, msg):
        
        print("on_message(): topic: {}".format(msg.topic))

        if(format(msg.topic) == "phone/book_station"):

        
        elif (format(msg.topic) == "phone/cancel_booking"):
        
        elif(format(msg.topic) == "station/connection"):
            # Extracting info from the json-message
            json_payload = json.loads((msg.payload).decode('utf-8'))
            msg_value = int(json_payload['msg']) #convert to a boolean
            print(msg_value)
            if(msg_value == 1):
               self.stm_driver.send("car_connected_to_station", "stm_car")
            else:
               self.stm_driver.send("car_disconnected_from_station", "stm_car")
        
        else:
            print("Received message from unknown topic: {}".format(msg.topic))
        
        
        
    def start(self, broker, port):
        print("Connecting to {}:{}".format(broker, port))
        self.client.connect(broker, port)

        self.client.subscribe("phone/book_station") # user_id
        self.client.subscribe("phone/cancel_booking") # user_id, station_id
        
        self.client.subscribe("station/connection") # user_id, station_id, 0 / 1
        #self.client.subscribe("car/request_info") # Not in use atm, but can be used to calculate the estimated charging time
        try:
            # line below should not have the () after the function!
            thread = Thread(target=self.client.loop_forever)
            thread.start()
        except KeyboardInterrupt:
            print("Interrupted")
            self.client.disconnect()

broker, port = "localhost", 1883

webserver = Webserver()
myclient = MQTT_Client_1()
webserver.mqtt_client = myclient.client


myclient.start(broker, port)