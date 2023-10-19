import time
from datetime import datetime
from supabase_py import create_client
import os
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

reader = SimpleMFRC522()

def fetch_spotify_id(nfc_id):
    tables = ['artists', 'albums', 'playlists']
    media_types = ['artist', 'album', 'playlist']

    for table, media_type in zip(tables, media_types):
        result = supabase.table(table).select('nfc_id').eq('nfc_id', str(nfc_id)).execute()
        if result and result[0]:
            return {"nfc_id": result[0].get('nfc_id'), "media_type": media_type}

    return None

def fetch_next_unmapped_media():
    tables = ['artists', 'albums', 'playlists']

    for table in tables:
        result = supabase.table(table).select('id').eq('nfc_id', None).limit(1).execute()
        if result and result[0]:
            return {"name": result[0].get('name'), "table": table}

    return None

def read_nfc_tag():
    try:
        id = reader.read()[0]
        return id
    finally:
        GPIO.cleanup()

def save_nfc_id_to_media(nfc_id, media):
    media['nfc_id'] = str(nfc_id)
    # media['updated_at'] = datetime.now().isoformat()
    supabase.table(media['table']).update(media, ['id']).execute()

def main():
    while True:
        print("Ready to scan NFC tag...")
        nfc_id = read_nfc_tag()

        # Check if the NFC ID is already in the DB
        existing_media = fetch_spotify_id(nfc_id)
        if existing_media:
            print(f"Warning: NFC ID {nfc_id} is already mapped to {existing_media['media_type']} with Spotify ID {existing_media['nfc_id']}")
            continue

        # Get the next media item without an NFC ID
        media = fetch_next_unmapped_media()
        if not media:
            print("No more media items left to map.")
            break

        # Save the NFC ID to the media object in the DB
        save_nfc_id_to_media(nfc_id, media)
        print(f"Mapped NFC ID {nfc_id} to {media['name']} in {media['table']} table ")

        time.sleep(1)  # Wait for a short duration before the next read to avoid rapid continuous reads

if __name__ == "__main__":
    main()
