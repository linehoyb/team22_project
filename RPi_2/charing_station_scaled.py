import stmpy
from threading import Thread
import paho.mqtt.client as mqtt
import time
import json
import logging
#from sense_hat import SenseHat



##DET SOM MANGLER NÅ ER AT DENNE IKKE KAN SENDE MELDINGER FORDI DEN IKKE HAR NOEN MQTT "ATTRIBUTES"
class Charging_station():

    def __init__(self, name_id, row, mqtt_client):
        #Dette er feil, men copilot likte det så det er en fin start
        self.mqtt_client = mqtt_client
        self.charging = False
        self.connection = False
        self.colors = (0,0,0) #The colours are initially off
        self.update_led()
        self.status = "Free"
        self.QoS = 2
        self.id = name_id
        self.row = row #Dette vil være raden den spesifike stasjonen skal ha på sense hatten
        self.mqtt_client.publish("station/status", "Station is ready", self.QoS)

        #Add transitions her.
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
        
    
        self.stm = stmpy.Machine(name=name_id, transitions=[t0, t1, t2, t3, t4, t5, t6, t7, t8], obj=self)

    def on_free(self):
        #Det jeg faktisk trenger her:
        #Status = free
        self.status = "Free"
        #connection = False
        self.connection = False
        self.mqtt_client.publish("station/status", json.dumps({"id": self.id, "status": self.status}), self.QoS)

        #led = green
        self.update_led()
        """
        if(self.color = "on"):
            sense = SenseHat()
            colour = (0, 255, 0)
            sense.clear(colour)
        """
        print("The station is free, and is not connected to a car.")

    def on_booked(self):
        self.status="Booked"
        self.mqtt_client.publish("station/status", json.dumps({"id": self.id, "status": self.status}), self.QoS)        #json.dumps({"id": self.id_number, "status": self.status})
        #led = blue
        self.update_led()
        """
        if(self.color = "on"):
            sense = SenseHat()
            colour = (0, 0, 255)
            sense.clear(colour)
        """
        print("The station is booked, but not connected to a car.")

    def on_connected(self):
        self.status="Connected"
        self.mqtt_client.publish("station/status", json.dumps({"id": self.id, "status": self.status}), self.QoS)
        #led = yellow
        self.update_led()
        """
        if(self.color = "on"):
            sense = SenseHat()
            colour = (255, 255, 0)
            sense.clear(colour)
        """
        #Kan eventuelt adde at det er en fade her og.
        #timer?
        print("The station is connected to a car.")

    def on_disconnected(self):
        self.status="Disconnected"
        self.mqtt_client.publish("station/status", json.dumps({"id": self.id, "status": self.status}), self.QoS)
        #led = red?
        self.update_led()
        """
        if(self.color = "on"):
            sense = SenseHat()
            colour = (255, 0, 0)
            sense.clear(colour)
        """
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
    
    def __init__(self):
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

        #Starter så stmpy driveren:
        self.stm_driver = stmpy.Driver()
        self.stm_driver.start(keep_active=True)

        #Kan hende jeg må starte stm-en et sted og (:
        #For å scale den må jeg starte 8 stykker
        for row in range(8):
            self.name_id = "station_" + str(row)
            print(self.name_id)
            new_stm = Charging_station(self.name_id ,row ,self.client)
            self.stm_driver.add_machine(new_stm.stm)
            self.stm_driver.start()

    def stop(self):
        #Stop the MQTT client
        self.client.loop_stop()

        #Stop the state machine driver
        self.stm_driver.stop()
        
    def on_connect(self, client, userdata, flags, rc):
        print("on_connect(): {}".format(mqtt.connack_string(rc)))

    def on_message(self, client, userdata, msg):
        
        print("on_message(): topic: {}".format(msg.topic))

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

            if(json_payload == str(1)):
                self.stm_driver.send("car_connected", json_id)
            else:
                self.stm_driver.send("car_disconnected", json_id)
        

        #Så må jeg se etter om det er true eller false:

        #Så må jeg enkelt og greit bare sende info for å triggre et shift i stm.


        """
        if(format(msg.topic) == "server/station_requested"):
            # Extracting info from the json-message
            json_payload = json.loads((msg.payload).decode('utf-8'))
            msg_value = int(json_payload['msg']) #convert to a integer
            print(msg_value)
            if(msg_value == 1):
                self.stm_driver.send("station_booked")
            else:
                self.stm_driver.send("station_free")
        if(format(msg.topic) == "phone/connected"):
            # Extracting info from the json-message
            json_payload = json.loads((msg.payload).decode('utf-8'))
            msg_value = int(json_payload['msg']) #convert to a integer
            print(msg_value)
            if(msg_value == 1):
                self.stm_driver.send("car_connected")
            else:
                self.stm_driver.send("car_disconnected")
        """
        
        
    def start(self, broker, port):
        print("Connecting to {}:{}".format(broker, port))
        self.client.connect(broker, port)

        self.client.subscribe("server/station_reserved")
        self.client.subscribe("phone/connected")
        self.client.loop_start()
        """
        try:
            # line below should not have the () after the function!
            thread = Thread(target=self.client.loop_forever)
            thread.start()
        except KeyboardInterrupt:
            print("Interrupted")
            self.client.disconnect()
        """
"""
broker, port = "localhost", 1883
station = Charging_station()
#Start stm her
station_machine = Machine(name="stm_station", transitions=[t0, t1, t2, t3, t4, t5, t6], obj=station)
station.stm = station_machine

driver = Driver()
driver.add_machine(station_machine)

myclient = MQTT_Client_1()
station.mqqt_client = myclient.client
myclient.stm_driver = driver

myclient.start(broker, port)
driver.start(keep_active=True)
"""

#Prøver selv under her. Fikk ikke Line sitt til å funke (:

#Dette er debugging tools om jeg trenger de til senere
"""
debug_level = logging.DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(debug_level)
ch = logging.StreamHandler()
ch.setLevel(debug_level)
formatter = logging.Formatter('%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

"""

Manager = Station_Manager()