# Pokémon Matching Cards 🎴

## Descripción de la aplicación

Pokémon Matching Cards es un juego de matching cards desarrollado en Python con temática Pokémon. El jugador (mi sobrino) debe encontrar todas las parejas de cartas en el menor tiempo posible y con el menor número de intentos. El tablero contiene 16 cartas (8 parejas) dispuestas boca abajo. En cada turno se voltean dos cartas: si coinciden, permanecen visibles; si no, se vuelven a ocultar tras 1,5 segundos.

Los recursos usados de Pokemon son assets gratuitos encontrados en: https://press.pokemon.com/en/Pokemon-Cafe-Mix/Focus/Pokemon-Cafe-Mix-artwork (don't sue me Nintendo)

---

## Librería externa utilizada

**pygame** — librería de desarrollo de videojuegos para Python.

Se utiliza para gestionar la ventana gráfica, el bucle principal del juego, la carga y renderizado de imágenes, la animación de volteo de cartas, la detección de eventos de ratón y teclado, y la reproducción de efectos de sonido.

---

## Instalación de dependencias

Asegúrate de tener Python 3.10 o superior instalado. Luego, desde la carpeta raíz del proyecto, ejecuta:

```bash
pip install -r requirements.txt
```

El archivo `requirements.txt` contiene:

```
pygame==2.6.1
```
(Se deja el archivo requirements por buenas prácticas pero al ser sólo una librería podría ejecutarse `pip install pygame` y fin)

---

## Ejecución de la aplicación

Desde la carpeta raíz del proyecto ejecuta:

```
python main.py
```

> ⚠️ Es importante ejecutar el comando desde la carpeta raíz (`Proy_Python_Librerias/`) y no desde dentro de `src/`, para que los imports del paquete funcionen correctamente.

---

## Descripción general del funcionamiento

### Estructura del proyecto

```
Proy_Python_Librerias/
├── main.py               # Punto de entrada de la aplicación
├── requirements.txt      # Dependencias externas
├── README.md
|
└── src/
    ├── assets/
    │   ├── images/           # Sprites de Pokémon, dorso de carta y fondo del tablero
    │   └── sounds/           # Efectos de sonido (.wav)
    ├── __init__.py       # Paquete src, expone Card, Board y Game
    ├── card.py           # Clase Card: representa una carta individual
    ├── board.py          # Clase Board: gestiona el tablero y la lógica de juego
    └── game.py           # Clase Game: bucle principal, estados y renderizado de UI
```

### Flujo del juego

1. Al ejecutar `main.py` se inicializa pygame y se crea la ventana de 700x700 px.
2. El tablero genera 16 cartas (8 parejas de Pokémon) en posiciones aleatorias.
3. El jugador hace clic en una carta para voltearla. Al voltear una segunda carta:
   - Si coinciden: se marcan como emparejadas y permanecen visibles con borde dorado.
   - Si no coinciden: se muestran 1,5 segundos y se vuelven boca abajo.
4. La partida termina cuando se encuentran las 8 parejas. El tiempo se detiene y se muestra la pantalla de resultados con el tiempo final y el número de intentos.
5. Pulsando `R` o el botón REINICIO se inicia una nueva partida con las cartas barajadas de nuevo.

### Módulos estándar utilizados

- **`random`** — para barajar las cartas al inicio de cada partida (`random.shuffle`).
- **`time`** — para controlar el temporizador de partida y la pausa de 1,5 segundos entre volteos fallidos.
- **`os`** — para construir rutas de archivos de forma portable entre sistemas operativos (`os.path.join`).
- **`sys`** — para cerrar la aplicación limpiamente (`sys.exit`).

### Controles

| Acción | Control |
|--------|---------|
| Voltear carta | Clic izquierdo |
| Reiniciar partida | Tecla `R` o botón REINICIO |
| Salir del juego | Tecla `ESC` |

---

## Principales dificultades encontradas y soluciones

### 1. Bug en la animación de volteo de cartas

**Problema:** La primera carta volteada en cada turno no se quedaba boca arriba correctamente. Tras la animación volvía a su estado original.

**Causa:** El atributo `self.volteada` se modificaba en tres sitios distintos durante la animación (en `actualizar()` y en `_dibujar_con_animacion()`), y los cambios se pisaban entre sí.

**Solución:** Se introdujo el atributo `_flip_destino` para separar el estado visual durante la animación del estado real de la carta. La regla quedó clara: `self.volteada` solo se modifica en un único sitio, al final de `actualizar()` cuando la animación termina por completo.

---

### 2. Gestión del tiempo de espera entre volteos fallidos

**Problema:** Era necesario mostrar las dos cartas fallidas durante 1,5 segundos antes de voltearlas, sin bloquear el bucle principal del juego.

**Causa:** Usar `time.sleep()` congela pygame completamente, lo que hace que la ventana deje de responder.

**Solución:** Se utilizó `time.time()` del módulo estándar `time` para registrar el momento del fallo y comprobar en cada frame si ha transcurrido el tiempo de espera, sin interrumpir el bucle principal en ningún momento.

---

### 3. Glitch visual en la última pareja

**Problema:** Al encontrar la última pareja, la pantalla de fin aparecía antes de que terminase la animación de volteo, causando un parpadeo visual.

**Causa:** El cambio de estado a `ESTADO_FIN` se producía en el mismo frame en que `partida_completada` pasaba a `True`, sin esperar a que las animaciones terminasen.

**Solución:** Se añadió una comprobación adicional antes de cambiar de estado, verificando que ninguna carta tenga una animación activa en ese momento mediante `any(c._flip_activo for c in self.board.cartas)`.

---

### 4. Emojis no renderizados en la UI

**Problema:** El emoji ⏱ usado como icono del temporizador aparecía como un cuadrado vacío en pantalla.

**Causa:** Las fuentes del sistema cargadas con `pygame.font.SysFont` no incluyen soporte para emojis Unicode.

**Solución:** Se sustituyó el emoji por un pequeño reloj dibujado directamente con las primitivas de pygame (`pygame.draw.circle` y `pygame.draw.line`), sin necesidad de ningún asset externo.

---

### 5. Imagen de fondo sin ocupar toda la ventana

**Problema:** La imagen de fondo del tablero (`board.png`) era rectangular (2000x1259 px) y al escalarla a la ventana cuadrada aparecía recortada o dejaba zonas negras.

**Causa:** La proporción de la imagen original no coincidía con la de la ventana del juego.

**Solución:** Se recortó la imagen al cuadrado central (1259x1259 px) y se reescaló a 700x700 px, ajustando a continuación las dimensiones de la ventana para que coincidiesen exactamente con las del fondo.
