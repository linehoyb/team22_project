from appJar import gui
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import json
import threading
import random

broker_address = "localhost"
port = 1883



def send_message(topic, message):
    publish.single(topic, message, hostname=broker_address, port=port)

def book_station(user_id): 
    topic = "phone/book_station"
    message = {"user_id" : user_id}
    send_message(topic, json.dumps(message))
    app.setLabel("status_label", f"User {user_id} booked the charging station")
    print(f"User {user_id} booked the charging station.")

def get_station():
    topic = "server/assigned_station"
    assigned_station = subscribe.simple(topic)
    payload = json.loads(assigned_station.payload.decode())
    station_id = payload["station_id"]
    return station_id



def cancel_booking(user_id):
    topic = "phone/cancel_booking"
    message = {"user_id" : user_id}
    send_message(topic, json.dumps(message))
    app.setLabel("status_label", f"User {user_id} cancelled the charging station")
    print(f"User {user_id} cancelled the booking.")

def initiate_id():
    return random.randint(1, 8)

def subscribe_to_battery(topic):
    msg = subscribe.simple(topic)
    payload = json.loads(msg.payload.decode())
    app.setLabel("status_label", f"Current Charge: {payload}%")

def request_button_pressed():
    topic = "car/request_info"
    message = ""
    send_message(topic, message)
    app.setLabel("status_label", "Info requested")

    threading.Thread(target=subscribe_to_battery, args=("car/battery",)).start()

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

def connect_button_pressed():
    topic = "phone/connected"
    station_id = get_station()
    message =  {"connected" :  0, "station_id" : "station_2"}
    send_message(topic, json.dumps(message))
    app.setLabel("status_label", "station_2 is connected")

def publish_to_book_station(): #for webserver
    topic = "phone/book_station"
    send_message(topic, user_id)

def publish_to_cancel_booking():    #for webserver
    topic = "phone/cancel_booking"
    station_id = get_station()
    message = {"user_id" : user_id, "station_id" : station_id}
    send_message(topic, json.dumps(message))

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("\nConnected to MQTT broker")
    else:
        print("Failed to connect to MQTT broker")
    
def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()}")


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

if __name__ == "__main__":
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker_address, port)
    client.loop_start()

    user_id = initiate_id()
    print(f"User id: {user_id}")

    app = gui("Chargify", "500x600")
    app.setBg("lightgrey")
    app.setFont(family = "Arial")

    app.addButtons(["Request Info", "Charge Vehicle", "Unplug Charger"], [request_button_pressed, charge_button_pressed, unplug_button_pressed], rowspan=2)
    app.addButtons(["Book Station", "Cancel Booking"], [lambda: book_station(user_id), lambda: cancel_booking(user_id)])
    app.addButtons(["Connect"], [connect_button_pressed])

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