# server.py
import socket
import threading

clientes = []          # lista de sockets
client_info = {}       # socket -> {"id":int, "name":str}
lock = threading.Lock()

def broadcast(msg_bytes, exclude_conn=None):
    with lock:
        for c in clientes.copy():
            if c is exclude_conn:
                continue
            try:
                c.send(msg_bytes)
            except:
                try:
                    clientes.remove(c)
                    del client_info[c]
                    c.close()
                except:
                    pass

def manejar_cliente(conn, addr):
    with lock:
        clientes.append(conn)
        assigned_id = len(clientes) - 1
        client_info[conn] = {"id": assigned_id, "name": None}

    print(f"Jugador conectado: {addr} (assigned id {assigned_id})")

    # informar al cliente su id de jugador
    try:
        conn.send(f"START:{assigned_id}".encode())
    except:
        pass

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode(errors='ignore')

            # Si es un nombre, guardarlo y notificar al resto
            if msg.startswith("NAME:"):
                name = msg.split(":", 1)[1]
                with lock:
                    client_info[conn]["name"] = name
                # mandar al resto que este cliente se llama name
                broadcast(f"NAME:{name}".encode(), exclude_conn=conn)
                # opcional: enviar al cliente los nombres ya conocidos de otros
                with lock:
                    for c, info in client_info.items():
                        if c != conn and info["name"]:
                            try:
                                conn.send(f"NAME:{info['name']}".encode())
                            except:
                                pass
                continue

            # Reenvío de jugadas (números)
            # Validamos si es número
            try:
                int(msg)
                # reenviar solo la jugada a los demás
                broadcast(data, exclude_conn=conn)
            except:
                # si no es número ni NAME ni START, ignoramos
                pass

    except Exception as e:
        print("Error manejando cliente:", e)

    print("Jugador desconectado:", addr)
    with lock:
        try:
            clientes.remove(conn)
            del client_info[conn]
        except:
            pass
    try:
        conn.close()
    except:
        pass

def main():
    HOST = "0.0.0.0"
    PORT = 5000
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(4)
    print(f"SERVIDOR LISTO — Esperando jugadores en {HOST}:{PORT} ...")

    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Servidor detenido por teclado.")
    finally:
        server.close()

if __name__ == "__main__":
    main()
