# server.py
import socket
import threading

clientes = []
lock = threading.Lock()

def manejar_cliente(conn, addr):
    print(f"Jugador conectado: {addr}")
    with lock:
        clientes.append(conn)

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            # reenviar jugada a todos menos al que la envió
            with lock:
                for c in clientes.copy():
                    try:
                        if c != conn:
                            c.send(data)
                    except Exception as e:
                        # Si falla enviar, removemos el cliente
                        try:
                            clientes.remove(c)
                            c.close()
                        except:
                            pass
    except Exception as e:
        pass

    print("Jugador desconectado:", addr)
    with lock:
        if conn in clientes:
            clientes.remove(conn)
    try:
        conn.close()
    except:
        pass

def main():
    HOST = "0.0.0.0"  # escuchar todas las interfaces
    PORT = 5000

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(2)
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
