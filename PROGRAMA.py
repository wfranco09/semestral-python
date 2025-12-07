import socket
import threading
import tkinter as tk
from tkinter import Button, Label, Tk, simpledialog, messagebox
import random

# ==================== CONFIGURACIÓN INICIAL ====================
# Valores por defecto para la conexión
IP_SERVIDOR_DEFECTO = "100.94.222.75"
PUERTO_DEFECTO = 5000

# Ventana temporal para los diálogos de configuración
root_cfg = Tk()
root_cfg.withdraw()  # Ocultar la ventana principal

# Solicitar IP del servidor al usuario
ip_input = simpledialog.askstring(
    "Conexión",
    "IP del servidor (LAN o Tailscale 100.x.x.x):",
    initialvalue=IP_SERVIDOR_DEFECTO,
)
if not ip_input:
    ip_input = IP_SERVIDOR_DEFECTO

# Solicitar puerto del servidor al usuario
puerto_input = simpledialog.askinteger(
    "Conexión",
    "Puerto del servidor:",
    initialvalue=PUERTO_DEFECTO,
)
if not puerto_input:
    puerto_input = PUERTO_DEFECTO

IP_SERVIDOR = ip_input
PUERTO = puerto_input

# ==================== CONEXIÓN AL SERVIDOR ====================
# Crear socket TCP/IP para la conexión
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Intentar conectar al servidor
    client.connect((IP_SERVIDOR, PUERTO))
    print("Conectado al servidor.")
except Exception as e:
    # Mostrar error si falla la conexión
    messagebox.showerror("Error", f"No se pudo conectar al servidor:\n{e}")
    raise SystemExit(1)

# Solicitar nombre del jugador
nombre_local = simpledialog.askstring("Identificación", "Ingresa tu nombre:")
if not nombre_local:
    nombre_local = "Jugador"

# Enviar nombre al servidor
client.sendall((f"NOMBRE:{nombre_local}\n").encode())

# ==================== VARIABLES GLOBALES DEL JUEGO ====================
# Nombres de los jugadores (se actualizan desde el servidor)
nombre_jugador1 = "Jugador 1"
nombre_jugador2 = "Jugador 2"

# Indica si este cliente es el Jugador 1 (True) o Jugador 2 (False)
ES_JUGADOR_1 = None

# Matriz 3D que almacena el estado del tablero [z][y][x]
# 0 = vacío, -1 = jugador 1 (X), 1 = jugador 2 (O)
jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]

# Lista de botones de la interfaz gráfica
botones = []

# Coordenadas de la última jugada
X = Y = Z = 0

# Bandera: 1 = juego terminado, 0 = juego en curso
g = 0

# Turno actual: 0 = jugador 1, 1 = jugador 2
jugador = 0

# Contadores de victorias
contador_ganadas_jugador1 = 0
contador_ganadas_jugador2 = 0

# ==================== RECEPCIÓN DESDE EL SERVIDOR ====================
# Buffer para acumular datos recibidos de la red
buffer_red = ""  

def aplicar_jugada_remota(i):
    """Aplica una jugada recibida del oponente"""
    botonClick(i, enviar=False)


def recibir_jugadas():
    """Hilo que escucha continuamente mensajes del servidor"""
    global nombre_jugador1, nombre_jugador2, buffer_red
    global puntaje_jugador1, puntaje_jugador2, ES_JUGADOR_1
    
    while True:
        try:
            # Recibir datos del servidor (máximo 1024 bytes)
            data = client.recv(1024)
            if not data:
                print("Conexión cerrada por el servidor.")
                break

            # Agregar datos al buffer y procesar línea por línea
            buffer_red += data.decode()

            while "\n" in buffer_red:
                # Separar la primera línea completa
                linea, buffer_red = buffer_red.split("\n", 1)
                texto = linea

                # Procesar comando NOMBRE1 (nombre del jugador 1)
                if texto.startswith("NOMBRE1:"):
                    nombre_jugador1 = texto.replace("NOMBRE1:", "")
                    puntaje_jugador1.config(
                        text=f"{nombre_jugador1}: {contador_ganadas_jugador1}"
                    )
                    # Identificar si soy el jugador 1
                    if ES_JUGADOR_1 is None and nombre_jugador1 == nombre_local:
                        ES_JUGADOR_1 = True
                    continue

                # Procesar comando NOMBRE2 (nombre del jugador 2)
                if texto.startswith("NOMBRE2:"):
                    nombre_jugador2 = texto.replace("NOMBRE2:", "")
                    puntaje_jugador2.config(
                        text=f"{nombre_jugador2}: {contador_ganadas_jugador2}"
                    )
                    # Identificar si soy el jugador 2
                    if ES_JUGADOR_1 is None and nombre_jugador2 == nombre_local:
                        ES_JUGADOR_1 = False
                    continue

                # Procesar jugadas (recibir índice de botón jugado)
                if texto.isdigit():
                    i = int(texto)
                    print("Oponente jugó:", i)
                    # Ejecutar jugada en el hilo principal de tkinter
                    tablero.after(0, aplicar_jugada_remota, i)

        except Exception as e:
            print("Error al recibir:", e)
            break

