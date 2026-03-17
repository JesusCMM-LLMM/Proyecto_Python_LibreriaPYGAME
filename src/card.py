import pygame
import os

# Tamaño estándar de todas las cartas en pantalla
CARD_SIZE = (120, 120)

# Duración de la animación de volteo en milisegundos
FLIP_DURATION = 300


class Card:
    """
    Representa una carta individual del tablero.

    Atributos principales:
        tipo        -- identificador del Pokémon (str), usado para comparar parejas
        volteada    -- True si el frontal está visible
        emparejada  -- True si ya fue encontrada su pareja
        rect        -- pygame.Rect con posición y tamaño en pantalla
    """

    def __init__(self, tipo: str, imagen_frente: pygame.Surface,
                 imagen_dorso: pygame.Surface, x: int, y: int,
                 sonido_volteo: pygame.mixer.Sound = None):
        self.tipo = tipo
        self.imagen_frente = imagen_frente
        self.imagen_dorso = imagen_dorso
        self.sonido_volteo = sonido_volteo

        # Estado de la carta
        self.volteada = False
        self.emparejada = False
        self.hover = False

        # Posición y tamaño
        self.rect = pygame.Rect(x, y, CARD_SIZE[0], CARD_SIZE[1])

        # --- Animación de volteo ---
        self._flip_activo = False
        self._flip_inicio = 0
        # Estado destino: True = boca arriba, False = boca abajo
        self._flip_destino = False

    # ------------------------------------------------------------------
    # Métodos públicos
    # ------------------------------------------------------------------

    def voltear(self):
        """
        Inicia la animación de volteo si la carta no está emparejada ni animándose.
        Reproduce el sonido de volteo si está disponible.
        """
        if self.emparejada or self._flip_activo:
            return

        if self.sonido_volteo:
            try:
                self.sonido_volteo.play()
            except pygame.error as e:
                print(f"[Card] Error al reproducir sonido: {e}")

        self._flip_activo = True
        self._flip_inicio = pygame.time.get_ticks()
        # El destino es siempre el opuesto al estado actual
        self._flip_destino = not self.volteada

    def contiene_punto(self, pos: tuple) -> bool:
        """Devuelve True si (x, y) están dentro del rect de la carta."""
        return self.rect.collidepoint(pos)

    def actualizar_hover(self, pos_raton: tuple):
        """Actualiza el estado hover según la posición del ratón."""
        self.hover = self.rect.collidepoint(pos_raton) and not self.emparejada

    def actualizar(self):
        """
        Avanza la animación de volteo.
        Al terminar, aplica _flip_destino a self.volteada.
        self.volteada NO se toca durante la animación, solo al final.
        """
        if not self._flip_activo:
            return

        transcurrido = pygame.time.get_ticks() - self._flip_inicio

        if transcurrido >= FLIP_DURATION:
            self._flip_activo = False
            self.volteada = self._flip_destino   # único punto donde cambia

    def dibujar(self, superficie: pygame.Surface):
        """Dibuja la carta aplicando animación y hover según corresponda."""
        if self._flip_activo:
            self._dibujar_con_animacion(superficie)
        else:
            imagen = self.imagen_frente if self.volteada else self.imagen_dorso
            self._dibujar_normal(superficie, imagen)

    # ------------------------------------------------------------------
    # Métodos privados
    # ------------------------------------------------------------------

    def _dibujar_normal(self, superficie: pygame.Surface, imagen: pygame.Surface):
        """Dibuja la carta estática con efecto hover y borde de emparejada."""
        if self.hover and not self.volteada:
            margen = 4
            imagen_grande = pygame.transform.scale(
                imagen, (CARD_SIZE[0] + margen * 2, CARD_SIZE[1] + margen * 2)
            )
            superficie.blit(imagen_grande, (self.rect.x - margen, self.rect.y - margen))
            pygame.draw.rect(superficie, (255, 255, 255),
                             self.rect.inflate(margen * 2, margen * 2), 2, border_radius=6)
        else:
            superficie.blit(imagen, self.rect.topleft)

        if self.emparejada:
            pygame.draw.rect(superficie, (212, 175, 55), self.rect, 3, border_radius=4)

    def _dibujar_con_animacion(self, superficie: pygame.Surface):
        """
        Simula el volteo comprimiendo la carta horizontalmente en dos fases:
        - Primera mitad: imagen actual se comprime de ancho completo a 0
        - Segunda mitad: imagen destino se expande de 0 a ancho completo
        self.volteada no se modifica aquí; solo se consulta _flip_destino.
        """
        transcurrido = pygame.time.get_ticks() - self._flip_inicio
        mitad = FLIP_DURATION // 2

        if transcurrido < mitad:
            factor = 1.0 - (transcurrido / mitad)
            imagen_actual = self.imagen_frente if self.volteada else self.imagen_dorso
        else:
            factor = (transcurrido - mitad) / mitad
            imagen_actual = self.imagen_frente if self._flip_destino else self.imagen_dorso

        ancho_escalado = max(1, int(CARD_SIZE[0] * factor))
        imagen_escalada = pygame.transform.scale(imagen_actual, (ancho_escalado, CARD_SIZE[1]))
        offset_x = self.rect.x + (CARD_SIZE[0] - ancho_escalado) // 2
        superficie.blit(imagen_escalada, (offset_x, self.rect.y))