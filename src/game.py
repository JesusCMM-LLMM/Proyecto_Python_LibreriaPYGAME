import pygame
import sys
import os

from .board import Board
from .card import CARD_SIZE

# -----------------------------------------------------------------------
# Configuración general de la ventana
# -----------------------------------------------------------------------

ANCHO = 700
ALTO = 700
FPS = 60
TITULO = "Pokémon Matching Cards"

# Rutas de assets
RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_IMAGENES = os.path.join(RUTA_BASE, "assets", "images")
RUTA_SONIDOS = os.path.join(RUTA_BASE, "assets", "sounds")

# Colores
COLOR_FONDO = (30, 60, 30)          # Verde oscuro tipo tapete
COLOR_UI_FONDO = (20, 40, 20)       # Barra superior
COLOR_TEXTO = (255, 255, 255)
COLOR_DORADO = (212, 175, 55)
COLOR_OVERLAY = (0, 0, 0, 180)      # Overlay semitransparente pantalla fin


# -----------------------------------------------------------------------
# Estados del juego
# -----------------------------------------------------------------------

ESTADO_JUGANDO = "jugando"
ESTADO_FIN = "fin"


class Game:
    """
    Clase principal que gestiona el bucle del juego, los estados,
    la pantalla, los sonidos y la interfaz de usuario.

    Estados posibles:
        ESTADO_JUGANDO -- el jugador interactúa con el tablero
        ESTADO_FIN     -- todas las parejas encontradas, muestra resultado
    """

    def __init__(self):
        """Inicializa pygame, la ventana, los sonidos y el tablero."""
        pygame.init()
        pygame.mixer.init()

        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption(TITULO)
        self.reloj = pygame.time.Clock()
        # En __init__, junto a los demás atributos:
        self.tiempo_final = 0

        # Fuentes
        self.fuente_grande = pygame.font.SysFont("arial", 42, bold=True)
        self.fuente_media = pygame.font.SysFont("arial", 28, bold=True)
        self.fuente_small = pygame.font.SysFont("arial", 22)

        # Cargamos sonidos
        self.sonido_volteo = self._cargar_sonido("flip.wav")
        self.sonido_acierto = self._cargar_sonido("match.wav")
        
        self.sonido_victoria = self._cargar_sonido("victory.wav")

        # Botón de reinicio
        self.btn_reinicio = self._cargar_imagen_ui("btn_reinicio.png", (180, 55))
        self.rect_btn_reinicio = pygame.Rect(
            ANCHO // 2 - 90, ALTO - 68, 180, 55
        )

        # Estado inicial
        self.estado = ESTADO_JUGANDO
        self.victoria_sonada = False

        # Creamos el tablero
        self.board = Board(
            ruta_assets=RUTA_IMAGENES,
            sonido_volteo=self.sonido_volteo,
            sonido_acierto=self.sonido_acierto,
        )

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------

    def ejecutar(self):
        """
        Bucle principal del juego.
        Mantiene el juego corriendo hasta que el usuario cierra la ventana.
        """
        while True:
            self._manejar_eventos()
            self._actualizar()
            self._dibujar()
            self.reloj.tick(FPS)

    # ------------------------------------------------------------------
    # Gestión de eventos
    # ------------------------------------------------------------------

    def _manejar_eventos(self):
        """Procesa todos los eventos de pygame en cada frame."""
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self._salir()

            if event.type == pygame.KEYDOWN:
                # R: reiniciar en cualquier momento
                if event.key == pygame.K_r:
                    self._reiniciar()
                # ESC: salir
                if event.key == pygame.K_ESCAPE:
                    self._salir()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._manejar_clic(event.pos)

    def _manejar_clic(self, pos: tuple):
        """
        Gestiona los clics del ratón según el estado actual del juego.

        Args:
            pos -- tupla (x, y) con la posición del clic
        """
        # Clic en botón de reinicio (visible en ambos estados)
        if self.rect_btn_reinicio.collidepoint(pos):
            self._reiniciar()
            return

        # Solo procesamos clics en el tablero si estamos jugando
        if self.estado == ESTADO_JUGANDO:
            self.board.manejar_clic(pos)

    # ------------------------------------------------------------------
    # Actualización
    # ------------------------------------------------------------------

    def _actualizar(self):
        """Actualiza la lógica del juego en cada frame."""
        if self.estado == ESTADO_JUGANDO:
            self.board.actualizar()
            self.board.actualizar_hover(pygame.mouse.get_pos())

            animaciones_activas = any(c._flip_activo for c in self.board.cartas)

            # Comprobamos si la partida ha terminado
            if self.board.partida_completada and not animaciones_activas:
                self.estado = ESTADO_FIN
                self.tiempo_final = self.board.tiempo_transcurrido
                if not self.victoria_sonada and self.sonido_victoria:
                    try:
                        self.sonido_victoria.play()
                    except pygame.error as e:
                        print(f"[Game] Error al reproducir victoria: {e}")
                    self.victoria_sonada = True

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------

    def _dibujar(self):
        """Dibuja todos los elementos en pantalla según el estado actual."""
        if not self.board.fondo:
            self.pantalla.fill(COLOR_FONDO)
        # Tablero
        self.board.dibujar(self.pantalla)

        # Barra superior de UI
        self._dibujar_ui_superior()

        # Botón de reinicio (parte inferior)
        self._dibujar_boton_reinicio()

        # Pantalla de fin si corresponde
        if self.estado == ESTADO_FIN:
            self._dibujar_pantalla_fin()

        pygame.display.flip()

    def _dibujar_ui_superior(self):
        """
        Dibuja la barra superior con el tiempo transcurrido
        y el número de intentos realizados.
        """
        # Fondo barra superior
        pygame.draw.rect(self.pantalla, COLOR_UI_FONDO, (0, 0, ANCHO, 100))
        pygame.draw.line(self.pantalla, COLOR_DORADO, (0, 100), (ANCHO, 100), 2)

        # Tiempo (módulo time via board.tiempo_transcurrido)
        segundos = int(self.tiempo_final if self.estado == ESTADO_FIN else self.board.tiempo_transcurrido)
        minutos = segundos // 60
        segs = segundos % 60
        # Reloj dibujado con pygame.draw
        cx, cy = 36, 35
        pygame.draw.circle(self.pantalla, COLOR_TEXTO, (cx, cy), 12, 2)
        pygame.draw.line(self.pantalla, COLOR_TEXTO, (cx, cy), (cx, cy - 8), 2)   # minutero
        pygame.draw.line(self.pantalla, COLOR_TEXTO, (cx, cy), (cx + 6, cy), 2)   # horario
        pygame.draw.circle(self.pantalla, COLOR_TEXTO, (cx, cy), 2)               # centro

        texto_tiempo = f"  {minutos:02d}:{segs:02d}"
        surf_tiempo = self.fuente_media.render(texto_tiempo, True, COLOR_TEXTO)
        self.pantalla.blit(surf_tiempo, (48, 20))

        # Intentos
        texto_intentos = f"Intentos: {self.board.intentos}"
        surf_intentos = self.fuente_media.render(texto_intentos, True, COLOR_TEXTO)
        self.pantalla.blit(surf_intentos, (ANCHO - surf_intentos.get_width() - 20, 20))

        # Parejas encontradas (centro)
        texto_parejas = f"{self.board.parejas_encontradas} / 8 parejas"
        surf_parejas = self.fuente_small.render(texto_parejas, True, COLOR_DORADO)
        self.pantalla.blit(surf_parejas, (ANCHO // 2 - surf_parejas.get_width() // 2, 25))

    def _dibujar_boton_reinicio(self):
        """Dibuja el botón de reinicio en la parte inferior de la pantalla."""
        if self.btn_reinicio:
            self.pantalla.blit(self.btn_reinicio, self.rect_btn_reinicio.topleft)
        else:
            # Fallback si no se encontró la imagen del botón
            pygame.draw.rect(self.pantalla, (180, 20, 20),
                             self.rect_btn_reinicio, border_radius=10)
            surf = self.fuente_small.render("REINICIO", True, COLOR_TEXTO)
            self.pantalla.blit(surf, (
                self.rect_btn_reinicio.centerx - surf.get_width() // 2,
                self.rect_btn_reinicio.centery - surf.get_height() // 2
            ))

        # Efecto hover sobre el botón
        if self.rect_btn_reinicio.collidepoint(pygame.mouse.get_pos()):
            overlay = pygame.Surface(self.rect_btn_reinicio.size, pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 40))
            self.pantalla.blit(overlay, self.rect_btn_reinicio.topleft)

    def _dibujar_pantalla_fin(self):
        """
        Dibuja el overlay de fin de partida con el tiempo final
        y el número de intentos.
        """
        # Overlay semitransparente
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill(COLOR_OVERLAY)
        self.pantalla.blit(overlay, (0, 0))

        # Título
        surf_titulo = self.fuente_grande.render("¡Completado!", True, COLOR_DORADO)
        self.pantalla.blit(surf_titulo, (
            ANCHO // 2 - surf_titulo.get_width() // 2, 280
        ))

        # Tiempo final
        segundos = int(self.tiempo_final)
        minutos = segundos // 60
        segs = segundos % 60
        surf_tiempo = self.fuente_media.render(
            f"Tiempo: {minutos:02d}:{segs:02d}", True, COLOR_TEXTO
        )
        self.pantalla.blit(surf_tiempo, (
            ANCHO // 2 - surf_tiempo.get_width() // 2, 350
        ))

        # Intentos
        surf_intentos = self.fuente_media.render(
            f"Intentos: {self.board.intentos}", True, COLOR_TEXTO
        )
        self.pantalla.blit(surf_intentos, (
            ANCHO // 2 - surf_intentos.get_width() // 2, 400
        ))

        # Instrucción para reiniciar
        surf_hint = self.fuente_small.render(
            "Pulsa R o el botón para jugar de nuevo", True, (180, 180, 180)
        )
        self.pantalla.blit(surf_hint, (
            ANCHO // 2 - surf_hint.get_width() // 2, 460
        ))

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _reiniciar(self):
        """Reinicia la partida completamente."""
        self.estado = ESTADO_JUGANDO
        self.victoria_sonada = False
        self.board.reiniciar(sonido_volteo=self.sonido_volteo)

    def _salir(self):
        """Cierra pygame y termina el programa limpiamente."""
        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------------
    # Helpers de carga de assets
    # ------------------------------------------------------------------

    def _cargar_sonido(self, nombre: str) -> pygame.mixer.Sound | None:
        """
        Carga un archivo de sonido desde assets/sounds/.
        Devuelve None si el archivo no existe, sin crashear.

        Args:
            nombre -- nombre del archivo (ej: "flip.wav")
        """
        ruta = os.path.join(RUTA_SONIDOS, nombre)
        try:
            return pygame.mixer.Sound(ruta)
        except FileNotFoundError:
            print(f"[Game] Sonido no encontrado: {nombre}")
            return None
        except pygame.error as e:
            print(f"[Game] Error al cargar sonido {nombre}: {e}")
            return None

    def _cargar_imagen_ui(self, nombre: str, size: tuple) -> pygame.Surface | None:
        """
        Carga y escala una imagen de UI desde assets/images/.
        Devuelve None si el archivo no existe.

        Args:
            nombre -- nombre del archivo (ej: "btn_reinicio.png")
            size   -- tupla (ancho, alto) al que escalar la imagen
        """
        ruta = os.path.join(RUTA_IMAGENES, nombre)
        try:
            img = pygame.image.load(ruta).convert_alpha()
            return pygame.transform.scale(img, size)
        except FileNotFoundError:
            print(f"[Game] Imagen UI no encontrada: {nombre}")
            return None
        except pygame.error as e:
            print(f"[Game] Error al cargar imagen {nombre}: {e}")
            return None
        