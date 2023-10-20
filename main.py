import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from supabase_py import create_client

# SupaBase initialization
supabase_url = "https://kawbaltqnmyidugkecqc.supabase.co"  # replace with your URL
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imthd2JhbHRxbm15aWR1Z2tlY3FjIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTU0MzcyOTUsImV4cCI6MjAxMTAxMzI5NX0.F2AN32QxlNf93MqD3UNTLP0wws52vQON0FTz0S2t40c"

def init_supabase():
    supabase = create_client(supabase_url, supabase_key)
    return supabase

def fetch_row_by_nfc_id(nfc_id):
    db = init_supabase()
    tables = ['artists', 'albums', 'playlists']
    media_types = ['artist', 'album', 'playlist']

    for table, media_type in zip(tables, media_types):
        result = db.table(table).select('id').eq('nfc_id', str(nfc_id)).execute()
        if result and len(result['data']) > 0:
            return {"id": result['data'][0].get('id'), "media_type": media_type}
    return None

def find_unmapped_row():
    db = init_supabase()
    tables = ['artists', 'albums', 'playlists']

    for table in tables:
        result = db.table(table).select('*').execute()
        rows = result.get('data', [])
        
        unmapped_rows = [row for row in rows if row.get('nfc_id') is None]
        if unmapped_rows:
            return {"table": table, "id": unmapped_rows[0].get('id'), "name": unmapped_rows[0].get('name')}
    return None

def assign_nfc_id_to_row(table, id, nfc_id):
    db = init_supabase()

    result = db.table(table).select('*').eq('id', str(id)).execute()
    row = result.get('data', [])[0]

    row['nfc_id'] = nfc_id

    response = db.table(table).insert(row, upsert=True).execute()

    return response

def main():
    reader = SimpleMFRC522()

    while True:
        
        print("Ready to scan NFC tag...")
        nfc_id = id = reader.read()[0]

        if fetch_row_by_nfc_id(nfc_id):
            print(f"Warning: NFC ID {nfc_id} is already mapped!")
            continue

        row_to_map = find_unmapped_row()
        if not row_to_map:
            print("All rows have been mapped!")
            continue

        assign_nfc_id_to_row(row_to_map["table"], row_to_map["id"], nfc_id)
        print(f"NFC ID {nfc_id} has been mapped to {row_to_map['table']} with name: {row_to_map['name']}")

if __name__ == "__main__":
    main()