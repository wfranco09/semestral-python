# cliente_vpython.py
import socket
import threading
from vpython import *
import time

# Pide el nombre antes de conectar
player_name = input("Tu nombre (ej. Winston Franco): ").strip() or "Jugador"

# =============== CONFIGURACIÓN DE RED =================
IP_SERVIDOR = "192.168.1.4"   # pon aquí la IP del servidor
PUERTO = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((IP_SERVIDOR, PUERTO))
print("Conectado al servidor.")

# Enviamos nuestro nombre al servidor
try:
    client.send(f"NAME:{player_name}".encode())
except:
    pass

# ========== LÓGICA DEL JUEGO (mantener mismo esquema de índices) ==========
jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
celdas = {}         # index -> objeto 3D (box)
marcadores = {}     # index -> lista de objetos dibujados (X/O)
selected_index = 0  # celda seleccionada (para moverse con teclado)
local_player_id = None  # 0 o 1 (recibido del servidor)
turno = 0           # 0 empieza por defecto; servidor no fuerza, cliente sí
jugador = 0         # usado para dibujar (sincronizado con turno local)
g = 0
contador_ganadas_jugador1 = 0
contador_ganadas_jugador2 = 0

opponent_name = "Esperando..."
# Utilidades index <-> XYZ
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

# HUD: score, turno, nombres
label_score = wtext(text=f"<b>{player_name} (X): {contador_ganadas_jugador1}</b>    <b>{opponent_name} (O): {contador_ganadas_jugador2}</b>\n")
wtext(text="   ")
label_turn = wtext(text=f"Turno: {'?' if local_player_id is None else ('Jugador ' + str(turno+1))}\n")
wtext(text="\n")
label_info = wtext(text=f"Tú: {player_name}    Oponente: {opponent_name}\n")
wtext(text="\n")

# Crear cubos 4x4x4
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

# resaltado seleccionado
prev_selected = None
def highlight_cell(i):
    global prev_selected
    if prev_selected is not None and prev_selected in celdas:
        # restaurar
        celdas[prev_selected].color = color.gray(0.6)
        celdas[prev_selected].opacity = 0.18
    prev_selected = i
    if i in celdas:
        celdas[i].color = color.yellow
        celdas[i].opacity = 0.35

# Dibujar X (rojo) y O (azul)
def dibujar_x(index):
    cubo = celdas[index]
    p = cubo.pos
    b1 = box(pos=p, size=vector(1.8,0.25,0.25), axis=vector(1,1,0), up=vector(0,0,1), color=color.red)
    b2 = box(pos=p, size=vector(1.8,0.25,0.25), axis=vector(-1,1,0), up=vector(0,0,1), color=color.red)
    marcadores[index].extend([b1,b2])

def dibujar_o(index):
    cubo = celdas[index]
    p = cubo.pos
    r = ring(pos=p, axis=vector(0,0,1), radius=0.9, thickness=0.25, up=vector(0,1,0), color=color.blue)
    marcadores[index].append(r)

# actualiza HUD textos
def actualizar_labels():
    label_score.text = f"<b>{player_name} (X): {contador_ganadas_jugador1}</b>    <b>{opponent_name} (O): {contador_ganadas_jugador2}</b>\n"
    # Mostrar quien es turno, o "Tu turno" si coincide
    turno_text = f"Turno: Jugador {turno+1}"
    if local_player_id is not None:
        if turno == local_player_id:
            turno_text += " (Tu turno)"
        else:
            turno_text += " (Turno oponente)"
    label_turn.text = turno_text + "\n"
    label_info.text = f"Tú: {player_name}    Oponente: {opponent_name}\n"

# Lógica de jugada local/remota con control de turno
def poner_jugada(i, enviar=True):
    global turno, g, contador_ganadas_jugador1, contador_ganadas_jugador2
    if local_player_id is None:
        print("Aún no sabes tu id de jugador (esperando START).")
        return
    if g:
        return
    # solo permitir jugar si es tu turno
    if turno != local_player_id:
        print("No es tu turno.")
        return

    X, Y, Z = index_to_xyz(i)
    if not jugadas[Z][Y][X]:
        # si local_player_id == 0 -> X, else O
        if local_player_id == 0:
            jugadas[Z][Y][X] = -1
            dibujar_x(i)
        else:
            jugadas[Z][Y][X] = 1
            dibujar_o(i)

        # enviar jugada
        if enviar:
            try:
                client.send(str(i).encode())
            except Exception as e:
                print("Error enviando jugada:", e)

        # comprobar victoria
        if verificar_todo(X, Y, Z):
            g = 1
            if local_player_id == 0:
                contador_ganadas_jugador1 += 1
            else:
                contador_ganadas_jugador2 += 1
            actualizar_labels()
            ganador_nombre = player_name if local_player_id == jugador else opponent_name
            # mostrar mensaje con nombre ganador (local en este caso)
            label_turn.text = f"¡{player_name} (Jugador {local_player_id+1}) GANÓ!\n"
            return

        # pasar turno al otro
        turno = 1 - turno
        actualizar_labels()
    else:
        print("Jugada inválida")

