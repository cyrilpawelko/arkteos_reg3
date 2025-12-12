#!/usr/bin/python
# -*- coding: utf-8 -*-
# Version 0.8
# https://github.com/cyrilpawelko/arkteos_reg3

import socket
import time
import datetime
import sys
import paho.mqtt.client as mqtt

#HOST = "MCHPBOARDxE.pawelko.local" # '192.168.3.80'
HOST = "192.168.3.11"
PORT = 9641
MQTT_HOST = "192.168.3.96"
MQTT_BASE_TOPIC = "arkteos/reg3/"   # don't forget the trailing slash

def signExtend8(x):
  return (x ^ 0x80) - 0x80

def signExtend16(x):
  return (x ^ 0x8000) - 0x8000

decoder = [
    { 'stream' : 163, 'name' : 'exterieur_temp' ,'descr' : 'Température extérieure', 'byte1': 24, 'weight1': 1, 'byte2': 25, 'weight2': 256, 'divider': 10 },
    { 'stream' : 163, 'name' : 'nb_degivrages' ,'descr' : 'Nombre de dégivrages', 'byte1': 26, 'weight1': 1, 'byte2': 27, 'weight2': 256, 'divider': 1 },
    { 'stream' : 163, 'name' : 'freq_comp_actuelle' ,'descr' : 'Fréquence compresseur actuelle', 'byte1': 52, 'weight1': 1, 'byte2': 53, 'weight2': 256, 'divider': 1 },
    { 'stream' : 163, 'name' : 'freq_comp_cible' ,'descr' : 'Fréquence compresseur cible', 'byte1': 54, 'weight1': 1, 'byte2': 55, 'weight2': 256, 'divider': 1 },
    { 'stream' : 163, 'name' : 'fan_speed_evaporator_1' ,'descr' : 'Vitesse ventalisateur groupe frigo 1', 'byte1': 56, 'weight1': 1, 'byte2': 57, 'weight2': 256, 'divider': 1 },
    { 'stream' : 163, 'name' : 'dc_voltage' ,'descr' : 'Voltage DC groupe frigo 1', 'byte1': 62, 'weight1': 1, 'byte2': 63, 'weight2': 256, 'divider': 1 },
    { 'stream' : 163, 'name' : 'temps_compresseur' ,'descr' : 'Temps de fonctionnement du compresseur', 'byte1': 40, 'weight1': 1, 'byte2': 41, 'weight2': 256, 'divider': 0.1 },
    { 'stream' : 163, 'name' : 'nb_cycles_compresseur' ,'descr' : 'Nombre de cycles compresseur (arrondi à 100)', 'byte1': 42, 'weight1': 1, 'byte2': 43, 'weight2': 256, 'divider': 0.01 },
    
    { 'stream' : 227, 'name' : 'puissance_inst_produite' ,'descr' : 'Puissance instanée produite', 'byte1': 16, 'weight1': 1, 'byte2': 17, 'weight2': 256, 'divider': 0.1 },
    { 'stream' : 227, 'name' : 'puissance_inst_consommee' ,'descr' : 'Puissance instanée consommée', 'byte1': 18, 'weight1': 1, 'byte2': 19, 'weight2': 256, 'divider': 0.1 },
    { 'stream' : 227, 'name' : 'temps_mise_sous_tension' ,'descr' : 'Temps mise sous tension (h)', 'byte1': 20, 'weight1': 1, 'byte2': 21, 'weight2': 256, 'divider': 1 },
    { 'stream' : 227, 'name' : 'modele_pac' ,'descr' : 'Modèle PAC', 'byte1': 46, 'weight1': 1, 'byte2': 0, 'weight2': 0, 'divider': 1 },
    { 'stream' : 227, 'name' : 'primaire_temp_eau_consigne' ,'descr' : 'Consigne température eau primaire ', 'byte1': 52, 'weight1': 1, 'byte2': 53, 'weight2': 256, 'divider': 10 },
    { 'stream' : 227, 'name' : 'primaire_temp_eau_aller' ,'descr' : 'Température eau primaire aller', 'byte1': 54, 'weight1': 1, 'byte2': 55, 'weight2': 256, 'divider': 10 },
    { 'stream' : 227, 'name' : 'primaire_temp_eau_retour' ,'descr' : 'Température eau primaire retour', 'byte1': 56, 'weight1': 1, 'byte2': 57, 'weight2': 256, 'divider': 10 },
    { 'stream' : 227, 'name' : 'primaire_debit_eau' ,'descr' : 'Débit eau primaire', 'byte1': 60, 'weight1': 1, 'byte2': 61, 'weight2': 256, 'divider': 10 },
    { 'stream' : 227, 'name' : 'primaire_pression' ,'descr' : 'Pression eau primaire', 'byte1': 62, 'weight1': 1, 'byte2': 0, 'weight2': 0, 'divider': 10 },
    { 'stream' : 227, 'name' : 'primaire_circulateur_consigne' ,'descr' : 'Consigne % circulateur primaire', 'byte1': 64, 'weight1': 1, 'byte2': 0, 'weight2': 0, 'divider': 1 },
    { 'stream' : 227, 'name' : 'zone1_temp_interieur' ,'descr' : 'Température intérieur zone 1', 'byte1': 68, 'weight1': 1, 'byte2': 69, 'weight2': 256, 'divider': 10 },
    { 'stream' : 227, 'name' : 'zone1_consigne' ,'descr' : 'Consigne intérieure zone 1', 'byte1': 70, 'weight1': 1, 'byte2': 71, 'weight2': 256, 'divider': 10 },
    { 'stream' : 227, 'name' : 'ecs_temp_eau_milieu' ,'descr' : 'Température ballon ECS milieu', 'byte1': 108, 'weight1': 1, 'byte2': 109, 'weight2': 256, 'divider': 10 },
    { 'stream' : 227, 'name' : 'ecs_temp_eau_bas' ,'descr' : 'Température ballon ECS bas', 'byte1': 110, 'weight1': 1, 'byte2': 111, 'weight2': 256, 'divider': 10 },
    { 'stream' : 227, 'name' : 'ecs_consigne' ,'descr' : 'Température consigne ECS', 'byte1': 122, 'weight1': 1, 'byte2': 123, 'weight2': 256, 'divider': 10 },
]

