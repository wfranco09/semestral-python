# client.py
import socket
import threading
import tkinter as tk
from tkinter import Button, Label, Tk, simpledialog

# =============== CONFIGURACIÓN DE RED =================
IP_SERVIDOR = "172.29.37.101"  # cambia si es necesario
PUERTO = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect((IP_SERVIDOR, PUERTO))
    print("Conectado al servidor.")
except Exception as e:
    print("No se pudo conectar al servidor:", e)
    raise SystemExit(1)

# ==================== PREGUNTAR NOMBRE ======================
root = Tk()
root.withdraw()  # esconder ventana pequeña
nombre_local = simpledialog.askstring("Identificación", "Ingresa tu nombre:")
if not nombre_local:
    nombre_local = "Jugador"

client.sendall(("NOMBRE:" + nombre_local).encode())

nombre_jugador1 = "Jugador 1"
nombre_jugador2 = "Jugador 2"

# ============================================================

# Variables del juego
jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
botones = []
X = Y = Z = 0
g = 0
jugador = 0

contador_ganadas_jugador1 = 0
contador_ganadas_jugador2 = 0

def recibir_jugadas():
    global nombre_jugador1, nombre_jugador2
    while True:
        try:
            data = client.recv(1024)
            if not data:
                print("Conexión cerrada por el servidor.")
                break

            texto = data.decode()

            # ============ RECEPCIÓN DE NOMBRES ============
            if texto.startswith("NOMBRE1:"):
                nombre_jugador1 = texto.replace("NOMBRE1:", "")
                puntaje_jugador1.config(text=f"{nombre_jugador1}: {contador_ganadas_jugador1}")
                continue

            if texto.startswith("NOMBRE2:"):
                nombre_jugador2 = texto.replace("NOMBRE2:", "")
                puntaje_jugador2.config(text=f"{nombre_jugador2}: {contador_ganadas_jugador2}")
                continue

            # ============ JUGADAS ============
            if texto.isdigit():
                i = int(texto)
                print("Oponente jugó:", i)
                aplicar_jugada_remota(i)

        except Exception as e:
            print("Error al recibir:", e)
            break

threading.Thread(target=recibir_jugadas, daemon=True).start()


# ========== Lógica del juego ==========

def crearBoton(valor, i):
    return Button(tablero, text=valor, width=5, height=1, font=("Helvetica", 15),
                  command=lambda: botonClick(i, enviar=True))

def botonClick(i, enviar=True):
    global jugador, jugadas, X, Y, Z, g
    Z = int(i / 16)
    y = i % 16
    Y = int(y / 4)
    X = y % 4

    if g:
        return

    if not jugadas[Z][Y][X]:
        marca = -1 if jugador == 0 else 1
        jugadas[Z][Y][X] = marca

        texto_marca = "X" if jugador == 0 else "O"
        botones[i].config(text=texto_marca, font='arial_black 15',
                          fg='blue' if jugador == 0 else 'red')

        if enviar:
            try:
                client.sendall(str(i).encode())
            except Exception as e:
                print("Error al enviar jugada:", e)

        if verificar_todo(X, Y, Z):
            ganador()
            return

        jugador = 1 - jugador
        texto_actual.config(text=(nombre_jugador1 if jugador == 0 else nombre_jugador2))

def aplicar_jugada_remota(i):
    botonClick(i, enviar=False)

def ganador():
    global jugador, g, contador_ganadas_jugador1, contador_ganadas_jugador2
    nombre = nombre_jugador1 if jugador == 0 else nombre_jugador2

    texto_ganador = Label(tablero, text=f'{nombre} GANÓ', font=('arial', 20),
                          fg='green', bg='lightgray')
    texto_ganador.place(x=50, y=30)

    g = 1

    if jugador == 0:
        contador_ganadas_jugador1 += 1
    else:
        contador_ganadas_jugador2 += 1

    actualizar_puntaje()

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

def tableronuevo():
    global jugadas, g, jugador
    jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
    g = 0
    jugador = 0
    for b in range(64):
        botones[b].config(text=' ')
    texto_actual.config(text=nombre_jugador1)

def actualizar_puntaje():
    puntaje_jugador1.config(text=f'{nombre_jugador1}: {contador_ganadas_jugador1}')
    puntaje_jugador2.config(text=f'{nombre_jugador2}: {contador_ganadas_jugador2}')


# ========== INTERFAZ TKINTER ==========
tablero = Tk()
tablero.title('Tic Tac Toe 3D ONLINE')
tablero.geometry("1040x720+100+50")
tablero.resizable(0, 0)
tablero.config(bg='lightgray')

puntaje_jugador1 = Label(tablero, text=f'{nombre_jugador1}: 0',
                         font=('arial', 20), fg='blue', bg='lightgray')
puntaje_jugador1.place(x=50, y=100)

puntaje_jugador2 = Label(tablero, text=f'{nombre_jugador2}: 0',
                         font=('arial', 20), fg='red', bg='lightgray')
puntaje_jugador2.place(x=50, y=150)

Button(tablero, text="Salir", command=tablero.destroy,
       bg='red', fg='white', font=('arial', 12, 'bold')).place(x=900, y=650)

Button(tablero, text="Reiniciar", command=tableronuevo,
       bg='blue', fg='white', font=('arial', 12, 'bold')).place(x=800, y=650)

titulo = Label(tablero, text='Tic Tac Toe 3D Online',
               font=('arial', 30, 'bold'), fg='black', bg='lightgray')
titulo.place(x=350, y=10)

for b in range(64):
    botones.append(crearBoton(' ', b))

contador = 0
for z in range(3, -1, -1):
    for y in range(4):
        for x in range(4):
            botones[contador].grid(row=y + z * 4, column=x + (3 - z) * 4)
            contador += 1

texto_actual = Label(tablero, text=nombre_jugador1,
                     font=('arial', 20), fg='green', bg='lightgray')
texto_actual.place(x=500, y=620)

tablero.mainloop()