def aplicar_jugada_remota(i):
    global turno, g, contador_ganadas_jugador1, contador_ganadas_jugador2
    # cuando recibimos del server, aplicamos sin reenviar
    X, Y, Z = index_to_xyz(i)
    if jugadas[Z][Y][X]:
        # ya ocupada (posible condición de carrera) -> ignorar
        return

    # marcar la jugada como la del otro
    if local_player_id == 0:
        # si yo soy 0, el otro es 1 -> el otro pone O (1)
        jugadas[Z][Y][X] = 1
        dibujar_o(i)
    else:
        jugadas[Z][Y][X] = -1
        dibujar_x(i)

    # comprobar victoria (del otro)
    if verificar_todo(X, Y, Z):
        g = 1
        if local_player_id == 0:
            contador_ganadas_jugador2 += 1
        else:
            contador_ganadas_jugador1 += 1
        actualizar_labels()
        # mostrar nombre del ganador (el otro)
        label_turn.text = f"¡{opponent_name} (Jugador {1-local_player_id+1}) GANÓ!\n"
        return

    # pasar turno
    turno = 1 - turno
    actualizar_labels()

# Verificaciones (misma lógica que tenías)
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

def reiniciar_tablero(ev=None):
    global jugadas, marcadores, g, turno
    jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
    for idx, objs in marcadores.items():
        for o in objs:
            try:
                o.visible = False
                del o
            except:
                pass
        marcadores[idx] = []
    g = 0
    turno = 0
    actualizar_labels()
    highlight_cell(selected_index)

# Manejo de clicks con mouse (opcional)
def on_click(evt):
    obj = evt.pick
    if obj and hasattr(obj, "index"):
        i = obj.index
        # mover selección virtual allí
        global selected_index
        selected_index = i
        highlight_cell(selected_index)

scene.bind("click", on_click)

# Manejo de teclado para moverte y colocar fichas
def keydown(evt):
    global selected_index
    key = evt.key.lower()
    X, Y, Z = index_to_xyz(selected_index)

    if key in ('left',):
        X = max(0, X-1)
    elif key in ('right',):
        X = min(3, X+1)
    elif key in ('up',):
        Y = min(3, Y+1)
    elif key in ('down',):
        Y = max(0, Y-1)
    elif key == 'w':  # subir capa Z
        Z = min(3, Z+1)
    elif key == 's':  # bajar capa Z
        Z = max(0, Z-1)
    elif key in ('enter', ' '):  # colocar ficha
        i = xyz_to_index(X, Y, Z)
        poner_jugada(i, enviar=True)
        return
    selected_index = xyz_to_index(X, Y, Z)
    highlight_cell(selected_index)

scene.bind('keydown', keydown)

# Botón reiniciar
button(bind=reiniciar_tablero, text="Reiniciar tablero")
highlight_cell(selected_index)
actualizar_labels()

# ========== HILO DE RECEPCIÓN ==========
def recibir_jugadas():
    global local_player_id, opponent_name, turno
    while True:
        try:
            data = client.recv(1024)
            if not data:
                break
            text = data.decode(errors='ignore')

            # START:id => mi id de jugador
            if text.startswith("START:"):
                try:
                    local_player_id = int(text.split(":",1)[1])
                    print("Tu player_id:", local_player_id)
                    # el que recibe START puede saber si empieza (0 empieza)
                    turno = 0  # por defecto
                    actualizar_labels()
                except:
                    pass
                continue

            # NAME:... => nombre del oponente (uno o varios mensajes posibles)
            if text.startswith("NAME:"):
                name = text.split(":",1)[1]
                # si el nombre no es el tuyo, guardarlo como oponente (simple heurística)
                if name != player_name:
                    opponent_name = name
                    actualizar_labels()
                continue

            # si es número => jugada
            try:
                i = int(text)
                print("Oponente jugó:", i)
                aplicar_jugada_remota(i)
            except:
                print("Recibido (ignorado):", text)

        except Exception as e:
            print("Error recibiendo:", e)
            break

threading.Thread(target=recibir_jugadas, daemon=True).start()

# Loop principal de VPython (para mantener la app viva)
while True:
    rate(30)
    # aquí se maneja todo por eventos y hilos
    pass
