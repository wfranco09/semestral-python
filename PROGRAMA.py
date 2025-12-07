import socket
import threading
import tkinter as tk
from tkinter import Button, Label, Tk, simpledialog
import random

# ================== VENTANA INICIAL ==================
root = Tk()
root.withdraw()  # Oculta ventana principal mientras pedimos datos

# Pedir IP del servidor (Tailscale)
IP_SERVIDOR = simpledialog.askstring("Conexión", "Ingresa la IP del servidor (Tailscale):")
if not IP_SERVIDOR:
    raise SystemExit("No ingresaste IP. Saliendo...")

# Pedir nombre del jugador
nombre_local = simpledialog.askstring("Identificación", "Ingresa tu nombre:")
if not nombre_local:
    nombre_local = "Jugador"

PUERTO = 5000
texto_ganador = None

# ================== CONEXIÓN AL SERVIDOR ==================
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client.connect((IP_SERVIDOR, PUERTO))
    print("Conectado al servidor.")
    # Enviar nombre al servidor
    client.sendall(("NOMBRE:" + nombre_local).encode())
except Exception as e:
    print("No se pudo conectar al servidor:", e)
    raise SystemExit(1)

# ================== VARIABLES DEL JUEGO ==================
nombre_jugador1 = "Jugador 1"
nombre_jugador2 = "Jugador 2"
jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
botones = []
X = Y = Z = 0
g = 0
jugador = 0
contador_ganadas_jugador1 = 0
contador_ganadas_jugador2 = 0

# ================== RECEPCIÓN DE JUGADAS Y NOMBRES ==================
def recibir_jugadas():
    global nombre_jugador1, nombre_jugador2
    while True:
        try:
            data = client.recv(1024)
            if not data:
                print("Conexión cerrada por el servidor.")
                break

            texto = data.decode()

            # Nombres enviados por el otro jugador
            if texto.startswith("NOMBRE1:"):
                nombre_jugador1 = texto.replace("NOMBRE1:", "")
                puntaje_jugador1.config(text=f"{nombre_jugador1}: {contador_ganadas_jugador1}")
                continue
            if texto.startswith("NOMBRE2:"):
                nombre_jugador2 = texto.replace("NOMBRE2:", "")
                puntaje_jugador2.config(text=f"{nombre_jugador2}: {contador_ganadas_jugador2}")
                continue

            # Jugadas
            if texto.isdigit():
                i = int(texto)
                aplicar_jugada_remota(i)

        except Exception as e:
            print("Error al recibir:", e)
            break

threading.Thread(target=recibir_jugadas, daemon=True).start()

# ================== LÓGICA DEL JUEGO ==================
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
    global jugador, g, contador_ganadas_jugador1, contador_ganadas_jugador2, texto_ganador
    nombre = nombre_jugador1 if jugador == 0 else nombre_jugador2

    if texto_ganador:
        texto_ganador.destroy()

    texto_ganador = Label(tablero, text=f"🎉 {nombre} GANÓ 🎉",
                          font=("Arial Black", 20), fg="#FFDD00", bg="#18324e")
    texto_ganador.place(x=650, y=550)
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
    puntaje_jugador1.config(text=f'{nombre_jugador1}: {contador_ganadas_jugador1}')
    puntaje_jugador2.config(text=f'{nombre_jugador2}: {contador_ganadas_jugador2}')

# ================== INTERFAZ TKINTER ==================
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

for b in range(64):
    botones.append(crearBoton(' ', b))

contador = 0
for z in range(3, -1, -1):
    for y in range(4):
        for x in range(4):
            botones[contador].grid(row=y + z * 4, column=x + (3 - z) * 4)
            contador += 1

texto_actual = Label(tablero, text=nombre_jugador1,
                     font=('arial', 20), fg='green', bg='#18324e')
texto_actual.place(x=500, y=620)

tablero.mainloop()
