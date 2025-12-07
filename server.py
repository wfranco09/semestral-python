import socket
import threading

clientes = []
clientes_lock = threading.Lock()

def manejar_cliente(conn, addr):
    print(f"Jugador conectado: {addr}")
    with clientes_lock:
        clientes.append(conn)

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            # reenviar jugada a todos menos al que la envió 
            with clientes_lock:
                for c in clientes.copy():
                    if c != conn:
                        try:
                            c.sendall(data)
                        except Exception as e:
                            print("Error al enviar a un cliente:", e)
                            try:
                                clientes.remove(c)
                                c.close()
                            except:
                                pass
    except Exception as e:
        print("Excepción en cliente:", e)
    finally:
        print("Jugador desconectado:", addr)
        with clientes_lock:
            try:
                clientes.remove(conn)
            except ValueError:
                pass
        conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 5000))
    server.listen(2)
    print("SERVIDOR LISTO — Esperando jugadores...")

    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Apagando servidor...")
    finally:
        with clientes_lock:
            for c in clientes:
                try:
                    c.close()
                except:
                    pass
        server.close()

if __name__ == "__main__":
    main()