# ==================== LÓGICA DEL JUEGO ====================
def crearBoton(valor, i):
    """Crea un botón para el tablero con su índice asociado"""
    return Button(
        tablero,
        text=valor,
        width=5,
        height=1,
        font=("Helvetica", 15),
        command=lambda: botonClick(i, enviar=True),
    )


def botonClick(i, enviar=True):
    """
    Maneja el clic en un botón del tablero
    i: índice del botón (0-63)
    enviar: si True, envía la jugada al servidor
    """
    global jugador, jugadas, X, Y, Z, g, ES_JUGADOR_1
    
    # Calcular coordenadas 3D desde el índice lineal
    Z = int(i / 16)  # Capa (0-3)
    y = i % 16
    Y = int(y / 4)   # Fila (0-3)
    X = y % 4        # Columna (0-3)

    # No permitir jugadas si el juego terminó
    if g:
        return

    # Validar turno: solo permitir jugar cuando es tu turno
    if enviar and ES_JUGADOR_1 is not None:
        if ES_JUGADOR_1 and jugador != 0:  # Soy jugador 1, pero no es mi turno
            return  
        if (not ES_JUGADOR_1) and jugador != 1:  # Soy jugador 2, pero no es mi turno
            return 

    # Verificar que la casilla esté vacía
    if not jugadas[Z][Y][X]:
        # Marcar la jugada: -1 para X, 1 para O
        marca = -1 if jugador == 0 else 1
        jugadas[Z][Y][X] = marca
        
        # Actualizar texto del botón
        texto_marca = "X" if jugador == 0 else "O"
        botones[i].config(
            text=texto_marca,
            font="arial 15",
            fg="blue" if jugador == 0 else "red",
        )

        # Enviar jugada al servidor (si es jugada local)
        if enviar:
            try:
                client.sendall(f"{i}\n".encode())
            except Exception as e:
                print("Error al enviar jugada:", e)

        # Verificar si hay ganador
        if verificar_todo(X, Y, Z):
            ganador()
            return

        # Cambiar turno al otro jugador
        jugador_cambia()


def jugador_cambia():
    """Cambia el turno al otro jugador"""
    global jugador
    jugador = 1 - jugador
    texto_actual.config(text=(nombre_jugador1 if jugador == 0 else nombre_jugador2))


def ganador():
    """Muestra mensaje de victoria y actualiza contadores"""
    global jugador, g, contador_ganadas_jugador1, contador_ganadas_jugador2
    
    nombre = nombre_jugador1 if jugador == 0 else nombre_jugador2
    texto_ganador = Label(tablero, text=f"🎉 {nombre} GANÓ 🎉",
                          font=("Arial Black", 20), fg="#FFDD00", bg="#18324e")
    texto_ganador.place(x=650, y=550)
    
    # Marcar el juego como terminado
    g = 1
    
    # Actualizar contador de victorias
    if jugador == 0:
        contador_ganadas_jugador1 += 1
    else:
        contador_ganadas_jugador2 += 1
    actualizar_puntaje()


def verificar_todo(X, Y, Z):
    """
    Verifica todas las posibles líneas ganadoras desde la posición (X,Y,Z)
    Retorna True si hay 4 en línea
    """
    return (
        horizontal(Y, Z)
        or vertical(X, Z)
        or profundidad(X, Y)
        or diagonal_frontal(Z)
        or diagonal_vertical(X)
        or diagonal_horizontal(Y)
        or diagonal_cruzada()
    )


def horizontal(Y, Z):
    """Verifica línea horizontal en la capa Z, fila Y"""
    return abs(sum(jugadas[Z][Y][x] for x in range(4))) == 4


def vertical(X, Z):
    """Verifica línea vertical en la capa Z, columna X"""
    return abs(sum(jugadas[Z][y][X] for y in range(4))) == 4


