import socket
import cv2
import pickle
import struct
import random
import time
from cryptography.fernet import Fernet

# PRE-SHARED STATIC KEY (Must match the receiver's key exactly)
STATIC_KEY = b'aom1jpw1iwtJtoyRiop5PWOshlpqfAACVUcU-7AdYqU=' 
cipher_suite = Fernet(STATIC_KEY)

# Initialize socket for tactical transmission simulation
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('127.0.0.1', 8080))
print("[INFO] Connected to Base Node using Pre-Shared Key.")

cap = cv2.VideoCapture(0)

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.resize(frame, (640, 480))
        
        # Package dynamic telemetry data and video frame
        current_hr = random.randint(72, 88)     # Fluctuates realistically
        current_spo2 = random.randint(96, 99)   # Fluctuates realistically
        
        telemetry_data = {
            "heart_rate": current_hr, 
            "spo2": current_spo2, 
            "status": "Active Field Feed",
            "timestamp": time.time()
        }
        raw_package = (telemetry_data, frame)
        serialized_data = pickle.dumps(raw_package)
        
        # Encrypt using the static pre-shared key
        encrypted_data = cipher_suite.encrypt(serialized_data)
        
        # Send packet size followed by encrypted payload (No key exchange needed!)
        message_size = struct.pack("L", len(encrypted_data))
        client_socket.sendall(message_size + encrypted_data)
        
except Exception as e:
    print(f"[ERROR] Transmission interrupted: {e}")
    
finally:
    cap.release()
    client_socket.close()