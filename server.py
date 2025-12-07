import socket
import threading

# ==================== CONSTANTES ====================
EOL = "\n"  # Delimitador de fin de línea
BUFSIZE = 1024  # Tamaño del buffer para recibir datos


def recv_line(sock, buffer_dict, key):
    # Recuperar buffer pendiente o iniciar vacío
    buffer = buffer_dict.get(key, "")
    
    while True:
        # Si ya tenemos una línea completa, devolverla
        if EOL in buffer:
            line, buffer = buffer.split(EOL, 1)
            buffer_dict[key] = buffer  # Guardar lo que sobra
            return line
        
        # Leer más datos del socket
        data = sock.recv(BUFSIZE)
        if not data:  # Conexión cerrada
            return None
        
        # Agregar nuevos datos al buffer
        buffer += data.decode("utf-8")


def handle_pair(c1, c2):
    """
    Maneja la comunicación entre dos clientes conectados.
    Intercambia nombres y luego reenvía todas las jugadas entre ellos.
    
    Args:
        c1: socket del jugador 1
        c2: socket del jugador 2
    """
    # Diccionario para buffers de cada cliente
    buffers = {}

    # ===== INTERCAMBIO DE NOMBRES =====
    # Recibir nombre de cada jugador (formato: "NOMBRE:nombre")
    name1_full = recv_line(c1, buffers, "c1")
    name2_full = recv_line(c2, buffers, "c2")
    
    # Si alguno se desconecta, cerrar ambas conexiones
    if name1_full is None or name2_full is None:
        c1.close()
        c2.close()
        return

    # Extraer solo el nombre (quitar "NOMBRE:")
    name1 = name1_full.replace("NOMBRE:", "", 1)
    name2 = name2_full.replace("NOMBRE:", "", 1)

    # Enviar ambos nombres a ambos clientes
    c1.sendall(f"NOMBRE1:{name1}{EOL}".encode("utf-8"))
    c1.sendall(f"NOMBRE2:{name2}{EOL}".encode("utf-8"))
    c2.sendall(f"NOMBRE1:{name1}{EOL}".encode("utf-8"))
    c2.sendall(f"NOMBRE2:{name2}{EOL}".encode("utf-8"))

    # ===== REENVÍO DE MENSAJES =====
    def forward(src, dst, key_src):
        """
        Lee mensajes de un cliente (src) y los reenvía al otro (dst).
        Se ejecuta en un hilo separado para cada dirección.
        
        Args:
            src: socket origen (quien envía)
            dst: socket destino (quien recibe)
            key_src: clave del buffer del origen
        """
        while True:
            # Leer un mensaje completo del origen
            msg = recv_line(src, buffers, key_src)
            if msg is None:  # Conexión cerrada
                break
            
            # Reenviar el mensaje al destino
            dst.sendall(f"{msg}{EOL}".encode("utf-8"))
        
        # Cerrar ambas conexiones cuando uno se desconecta
        src.close()
        dst.close()

    # Crear hilos bidireccionales para el reenvío
    t1 = threading.Thread(target=forward, args=(c1, c2, "c1"))  # c1 → c2
    t2 = threading.Thread(target=forward, args=(c2, c1, "c2"))  # c2 → c1
    
    # Iniciar ambos hilos
    t1.start()
    t2.start()
    
    # Esperar a que ambos hilos terminen (cuando se desconecten)
    t1.join()
    t2.join()


def main():
    """
    Función principal del servidor.
    Acepta dos conexiones y las empareja para jugar.
    """
    # ===== CONFIGURACIÓN DEL SERVIDOR =====
    HOST = ""    # Escuchar en todas las interfaces de red
    PORT = 5000  # Puerto del servidor

    # Crear socket TCP/IP
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Permitir reusar la dirección inmediatamente después de cerrar
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Vincular socket al puerto
    srv.bind((HOST, PORT))
    
    # Escuchar hasta 2 conexiones pendientes
    srv.listen(2)
    print(f"SERVER: escuchando en puerto {PORT}...")

    # ===== ACEPTAR JUGADORES =====
    print("SERVER: esperando jugadores...")
    
    # Esperar primera conexión (Jugador 1)
    c1, addr1 = srv.accept()
    print("SERVER: jugador 1 conectado desde", addr1)
    
    # Esperar segunda conexión (Jugador 2)
    c2, addr2 = srv.accept()
    print("SERVER: jugador 2 conectado desde", addr2)

    # Manejar la partida entre estos dos jugadores
    handle_pair(c1, c2)

    # Una vez termina la partida, cerrar el servidor
    print("SERVER: partida terminada, cerrando servidor.")
    srv.close()


# ===== PUNTO DE ENTRADA =====
if __name__ == "__main__":
    main()