def profundidad(X, Y):
    """Verifica línea en profundidad (atravesando capas) en posición X,Y"""
    return abs(sum(jugadas[z][Y][X] for z in range(4))) == 4


def diagonal_frontal(Z):
    """Verifica diagonales frontales en la capa Z"""
    return (
        abs(sum(jugadas[Z][i][i] for i in range(4))) == 4
        or abs(sum(jugadas[Z][i][3 - i] for i in range(4))) == 4
    )


def diagonal_vertical(X):
    """Verifica diagonales verticales en la columna X"""
    return (
        abs(sum(jugadas[i][i][X] for i in range(4))) == 4
        or abs(sum(jugadas[i][3 - i][X] for i in range(4))) == 4
    )


def diagonal_horizontal(Y):
    """Verifica diagonales horizontales en la fila Y"""
    return (
        abs(sum(jugadas[i][Y][i] for i in range(4))) == 4
        or abs(sum(jugadas[3 - i][Y][i] for i in range(4))) == 4
    )


def diagonal_cruzada():
    """Verifica las 4 diagonales tridimensionales que cruzan todo el cubo"""
    return (
        abs(sum(jugadas[i][i][i] for i in range(4))) == 4
        or abs(sum(jugadas[i][i][3 - i] for i in range(4))) == 4
        or abs(sum(jugadas[i][3 - i][i] for i in range(4))) == 4
        or abs(sum(jugadas[i][3 - i][3 - i] for i in range(4))) == 4
    )


def tableronuevo():
    global jugadas, g, jugador, texto_ganador
    jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
    g = 0
    jugador = 0

    for b in range(64):
        botones[b].config(text=' ')

    texto_actual.config(text=nombre_jugador1)

    if texto_ganador:
        texto_ganador.destroy()
        texto_ganador = None


def actualizar_puntaje():
    """Actualiza las etiquetas con el puntaje actual"""
    puntaje_jugador1.config(
        text=f"{nombre_jugador1}: {contador_ganadas_jugador1}"
    )
    puntaje_jugador2.config(
        text=f"{nombre_jugador2}: {contador_ganadas_jugador2}"
    )

# ==================== INTERFAZ GRÁFICA (TKINTER) ====================

# Crear ventana principal
tablero = Tk()
tablero.title('Tic Tac Toe 3D ONLINE')
tablero.geometry("1040x720+100+50")
tablero.resizable(0, 0)
tablero.config(bg='#18324e')

neon_colors = ['#FF073A', '#FF8C00', '#FFD300', '#0AFF99', '#00CFFF', '#8A2BE2']
def animar_titulo():
    color = random.choice(neon_colors)
    titulo.config(fg=color)
    tablero.after(200, animar_titulo)

puntaje_jugador1 = Label(tablero, text=f'{nombre_jugador1}: 0',
                         font=('arial', 20), fg='white', bg='#18324e')
puntaje_jugador1.place(x=50, y=100)

puntaje_jugador2 = Label(tablero, text=f'{nombre_jugador2}: 0',
                         font=('arial', 20), fg='white', bg='#18324e')
puntaje_jugador2.place(x=50, y=150)

Button(tablero, text="❌ Salir",
       font=("Arial Black", 12),
       bg="#e63946", fg="white",
       width=12,
       command=tablero.destroy).place(x=700, y=650)

Button(tablero, text="🔄 Reiniciar",
       font=("Arial Black", 12),
       bg="#0077b6", fg="white",
       width=12,
       command=tableronuevo).place(x=850, y=650)

titulo = Label(tablero, text='Tic Tac Toe 3D Online',
               font=('arial', 30, 'bold'), fg='black', bg='#18324e')
titulo.place(x=350, y=10)
animar_titulo()

# Crear los 64 botones del tablero (4x4x4)
for b in range(64):
    botones.append(crearBoton(" ", b))

# Posicionar botones en una cuadrícula 4x4 x 4 capas
contador = 0
for z in range(3, -1, -1):  # De capa superior a inferior
    for y in range(4):       # Filas
        for x in range(4):   # Columnas
            botones[contador].grid(row=y + z * 4, column=x + (3 - z) * 4)
            contador += 1

# Etiqueta que muestra el turno actual
texto_actual = Label(
    tablero,
    text=nombre_jugador1,
    font=("arial", 20),
    fg="white",
    bg="#18324e",
)
texto_actual.place(x=500, y=620)

# Iniciar hilo para recibir jugadas del servidor
threading.Thread(target=recibir_jugadas, daemon=True).start()

# Iniciar bucle principal de la interfaz
tablero.mainloop()