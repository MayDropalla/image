from smartcard.System import readers
from smartcard.Exceptions import NoCardException
import time

# Default Rickroll URL
DEFAULT_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

def find_reader():
    r = readers()
    if len(r) == 0:
        print("No smart card readers found!")
        return None
    print("Available readers:")
    for i, reader in enumerate(r):
        print(f"{i}: {reader}")
    return r[0]

def wait_for_tag(reader):
    print(f"Waiting for a tag on reader: {reader}")
    while True:
        try:
            connection = reader.createConnection()
            connection.connect()
            print("Tag detected!")
            return connection
        except NoCardException:
            time.sleep(1)

def ask_for_permission():
    while True:
        choice = input("Do you want to overwrite the tag? [y/n]: ").strip().lower()
        if choice in ("y", "yes"):
            return True
        elif choice in ("n", "no"):
            return False

def get_url():
    url = input(f"Enter the URL to write [{DEFAULT_URL}]: ").strip()
    if url == "":
        url = DEFAULT_URL
    return url

def build_ndef_uri(url):
    """
    Build a full NDEF TLV for a URI record (iPhone compatible)
    """
    url_bytes = url.encode('utf-8')
    # NDEF URI Record Header: MB=1, ME=1, SR=1, TNF=0x1 (Well Known)
    ndef_header = bytes([0xD1, 0x01, len(url_bytes) + 1, 0x55, 0x00])
    ndef_message = ndef_header + url_bytes
    # TLV wrapper: 0x03 = NDEF TLV, 0xFE = terminator
    tlv = bytes([0x03, len(ndef_message)]) + ndef_message + bytes([0xFE])
    return tlv

def write_ndef_tag(connection, url):
    print(f"Writing URL: {url}")
    tlv = build_ndef_uri(url)

    # Write TLV in 4-byte pages starting at page 4
    for i in range(0, len(tlv), 4):
        page = 4 + i // 4
        chunk = tlv[i:i+4]
        while len(chunk) < 4:
            chunk += bytes([0x00])
        apdu = [0xFF, 0xD6, 0x00, page, 4] + list(chunk)
        data, sw1, sw2 = connection.transmit(apdu)
        if sw1 != 0x90:
            print(f"Failed writing page {page}, status: {sw1:X}{sw2:X}")
            return False

    print("URL written successfully! Your tag is iPhone-ready.")
    return True

if __name__ == "__main__":
    reader = find_reader()
    if reader is None:
        exit(1)

    connection = wait_for_tag(reader)
    print("Note: existing tag data may be overwritten.")
    if ask_for_permission():
        url_to_write = get_url()
        write_ndef_tag(connection, url_to_write)
    else:
        print("Operation cancelled by user.")