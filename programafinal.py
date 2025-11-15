# cliente_vpython.py
import socket
import threading
from vpython import *
import time

# =============== NOMBRE DEL JUGADOR =================
player_name = input("Tu nombre: ").strip() or "Jugador"

# =============== CONFIGURACIÓN DE RED =================
IP_SERVIDOR = "192.168.1.4"   # ← CAMBIA ESTO POR LA IP DE TU SERVIDOR
PUERTO = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((IP_SERVIDOR, PUERTO))
print("Conectado al servidor.")

# Enviar nombre
client.send(f"NAME:{player_name}".encode())

# =====================================================================
#               LÓGICA Y ESTRUCTURAS DEL JUEGO 3D
# =====================================================================
jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
celdas = {}
marcadores = {}
selected_index = 0
local_player_id = None
turno = 0
g = 0

contador_ganadas_jugador1 = 0
contador_ganadas_jugador2 = 0
opponent_name = "Esperando..."

def index_to_xyz(i):
    Z = int(i / 16)
    y = i % 16
    Y = int(y / 4)
    X = y % 4
    return X, Y, Z

def xyz_to_index(X, Y, Z):
    return Z*16 + Y*4 + X

# =====================================================================
#                          INTERFAZ 3D
# =====================================================================
scene.background = color.white
scene.title = "Tic Tac Toe 3D - VPython"
scene.width = 1000
scene.height = 700

label_score = wtext(text=f"<b>{player_name} (X): 0</b>    <b>{opponent_name} (O): 0</b>\n")
wtext(text=" ")
label_turn = wtext(text=f"Turno: ?\n")
label_info = wtext(text=f"Tú: {player_name}    Oponente: {opponent_name}\n")
wtext(text="\n")

index = 0
spacing = 2.4
offset = vector(-spacing*1.5, -spacing*1.5, -spacing*1.5)

for Z in range(4):
    for Y in range(4):
        for X in range(4):
            pos = vector(X*spacing, Y*spacing, Z*spacing) + offset
            cubo = box(pos=pos, size=vector(1.6,1.6,1.6), opacity=0.18, color=color.gray(0.6))
            cubo.index = index
            celdas[index] = cubo
            marcadores[index] = []
            index += 1

prev_selected = None
def highlight_cell(i):
    global prev_selected
    if prev_selected is not None:
        celdas[prev_selected].color = color.gray(0.6)
        celdas[prev_selected].opacity = 0.18

    prev_selected = i
    celdas[i].color = color.yellow
    celdas[i].opacity = 0.35

def dibujar_x(index):
    cubo = celdas[index]
    p = cubo.pos
    b1 = box(pos=p, size=vector(1.8,0.25,0.25), axis=vector(1,1,0), color=color.red)
    b2 = box(pos=p, size=vector(1.8,0.25,0.25), axis=vector(-1,1,0), color=color.red)
    marcadores[index].extend([b1, b2])

def dibujar_o(index):
    cubo = celdas[index]
    p = cubo.pos
    r = ring(pos=p, axis=vector(0,0,1), radius=0.9, thickness=0.25, color=color.blue)
    marcadores[index].append(r)

def actualizar_labels():
    label_score.text = f"<b>{player_name} (X): {contador_ganadas_jugador1}</b>    <b>{opponent_name} (O): {contador_ganadas_jugador2}</b>\n"
    t = f"Turno: Jugador {turno+1}"
    if local_player_id is not None:
        if turno == local_player_id:
            t += " (Tu turno)"
        else:
            t += " (Oponente)"
    label_turn.text = t + "\n"
    label_info.text = f"Tú: {player_name}    Oponente: {opponent_name}\n"

