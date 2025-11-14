import socket
import threading

clientes = []

def manejar_cliente(conn, addr):
    print(f"Jugador conectado: {addr}")
    clientes.append(conn)

    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            
            # reenviar jugada a todos menos al que la envió
            for c in clientes:
                if c != conn:
                    c.send(data.encode())
    except:
        pass

    print("Jugador desconectado:", addr)
    clientes.remove(conn)
    conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 5000))
server.listen(2)

print("SERVIDOR LISTO — Esperando jugadores...")

while True:
    conn, addr = server.accept()
    threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True).start()
