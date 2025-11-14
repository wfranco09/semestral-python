import socket
import threading
from tkinter import *
import tkinter as tk

# =============== CONFIGURACIÓN DE RED =================
IP_SERVIDOR = "172.29.34.2"
PUERTO = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((IP_SERVIDOR, PUERTO))
print("Conectado al servidor.")

# ======================================================


def recibir_jugadas():
    while True:
        try:
            data = client.recv(1024).decode()
            if data:
                i = int(data)
                print("Oponente jugó:", i)
                aplicar_jugada_remota(i)
        except:
            break


threading.Thread(target=recibir_jugadas, daemon=True).start()



# ========== TU JUEGO COMPLETO =============
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
        if jugador == 0:
            jugadas[Z][Y][X] = -1
            botones[i].config(text="X", font='arial_black 15', fg='blue')
        else:
            jugadas[Z][Y][X] = 1
            botones[i].config(text="O", font='arial_black 15', fg='red')

        # Enviar al servidor SOLO si es jugada local
        if enviar:
            client.send(str(i).encode())

        if verificar_todo(X, Y, Z):
            ganador()
            return

        jugador = not jugador
        texto_actual.config(text='Jugador ' + str(jugador + 1))
    else:
        aviso = Label(tablero, text='Jugada inválida', font='arial, 20', fg='green')
        aviso.place(x=50, y=30)


def aplicar_jugada_remota(i):
    """Actualiza el tablero sin enviar jugada al servidor."""
    global jugador
    botonClick(i, enviar=False)


def ganador():
    global jugador, g
    texto_ganador = Label(tablero, text=f'Jugador {jugador + 1} GANÓ', font='arial, 20', fg='green')
    texto_ganador.place(x=50, y=30)
    g = 1
    contar_ganadas()
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
    global jugadas, botones, X, Y, Z, g, jugador
    jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
    X = Y = Z = 0
    g = jugador = 0
    for b in range(64):
        botones[b].config(text=' ')
    texto_actual.config(text='Jugador 1')


def contar_ganadas():
    global contador_ganadas_jugador1, contador_ganadas_jugador2, jugador
    if jugador == 0:
        contador_ganadas_jugador1 += 1
    else:
        contador_ganadas_jugador2 += 1

def actualizar_puntaje():
    puntaje_jugador1.config(text=f'Jugador 1: {contador_ganadas_jugador1}')
    puntaje_jugador2.config(text=f'Jugador 2: {contador_ganadas_jugador2}')


# ========== INTERFAZ TKINTER ==========

jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
botones = []
X = Y = Z = 0
g = jugador = 0

tablero = Tk()
tablero.title('Tic Tac Toe 3D ONLINE')
tablero.geometry("1040x720+100+50")
tablero.resizable(0, 0)
tablero.config(bg='lightgray')

contador_ganadas_jugador1 = 0
contador_ganadas_jugador2 = 0

puntaje_jugador1 = Label(tablero, text='Jugador 1: 0', font=('arial', 20), fg='blue')
puntaje_jugador1.place(x=50, y=100)

puntaje_jugador2 = Label(tablero, text='Jugador 2: 0', font=('arial', 20), fg='red')
puntaje_jugador2.place(x=50, y=150)

Button(tablero, text="Salir", command=tablero.destroy, bg='red',
       fg='white', font=('arial', 12, 'bold')).place(x=900, y=650)

titulo = Label(tablero, text='Tic Tac Toe 3D Online', font=('arial', 30, 'bold'),
               fg='black', bg='lightgray')
titulo.place(x=350, y=10)

Button(tablero, text="Reiniciar", command=tableronuevo, bg='blue',
       fg='white', font=('arial', 12, 'bold')).place(x=800, y=650)

for b in range(64):
    botones.append(crearBoton(' ', b))

contador = 0
for z in range(3, -1, -1):
    for y in range(4):
        for x in range(4):
            botones[contador].grid(row=y + z * 4, column=x + (3 - z) * 4)
            contador += 1

texto_actual = Label(tablero, text='Jugador 1', font=('arial', 20), fg='green')
texto_actual.place(x=500, y=620)

tablero.mainloop()