statuts_pac = { 0: "Arret", 1: "Attente", 2:  "Chaud", 3: "Froid", 4: "Hors Gel", 5: "Ext Chaud", 6:"Ext Froid", 7:"Chaud Froid", 8:"ECS", 9:"Piscine" }
statuts_frigo = { 0: "Arret", 1: "Refroidissement", 2:  "Chauffage", 3: "Degivrage" }
modeles_pac = { 0x10 : "AJPAC_III", 0x11 : "BAGUIO_ZURAN_IV", 0x12: "TIMAX_III", 0x13 : "GEOTWIN_IV", 0x14 : "CAIROX", 0x15 : "PHOENIX", 0x16 : "ARKTEA", 0x17 : "GEOINVERTER", 0x18 : "LAST_MODEL"}

stream_received = { 163 : False, 227 : False}

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False

if hasattr(mqtt,"CallbackAPIVersion") :
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,"arkteos-reg3.py")
else :
    mqtt_client = mqtt.Client("arkteos-reg3.py")

try:
    mqtt_client.connect(MQTT_HOST)
except:
    print("Error: MQTT connection failed")
    exit(1)

while not connected : # Wait for connection to be available, sometimes one or two minutes after previous client disconnection
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
            print("---------------------------")
            print("A - Bytes value = %.1f, %s" % (bytes_value,bin(bytes_value)))
            if (bytes_value >> 15): # negative value
                bytes_value = bytes_value - (1 << 16) # convert to signed int16
                print("Signed ! value is %.1f" % bytes_value)
            item_value=(bytes_value/item['divider'])
        print('%s:%.1f, ' % (item['name'], item_value),end='')
        mqtt_client.publish(MQTT_BASE_TOPIC + item['name'], item_value)
        print()
    if data_lenght == 227 :
        statut_pac = data[12] & 0b11111
        statut_pac_s = statuts_pac[statut_pac]
        print(statut_pac,statut_pac_s)
        mqtt_client.publish(MQTT_BASE_TOPIC + 'statut_pac', statut_pac)
        mqtt_client.publish(MQTT_BASE_TOPIC + 'statut_pac_s', statut_pac_s)
        active_error_reg = data[30] + (data[31] & 0x0f) * 256
        mqtt_client.publish(MQTT_BASE_TOPIC + 'active_error_reg', active_error_reg)
        signal_rf_sonde_1 = signExtend8(data[193])
        mqtt_client.publish(MQTT_BASE_TOPIC + 'signal_rf_sonde_1', signal_rf_sonde_1)
        modele_pac_s = modeles_pac[data[46]]
        mqtt_client.publish(MQTT_BASE_TOPIC + 'modele_pac_s', modele_pac_s)

    if data_lenght == 163 :
        statut_frigo = data[36] >> 4
        statut_frigo_s = statuts_frigo[statut_frigo]
        print(statut_frigo,statut_frigo_s)
        mqtt_client.publish(MQTT_BASE_TOPIC + 'statut_frigo', statut_frigo)
        mqtt_client.publish(MQTT_BASE_TOPIC + 'statut_frigo_s', statut_frigo_s)

        active_error_fri = data[12] + (data[13] & 0x0f) * 256
        mqtt_client.publish(MQTT_BASE_TOPIC + 'active_error_fri', active_error_fri)
        
    print('')

print('Disconnect')
client.shutdown(socket.SHUT_RDWR)
client.close()
