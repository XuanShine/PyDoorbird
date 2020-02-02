""" Détecte la pression sur le bouton du portier vidéo et fait sonner un buzzer du raspberry pi
"""
import os
import pickle
import threading as thread
import time
from queue import Empty, SimpleQueue
import logging
from datetime import datetime

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
        time.sleep(time_wait)
        return connection(user, password, number_try+1)
    except Exception:
        import traceback
        logging.error(f"Exception dans la main fonction connection de pydoorbird: {traceback.format_exc()}")
        # return connection(user, password, number_try+1)

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

def watch_doorbell(stream, q=None):
    t = thread.currentThread()
    logging.warning(f"WARNING WARNING WARNING !!!! This thread may not be stop !! : «{t}»")
    # FIXME : find a way to kill this thread as ".iter_lines" is bloquant
    now = lambda : datetime.now().strftime("%H:%M:%S")
    for elt in stream.iter_lines():
        if not getattr(t, "do_run", True):
            print(f"thread «{t}» watch_doorbell stopped")
            return
        if elt:
            elt = elt.decode("utf-8")
            if q:
                q.put(f"{now()} - {elt}")
            if "doorbell:H" in elt:
                logging.info(f"{now()}: Doorbird entrée sonné.")
                # print(f"{now()}: Doorbird entrée sonné.")
                if rpi:
                    buzzer.buzz()

def watch_stream(q, process_watch):
    try:
        while True:
            result = q.get(block=True, timeout=30)
            logging.debug(result)
            # print(result)
    except Empty:
        logging.warning(f"No signal from doorbell for more than 3 minutes. Stream reconnecting...")
        print(f"No signal from doorbell for more than 3 minutes. Stream reconnecting...")
        # process_watch.close()
        process_watch.do_run = False
        q.put("reconnect")



def main():
    stream = init()
    queue = SimpleQueue()
    watch1 = thread.Thread(target=watch_doorbell, args=(stream, queue))
    watch2 = thread.Thread(target=watch_stream, args=(queue, watch1))
    # print("Ready to staart")
    watch1.start()
    # print("watch1 started")
    watch2.start()
    # print("watch2 started")
    # watch1.join()
    watch2.join()
    while not queue.empty():
        if queue.get() == "reconnect":
            main()
            break

if __name__ == "__main__":
    main()