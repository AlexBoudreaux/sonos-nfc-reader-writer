# Sonos NFC Reader/Writer

This project allows you to map NFC tags to Spotify artists, albums, or playlists using a Raspberry Pi and Firebase. It consists of two main components: a tag reader/writer (main.py) and a simple NFC read test (read-test.py).

## Prerequisites

- Raspberry Pi (with Raspbian OS)
- MFRC522 NFC module
- Python 3.7+
- Firebase account and project
- Sonos speaker (for future integration)

## Setup

1. Update and upgrade your Raspberry Pi:
   ```
   sudo apt update
   sudo apt upgrade -y
   ```

2. Install Python, pip, and git:
   ```
   sudo apt install python3 python3-pip git -y
   ```

3. Verify the installations:
   ```
   python3 --version
   pip3 --version
   git --version
   ```

4. Enable SPI on the Raspberry Pi:
   - Run `sudo raspi-config`
   - Navigate to "Interface Options"
   - Select "SPI"
   - Choose "Yes" to enable SPI
   - Select "Finish" 
   - Run `sudo reboot`

5. Clone the repository:
   ```
   git clone https://github.com/yourusername/sonos-nfc-reader-writer.git
   cd sonos-nfc-reader-writer
   ```

6. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

7. Install required packages:
   ```
   pip install -r requirements.txt
   ```

8. Set up Firebase:
   - Create a Firebase project at https://console.firebase.google.com/
   - Generate a new private key for your service account:
     - Go to Project settings > Service Accounts
     - Click "Generate new private key"
     - Save the JSON file securely
   - Rename the JSON file to `spotify-db-firebase-admin-creds.json` and place it in the project root

9. Configure environment variables:
   - Copy `.env.sample` to `.env`
   - Update the `FIREBASE_CREDENTIALS` path in `.env` to point to your Firebase credentials JSON file
   - Set the `SONOS_SPEAKER_NAME` to your Sonos speaker name (for future use)

10. Set up the MFRC522 NFC module:
    Connect the MFRC522 module to the Raspberry Pi as follows:
    - SDA  -> Pin 24 (GPIO 8)
    - SCK  -> Pin 23 (GPIO 11)
    - MOSI -> Pin 19 (GPIO 10)
    - MISO -> Pin 21 (GPIO 9)
    - IRQ  -> Not connected
    - GND  -> Pin 6 (GND)
    - RST  -> Pin 22 (GPIO 25)
    - 3.3V -> Pin 1 (3.3V)

## Usage

### NFC Read Test

To test your NFC reader setup:

1. Run the read-test script:
   ```
   python read-test.py
   ```
2. Scan an NFC tag when prompted
3. The script will display the tag's ID

### Main NFC Reader/Writer

The main script maps unmapped NFC tags to unmapped entries in your Firebase database:

1. Run the main script:
   ```
   python main.py
   ```
2. Scan an NFC tag when prompted
3. The script will map the tag to an unmapped entry in Firebase (artist, album, or playlist)

## Architecture

- `main.py`: Core script for reading NFC tags and mapping them to Firebase entries
- `read-test.py`: Simple script to test NFC tag reading
- Firebase: Stores mappings between NFC tag IDs and Spotify media (artists, albums, playlists)
- Future: Sonos integration for playing mapped content

## Firebase Structure

The Firebase database contains three collections:
- `artists`
- `albums`
- `playlists`

Each document in these collections has an `nfc_id` field, which is initially `null`. When an NFC tag is scanned, it's mapped to an unmapped entry (where `nfc_id` is `null`).

## Contributing

Feel free to submit issues or pull requests for any improvements or bug fixes.

## License

[MIT License](LICENSE)

