import unittest

# Importar las clases de POO
from db_connection import create_connection, close_connection
from mysql_env import crear_tablas, insert_usuario
from usuario import Usuario, hash_password
from juego_mesa import JuegoMesa
from venta import Venta

# --- CONFIGURACIoN DE PRUEBA ---
TEST_PASSWORD = "TestPassword123"
TEST_JUEGO = "test game"
TEST_JUEGO_ID = 0
TEST_CLIENTE_ID = 0
TEST_VENDEDOR_ID = 0


class TestTienda(unittest.TestCase):
    """Clase principal para ejecutar las pruebas unitarias."""

    @classmethod
    def setUpClass(cls):
        """Prepara la conexion y la estructura de la BD antes de todas las pruebas."""
        cls.conn = create_connection()
        if cls.conn:
            crear_tablas(cls.conn)

            # Pongo usuarios de prueba
            insert_usuario(cls.conn, "AdminTest", "admin", hash_password(TEST_PASSWORD))
            insert_usuario(
                cls.conn, "ClientTest", "cliente", hash_password(TEST_PASSWORD)
            )

            # Pongo IDs para la prueba de FOREIGN KEY
            cls.admin_user = Usuario.buscar_por_nombre("AdminTest")
            cls.cliente_user = Usuario.buscar_por_nombre("ClientTest")
            global TEST_CLIENTE_ID, TEST_VENDEDOR_ID
            TEST_CLIENTE_ID = cls.cliente_user.id
            TEST_VENDEDOR_ID = cls.admin_user.id

        else:
            raise Exception(
                "No se pudo conectar a la BD de prueba. Revisar credenciales."
            )


    # Limpiamos las tablas para probar en un ambiente limpio
    def setUp(self):
        """Limpia los registros de juegos antes de cada prueba individual."""
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ventas")
        cursor.execute("DELETE FROM ludoteca_sesiones")
        cursor.execute("DELETE FROM ludoteca_participantes")
        cursor.execute("DELETE FROM juegos_mesa")
        conn.commit()
        cursor.close()
        close_connection(conn)

    # --- PRUEBA 1: Probamos los CRUD ---
    def test_1_crud_juego_mesa(self):
        """Prueba la creacion y busqueda de un producto."""
        global TEST_JUEGO_ID

        # 1. Crear 
        juego = JuegoMesa.crear(TEST_JUEGO, "Fabricante Test", 10, 50.00, 5.00)
        self.assertIsNotNone(juego, "La creacion del juego fallo.")
        self.assertEqual(juego.titulo, TEST_JUEGO)
        TEST_JUEGO_ID = juego.id

        # 2. Buscar (R)
        juego_buscado = JuegoMesa.buscar_por_titulo(TEST_JUEGO)
        self.assertIsNotNone(juego_buscado, "La busqueda por juego fallo.")
        self.assertEqual(juego_buscado.stock, 10)

        # 3. Eliminar (D)
        JuegoMesa.eliminar(juego.id)
        juego_eliminado = JuegoMesa.buscar_por_titulo(TEST_JUEGO)
        self.assertIsNone(juego_eliminado, "La eliminacion del juego fallo.")
        
        print("\nPrueba 1 (CRUD Juegos): Realizada con exito - Se creo, busco y elimino correctamente.")

    # --- PRUEBA 2: Probar stock ---
    def test_2_stock_insuficiente(self):
        """Prueba que una venta falle si no hay stock."""
        juego = JuegoMesa.crear("Juego Sin Stock", "F", 5, 20.00, 2.00)

        # vender 6 cuando nomas hay 5
        with self.assertRaisesRegex(Exception, "Inventario insuficiente"):
            juego.reducir_stock(6)
            
        print("\nPrueba 2 (Validacion Stock): Realizada con exito - El sistema impidio vender sin inventario.")

    # --- PRUEBA 3: Probar la reduccion del stock ---
    def test_3_transaccion_venta_exitosa(self):
        """Prueba que una venta registre la accion y reduzca el stock."""
        juego = JuegoMesa.crear("Venta Test", "F", 5, 20.00, 2.00)

        # 1. Vender
        venta = Venta.crear(TEST_CLIENTE_ID, juego.id, 3)
        self.assertIsNotNone(venta, "La creacion de la venta fallo.")
        self.assertEqual(venta.precio_total, 60.00)  # 3 * 20.00

        # 2. Ver que el stock se actualizo correctamente en la BD
        juego_actualizado = JuegoMesa.buscar_por_id(juego.id)
        self.assertEqual(juego_actualizado.stock, 2)  # 5 - 3 = 2

        # 3. Eliminar la venta y verificar que el stock regrese
        Venta.eliminar(venta.id)
        juego_post_eliminacion = JuegoMesa.buscar_por_id(juego.id)
        self.assertEqual(juego_post_eliminacion.stock, 5)  
        
        print("\nPrueba 3 (Transaccion Venta): Realizada con exito - Venta registrada y stock actualizado.")

    # --- PRUEBA 4: Autenticacion Y hashing ---
    def test_4_autenticacion_usuario(self):
        """Prueba que el hashing y la autenticacion funcionen correctamente."""
        # 1. Prueba de autenticacion exitosa 
        cliente_auth = Usuario.autenticar("ClientTest", TEST_PASSWORD)
        self.assertIsNotNone(
            cliente_auth, "La autenticacion del usuario cliente fallo."
        )

        # 2. Prueba de autenticacion fallida
        cliente_fail = Usuario.autenticar("ClientTest", "contraseña incorrecta")
        self.assertIsNone(cliente_fail, "La autenticacion fallida no devolvio None.")
        
        print("\nPrueba 4 (Seguridad): Realizada con exito - Autenticacion correcta y rechazo de claves erroneas.")


# Ejecucion de las pruebas
if __name__ == "__main__":
    unittest.main()