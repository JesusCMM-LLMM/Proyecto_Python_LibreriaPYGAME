import pygame
import os
import random
import time

from .card import Card, CARD_SIZE

# -----------------------------------------------------------------------
# Configuración del tablero
# -----------------------------------------------------------------------
FILAS = 4
COLUMNAS = 4
MARGEN = 15
OFFSET_Y = 110       # espacio para la barra superior
ANCHO_VENTANA = 700 # para calcular el centrado
ALTO_VENTANA = 700

# Calculamos OFFSET_X para centrar el tablero horizontalmente
ANCHO_TABLERO = COLUMNAS * CARD_SIZE[0] + (COLUMNAS - 1) * MARGEN
OFFSET_X = (ANCHO_VENTANA - ANCHO_TABLERO) // 2

ESPERA_VOLTEO = 1.5          # Segundos que se ven dos cartas no emparejadas

# Nombres de los 8 Pokémon — deben coincidir con los archivos en assets/images/
TIPOS_POKEMON = [
    "charmander",
    "eevee",
    "grookey",
    "pikachu",
    "piplup",
    "squirtle",
    "rowlett",
    "togepi",
]


class Board:
    """
    Gestiona el tablero completo del juego:
      - Carga y escala los assets de las cartas
      - Genera y coloca las 16 cartas (8 parejas) en posición aleatoria
      - Controla la lógica de selección y emparejamiento
      - Lleva la cuenta de intentos y tiempo de partida
    """

    def __init__(self, ruta_assets: str, sonido_volteo: pygame.mixer.Sound = None,
                 sonido_acierto: pygame.mixer.Sound = None):
        """
        Inicializa el tablero cargando assets y generando las cartas.

        Args:
            ruta_assets    -- ruta a la carpeta assets/images/
            sonido_volteo  -- Sound que se pasa a cada carta al crearla
            sonido_acierto -- Sound que se reproduce al encontrar pareja
            sonido_error   -- Sound que se reproduce al fallar
        """
        self.ruta_assets = ruta_assets
        self.sonido_acierto = sonido_acierto
        

        # Estado de selección
        self.carta_seleccionada: Card | None = None   # Primera carta volteada
        self.esperando_volteo = False                  # True durante la pausa de 1.5s
        self.tiempo_espera = 0.0                       # Marca de tiempo del fallo

        # Estadísticas
        self.intentos = 0
        self.parejas_encontradas = 0
        self.tiempo_inicio = time.time()

        # Cargamos imágenes y construimos las cartas
        self._imagenes = self._cargar_imagenes()
        self.cartas: list[Card] = self._generar_cartas(sonido_volteo)
        # Cargamos la imagen de fondo del tablero
        self.fondo = self._cargar_fondo(ruta_assets)

    # ------------------------------------------------------------------
    # Propiedades de consulta
    # ------------------------------------------------------------------

    @property
    def partida_completada(self) -> bool:
        """Devuelve True cuando todas las parejas han sido encontradas."""
        return self.parejas_encontradas == len(TIPOS_POKEMON)

    @property
    def tiempo_transcurrido(self) -> float:
        """Devuelve los segundos transcurridos desde el inicio de la partida."""
        return time.time() - self.tiempo_inicio

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------

    def manejar_clic(self, pos: tuple):
        """
        Procesa un clic del ratón sobre el tablero.
        Ignora el clic si ya hay dos cartas esperando volteo.

        Args:
            pos -- tupla (x, y) con la posición del clic
        """
        if self.esperando_volteo or self.partida_completada:
            return

        for carta in self.cartas:
            if carta.contiene_punto(pos) and not carta.volteada and not carta.emparejada:
                carta.voltear()
                self._procesar_seleccion(carta)
                break

    def actualizar(self):
        """
        Actualiza el estado del tablero en cada frame:
          - Progresa las animaciones de todas las cartas
          - Comprueba si ha pasado el tiempo de espera tras un fallo
        """
        for carta in self.cartas:
            carta.actualizar()

        # Comprobamos si ha pasado el tiempo de espera tras un fallo
        if self.esperando_volteo:
            if time.time() - self.tiempo_espera >= ESPERA_VOLTEO:
                self._voltear_cartas_fallidas()

    def actualizar_hover(self, pos_raton: tuple):
        """
        Actualiza el estado hover de todas las cartas.
        Solo afecta a cartas que no estén emparejadas ni volteadas.

        Args:
            pos_raton -- posición actual del ratón
        """
        for carta in self.cartas:
            # No aplicamos hover si estamos esperando volteo
            if not self.esperando_volteo:
                carta.actualizar_hover(pos_raton)
            else:
                carta.hover = False

    def dibujar(self, superficie: pygame.Surface):
        if self.fondo:
            ancho_fondo = self.fondo.get_width()
            alto_fondo = self.fondo.get_height()
            x = (ANCHO_VENTANA - ancho_fondo) // 2
            y = (ALTO_VENTANA - alto_fondo) // 2
            superficie.blit(self.fondo, (x, y))
        """
        Dibuja todas las cartas del tablero en la superficie indicada.

        Args:
            superficie -- pygame.Surface principal del juego
        """
        for carta in self.cartas:
            carta.dibujar(superficie)

    def reiniciar(self, sonido_volteo: pygame.mixer.Sound = None):
        """
        Reinicia el tablero completamente: rebaraja las cartas y
        resetea todas las estadísticas.

        Args:
            sonido_volteo -- Sound opcional (el mismo que al crear el tablero)
        """
        self.carta_seleccionada = None
        self.esperando_volteo = False
        self.tiempo_espera = 0.0
        self.intentos = 0
        self.parejas_encontradas = 0
        self.tiempo_inicio = time.time()
        self.cartas = self._generar_cartas(sonido_volteo)

    # ------------------------------------------------------------------
    # Métodos privados
    # ------------------------------------------------------------------
    
    def _cargar_fondo(self, ruta_assets: str) -> pygame.Surface | None:
        """Carga y escala la imagen de fondo del tablero."""
        ruta = os.path.join(ruta_assets, "board.png")
        try:
            img = pygame.image.load(ruta).convert()
            return pygame.transform.scale(img, (ANCHO_VENTANA, ALTO_VENTANA))
        except FileNotFoundError:
            print(f"[Board] No se encontró board.png — usando color de fondo")
        return None

    def _cargar_imagenes(self) -> dict:
        """
        Carga y escala todas las imágenes de las cartas desde la carpeta assets.

        Returns:
            Diccionario { tipo: Surface } con frentes y la clave "dorso"
        """
        imagenes = {}

        # Cargamos el dorso
        try:
            ruta_dorso = os.path.join(self.ruta_assets, "card_back.png")
            imagenes["dorso"] = pygame.transform.scale(
                pygame.image.load(ruta_dorso).convert_alpha(), CARD_SIZE
            )
        except FileNotFoundError:
            print(f"[Board] No se encontró card_back.png en {self.ruta_assets}")
            imagenes["dorso"] = self._imagen_placeholder(CARD_SIZE, (80, 80, 80))

        # Cargamos cada frente de Pokémon
        for tipo in TIPOS_POKEMON:
            try:
                ruta = os.path.join(self.ruta_assets, f"card_{tipo}.png")
                imagenes[tipo] = pygame.transform.scale(
                    pygame.image.load(ruta).convert_alpha(), CARD_SIZE
                )
            except FileNotFoundError:
                print(f"[Board] No se encontró card_{tipo}.png — usando placeholder")
                imagenes[tipo] = self._imagen_placeholder(CARD_SIZE, (200, 50, 50))

        return imagenes

    def _imagen_placeholder(self, size: tuple, color: tuple) -> pygame.Surface:
        """
        Crea una superficie de color sólido como sustituto si falta un asset.

        Args:
            size  -- (ancho, alto) de la imagen
            color -- color RGB del placeholder
        """
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((*color, 255))
        return surf

    def _generar_cartas(self, sonido_volteo) -> list[Card]:
        """
        Genera las 16 cartas (8 parejas), las baraja y les asigna posición.

        Returns:
            Lista de objetos Card listos para usar
        """
        # Creamos dos cartas por cada tipo (la pareja)
        tipos_barajados = TIPOS_POKEMON * 2
        random.shuffle(tipos_barajados)

        cartas = []
        for i, tipo in enumerate(tipos_barajados):
            fila = i // COLUMNAS
            columna = i % COLUMNAS

            x = OFFSET_X + columna * (CARD_SIZE[0] + MARGEN)
            y = OFFSET_Y + fila * (CARD_SIZE[1] + MARGEN)

            carta = Card(
                tipo=tipo,
                imagen_frente=self._imagenes[tipo],
                imagen_dorso=self._imagenes["dorso"],
                x=x,
                y=y,
                sonido_volteo=sonido_volteo
            )
            cartas.append(carta)

        return cartas

    def _procesar_seleccion(self, carta: Card):
        """
        Gestiona la lógica de selección de cartas:
          - Si es la primera carta, la guarda como seleccionada
          - Si es la segunda, compara con la primera y actúa en consecuencia

        Args:
            carta -- la carta que acaba de voltear el jugador
        """
        if self.carta_seleccionada is None:
            # Primera carta de la jugada
            self.carta_seleccionada = carta
        else:
            # Segunda carta: comparamos
            self.intentos += 1

            if self.carta_seleccionada.tipo == carta.tipo:
                # ¡Pareja encontrada!
                self.carta_seleccionada.emparejada = True
                carta.emparejada = True
                self.parejas_encontradas += 1
                self.carta_seleccionada = None

                if self.sonido_acierto:
                    try:
                        self.sonido_acierto.play()
                    except pygame.error as e:
                        print(f"[Board] Error al reproducir sonido de acierto: {e}")
            else:
                # Fallo: guardamos la segunda carta y activamos espera
                self._carta_fallida = carta
                self.esperando_volteo = True
                self.tiempo_espera = time.time()


    def _voltear_cartas_fallidas(self):
        """
        Voltea boca abajo las dos cartas del intento fallido
        una vez transcurrido el tiempo de espera.
        """
        if self.carta_seleccionada:
            self.carta_seleccionada.voltear()
        if hasattr(self, "_carta_fallida") and self._carta_fallida:
            self._carta_fallida.voltear()

        self.carta_seleccionada = None
        self._carta_fallida = None
        self.esperando_volteo = False