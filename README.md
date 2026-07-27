
<h1 align="center"> Implementación de un Sistema de Comunicación Segura </h1>
<p align="center">
  
Sistema de mensajería cliente-servidor con interfaz gráfica (Tkinter),
pensado como proyecto académico para demostrar, de forma práctica, la
diferencia entre comunicación en texto plano, un cifrado débil (rompible
por fuerza bruta) y un cifrado fuerte de extremo a extremo (RSA
implementado desde cero).

## Descripción

El proyecto está compuesto por tres aplicaciones que se comunican por
sockets TCP:

- **`servidor.py`**: enruta los mensajes entre los clientes conectados.
  Nunca cifra ni descifra nada: solo reenvía bytes (actúa de "cartero").
  Mantiene una lista blanca de usuarios autorizados y el modo de cifrado
  global activo.
- **`cliente.py`**: interfaz gráfica de chat para un usuario normal.
  Permite enviar mensajes privados o a todos ("TODOS"), y muestra los
  mensajes descifrados según el modo activo.
- **`admin.py`**: interfaz gráfica de administración. Se conecta
  automáticamente como `"Admin"` (el único usuario permitido al
  arrancar el servidor) y puede registrar/expulsar usuarios y cambiar el
  modo de cifrado global para todo el sistema.

Los módulos `protocolo.py` y `crypto_utils.py` son compartidos por los
tres programas anteriores:

- **`protocolo.py`**: define un formato de mensajes delimitados por `\n`
  y un buffer de recepción que reconstruye mensajes completos aunque
  TCP los entregue partidos o pegados.
- **`crypto_utils.py`**: implementa dos esquemas de cifrado:
  1. **DEBIL**: desplazamiento fijo de bytes (tipo César), con clave de
     1 byte (256 posibilidades) — deliberadamente rompible por fuerza
     bruta, con fines pedagógicos.
  2. **RSA**: implementado desde cero (sin librerías externas de
     criptografía) usando primalidad de Miller-Rabin, exponenciación e
     inverso modular. Cada usuario genera su propio par de claves y el
     cifrado ocurre de extremo a extremo: el servidor nunca ve el texto
     plano ni las claves privadas.

Ver [`docs/protocolo_y_cifrado.md`](docs/protocolo_y_cifrado.md) para el
detalle técnico completo del protocolo y de ambos esquemas de cifrado.

> ⚠️ **Aviso de uso**: este proyecto fue desarrollado con fines
> exclusivamente académicos y didácticos, como práctica de sockets TCP,
> cifrado y matemáticas discretas. No se recomienda su uso más allá de
> un propósito didáctico o de aprendizaje (por ejemplo, no está pensado
> para manejar comunicaciones reales o información sensible): no cuenta
> con autenticación robusta, el cifrado RSA no usa *padding* estándar
> (como OAEP) y el generador de primos no es criptográficamente seguro
> para producción.

## Integrantes

- Linda Carolina Cortes Bustos
- Antonio Garay Pinzon
- Angel David Baez Camargo

## Requisitos

- **Python 3.8 o superior** (se usa `pow(e, -1, phi)` para el inverso
  modular, disponible desde la versión 3.8).
- **Tkinter** para las interfaces gráficas. En la mayoría de instalaciones
  de Python en Windows y macOS ya viene incluido. En Linux, si no está
  disponible, instalarlo con:
  ```bash
  sudo apt install python3-tk
  ```
- **Ninguna dependencia externa adicional**: todo el proyecto usa
  únicamente la librería estándar de Python (`socket`, `threading`,
  `tkinter`, `base64`, `random`, `unittest`). Por eso no se incluye un
  `requirements.txt` con paquetes de terceros.
- Los tres programas (`servidor.py`, `cliente.py`, `admin.py`) deben
  ejecutarse en la misma red/máquina que puedan alcanzar la IP y el
  puerto configurados (por defecto `127.0.0.1:5555`, es decir, solo la
  misma máquina). Para probar entre varias máquinas de una misma red,
  cambiar `self.host` en `cliente.py`/`admin.py` por la IP del servidor,
  y `HOST = '0.0.0.0'` en `servidor.py` ya permite conexiones externas.

## Instalación

1. Verificar la versión de Python instalada:
   ```bash
   python3 --version
   ```
2. Clonar o descomprimir el proyecto, respetando la estructura de
   carpetas. No es necesario crear un entorno virtual
   ni instalar paquetes, ya que no hay dependencias externas.

## Estructura de carpetas

```
chat-seguro/
├── README.md
├── src/
│   ├── servidor.py        # Servidor central (routing, lista blanca, modo de cifrado)
│   ├── cliente.py          # Interfaz gráfica del cliente
│   ├── admin.py            # Interfaz gráfica del administrador
│   ├── protocolo.py         # Framing de mensajes sobre TCP
│   └── crypto_utils.py     # Cifrado DEBIL y RSA + helpers de alto nivel
├── tests/
│   └── test_crypto_utils.py  # Pruebas automáticas del módulo de cifrado
└── docs/
    └── protocolo_y_cifrado.md  # Detalle técnico del protocolo y los cifrados
```

## Ejecución

Todos los comandos se ejecutan desde la carpeta `src/` (los tres archivos
deben estar en la misma carpeta porque se importan entre sí).

1. **Iniciar el servidor** (dejar esta terminal abierta):
   ```bash
   cd chat-seguro/src
   python3 servidor.py
   ```
   Debería mostrar:
   ```
   Servidor escuchando en 0.0.0.0:5555
   Modo de cifrado: PLANO
   ```

2. **Iniciar el panel de Admin** (en otra terminal):
   ```bash
   cd chat-seguro/src
   python3 admin.py
   ```
   Se conecta automáticamente como `"Admin"`.

3. **Registrar y conectar clientes**: desde el panel de Admin, escribir
   el nombre del usuario en el campo "Usuario a gestionar" y presionar
   **"Registrar (Permitir Ingreso)"**. Recién después de eso ese usuario
   puede conectarse.

4. **Iniciar uno o más clientes** (en terminales adicionales):
   ```bash
   cd chat-seguro/src
   python3 cliente.py
   ```
   Al abrirse, pedirá un nombre de usuario; debe coincidir exactamente
   con el nombre registrado por el Admin en el paso anterior.

## Ejemplo de uso

1. `servidor.py` corriendo.
2. `admin.py` abierto → registrar a `"ana"` con el botón correspondiente.
3. `cliente.py` abierto en otra terminal → login como `"ana"`.
4. Desde `cliente.py`, escribir `TODOS` en "Destinatario" y enviar un
   mensaje: llegará a todos los conectados (incluido el Admin) en modo
   `PLANO` (texto sin cifrar).
5. Desde `admin.py`, cambiar el combo de "Modo de cifrado global" a
   `RSA` y presionar "Aplicar a todo el servidor". Todos los clientes
   recibirán la notificación `SISTEMA_MODO|RSA` y a partir de ahí sus
   mensajes se cifrarán/descifrarán automáticamente de extremo a extremo
   con las claves ya intercambiadas al conectarse.
6. Repetir el paso 4 en modo `DEBIL` y capturar el tráfico con Wireshark
   filtrando por el puerto `5555`, para comparar visualmente cómo se ve
   el mismo mensaje en los tres modos.

## Pruebas / verificación del funcionamiento

### Pruebas automáticas

El módulo `crypto_utils.py` (cifrado DEBIL, RSA y los helpers de alto
nivel) cuenta con una batería de pruebas unitarias que no requieren
sockets ni interfaz gráfica:

```bash
cd chat-seguro
python3 -m unittest tests.test_crypto_utils -v
```

Resultado esperado: `13 tests` ejecutados, todos `OK`.

> No se automatizaron pruebas de `servidor.py`, `cliente.py` ni
> `admin.py` porque dependen de sockets en vivo y de una interfaz
> gráfica Tkinter en ejecución; en su lugar, la verificación de esa
> parte se hace de forma manual siguiendo la siguiente guia.

### Guía de verificación manual (integración completa)

1. Iniciar `servidor.py`, `admin.py`, y **dos** instancias de
   `cliente.py` (por ejemplo `"ana"` y `"bruno"`), registrando a ambos
   desde el Admin antes de conectarlos.
2. **Lista blanca**: intentar conectar un tercer cliente sin registrarlo
   primero → debe recibir "Acceso denegado" y cerrarse.
3. **Mensaje privado en PLANO**: `ana` envía un mensaje a `bruno` →
   debe aparecer solo en la ventana de `bruno` (y en el log del Admin
   si el Admin lo tiene como destinatario/está en TODOS).
4. **Cambio de modo DEBIL**: desde Admin, aplicar `DEBIL` → todos los
   clientes deben mostrar la etiqueta de cifrado actualizada; un
   mensaje enviado debe seguir viéndose en texto plano en la interfaz
   (porque se descifra automáticamente), pero al capturarlo con
   Wireshark debe verse como Base64.
5. **Cambio de modo RSA**: aplicar `RSA` → un mensaje enviado a "TODOS"
   debe seguir llegando correctamente descifrado a cada cliente, aun
   cuando cada uno recibió una copia cifrada distinta.
6. **Expulsión**: desde Admin, expulsar a `bruno` (Kick) → su ventana
   debe mostrar "Has sido desconectado" y cerrar el socket.
7. **KICKALL**: debe desconectar a todos los clientes menos al Admin.

## Nota sobre uso de IA

Durante el desarrollo de este proyecto se utilizó inteligencia
artificial (Claude, de Anthropic) como apoyo puntual para: entender
conceptos teóricos (framing TCP, primalidad de Miller-Rabin, RSA),
sugerir mejoras de código y buenas prácticas, ayudar con el diseño de
las interfaces gráficas (Tkinter) de `cliente.py` y `admin.py`, y
apoyar la redacción del informe. El diseño general del sistema y la
lógica de negocio fueron trabajo del equipo.

## Estado actual del proyecto

- ✅ Comunicación cliente-servidor funcional vía TCP con framing robusto
  (`protocolo.py`), resistente a mensajes largos y partidos por TCP.
- ✅ Lista blanca de usuarios administrada por el Admin.
- ✅ Comandos de administración: registrar, expulsar individual y
  expulsar a todos.
- ✅ Tres modos de cifrado funcionales y conmutables en caliente desde
  el panel de Admin: `PLANO`, `DEBIL` (rompible, con fines
  demostrativos) y `RSA` (extremo a extremo, implementado desde cero).
- ✅ Distribución automática de claves públicas RSA al conectarse cada
  usuario.
- ✅ Pruebas automáticas del módulo de cifrado (13/13 pasando).
- ⚠️ **Limitaciones conocidas** (ver también `docs/protocolo_y_cifrado.md`):
  - El RSA implementado es con fines didácticos: no usa *padding*
    (como OAEP) y el generador de primos no es criptográficamente
    seguro para un entorno de producción real.
  - No hay persistencia: la lista blanca, las claves públicas y el
    historial de chat viven solo en memoria mientras el servidor está
    corriendo (se pierden al reiniciarlo).
  - No hay autenticación por contraseña: el "registro" del Admin solo
    valida el *nombre* de usuario, no verifica identidad.
  - Pendiente (a criterio del equipo): agregar la sección "Integrantes"
    en este README con los datos reales del grupo.