# =====================================================================
#                          JUGADAS
# =====================================================================
def poner_jugada(i, enviar=True):
    global turno, g, contador_ganadas_jugador1, contador_ganadas_jugador2

    if local_player_id is None:
        print("Aún no sabes tu id.")
        return

    if turno != local_player_id:
        print("No es tu turno.")
        return

    X, Y, Z = index_to_xyz(i)
    if jugadas[Z][Y][X] != 0:
        return

    if local_player_id == 0:
        jugadas[Z][Y][X] = -1
        dibujar_x(i)
    else:
        jugadas[Z][Y][X] = 1
        dibujar_o(i)

    if enviar:
        client.send(str(i).encode())

    if verificar_todo(X,Y,Z):
        g = 1
        if local_player_id == 0:
            contador_ganadas_jugador1 += 1
        else:
            contador_ganadas_jugador2 += 1
        actualizar_labels()
        label_turn.text = f"¡GANASTE!\n"
        return

    turno = 1 - turno
    actualizar_labels()

def aplicar_jugada_remota(i):
    global turno, g, contador_ganadas_jugador1, contador_ganadas_jugador2

    X, Y, Z = index_to_xyz(i)
    if jugadas[Z][Y][X] != 0:
        return

    if local_player_id == 0:
        jugadas[Z][Y][X] = 1
        dibujar_o(i)
    else:
        jugadas[Z][Y][X] = -1
        dibujar_x(i)

    if verificar_todo(X,Y,Z):
        g = 1
        if local_player_id == 0:
            contador_ganadas_jugador2 += 1
        else:
            contador_ganadas_jugador1 += 1
        actualizar_labels()
        label_turn.text = f"¡Perdiste!\n"
        return

    turno = 1 - turno
    actualizar_labels()

# =====================================================================
#                    VERIFICACIÓN DE LÍNEAS
# =====================================================================
def verificar_todo(X,Y,Z):
    return (
        horizontal(Y,Z) or vertical(X,Z) or profundidad(X,Y) or
        diagonal_frontal(Z) or diagonal_vertical(X) or
        diagonal_horizontal(Y) or diagonal_cruzada()
    )

def horizontal(Y,Z):
    return abs(sum(jugadas[Z][Y][x] for x in range(4))) == 4

def vertical(X,Z):
    return abs(sum(jugadas[Z][y][X] for y in range(4))) == 4

def profundidad(X,Y):
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

# =====================================================================
#                          EVENTOS
# =====================================================================
def on_click(evt):
    obj = evt.pick
    if obj and hasattr(obj, "index"):
        global selected_index
        selected_index = obj.index
        highlight_cell(selected_index)

scene.bind("click", on_click)

def keydown(evt):
    global selected_index
    key = evt.key.lower()
    X, Y, Z = index_to_xyz(selected_index)

    if key == "left": X = max(0, X-1)
    elif key == "right": X = min(3, X+1)
    elif key == "up": Y = min(3, Y+1)
    elif key == "down": Y = max(0, Y-1)
    elif key == "w": Z = min(3, Z+1)
    elif key == "s": Z = max(0, Z-1)
    elif key in ("enter", " "):
        i = xyz_to_index(X,Y,Z)
        poner_jugada(i)
        return

    selected_index = xyz_to_index(X,Y,Z)
    highlight_cell(selected_index)

scene.bind("keydown", keydown)

def reiniciar(ev=None):
    global jugadas, marcadores, g, turno
    jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
    for idx in marcadores:
        for m in marcadores[idx]:
            m.visible = False
        marcadores[idx] = []
    g = 0
    turno = 0
    actualizar_labels()

button(bind=reiniciar, text="Reiniciar tablero")

highlight_cell(selected_index)
actualizar_labels()

# =====================================================================
#                    HILO DE RECEPCIÓN
# =====================================================================
def recibir():
    global local_player_id, opponent_name, turno

    while True:
        try:
            data = client.recv(1024)
            if not data:
                break

            text = data.decode()

            if text.startswith("START:"):
                local_player_id = int(text.split(":")[1])
                turno = 0
                actualizar_labels()
                continue

            if text.startswith("NAME:"):
                n = text.split(":",1)[1]
                if n != player_name:
                    opponent_name = n
                    actualizar_labels()
                continue

            # jugada remota
            try:
                i = int(text)
                aplicar_jugada_remota(i)
            except:
                pass

        except:
            break

threading.Thread(target=recibir, daemon=True).start()

# =====================================================================
#                      LOOP PRINCIPAL
# =====================================================================
try:
    while True:
        rate(30)
except KeyboardInterrupt:
    pass
finally:
    client.close()
