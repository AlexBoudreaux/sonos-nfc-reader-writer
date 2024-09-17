import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import threading
import queue
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Firebase initialization
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS"))
firebase_admin.initialize_app(cred)
db = firestore.client()

def fetch_row_by_nfc_id(nfc_id):
    collections = ['artists', 'albums', 'playlists']
    media_types = ['artist', 'album', 'playlist']

    for collection, media_type in zip(collections, media_types):
        doc = db.collection(collection).where('nfc_id', '==', str(nfc_id)).limit(1).get()
        if doc:
            return {"id": doc[0].id, "media_type": media_type}
    return None

def find_unmapped_row():
    collections = ['artists', 'albums', 'playlists']

    for collection in collections:
        docs = db.collection(collection).where('nfc_id', '==', None).limit(1).get()
        if docs:
            doc = docs[0]
            return {"table": collection, "id": doc.id, "name": doc.to_dict().get('name')}
    return None

def assign_nfc_id_to_row(table, id, nfc_id):
    doc_ref = db.collection(table).document(id)
    doc_ref.update({'nfc_id': str(nfc_id)})
    return doc_ref.get().to_dict()

def worker(nfc_queue):
    while True:
        nfc_id = nfc_queue.get()
        if nfc_id is None:  # Sentinel value to end the worker thread
            break

        if fetch_row_by_nfc_id(nfc_id):
            logger.warning(f"Warning: NFC ID {nfc_id} is already mapped!")
            continue

        row_to_map = find_unmapped_row()
        if not row_to_map:
            logger.info("All rows have been mapped!")
            continue

        assign_nfc_id_to_row(row_to_map["table"], row_to_map["id"], nfc_id)
        logger.info(f"NFC ID {nfc_id} has been mapped to {row_to_map['table']} with name: {row_to_map['name']}")
        nfc_queue.task_done()

def main():
    reader = SimpleMFRC522()
    nfc_queue = queue.Queue()
    
    worker_thread = threading.Thread(target=worker, args=(nfc_queue,))
    worker_thread.start()

    try:
        while True:
            logger.info("Ready to scan NFC tag...")
            nfc_id = reader.read()[0]
            nfc_queue.put(nfc_id)
    except KeyboardInterrupt:
        nfc_queue.put(None) 
        worker_thread.join()

if __name__ == "__main__":
    main()