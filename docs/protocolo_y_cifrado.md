# Protocolo de comunicación y esquemas de cifrado

Este documento amplía, a nivel técnico, cómo se comunican `servidor.py`,
`cliente.py` y `admin.py`, y cómo funcionan los dos esquemas de cifrado
implementados en `crypto_utils.py`.

## 1. Formato de los mensajes sobre el socket

Todo el tráfico TCP usa **texto delimitado por `\n`** (ver `protocolo.py`).
Cada línea tiene la forma:

```
destinatario|contenido
```

- `enviar(conn, texto)` agrega el `\n` final y hace `sendall`.
- `BufferRecepcion` acumula bytes crudos y va extrayendo líneas completas,
  porque TCP no garantiza que un `recv()` devuelva exactamente un mensaje
  (puede llegar partido o con varios mensajes pegados). Esto es
  especialmente importante con RSA, donde los mensajes cifrados son
  mucho más largos que en texto plano.

### Mensajes especiales (prefijos reservados en el campo "destinatario")

| Prefijo         | Dirección           | Significado                                                             |
|-----------------|----------------------|--------------------------------------------------------------------------|
| `__PUBKEY__`    | cliente → servidor   | Registra/actualiza la clave pública RSA del usuario                     |
| `CLAVEPUB`      | servidor → cliente   | Distribuye `nombre_usuario\|clave` a los demás conectados               |
| `SISTEMA_MODO`  | servidor → cliente   | Notifica el modo de cifrado activo (`PLANO`, `DEBIL` o `RSA`)           |
| `Sistema`       | servidor → cliente   | Mensajes informativos (registro, expulsión, errores)                    |
| `REGISTER`      | Admin → servidor     | Agrega un usuario a la lista blanca                                     |
| `KICK`          | Admin → servidor     | Desconecta a un usuario puntual                                         |
| `KICKALL`       | Admin → servidor     | Desconecta a todos menos al Admin                                       |
| `CIFRADO`       | Admin → servidor     | Cambia el modo de cifrado global                                        |
| `TODOS`         | cliente → servidor   | Mensaje de difusión (broadcast) a todos los conectados                  |

## 2. Flujo de conexión

1. El cliente/admin abre el socket y envía su nombre de usuario como
   primer mensaje.
2. El servidor verifica que el nombre esté en `usuarios_permitidos`
   (lista blanca). Si no lo está, responde `Sistema|Acceso denegado...`
   y cierra la conexión. **Solo `"Admin"` está permitido desde el arranque**;
   cualquier otro usuario debe ser registrado por el Admin con el botón
   "Registrar".
3. El servidor informa el modo de cifrado activo (`SISTEMA_MODO|...`).
4. En segundo plano, el cliente genera su par de claves RSA (1024 bits)
   y las registra en el servidor con `__PUBKEY__`, sin bloquear la interfaz.
5. El servidor reenvía esa clave pública a todos los demás conectados y,
   al recién llegado, le envía el directorio completo de claves existentes.

## 3. Modo de cifrado "DEBIL" (Cesar por bytes)

- Cada byte del mensaje se desplaza `+7` (módulo 256) y el resultado se
  codifica en Base64 para poder viajar como texto.
- **Es intencionalmente inseguro**: solo hay 256 claves posibles. La función
  `romper_cifrado_debil()` prueba las 256 y permite reconstruir el mensaje
  por fuerza bruta en milisegundos.
- Objetivo pedagógico: capturar el tráfico con Wireshark en este modo y
  demostrar que un espacio de claves pequeño no ofrece protección real.

## 4. Modo de cifrado "RSA" (implementado desde cero)

Implementado sin librerías externas de criptografía, usando conceptos de
Matemáticas Discretas:

- **Primalidad**: test de Miller-Rabin probabilístico (`_es_primo`, 20 rondas).
- **Generación de claves**: dos primos `p`, `q` de `bits/2` cada uno,
  `n = p*q`, `φ(n) = (p-1)(q-1)`, exponente público fijo `e = 65537`
  (ajustado si no es coprimo con `φ(n)`), exponente privado `d` calculado
  como el inverso modular de `e` módulo `φ(n)` (`pow(e, -1, phi)`,
  disponible desde Python 3.8).
- **Cifrado por bloques**: el mensaje se parte en bloques de
  `(bits_de_n // 8) - 1` bytes (para garantizar que cada bloque numérico
  sea menor que `n`), cada bloque se cifra como `c = m^e mod n`, y los
  bloques cifrados se envían separados por comas.
- **Descifrado**: `m = c^d mod n` para cada bloque, reensamblando los bytes.
- **Extremo a extremo real**: el servidor solo almacena y reenvía las
  claves *públicas* (`claves_publicas`); nunca ve las claves privadas ni
  tiene forma de descifrar el contenido. Actúa exclusivamente como
  "cartero".
- **Envío a "TODOS" en modo RSA**: no existe una clave "de todos", así que
  `preparar_envios()` genera una copia cifrada distinta por cada contacto
  conocido en el directorio de claves.

### Limitación conocida

El generador de primos (`_generar_primo`) usa `random.getrandbits`, que no
es criptográficamente seguro (no es apto para producción real), y el
esquema no incluye *padding* (como OAEP). Es una implementación con fines
didácticos para visualizar el algoritmo, no un reemplazo de una librería
de criptografía auditada (p. ej. `cryptography` o `PyCryptodome`).

## 5. Rol del Admin

`admin.py` se conecta automáticamente como `"Admin"` (único usuario en la
lista blanca al iniciar el servidor) y expone:

- Registrar/expulsar usuarios individuales o a todos.
- Cambiar el modo de cifrado global, lo que el servidor propaga a todos
  los clientes conectados vía `SISTEMA_MODO`.
- Enviar mensajes globales, cifrados según el modo activo igual que
  cualquier otro cliente.
