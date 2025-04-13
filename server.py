import socket
import threading

HOST = '0.0.0.0'  # nasłuchiwanie na wszystkich interfejsach
PORT = 12345

conn = None

def start_server(port=12345):
    global conn
    HOST = '0.0.0.0'
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, port))
    server.listen(1)
    print(f"[SERVER] Czekam na gracza na porcie {port}...")
    conn, addr = server.accept()
    print(f"[SERVER] Połączono z: {addr}")
    receive_test_message()


def receive_test_message():
    message = receive_data()
    print(f"[SERVER] Otrzymano wiadomość: {message}")

def send_data(data: str):
    global conn
    if conn:
        conn.sendall(data.encode())
    else:
        print("[ERROR] Próba wysłania danych bez połączenia!")

def receive_data() -> str:
    global conn
    if conn:
        return conn.recv(1024).decode()
    else:
        print("[ERROR] Próba odebrania danych bez połączenia!")
        return ""

