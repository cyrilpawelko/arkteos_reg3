#!/usr/bin/python
# Démon proxy pour servir plusieurs clients Arkteos simultanément

import socket
import threading
import sys
import time
import logging
from datetime import datetime

# Variables pour l'hôte et le port du serveur "chaudiere"
HOST = "192.168.3.80"  # Adresse IP du serveur distant
PORT = 9641            # Port du serveur distant

# Événement global pour gérer l'arrêt du programme
stop_event = threading.Event()

# Liste des clients connectés
clients = []

logger = logging.getLogger(__name__)

# Send getDeviceInfo1 to keep connection alive
def sendKeepAlive(socket):
  payload = [ 0xf7, 0x40, 0x02, 0x01, 0x06, 0x80, 0x00, 0x00 ]
  socket.sendall(buildFrame(payload, 0x39df))

# Fonction pour ajouter un horodatage aux messages
def log(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}")
    logger.info(f"[{now}] {message}")

# Connexion au serveur distant, avec gestion des tentatives de reconnexion
def connect_to_chaudiere():
    while not stop_event.is_set():
        try:
            chaudiere_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            chaudiere_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            chaudiere_socket.connect((HOST, PORT))
            log(f"Connecté au serveur '{HOST}' sur le port {PORT}")
            return chaudiere_socket
        except Exception as e:
            log(f"Échec de connexion au serveur '{HOST}:{PORT}' : {e}. Nouvelle tentative dans 10 secondes...")
            time.sleep(10)
    return None

# Fonction pour envoyer un paquet vide au serveur distant toutes les 5 minutes
def send_keepalive(chaudiere_socket):
    while not stop_event.is_set():
        time.sleep(300)  # 5 minutes (300 secondes)
#        log(f"{chaudiere_socket}")
        if True :
            try:
                log(f"Envoi d'un paquet vide pour keepalive au serveur distant.")
                chaudiere_socket.sendall(b'0')  # Paquet vide pour maintenir la connexion (ne fonctionne pas ?)
            except Exception as e:
                log(f"Erreur lors de l'envoi du keepalive au serveur distant : {e}")
                break # essai
        else:
            log(f"La connexion au serveur distant a été fermée. Impossible d'envoyer le keepalive.")
            break

# Gestion des clients connectés au serveur local
def handle_client(client_socket, client_addr, chaudiere_socket):
    # Ajouter le client à la liste des clients connectés
    with threading.Lock():
        clients.append(client_socket)

    try:
        # Démarrer un thread pour surveiller les données envoyées par le serveur distant
        def forward_from_chaudiere():
            try:
                while not stop_event.is_set():
                    response = chaudiere_socket.recv(1024)
                    if not response:
                        break
                    log(f"Reçu du serveur distant : {len(response)} octets")

                    # Envoyer les données à tous les clients
                    with threading.Lock():
                        for c in clients:
                            try:
                                c.sendall(response)
                                log(f"Données envoyées à {c.getpeername()}")
                            except Exception as e:
                                log(f"Erreur lors de l'envoi à {c.getpeername()}: {e}")
            except Exception as e:
                log(f"Erreur, Connexion au serveur distant perdue : {e}")
                chaudiere_socket.close()

        # Lancer le thread pour surveiller le serveur distant
        threading.Thread(target=forward_from_chaudiere, daemon=True).start()

        # Boucle principale pour surveiller les données envoyées par le client
        while not stop_event.is_set():
            data = client_socket.recv(1024)  # Réception des données du client
            if not data:
                break

            if chaudiere_socket and chaudiere_socket.fileno() != -1:
                log(f"Reçu du client {client_addr} : {len(data)} octets")
                chaudiere_socket.sendall(data)  # Transférer au serveur distant
            else:
                # Si le serveur distant n'est pas connecté, on oublie les données
                log(f"Connexion au serveur distant perdue, données ignorées de {client_addr} : {len(data)} octets")

    except Exception as e:
        log(f"Erreur avec le client {client_addr} : {e}")
    finally:
        with threading.Lock():
            clients.remove(client_socket)  # Supprimer le client de la liste des clients
        client_socket.close()

# Lancement du serveur TCP local
def start_local_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Lancer le serveur sur toutes les interfaces locales, sauf 127.0.0.1
    local_ip = socket.gethostbyname(socket.gethostname())  # Résolution de l'IP locale
    server_socket.bind((local_ip, PORT))
    server_socket.listen(5)
    log(f"Serveur local en écoute sur {local_ip}:{PORT}")

    chaudiere_socket = None

    try:
        while not stop_event.is_set():
            # Vérification/reconnexion au serveur distant si nécessaire
            if chaudiere_socket is None or chaudiere_socket.fileno() == -1:
                chaudiere_socket = connect_to_chaudiere()
    
                # Démarrage du keepalive, sinon déconnexion après 10 minutes d'inactivité des clients
                keepalive_thread = threading.Thread(target=send_keepalive, args=(chaudiere_socket,))
                keepalive_thread.daemon = True
                keepalive_thread.start()

            server_socket.settimeout(1)  # Timeout pour permettre un arrêt propre

            try:
                client_socket, addr = server_socket.accept()
                log(f"Nouvelle connexion depuis {addr}")
                client_thread = threading.Thread(target=handle_client, args=(client_socket, addr, chaudiere_socket))
                client_thread.start()
            except socket.timeout:
                continue
    except Exception as e:
        log(f"Erreur dans le serveur local : {e}")
    finally:
        stop_event.set()
        server_socket.close()
        if chaudiere_socket:
            chaudiere_socket.close()
        log("Serveur arrêté.")

   
if __name__ == "__main__":
    logging.basicConfig(filename='arkteos-proxy.log', level=logging.INFO)  

    try:
        start_local_server()
    except KeyboardInterrupt:
        log("Interruption détectée (CTRL+C). Arrêt en cours...")
        stop_event.set()
        sys.exit(0)
