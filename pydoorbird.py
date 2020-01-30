""" Détecte la pression sur le bouton du portier vidéo et fait sonner un buzzer du raspberry pi
"""
import os
import pickle
from threading import Thread
import logging

import requests as req

import buzzer

ip_device = "10.0.0.74"

# TODO: faire attention au fichier de logs
logging.basicConfig(filename="doorbird.log", level=logging.DEBUG, format="%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s")

def init():
    logins_path = os.path.join(os.path.dirname(__file__), '..', "id_doorbird.pkl")
    with open(logins_path, "rb") as f_in:
        info = pickle.load(f_in)
    user = info["user"]
    password = info["password"]
    del info

    try:
        stream_doorbell = req.get(f"http://{ip_device}/bha-api/monitor.cgi?ring=doorbell", auth=(user, password), stream=True)
    except Exception:
        import traceback
		logging.error(f"ERROR connection au stream échouée; vérifier ip doorbird: {ip_device}:\n{traceback.format_exc()}")
        return -1
    del user
    del password
    return stream_doorbell

def watch(stream):
    for elt in stream_doorbell.iter_lines():
        if elt:
            if "doorbell:H" in elt.decode("utf-8"):
                logging.info("Doorbird entrée sonné.")
                buzzer.buzz()

def main():
    try_connection = 0
    while True:
        stream = init()
        if stream != -1:
            break
        elif try_connection > 30:
            raise ConnectionError("Erreur de connexion dans pydoorbird.py")
        else:
            try_connection += 1
            logging.warning(f"Tentative de reconnection dans {try_connection * 10} secondes...")
            time.sleep(10 * try_connection)
    watch_entree = Thread(target=watch, args=(stream,))
    watch_entree.start()

if __name__ == "__main__":
    main()
