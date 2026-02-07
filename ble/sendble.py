import asyncio
import struct
import pandas as pd
from bleak import BleakScanner, BleakClient

# --- Configuration ---
DEVICE_NAME = "PPG_IMU_System"
OUTPUT_PPG = "ppg_data.csv"
OUTPUT_IMU = "imu_data.csv"

# UUIDs
UUID_START    = "00002a57-0000-1000-8000-00805f9b34fb"
UUID_TRANSMIT = "00002a58-0000-1000-8000-00805f9b34fb"
UUID_STATUS   = "00002a59-0000-1000-8000-00805f9b34fb"

# State Variables
raw_buffer = bytearray()
header_found = False
expected_bytes = 0
transfer_complete_event = asyncio.Event()

def data_handler(sender, data):
    global raw_buffer, header_found, expected_bytes
    
    # Add new data to buffer
    raw_buffer.extend(data)
    
    # 1. Search for Magic Marker (0xDEADBEEF) if not found yet
    if not header_found:
        # Look for the byte sequence: EF BE AD DE (Little Endian for 0xDEADBEEF)
        marker_index = raw_buffer.find(b'\xEF\xBE\xAD\xDE')
        
        if marker_index != -1:
            # Found it! Align buffer to start here
            print(f"\n[SYNC] Magic Marker found at index {marker_index}!")
            raw_buffer = raw_buffer[marker_index:] # Discard previous garbage
            
            # We need at least 12 bytes to read the full header
            if len(raw_buffer) >= 12:
                parse_header()
    
    # 2. If header is found, track progress
    if header_found:
        current_len = len(raw_buffer)
        percent = (current_len / expected_bytes) * 100
        print(f"\rProgress: {current_len} / {expected_bytes} bytes ({percent:.1f}%)", end="", flush=True)
        
        if current_len >= expected_bytes:
            print("\nDownload complete!")
            transfer_complete_event.set()

def parse_header():
    global header_found, expected_bytes
    # Header Format: [Magic(4)] [PPG_Count(4)] [IMU_Count(4)]
    # offset 4 because we skip the Magic word
    ppg_count, imu_count = struct.unpack_from('<II', raw_buffer, 4)
    
    # Sanity Check
    if ppg_count > 50000 or imu_count > 10000:
        print(f"\n[ERROR] Corrupted Header detected! (PPG: {ppg_count}, IMU: {imu_count})")
        print("Waiting for next marker...")
        # Remove the first byte and try searching again next time
        raw_buffer.pop(0) 
        return

    expected_bytes = 12 + (ppg_count * 4) + (ppg_count * 4) + (imu_count * 24) + 4
    header_found = True
    
    print(f"\n[HEADER VALIDATED]")
    print(f" - PPG Samples: {ppg_count}")
    print(f" - IMU Samples: {imu_count}")
    print(f" - Expecting:   {expected_bytes} bytes")

def status_handler(sender, data):
    status = data.decode('utf-8').strip()
    # If Arduino says IDLE, but we haven't finished, we might have dropped packets
    if status == "IDLE" and header_found and len(raw_buffer) < expected_bytes:
        print("\n[WARNING] Device went IDLE before transfer completed. Dropped packets?")
        transfer_complete_event.set() # Force finish to save what we have

async def main():
    print(f"Scanning for {DEVICE_NAME}...")
    device = await BleakScanner.find_device_by_filter(lambda d, ad: d.name and DEVICE_NAME in d.name)
    
    if not device:
        print("Device not found.")
        return

    async with BleakClient(device) as client:
        print(f"Connected to {device.address}")
        
        await client.start_notify(UUID_STATUS, status_handler)
        await client.start_notify(UUID_TRANSMIT, data_handler)

        # Start Collection
        print("Starting Collection (20s)...")
        await client.write_gatt_char(UUID_START, bytearray([0x01]))
        await asyncio.sleep(21) 
        
        # Start Transmission
        print("Requesting Data...")
        global raw_buffer, header_found
        raw_buffer = bytearray()
        header_found = False
        
        await client.write_gatt_char(UUID_TRANSMIT, bytearray([0x01]))
        
        print("Waiting for Magic Marker...")
        try:
            await asyncio.wait_for(transfer_complete_event.wait(), timeout=90.0)
        except asyncio.TimeoutError:
            print("\nTimeout reached. Saving received data...")

        save_csv(raw_buffer)

def save_csv(data):
    if not header_found:
        print("\nError: No valid header found. Cannot save CSV.")
        return

    offset = 4 # Skip Magic Marker
    ppg_count, imu_count = struct.unpack_from('<II', data, offset)
    offset += 8
    
    print("\nParsing data...")
    
    # Parse PPG1
    ppg1 = []
    for _ in range(ppg_count):
        if offset + 4 > len(data): break
        ppg1.append(struct.unpack_from('<I', data, offset)[0])
        offset += 4

    # Parse PPG2
    ppg2 = []
    for _ in range(ppg_count):
        if offset + 4 > len(data): break
        ppg2.append(struct.unpack_from('<I', data, offset)[0])
        offset += 4
        
    # Trim to matching lengths to avoid "All arrays must be of the same length" error
    min_len = min(len(ppg1), len(ppg2))
    ppg1 = ppg1[:min_len]
    ppg2 = ppg2[:min_len]

    # Parse IMU
    imu_records = []
    for _ in range(imu_count):
        if offset + 24 > len(data): break
        vals = struct.unpack_from('<ffffff', data, offset)
        imu_records.append(vals)
        offset += 24
        
    # Parse Temp
    temp = 0.0
    if offset + 4 <= len(data):
        temp = struct.unpack_from('<f', data, offset)[0]

    # Save
    pd.DataFrame({'Sensor1': ppg1, 'Sensor2': ppg2}).to_csv(OUTPUT_PPG, index_label='Sample')
    
    df_imu = pd.DataFrame(imu_records, columns=['Ax', 'Ay', 'Az', 'Gx', 'Gy', 'Gz'])
    df_imu['Temp_C'] = temp
    df_imu.to_csv(OUTPUT_IMU, index=False)
    
    print(f"Success! Saved {OUTPUT_PPG} and {OUTPUT_IMU}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass