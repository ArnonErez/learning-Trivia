from admin_menu import AdminMenu
from game import Game
from console_ui import ConsoleUI as UI
import sys


# choose the game mode according to the command-line parameter or use default mode
modes = {'normal', 'admin'}
mode = 'normal'
if len(sys.argv) > 1:
    mode = sys.argv[1]
    if mode not in modes:
        UI.alert(f"Invalid argument {mode}. mode parameter should be one of [{modes}] or left empty. "
                 f" The default mode is {default_mode}")
        exit(1)

if mode and mode == 'admin':
    session = AdminMenu()
else:
    session = Game()


# Start the game

UI.welcome("!! WELCOME TO THE AMAZING TRIVIA GAME !!")
finished = False
while not finished:
    session.start()
    if not session.restart():
        finished = True
    else:
        UI.restart()
UI.alert("See you next time :)")
