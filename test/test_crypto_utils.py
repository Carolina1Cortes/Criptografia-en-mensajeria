"""
test_crypto_utils.py
=====================
Pruebas automáticas para el módulo crypto_utils.py.

No se prueban servidor.py / cliente.py / admin.py directamente porque
dependen de sockets abiertos y de una interfaz gráfica (Tkinter) en
ejecución. En su lugar, este archivo cubre la lógica de cifrado, que es
la parte "pura" (sin I/O) y la más sensible a errores silenciosos.

Cómo ejecutar:
    cd chat-seguro
    python -m unittest tests.test_crypto_utils -v

o simplemente:
    python tests/test_crypto_utils.py
"""

import os
import sys
import unittest

# Permite ejecutar el archivo desde cualquier carpeta, agregando src/ al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import crypto_utils as cu  # noqa: E402


class TestCifradoDebil(unittest.TestCase):

    def test_cifrar_y_descifrar_devuelve_texto_original(self):
        original = "Hola, esto es una prueba con ñ y acentos áéí!"
        cifrado = cu.cifrar_debil(original)
        self.assertNotEqual(cifrado, original)
        self.assertEqual(cu.descifrar_debil(cifrado), original)

    def test_clave_incorrecta_no_reconstruye_el_texto(self):
        original = "mensaje secreto"
        cifrado = cu.cifrar_debil(original, clave=7)
        # Con otra clave, el resultado no debería coincidir
        self.assertNotEqual(cu.descifrar_debil(cifrado, clave=99), original)

    def test_romper_cifrado_encuentra_la_clave_correcta(self):
        original = "texto de prueba para fuerza bruta"
        clave_real = 42
        cifrado = cu.cifrar_debil(original, clave=clave_real)
        resultados = cu.romper_cifrado_debil(cifrado)
        self.assertEqual(len(resultados), 256)
        self.assertEqual(resultados[clave_real], original)


class TestRSA(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 256 bits alcanza para probar rápido; en producción se usan 1024.
        cls.pub, cls.priv = cu.generar_claves_rsa(256)

    def test_claves_generadas_tienen_formato_correcto(self):
        e, n = self.pub
        d, n2 = self.priv
        self.assertEqual(n, n2)
        self.assertIsInstance(e, int)
        self.assertIsInstance(d, int)

    def test_cifrar_y_descifrar_mensaje_corto(self):
        original = "Hola"
        cifrado = cu.rsa_cifrar(original, self.pub)
        self.assertEqual(cu.rsa_descifrar(cifrado, self.priv), original)

    def test_cifrar_y_descifrar_mensaje_largo_con_varios_bloques(self):
        original = "Este es un mensaje bastante más largo que un solo bloque " * 3
        cifrado = cu.rsa_cifrar(original, self.pub)
        self.assertEqual(cu.rsa_descifrar(cifrado, self.priv), original)

    def test_serializar_y_deserializar_clave_publica(self):
        texto = cu.clave_publica_a_texto(self.pub)
        self.assertIn(",", texto)
        self.assertEqual(cu.texto_a_clave_publica(texto), self.pub)

    def test_no_se_puede_descifrar_con_clave_privada_ajena(self):
        otro_pub, otro_priv = cu.generar_claves_rsa(256)
        cifrado = cu.rsa_cifrar("mensaje confidencial", self.pub)
        resultado = cu.rsa_descifrar(cifrado, otro_priv)
        self.assertNotEqual(resultado, "mensaje confidencial")


class TestPrepararEnviosYProcesarEntrante(unittest.TestCase):

    def setUp(self):
        self.pub_a, self.priv_a = cu.generar_claves_rsa(256)
        self.pub_b, self.priv_b = cu.generar_claves_rsa(256)

    def test_modo_plano_no_altera_el_texto(self):
        envios = cu.preparar_envios("Bob", "hola", "PLANO", {})
        self.assertEqual(envios, [("Bob", "hola")])

    def test_modo_debil_cifra_el_texto(self):
        envios = cu.preparar_envios("Bob", "hola", "DEBIL", {})
        destinatario, payload = envios[0]
        self.assertEqual(destinatario, "Bob")
        self.assertEqual(cu.descifrar_debil(payload), "hola")

    def test_modo_rsa_sin_clave_conocida_lanza_error(self):
        with self.assertRaises(ValueError):
            cu.preparar_envios("Bob", "hola", "RSA", {})

    def test_modo_rsa_a_todos_cifra_una_copia_por_contacto(self):
        directorio = {"A": self.pub_a, "B": self.pub_b}
        envios = cu.preparar_envios("TODOS", "hola a todos", "RSA", directorio)
        self.assertEqual(len(envios), 2)
        destinos = dict(envios)
        self.assertEqual(cu.rsa_descifrar(destinos["A"], self.priv_a), "hola a todos")
        self.assertEqual(cu.rsa_descifrar(destinos["B"], self.priv_b), "hola a todos")

    def test_procesar_entrante_con_payload_corrupto_no_lanza_excepcion(self):
        resultado = cu.procesar_entrante("###no-es-un-numero###", "RSA", self.priv_a)
        self.assertEqual(resultado, "[No se pudo descifrar este mensaje]")


if __name__ == "__main__":
    unittest.main(verbosity=2)
