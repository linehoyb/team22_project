'''
In MQTTX:
* Subscribe to the topic "game/#" to see the necessary game info.

* Publish to the topic "master" to start the timer and to move on to the next question.
* Publish to the topic "player" to stop the timer and get the "Player can answer" prompt.
* It does not matter what the msg is, but it will be printed in the terminal here just for fun :).

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

class Quizbuzzer:
    
    def on_init(self):
        print("Init!")
        self.QoS = 2
        self.mqtt_client.publish("game", "Let the quiz begin!", self.QoS)

    def idle(self):
        print("Master ask a question and start timer")
        self.mqtt_client.publish("game", "Master ask a question and start timer", self.QoS)
        
        
    def start_countdown(self):
        # stm starts timer
        print("Countdown started!")
        self.mqtt_client.publish("game", "Go!", self.QoS)
        
    def on_timer_finished(self):
        # stm timer done
        print("The players time is up!")
        self.mqtt_client.publish("game", "Times up!", self.QoS)
        
    def on_player_buzzer(self):
        # stop timer
        print("Player buzzed!")
        self.mqtt_client.publish("game", "Player can answer", self.QoS)
        # print("Player {} buzzed!".format(player_nmb))
        # self.mqtt_client.publish("game", "Player {} can answer".format(player_nmb))

# initial transition
t0 = {"source": "initial", 
      "target": "IDLE",
      "effect": "on_init; idle"
      }
t1 = {
    "trigger": "master_message",
    "source": "IDLE",
    "target": "COUNTDOWN_RUNNING",
    "effect": "start_countdown; start_timer('timer', 10000)"
    }
t2 = {
    "trigger": "player_message",
    "source": "COUNTDOWN_RUNNING",
    "target": "PLAYER_ANSWER",
    "effect": "stop_timer('timer'); on_player_buzzer"
    }
t3 = {
    "trigger": "timer",
    "source": "COUNTDOWN_RUNNING",
    "target": "TIMES_UP",
    "effect": "on_timer_finished"
    }

t4 = {
    "trigger": "master_message",
    "source": "TIMES_UP",
    "target": "IDLE",
    "effect": "idle"
    }
t5 = {
    "trigger": "master_message",
    "source": "PLAYER_ANSWER",
    "target": "IDLE",
    "effect": "idle"
    }

class MQTT_Client_1:
    
    def __init__(self):
        self.previous_time = time.time()
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        
    def on_connect(self, client, userdata, flags, rc):
        print("on_connect(): {}".format(mqtt.connack_string(rc)))

    def on_message(self, client, userdata, msg):
        print("on_message(): topic: {}".format(msg.topic))
        if(format(msg.topic) == "master"):
           self.stm_driver.send("master_message", "stm_quizbuzzer")
        if(format(msg.topic) == "player"):
           self.stm_driver.send("player_message", "stm_quizbuzzer")
        
        json_data = json.loads((msg.payload).decode('utf-8'))
        #msg_value = int(json_data['msg']) #convert to a integer
        msg_value = json_data['msg']
        print(msg_value)
        
    def start(self, broker, port):
        print("Connecting to {}:{}".format(broker, port))
        self.client.connect(broker, port)

        self.client.subscribe("master")
        self.client.subscribe("player")
        try:
            # line below should not have the () after the function!
            thread = Thread(target=self.client.loop_forever)
            thread.start()
        except KeyboardInterrupt:
            print("Interrupted")
            self.client.disconnect()

broker, port = "localhost", 1883

quizbuzzer = Quizbuzzer()
quizbuzzer_machine = Machine(name="stm_quizbuzzer", transitions=[t0, t1, t2, t3, t4, t5], obj=quizbuzzer)
quizbuzzer.stm = quizbuzzer_machine

driver = Driver()
driver.add_machine(quizbuzzer_machine)

myclient = MQTT_Client_1()
quizbuzzer.mqtt_client = myclient.client
myclient.stm_driver = driver

myclient.start(broker, port)
driver.start()



