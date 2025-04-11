import socket

conn = None

def connect_to_server(ip: str, port: int = 12345):
    global conn
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((ip, port))
    print(f"[CLIENT] Połączono z serwerem {ip}:{port}")
def send_test_message():
    send_data("HELLO_FROM_CLIENT")

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

