# server.py
import socket
import threading

IP_SERVIDOR = "0.0.0.0"   # escucha en todas las interfaces
PUERTO = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP_SERVIDOR, PUERTO))
server.listen(2)

print(f"Servidor iniciado en {IP_SERVIDOR}:{PUERTO}")
print("Esperando jugadores...\n")

clientes = []
nombres = ["Jugador1", "Jugador2"]


def manejar_cliente(conn, idx):
    global clientes

    try:
        # Mandar START y asignar rol
        conn.send(f"START:{idx}".encode())

        # Mandar nombre del otro cuando llegue
        if len(clientes) == 2:
            # Enviar nombre al otro
            try:
                clientes[0].send(f"NAME:{nombres[1]}".encode())
                clientes[1].send(f"NAME:{nombres[0]}".encode())
            except:
                pass

        while True:
            data = conn.recv(1024)
            if not data:
                break

            # reenviar la jugada o mensaje al otro jugador
            for i, c in enumerate(clientes):
                if i != idx:
                    try:
                        c.send(data)
                    except:
                        pass

    except Exception as e:
        print("Error:", e)

    finally:
        print(f"Jugador {idx+1} desconectado.")
        try:
            conn.close()
        except:
            pass


# ======================
# ACEPTAR JUGADORES
# ======================
while len(clientes) < 2:
    conn, addr = server.accept()
    print(f"Jugador conectado desde {addr}")

    clientes.append(conn)

    # Recibir nombre NAME:<nombre>
    try:
        raw = conn.recv(1024).decode()
        if raw.startswith("NAME:"):
            nombres[len(clientes)-1] = raw.split(":", 1)[1]
            print(f"Nombre del jugador {len(clientes)}: {nombres[len(clientes)-1]}")
    except:
        pass

    threading.Thread(target=manejar_cliente, args=(conn, len(clientes)-1), daemon=True).start()

print("\n¡Los 2 jugadores están conectados!\nServidor listo para partida.")
