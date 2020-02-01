""" Détecte la pression sur le bouton du portier vidéo et fait sonner un buzzer du raspberry pi
"""
import os
import pickle
from threading import Thread
import logging

import requests as req
from requests import exceptions

try:
    rpi = True
    import buzzer
except ImportError:
    print("No module RPi.GPIO")
    rpi = False

ip_device = "10.0.0.74"

# TODO: faire attention au fichier de logs
logging.basicConfig(filename="doorbird.log", level=logging.DEBUG, format="%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s")

def connection(user, password, number_try=1):
    try:
        stream_doorbell = req.get(f"http://{ip_device}/bha-api/monitor.cgi?ring=doorbell", auth=(user, password), stream=True)
    except exceptions.ConnectionError as e:  # Pas de connection ou IP erronée
        time_wait = 2 ** number_try
        if time_wait > 3600:
            # IMPROVE: check if there is a connection available, and scan the network
            logging.error(f"ERROR {number_try} try connection au stream échouée; Arrêt de tentative de reconnexion. Vérifier la connection et l’ip doorbird: {ip_device}")
            raise ConnectionError("")
        import traceback
        logging.warning(f"ERROR {number_try} try connection au stream échouée; Reconnect in {time_wait}s. Vérifier la connection et l’ip doorbird: {ip_device}")
        time.pause(time_wait)
        connection(user, password, number_try+1)
    except Exception:
        import traceback
        logging.error(f"Exception dans la main fonction connection de pydoorbird: {traceback.format_exc()}")

    if stream_doorbell.status_code == 401:
        logging.error("Connection to Doorbird impossible. Logins incorrect.")
        raise ConnectionRefusedError("Connection to Doorbird impossible. Logins incorrect.")
    elif stream_doorbell.status_code == 200:
        logging.info("Connection to Doorbird's Stream established")
    return stream_doorbell


def init():
    logins_path = os.path.join(os.path.dirname(__file__), '..', "id_doorbird.pkl")
    with open(logins_path, "rb") as f_in:
        info = pickle.load(f_in)
    user = info["user"]
    password = info["password"]
    del info

    stream = connection(user, password)
    del user
    del password

    return stream

def watch(stream):
    for elt in stream.iter_lines():
        if elt:
            if "doorbell:H" in elt.decode("utf-8"):
                logging.info("Doorbird entrée sonné.")
                if rpi:
                    buzzer.buzz()

def main():
    stream = init()

    # FIXME surveiller les retours de watch_entree et en cas de problème, relancer la connexion
    watch_entree = Thread(target=watch, args=(stream,))
    watch_entree.start()

if __name__ == "__main__":
    main()