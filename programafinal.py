# cliente_vpython.py
import socket
import threading
from vpython import *
import time

# =============== CONFIGURACIÓN DE RED =================
IP_SERVIDOR = "172.29.34.2"   # cambia a la IP del servidor si hace falta
PUERTO = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((IP_SERVIDOR, PUERTO))
print("Conectado al servidor.")

# ========== LÓGICA DEL JUEGO (mantener mismo esquema de índices) ==========
jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
celdas = {}    # index -> objeto 3D
marcadores = {}  # index -> lista de objetos dibujados (para limpiar si reinicias)
botones_ui = {}  # contenedor para controles vpython
botones_3d = []
jugador = 0     # 0 = jugador1 (X), 1 = jugador2 (O)
g = 0
contador_ganadas_jugador1 = 0
contador_ganadas_jugador2 = 0

# Utilidades para index <-> XYZ
def index_to_xyz(i):
    Z = int(i / 16)
    y = i % 16
    Y = int(y / 4)
    X = y % 4
    return X, Y, Z

def xyz_to_index(X, Y, Z):
    return Z*16 + Y*4 + X

# ========== VISIBLE 3D (VPython) ==========
scene.background = color.white
scene.title = "Tic Tac Toe 3D - VPython"
scene.width = 1000
scene.height = 700

# Panel de texto simple
label_score = wtext(text=f"<b>Jugador1 (X): {contador_ganadas_jugador1}</b>    <b>Jugador2 (O): {contador_ganadas_jugador2}</b>\n")
wtext(text="   ")
label_turn = wtext(text=f"Turno: Jugador {jugador+1}\n")
wtext(text="\n")

# Crear cubos 4x4x4; los mantenemos con index igual al de tu cliente tkinter
index = 0
spacing = 2.4
offset = vector(-spacing*1.5, -spacing*1.5, -spacing*1.5)  # centrar
for Z in range(4):
    for Y in range(4):
        for X in range(4):
            pos = vector(X*spacing, Y*spacing, Z*spacing) + offset
            cubo = box(pos=pos, size=vector(1.6,1.6,1.6), opacity=0.07, color=color.gray(0.5))
            cubo.index = index
            celdas[index] = cubo
            marcadores[index] = []
            index += 1

# Dibujar X u O en la celda dada (coordenadas en espacio 3D derivadas de pos del cubo)
def dibujar_x(index):
    cubo = celdas[index]
    p = cubo.pos
    # dos barras cruzadas
    b1 = box(pos=p, size=vector(1.8,0.25,0.25), axis=vector(1,1,0), up=vector(0,0,1), color=color.blue)
    b2 = box(pos=p, size=vector(1.8,0.25,0.25), axis=vector(-1,1,0), up=vector(0,0,1), color=color.blue)
    marcadores[index].extend([b1,b2])

def dibujar_o(index):
    cubo = celdas[index]
    p = cubo.pos
    # ring (anillo)
    r = ring(pos=p, axis=vector(0,0,1), radius=0.9, thickness=0.25, up=vector(0,1,0), color=color.red)
    marcadores[index].append(r)

# Lógica cuando se hace una jugada (local o remota). enviar controla si manda al servidor.
def poner_jugada(i, enviar=True):
    global jugador, g, contador_ganadas_jugador1, contador_ganadas_jugador2
    X, Y, Z = index_to_xyz(i)
    if g:
        return
    if not jugadas[Z][Y][X]:
        if jugador == 0:
            jugadas[Z][Y][X] = -1
            dibujar_x(i)
        else:
            jugadas[Z][Y][X] = 1
            dibujar_o(i)

        if enviar:
            try:
                client.send(str(i).encode())
            except Exception as e:
                print("Error enviando jugada:", e)

        if verificar_todo(X, Y, Z):
            # ganar
            g = 1
            if jugador == 0:
                contador_ganadas_jugador1 += 1
            else:
                contador_ganadas_jugador2 += 1
            actualizar_puntaje()
            label_turn.text = f"¡Jugador {jugador+1} GANÓ!\n"
            return

        jugador = not jugador
        label_turn.text = f"Turno: Jugador {jugador+1}\n"
    else:
        print("Jugada inválida")

