import socket
import threading
import time

def run_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('127.0.0.1', 8000))
    s.listen(1)
    conn, addr = s.accept()
    data = conn.recv(1024)
    conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK")
    conn.close()
    s.close()

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(0.5)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect(('127.0.0.1', 8000))
    client.sendall(b"GET / HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
    resp = client.recv(1024)
    print("Received response:", resp.decode('utf-8', errors='ignore'))
    print("Connect result: SUCCESS")
except Exception as e:
    print("Connect result: FAILED:", type(e), e)
finally:
    client.close()

