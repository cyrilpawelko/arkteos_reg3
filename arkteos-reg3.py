#!/usr/bin/python
# Version 0.2
# https://github.com/cyrilpawelko/arkteos_reg3

import socket
import time
import datetime
import sys
import paho.mqtt.client as mqtt

HOST = '192.168.3.80'
PORT = 9641
MQTT_HOST = "192.168.3.11"
MQTT_BASE_TOPIC = "arkteos/reg3/"   # don't forget the trailing slash

decoder = [
    { 'stream' : 227, 'name' : 'primaire_pression' ,'descr' : 'Pression eau primaire', 'byte1': 62, 'weight1': 1, 'byte2': 0, 'weight2': 0, 'divider': 10 },






    { 'stream' : 227, 'name' : 'primaire_temp_eau_aller' ,'descr' : 'Température eau primaire aller', 'byte1': 54, 'weight1': 1, 'byte2': 55, 'weight2': 256, 'divider': 10 },
    { 'stream' : 227, 'name' : 'primaire_temp_eau_retour' ,'descr' : 'Température eau primaire retour', 'byte1': 56, 'weight1': 1, 'byte2': 57, 'weight2': 256, 'divider': 10 },

    { 'stream' : 163, 'name' : 'exterieur_temp' ,'descr' : 'Température extérieure', 'byte1': 24, 'weight1': 1, 'byte2': 25, 'weight2': 256, 'divider': 10 },
    { 'stream' : 227, 'name' : 'zone1_temp_interieur' ,'descr' : 'Température intérieur zone 1', 'byte1': 68, 'weight1': 1, 'byte2': 69, 'weight2': 256, 'divider': 10 },


    { 'stream' : 227, 'name' : 'zone1_consigne' ,'descr' : 'Consigne intérieure zone 1', 'byte1': 70, 'weight1': 1, 'byte2': 71, 'weight2': 256, 'divider': 10 },

    { 'stream' : 227, 'name' : 'ecs_temp_eau_milieu' ,'descr' : 'Température ballon ECS milieu', 'byte1': 108, 'weight1': 1, 'byte2': 109, 'weight2': 256, 'divider': 10 },
    { 'stream' : 227, 'name' : 'ecs_temp_eau_bas' ,'descr' : 'Température ballon ECS bas', 'byte1': 110, 'weight1': 1, 'byte2': 111, 'weight2': 256, 'divider': 10 },

]

stream_received_163 = False
stream_received_227 = False
stream_received = { 163 : False, 227 : False}

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False

mqtt_client = mqtt.Client("arkteos-reg3.py")
try:
    mqtt_client.connect(MQTT_HOST)
except:
    print("Error: MQTT connection failed")
    exit(1)

while not connected : # Wait for connection to be available, sometimes one or two minutes
    try :
        client.connect((HOST, PORT))
        connected = True
    except socket.error as e:
        print("Connection failed (%s), waiting" % e)
        time.sleep(3)
print('Connection to ' + HOST + ':' + str(PORT) + ' successfull.')

while not ( stream_received[163] and stream_received[227] ):
    data_lenght = 0
    try :
        data = client.recv(1024)
        data_lenght = len(data)
    except KeyboardInterrupt:
        pass
    #print('Received %s octets' %data_lenght)
    data_lenght = len(data)
    stream_received[data_lenght] = True
    for item in ( x for x in decoder if x["stream"] == data_lenght) :
        if item['byte2']==0 :
            item_value=(data[item['byte1']]*item['weight1'])/item['divider']
        else :
            bytes_value=data[item['byte1']]*item['weight1']+data[item['byte2']]*item['weight2']
            if (bytes_value >> 15): # negative value
                bytes_value = bytes_value - (1 >> 16) # convert to signed int16
                print("Signed ! value is %.1f" % bytes_value)
            item_value=(bytes_value/item['divider'])
        print('%s:%.1f, ' % (item['name'], item_value),end='')
        mqtt_client.publish(MQTT_BASE_TOPIC + item['name'], item_value)
    print('')

print('Disconnect')
client.shutdown(socket.SHUT_RDWR)
client.close()
