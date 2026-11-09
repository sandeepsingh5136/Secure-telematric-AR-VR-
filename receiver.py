import socket
import cv2
import pickle
import struct
import time
from cryptography.fernet import Fernet

# PRE-SHARED STATIC KEY (Must match the sender's key exactly)
STATIC_KEY = b'aom1jpw1iwtJtoyRiop5PWOshlpqfAACVUcU-7AdYqU='
cipher_suite = Fernet(STATIC_KEY)

# Set up socket server at base station
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('127.0.0.1', 8080))
server_socket.listen(5)
print("[INFO] Base Node listening for secure pre-shared key telemetry...")

conn, addr = server_socket.accept()
print(f"[INFO] Connection accepted from Field Node: {addr}")

data = b""
payload_size = struct.calcsize("L")

try:
    while True:
        while len(data) < payload_size:
            packet = conn.recv(4096)
            if not packet:
                break
            data += packet
            
        if not data:
            break
            
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("L", packed_msg_size)[0]
        
        while len(data) < msg_size:
            data += conn.recv(4096)
            
        encrypted_frame_data = data[:msg_size]
        data = data[msg_size:]
        

       # Decrypt using the static pre-shared key
        decrypted_data = cipher_suite.decrypt(encrypted_frame_data)
        telemetry_data, frame = pickle.loads(decrypted_data)
        
        # --- FEATURE 2: LATENCY & BANDWIDTH METRICS ---
        receive_time = time.time()
        send_time = telemetry_data.get('timestamp', receive_time)
        latency_ms = (receive_time - send_time) * 1000  # Convert to milliseconds
        packet_size_kb = len(encrypted_frame_data) / 1024  # Convert bytes to KB
        
        # Print metrics to terminal
        print(f"[NET METRICS] Latency: {latency_ms:.1f}ms | Payload Size: {packet_size_kb:.1f} KB")
        # ---------------------------------------------
        
        # Extract live vitals
        hr = telemetry_data['heart_rate']
        spo2 = telemetry_data['spo2']
        
        # TACTICAL AR/VR HUD OVERLAY
        if hr > 92 or hr < 65:
            cv2.putText(frame, "[CRITICAL] ABNORMAL VITALS - EVAC REQUIRED!", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.rectangle(frame, (0, 0), (640, 480), (0, 0, 255), 3)
        else:
            cv2.putText(frame, "[SECURE LINK] FIELD MEDIC STABLE", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.rectangle(frame, (0, 0), (640, 480), (0, 255, 0), 1)
            
        cv2.putText(frame, f"HEART RATE: {hr} BPM", (20, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"SpO2 LEVEL: {spo2}%", (20, 110), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # --- DISPLAY LATENCY & BANDWIDTH ON THE HUD WINDOW ---
        cv2.putText(frame, f"LATENCY: {latency_ms:.1f} ms", (20, 140), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"BANDWIDTH: {packet_size_kb:.1f} KB/frame", (20, 170), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        # ----------------------------------------------------
        
        cv2.imshow("Base Command - AR/VR Tele-Consultation HUD", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    conn.close()
    server_socket.close()
    cv2.destroyAllWindows()