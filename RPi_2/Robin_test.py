import stmpy
from threading import Thread
import paho.mqtt.client as mqtt
import time
import json
import logging
from sense_hat import SenseHat



##DET SOM MANGLER NÅ ER AT DENNE IKKE KAN SENDE MELDINGER FORDI DEN IKKE HAR NOEN MQTT "ATTRIBUTES"
class Charging_station():

    def __init__(self, name_id, row, mqtt_client, sense_hat):
        #Dette er feil, men copilot likte det så det er en fin start
        self.mqtt_client = mqtt_client
        self.charging = False
        self.connection = False
        self.sense_hat = sense_hat
        self.colors = (0,0,0) #The colours are initially off
        self.update_led()
        self.status = "Free"
        self.QoS = 2
        self.id = name_id
        self.row = row #Dette vil være raden den spesifike stasjonen skal ha på sense hatten
        self._setup_transitions()
        self._publish_initial_status()

               

    def _setup_transitions(self):
        t0 = {
            "source": "initial", 
            "target": "Free",
            "effect": "on_free();"
            }
        t1 = {
            "trigger": "station_booked",
            "source": "Free",
            "target": "Booked",
            "effect": "on_booked()"
            }
        t2 = {
            "trigger": "statoion_free",
            "source": "Booked",
            "target": "Free",
            "effect": "on_free()"
            }
        t3 = {
            "trigger": "car_connected",
            "source": "Booked",
            "target": "Connected",
            "effect": "on_connected()"
            }

        t4 = {
            "trigger": "car_disconnected",
            "source": "Connected",
            "target": "Disconnected",
            "effect": "on_disconnected()"
            }

        t5 = {
            "trigger": "station_booked",
            "source": "Disconnected",
            "target": "Booked",
            "effect": "on_booked()"
            }

        t6 = {
            "trigger": "station_free",
            "source": "Disconnected",
            "target": "Free",
            "effect": "on_free()"
            }
        
        t7 = {
            "trigger": "station_free",
            "source": "Free",
            "target": "Free"
            }
        t8 = {
            "trigger": "car_connected",
            "source": "Free",
            "target": "Connected",
            "effect": "on_connected()"
            }
            
        self.stm = stmpy.Machine(name=self.id, transitions=[t0, t1, t2, t3, t4, t5, t6, t7, t8], obj=self)

    def _publish_initial_status(self):
        self.mqtt_client.publish("station/status", "Station is ready", self.QoS)

    def on_free(self):
        #Det jeg faktisk trenger her:
        #Status = free
        self.status = "Free"
        #connection = False
        self.connection = False
        self.mqtt_client.publish("station/status", json.dumps({"id": self.id, "status": self.status}), self.QoS)

        #led = green
        self.update_led()

        print("The station is free, and is not connected to a car.")

    def on_booked(self):
        self.status="Booked"
        self.mqtt_client.publish("station/status", json.dumps({"id": self.id, "status": self.status}), self.QoS)        #json.dumps({"id": self.id_number, "status": self.status})
        #led = blue
        self.update_led()

        print("The station is booked, but not connected to a car.")

    def on_connected(self): #Jeg mangler å legge til user_id til stasjonen
        self.status="Connected"
        self.mqtt_client.publish("station/status", json.dumps({"id": self.id, "status": self.status}), self.QoS)
        #led = yellow
        self.update_led()

        #Kan eventuelt adde at det er en fade her og.
        #timer?
        print("The station is connected to a car.")

    def on_disconnected(self): #Jeg mangler å fjærne user_id fra stasjonen
        self.status="Disconnected"
        self.mqtt_client.publish("station/status", json.dumps({"id": self.id, "status": self.status}), self.QoS)
        #led = red?
        self.update_led()

        print("The station is disconnected from a car.")
        #publish station/connection = 0
    
    def update_led(self):
        colors = {
            "Free": (0, 255, 0),        # Green
            "Booked": (0, 0, 255),      # Blue
            "Connected": (255, 255, 0), # Yellow
            "Disconnected": (255, 0, 0) # Red
        }
        self.sense_hat.set_pixel(self.id_number - 1, 0, colors[self.status])


