import time
from datetime import datetime
from supabase_py import create_client, Client
from dotenv import load_dotenv
import os
import nfc

# Assuming you've set up the NFC reader library and have a function like this:
# from your_nfc_library import read_nfc_tag  # You'll need to replace this with your actual import

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

def fetch_spotify_id(nfc_id):
    # db = init_supabase()
    tables = ['Artists', 'Albums', 'Playlists']
    media_types = ['artist', 'album', 'playlist']

    for table, media_type in zip(tables, media_types):
        result = supabase.table(table).select('spotify_id').eq('nfc_id', nfc_id).execute()
        if result and result[0]:
            return {"spotify_id": result[0].get('spotify_id'), "media_type": media_type}

    return None

def fetch_next_unmapped_media():
    """
    Fetches the next media item (album, artist, or playlist) from the DB 
    that doesn't have an NFC ID mapped to it.
    """
    # db = init_supabase()
    tables = ['Artists', 'Albums', 'Playlists']

    for table in tables:
        result = supabase.table(table).select('id').eq('nfc_id', None).limit(1).execute()
        if result and result[0]:
            return {"media_id": result[0].get('id'), "table": table}

    return None

def read_nfc_tag():
    clf = nfc.ContactlessFrontend('usb')
    tag = clf.connect(rdwr={'on-connect': lambda tag: False})
    clf.close()
    return tag

def save_nfc_id_to_media(nfc_id, media):
    """
    Maps the NFC ID to the media object in the DB.
    """
    media['nfc_id'] = nfc_id
    media['updated_at'] = datetime.now().isoformat()
    supabase.table(media['table']).update(media, ['id']).execute()

def main():
    while True:
        print("Ready to scan NFC tag...")
        nfc_id = read_nfc_tag()

        # Check if the NFC ID is already in the DB
        existing_media = fetch_spotify_id(nfc_id)
        if existing_media:
            print(f"Warning: NFC ID {nfc_id} is already mapped to {existing_media['media_type']} with Spotify ID {existing_media['spotify_id']}")
            continue

        # Get the next media item without an NFC ID
        media = fetch_next_unmapped_media()
        if not media:
            print("No more media items left to map.")
            break

        # Save the NFC ID to the media object in the DB
        save_nfc_id_to_media(nfc_id, media)
        print(f"Mapped NFC ID {nfc_id} to {media['table']} with ID {media['media_id']}")

        time.sleep(1)  # Wait for a short duration before the next read to avoid rapid continuous reads

if __name__ == "__main__":
    main()
