import socket
import threading

clientes = []
nombres = ["", ""]   # para 2 jugadores
clientes_lock = threading.Lock()

def manejar_cliente(conn, addr, index):
    global nombres

    print(f"Jugador conectado: {addr}")

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            mensaje = data.decode()

            # ======= SI ES UN NOMBRE =======
            if mensaje.startswith("NOMBRE:"):
                nombre = mensaje.replace("NOMBRE:", "")
                nombres[index] = nombre  
                print(f"Jugador {index+1} es: {nombre}")

                # Enviar nombres actualizados a ambos jugadores
                enviar_nombres()
                continue

            # ======= SI ES UNA JUGADA =======
            with clientes_lock:
                for i, c in enumerate(clientes):
                    if c != conn:
                        try:
                            c.sendall(data)
                        except:
                            pass

    except Exception as e:
        print("Error:", e)

    finally:
        print(f"Jugador desconectado: {addr}")

        with clientes_lock:
            try:
                clientes.remove(conn)
            except:
                pass

        conn.close()


def enviar_nombres():
    """Envía NOMBRE1 y NOMBRE2 a ambos jugadores cuando los tengan."""
    if len(clientes) < 2:
        return  # esperar al otro jugador

    try:
        clientes[0].sendall(f"NOMBRE1:{nombres[0]}".encode())
        clientes[0].sendall(f"NOMBRE2:{nombres[1]}".encode())

        clientes[1].sendall(f"NOMBRE1:{nombres[0]}".encode())
        clientes[1].sendall(f"NOMBRE2:{nombres[1]}".encode())
    except:
        pass


def main():
    global clientes

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 5000))
    server.listen(2)

    print("SERVIDOR LISTO — Esperando jugadores...")

    try:
        while len(clientes) < 2:
            conn, addr = server.accept()
            with clientes_lock:
                clientes.append(conn)

            index = len(clientes) - 1  # 0 ó 1
            threading.Thread(target=manejar_cliente, args=(conn, addr, index), daemon=True).start()

    except KeyboardInterrupt:
        print("Apagando servidor...")
    finally:
        for c in clientes:
            try:
                c.close()
            except:
                pass
        server.close()


if __name__ == "__main__":
    main()
