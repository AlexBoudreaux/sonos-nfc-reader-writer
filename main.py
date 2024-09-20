import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import threading
import queue
import os
import time
from rich import print
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from rich.console import Console
from rich.panel import Panel

# Suppress GPIO warnings
GPIO.setwarnings(False)

# Load environment variables
load_dotenv()

# Firebase initialization
cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS"))
firebase_admin.initialize_app(cred)
db = firestore.client()

# Add this near the top of the file
console = Console()

def fetch_row_by_nfc_id(nfc_id):
    collections = ['artists', 'albums', 'playlists']
    media_types = ['artist', 'album', 'playlist']

    for collection, media_type in zip(collections, media_types):
        docs = db.collection(collection).get()
        for doc in docs:
            if doc.to_dict().get('nfc_id') == str(nfc_id):
                return {"id": doc.id, "media_type": media_type}
    return None

def find_unmapped_row():
    collections = ['artists', 'albums', 'playlists']

    for collection in collections:
        docs = db.collection(collection).get()
        for doc in docs:
            if 'nfc_id' not in doc.to_dict() or doc.to_dict()['nfc_id'] is None:
                return {"table": collection, "id": doc.id, "name": doc.to_dict().get('name')}
    return None

def assign_nfc_id_to_row(table, id, nfc_id):
    doc_ref = db.collection(table).document(id)
    doc_ref.update({'nfc_id': str(nfc_id)})
    return doc_ref.get().to_dict()

def worker(nfc_queue, processing_event):
    while True:
        nfc_id = nfc_queue.get()
        if nfc_id is None:  # Sentinel value to end the worker thread
            break

        processing_event.set()  # Set the event to indicate processing has started

        existing_mapping = fetch_row_by_nfc_id(nfc_id)
        if existing_mapping:
            doc = db.collection(existing_mapping['media_type'] + 's').document(existing_mapping['id']).get()
            if doc.exists:
                console.print(Panel(f"NFC ID {nfc_id} is already mapped to {existing_mapping['media_type']} with Name: {doc.to_dict().get('name')}", title="Existing Mapping", border_style="blue"))
        else:
            row_to_map = find_unmapped_row()
            if not row_to_map:
                console.print(Panel("All rows have been mapped!", title="Mapping Status", border_style="yellow"))
            else:
                updated_doc = assign_nfc_id_to_row(row_to_map["table"], row_to_map["id"], nfc_id)
                console.print(Panel(f"NFC ID {nfc_id} has been mapped to {row_to_map['table']} with name: {updated_doc['name']}", title="New Mapping", border_style="green"))

        console.print("------------------------------------------------------")
        nfc_queue.task_done()
        processing_event.clear()  # Clear the event to indicate processing is complete

def main():
    reader = SimpleMFRC522()
    nfc_queue = queue.Queue()
    processing_event = threading.Event()
    
    worker_thread = threading.Thread(target=worker, args=(nfc_queue, processing_event))
    worker_thread.start()

    try:
        while True:
            if not processing_event.is_set():
                console.print("Ready to scan NFC tag...", style="bold cyan")
                try:
                    nfc_id = reader.read_no_block()[0]
                    if nfc_id is not None:
                        nfc_queue.put(nfc_id)
                        console.print("Tag scanned. Processing...", style="bold yellow")
                        processing_event.wait()  # Wait for processing to complete
                except Exception as e:
                    console.print(f"Error reading NFC tag: {e}", style="bold red")
            else:
                # Optional: add a small delay to reduce CPU usage
                time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("\nExiting...", style="bold red")
        nfc_queue.put(None) 
        worker_thread.join()

if __name__ == "__main__":
    main()