from appJar import gui
import paho.mqtt.publish as publish
import paho.mqtt.subscribe as subscribe
import json
import threading

broker_address = "localhost"
port = 1883

def send_message(topic, message):
    publish.single(topic, message, hostname=broker_address, port=port)

def subscribe_to_topic(topic):
    msg = subscribe.simple(topic)
    handle_received_message(msg)

def handle_received_message(msg): 
    payload = json.loads(msg.payload.decode())
    app.setLabel("status_label", f"Current Charge: {payload}%")

def request_button_pressed():
    topic = "car/request_info"
    message = ""
    send_message(topic, message)
    app.setLabel("status_label", "Info requested")

    threading.Thread(target=subscribe_to_topic, args=("car/battery",)).start()

def charge_button_pressed():
    topic = "station/connection"
    message = {"msg" : 1}
    send_message(topic, json.dumps(message))
    #app.addButton ("Unplug Charger", unplug_button_pressed)
    app.setLabel("status_label", "Car now charging")

def unplug_button_pressed():
    topic = "station/connection"
    message = {"msg" : 0}
    send_message(topic, json.dumps(message))
    #app.removeButton("Unplug Charger")
    app.setLabel("status_label", "Car charger unplugged")

# def connect_button_pressed():
#     topic = "phone/connected"
#     message = {"msg" : 1}
#     send_message(topic, json.dumps(message))
#     app.addButton ("Disconnect", disconnect_button_pressed)
#     app.setButtonRelief("Disconnect", "raised")
#     app.setButtonWidth("Disconnect", 20)
#     app.setLabel("status_label", "Phone establishing connection")

# def disconnect_button_pressed():
#     topic = "phone/connected"
#     message = {"msg" : 0}
#     send_message(topic, json.dumps(message))
#     app.removeButton("Disconnect")
#     app.setLabel("status_label", "Disconnected")

app = gui("Chargify", "500x600")
app.setBg("lightgrey")
app.setFont(family = "Arial")
app.addButtons(["Request Info", "Charge Vehicle", "Unplug Charger"], [request_button_pressed, charge_button_pressed, unplug_button_pressed], rowspan=2)
app.label("status_label", "")

app.setButtonRelief("Request Info", "raised")
app.setButtonRelief("Charge Vehicle", "raised")

app.setButtonWidth("Request Info", 20)
app.setButtonWidth("Charge Vehicle", 20)

app.label("status_label", "")
app.setLabelWidth("status_label", 50)
app.setLabelHeight("status_label", 3)
app.setLabelRelief("status_label", "raised")
app.setPadding(10, 10)

app.go()