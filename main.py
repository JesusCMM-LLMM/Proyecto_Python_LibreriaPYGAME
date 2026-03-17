import sys
import pygame
from src import Game


def main():
    """
    Punto de entrada de la aplicación.
    Inicializa el juego y arranca el bucle principal.
    """
    try:
        juego = Game()
        juego.ejecutar()
    except Exception as e:
        print(f"[main] Error inesperado: {e}")
        pygame.quit()
        sys.exit(1)


if __name__ == "__main__":
    main()