class Station_Manager():
    #lalala
    
    def __init__(self, sense_hat):
        #Starter med å lage en mqtt client:
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        #Callback methods:
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        #Connect to the broker
        self.client.connect("localhost", 1883)
        #Subscribe to the topics needed
        #Dette vil her være: "station/connection"
        self.client.subscribe("station/connection")
        self.client.subscribe("phone/connected")
        #Start the internal loop to process MQTT messages
        self.client.loop_start()
        self.stations = {}
        self.sense_hat = sense_hat

        #Starter så stmpy driveren:
        self.stm_driver = stmpy.Driver()
        self.stm_driver.start(keep_active=True)

        #Kan hende jeg må starte stm-en et sted og (:
        #For å scale den må jeg starte 8 stykker
        for row in range(8):
            self.name_id = "station_" + str(row)
            print(self.name_id)
            self.stations[row] = self.name_id
            self.stations[self.name_id] = None
            new_stm = Charging_station(self.name_id ,row ,self.client, self.sense_hat)
            self.stm_driver.add_machine(new_stm.stm)
            self.stm_driver.start()

    def stop(self):
        #Stop the MQTT client
        self.client.loop_stop()

        #Stop the state machine driver
        self.stm_driver.stop()
        
    def on_connect(self, client, userdata, flags, rc):
        self._print_connection_message("on_connect(): ", rc)

    def on_message(self, client, userdata, msg):        
        self._print_connection_message("on_message(): topic: ", msg.topic)

    def _print_connection_message(self, prefix, message):
        print(prefix + str(message))


        #Henter først info fra json-melding
        json_msg = json.loads((msg.payload).decode('utf-8'))
        #Neste så må jeg finne ut hva slags command jeg har fått:
        #json.topic = hvor jeg fikk den fra (eks: station/connection)
        json_topic = msg.topic

        #json.payload = hva som ble sendt (eks: "msg": 1)
        json_id = json_msg["station_id"]
        
        #Først ser jeg hvor jeg fikk meldingen fra:
        if(json_topic == "station/connection"):
            json_payload = json_msg["status"]
            
            #Så ser jeg hva meldingen var
            if(json_payload == str(1)):
                self.stm_driver.send("station_booked", json_id)
            else:
                self.stm_driver.send("statoion_free", json_id)
        if(json_topic == "phone/connected"):
            json_payload = json_msg["connecteed"]
            #Trenger å store denne et sted så jeg kan bruke den senere
            json_user_id = json_msg["user_id"]
            if(json_payload == str(1)):
                self.stations[json_id] = json_user_id
                self.mqtt_client.publish("station/connection", json.dumps({"station_id": json_id, "status": 1, "user_id": json_user_id}), self.QoS)
                self.stm_driver.send("car_connected", json_id)
            else:
                self.stations[json_id] = None
                self.mqtt_client.publish("station/connection", json.dumps({"station_id": json_id, "status": 0, "user_id": json_user_id}), self.QoS)
                self.stm_driver.send("car_disconnected", json_id)
        

        #Så må jeg se etter om det er true eller false:

        #Så må jeg enkelt og greit bare sende info for å triggre et shift i stm.

    def start(self, broker, port):
        print("Connecting to {}:{}".format(broker, port))
        self.client.connect(broker, port)

        self.client.subscribe("server/station_reserved")
        self.client.subscribe("phone/connected")
        self.client.loop_start()


#Prøver selv under her. Fikk ikke Line sitt til å funke (:

#Dette er debugging tools om jeg trenger de til senere
sense_hat = SenseHat()

Manager = Station_Manager(sense_hat)#Add "sense_hat" to the arguments when needed