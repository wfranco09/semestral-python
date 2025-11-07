from tkinter import *
import tkinter as tk

def crearBoton(valor, i):
    return Button(tablero, text=valor, width=5, height=1, font=("Helvetica", 15), command=lambda: botonClick(i))

def botonClick(i):
    global jugador, jugadas, X, Y, Z, g        

    Z = int(i / 16)
    y = i % 16
    Y = int(y / 4)
    X = y % 4
    print('Z='+str(Z)+' Y='+str(Y)+' X='+str(X))
    if g:
        tablero.destroy()
        return
    if not jugadas[Z][Y][X]:
        if jugador == 0:
            jugadas[Z][Y][X] = -1
            botones[i].config(text="X", font='arial_black 15', fg='blue')
        else:
            jugadas[Z][Y][X] = 1
            botones[i].config(text="O", font='arial_black 15', fg='red')

        if verificar_todo(X, Y, Z):
            ganador()
            return

        if not g:
            jugador = not jugador
            texto = Label(tablero, text='Jugador ' + str(jugador + 1), font='arial, 20', fg='green')
            texto.place(x=500, y=620)
    else:
        texto = Label(tablero, text='Jugada Inválida', font='arial, 20', fg='green')
        texto.place(x=50, y=30)
    print(jugadas)

def ganador():
    global jugador, g
    texto = Label(tablero, text='Jugador ' + str(jugador + 1) + ' GANÓ', font='arial, 20', fg='green')
    texto.place(x=50, y=30)
    g = 1
    contar_ganadas()  
    actualizar_puntaje()  

# ------------------------------
# FUNCIONES DE DETECCIÓN DE GANADOR
# ------------------------------
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
    s = sum(jugadas[Z][Y][x] for x in range(4))
    return abs(s) == 4

def vertical(X, Z):
    s = sum(jugadas[Z][y][X] for y in range(4))
    return abs(s) == 4

def profundidad(X, Y):
    s = sum(jugadas[z][Y][X] for z in range(4))
    return abs(s) == 4

def diagonal_frontal(Z):
    if abs(sum(jugadas[Z][i][i] for i in range(4))) == 4:
        return True
    if abs(sum(jugadas[Z][i][3 - i] for i in range(4))) == 4:
        return True
    return False

def diagonal_vertical(X):
    if abs(sum(jugadas[i][i][X] for i in range(4))) == 4:
        return True
    if abs(sum(jugadas[i][3 - i][X] for i in range(4))) == 4:
        return True
    return False

def diagonal_horizontal(Y):
    if abs(sum(jugadas[i][Y][i] for i in range(4))) == 4:
        return True
    if abs(sum(jugadas[3 - i][Y][i] for i in range(4))) == 4:
        return True
    return False

def diagonal_cruzada():
    if abs(sum(jugadas[i][i][i] for i in range(4))) == 4:
        return True
    if abs(sum(jugadas[i][i][3 - i] for i in range(4))) == 4:
        return True
    if abs(sum(jugadas[i][3 - i][i] for i in range(4))) == 4:
        return True
    if abs(sum(jugadas[i][3 - i][3 - i] for i in range(4))) == 4:
        return True
    return False

# funcion para limpiar el tablero y empezar un juego nuevo
def tableronuevo():
    global jugadas, botones, X, Y, Z, g, jugador
    jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
    X = Y = Z = 0
    g = jugador = 0
    for b in range(64):
        botones[b].config(text=' ')
    texto = Label(tablero, text='Jugador ' + str(jugador + 1), font='arial, 20', fg='green')
    texto.place(x=500, y=620)

# función para marcar el puntaje
def contar_ganadas():
    global contador_ganadas_jugador1, contador_ganadas_jugador2, jugador
    if jugador == 0:
        contador_ganadas_jugador1 += 1
    else:
        contador_ganadas_jugador2 += 1

# función para actualizar los labels de puntaje
def actualizar_puntaje():
    puntaje_jugador1.config(text='Jugador 1: ' + str(contador_ganadas_jugador1))
    puntaje_jugador2.config(text='Jugador 2: ' + str(contador_ganadas_jugador2))

# ------------------------------
# CONFIGURACIÓN DEL TABLERO
# ------------------------------
jugadas = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
botones = []
X = Y = Z = 0
g = jugador = 0

tablero = Tk()
tablero.title('Tic Tac Toe 3D')
tablero.geometry("1040x720+100+5")
tablero.resizable(0, 0)
tablero.config(bg='lightgray')

# contador de partidas ganadas
contador_ganadas_jugador1 = 0
contador_ganadas_jugador2 = 0

# puntaje del jugador 1 y 2
puntaje_jugador1 = Label(tablero, text='Jugador 1: ' + str(contador_ganadas_jugador1), font='arial, 20', fg='blue')
puntaje_jugador1.place(x=50, y=100)
puntaje_jugador2 = Label(tablero, text='Jugador 2: ' + str(contador_ganadas_jugador2), font='arial, 20', fg='red')
puntaje_jugador2.place(x=50, y=150)

# boton para cerrar el juego
botonSalir = Button(tablero, text="Salir", command=tablero.destroy, bg='red', fg='white', font=('arial', 12, 'bold'))
botonSalir.place(x=900, y=650)

#label del titulo
titulo = Label(tablero, text='Tic Tac Toe 3D', font=('arial', 30, 'bold'), fg='black', bg='lightgray')
titulo.place(x=400, y=10)

#boton para reiniciar el juego
botonReiniciar = Button(tablero, text="Reiniciar", command=lambda: tableronuevo(), bg='blue', fg='white', font=('arial', 12, 'bold'))
botonReiniciar.place(x=800, y=650)

for b in range(64):
    botones.append(crearBoton(' ', b))

contador = 0
for z in range(3, -1, -1):
    for y in range(4):
        for x in range(4): 
            botones[contador].grid(row=y + z * 4, column=x + (3 - z) * 4)
            contador += 1

texto = Label(tablero, text='Jugador ' + str(jugador + 1), font='arial, 20', fg='green')
texto.place(x=500, y=620)
tablero.mainloop()