def aplicar_jugada_remota(i):
    # cuando recibimos del server, aplicamos sin reenviar
    poner_jugada(i, enviar=False)

# Las mismas funciones de verificación que ya tienes
def verificar_todo(X, Y, Z):
    return (
        horizontal(Y, Z) or
        vertical(X, Z) or
        profundidad(X, Y) or
        diagonal_frontal(Z) or
        diagonal_vertical(X) or
        diagonal_horizontal(Y) or
        diagonal_cruzada()
    )

def horizontal(Y, Z):
    return abs(sum(jugadas[Z][Y][x] for x in range(4))) == 4

def vertical(X, Z):
    return abs(sum(jugadas[Z][y][X] for y in range(4))) == 4

def profundidad(X, Y):
    return abs(sum(jugadas[z][Y][X] for z in range(4))) == 4

def diagonal_frontal(Z):
    return (
        abs(sum(jugadas[Z][i][i] for i in range(4))) == 4 or
        abs(sum(jugadas[Z][i][3-i] for i in range(4))) == 4
    )

def diagonal_vertical(X):
    return (
        abs(sum(jugadas[i][i][X] for i in range(4))) == 4 or
        abs(sum(jugadas[i][3-i][X] for i in range(4))) == 4
    )

def diagonal_horizontal(Y):
    return (
        abs(sum(jugadas[i][Y][i] for i in range(4))) == 4 or
        abs(sum(jugadas[3-i][Y][i] for i in range(4))) == 4
    )

def diagonal_cruzada():
    return (
        abs(sum(jugadas[i][i][i] for i in range(4))) == 4 or
        abs(sum(jugadas[i][i][3-i] for i in range(4))) == 4 or
        abs(sum(jugadas[i][3-i][i] for i in range(4))) == 4 or
        abs(sum(jugadas[i][3-i][3-i] for i in range(4))) == 4
    )

def actualizar_puntaje():
    # actualizar texto simple
    label_score.text = f"<b>Jugador1 (X): {contador_ganadas_jugador1}</b>    <b>Jugador2 (O): {contador_ganadas_jugador2}</b>\n"

def reiniciar_tablero(ev=None):
    global jugadas, marcadores, g, jugador
    jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
    # borrar marcadores 3D
    for idx, objs in marcadores.items():
        for o in objs:
            try:
                o.visible = False
                del o
            except:
                pass
        marcadores[idx] = []
    g = 0
    jugador = 0
    label_turn.text = f"Turno: Jugador {jugador+1}\n"

# Bind click event
def on_click(evt):
    evt.pick  # objeto seleccionado por click (puede ser None)
    obj = evt.pick
    if obj and hasattr(obj, "index"):
        i = obj.index
        poner_jugada(i, enviar=True)

scene.bind("click", on_click)

# UI: botón reiniciar (vpython)
button(bind=reiniciar_tablero, text="Reiniciar tablero")

# ========== HILO DE RECEPCIÓN ==========
def recibir_jugadas():
    while True:
        try:
            data = client.recv(1024).decode()
            if not data:
                break
            # si llega algo que no sea un número, ignorar
            try:
                i = int(data)
                print("Oponente jugó:", i)
                aplicar_jugada_remota(i)
            except:
                print("Mensaje no-numérico recibido:", data)
        except Exception as e:
            print("Error recibiendo:", e)
            break

threading.Thread(target=recibir_jugadas, daemon=True).start()

# VPython tiene su propio loop de render; para que el script no acabe:
while True:
    rate(30)
    # loop vacío - todo se maneja por eventos
    pass
