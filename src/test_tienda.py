# test_tienda.py

import unittest
import time
import os
from datetime import datetime, timedelta

# Importar las clases de POO
from db_connection import create_connection, close_connection
from mysql_env import crear_tablas, insert_usuario
from usuario import Usuario, hash_password
from juego_mesa import JuegoMesa
from venta import Venta
from ludoteca_sesion import LudotecaSesion
from ludoteca_participante import LudotecaParticipante

# --- CONFIGURACIÓN DE PRUEBA ---
# Se recomienda usar una BD de prueba diferente en un entorno real,
# pero aquí usamos la BD principal limpiando los datos.
TEST_PASSWORD = "testpwd"
TEST_JUEGO = "Test Catan"
TEST_JUEGO_ID = 0 
TEST_CLIENTE_ID = 0
TEST_VENDEDOR_ID = 0


class TestTienda(unittest.TestCase):
    """Clase principal para ejecutar las pruebas unitarias."""

    @classmethod
    def setUpClass(cls):
        """Prepara la conexión y la estructura de la BD antes de todas las pruebas."""
        cls.conn = create_connection()
        if cls.conn:
            # Creamos las tablas
            crear_tablas(cls.conn) 
            
            # Insertar usuarios base necesarios para transacciones
            insert_usuario(cls.conn, "AdminTest", "admin", hash_password(TEST_PASSWORD))
            insert_usuario(cls.conn, "ClientTest", "cliente", hash_password(TEST_PASSWORD))
            
            # Obtener IDs para usar en las pruebas de FOREIGN KEY
            cls.admin_user = Usuario.buscar_por_nombre("AdminTest")
            cls.cliente_user = Usuario.buscar_por_nombre("ClientTest")
            global TEST_CLIENTE_ID, TEST_VENDEDOR_ID
            TEST_CLIENTE_ID = cls.cliente_user.id
            TEST_VENDEDOR_ID = cls.admin_user.id
            
        else:
            raise Exception("No se pudo conectar a la BD de prueba. Revisar credenciales.")

    @classmethod
    def tearDownClass(cls):
        """Cierra la conexión después de todas las pruebas."""
        # Se puede agregar lógica para ELIMINAR las tablas después de la prueba
        close_connection(cls.conn)

    def setUp(self):
        """Limpia los registros de juegos antes de cada prueba individual."""
        # Esto asegura que cada prueba empieza con un catálogo limpio
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ventas")
        cursor.execute("DELETE FROM ludoteca_sesiones")
        cursor.execute("DELETE FROM ludoteca_participantes")
        cursor.execute("DELETE FROM juegos_mesa")
        conn.commit()
        cursor.close()
        close_connection(conn)
        
    # --- PRUEBA 1: CRUD BÁSICO DE JUEGO MESA ---
    def test_1_crud_juego_mesa(self):
        """Prueba la creacion y busqueda de un producto."""
        global TEST_JUEGO_ID
        
        # 1. Crear (C)
        juego = JuegoMesa.crear(TEST_JUEGO, "Fabricante Test", 10, 50.00, 5.00)
        self.assertIsNotNone(juego, "La creación del juego falló.")
        self.assertEqual(juego.titulo, TEST_JUEGO)
        TEST_JUEGO_ID = juego.id

        # 2. Buscar (R)
        juego_buscado = JuegoMesa.buscar_por_titulo(TEST_JUEGO)
        self.assertIsNotNone(juego_buscado, "La búsqueda por título falló.")
        self.assertEqual(juego_buscado.stock, 10)
        
        # 3. Eliminar (D)
        JuegoMesa.eliminar(juego.id)
        juego_eliminado = JuegoMesa.buscar_por_titulo(TEST_JUEGO)
        self.assertIsNone(juego_eliminado, "La eliminación del juego falló.")

    # --- PRUEBA 2: LÓGICA DE EXCEPCIONES (STOCK) ---
    def test_2_stock_insuficiente(self):
        """Prueba que una venta falle si no hay stock (Manejo de Excepciones)."""
        juego = JuegoMesa.crear("Juego Sin Stock", "F", 5, 20.00, 2.00)
        
        # Intentar vender 6 unidades cuando solo hay 5
        with self.assertRaisesRegex(Exception, "Inventario insuficiente"):
            juego.reducir_stock(6)

    # --- PRUEBA 3: TRANSACCIÓN DE VENTA (Atomicidad y Lógica de Negocio) ---
    def test_3_transaccion_venta_exitosa(self):
        """Prueba que una venta registre la transacción y reduzca el stock."""
        juego = JuegoMesa.crear("Venta Test", "F", 5, 20.00, 2.00)
        
        # 1. Crear Venta (Debe reducir stock)
        venta = Venta.crear(TEST_CLIENTE_ID, juego.id, 3)
        self.assertIsNotNone(venta, "La creación de la venta falló.")
        self.assertEqual(venta.precio_total, 60.00) # 3 * 20.00
        
        # 2. Verificar que el stock se actualizó correctamente en la BD
        juego_actualizado = JuegoMesa.buscar_por_id(juego.id)
        self.assertEqual(juego_actualizado.stock, 2) # 5 - 3 = 2
        
        # 3. Eliminar la venta y verificar que el stock regrese (Rollback Lógico)
        Venta.eliminar(venta.id)
        juego_post_eliminacion = JuegoMesa.buscar_por_id(juego.id)
        self.assertEqual(juego_post_eliminacion.stock, 5) # Stock debe volver a 5

    # --- PRUEBA 4: AUTENTICACIÓN Y HASHING ---
    def test_4_autenticacion_usuario(self):
        """Prueba que el hashing y la autenticación funcionen correctamente."""
        # 1. Prueba de autenticación exitosa (ClientTest)
        cliente_auth = Usuario.autenticar("ClientTest", TEST_PASSWORD)
        self.assertIsNotNone(cliente_auth, "La autenticación del usuario cliente falló.")
        
        # 2. Prueba de autenticación fallida (contraseña incorrecta)
        cliente_fail = Usuario.autenticar("ClientTest", "contraseñaincorrecta")
        self.assertIsNone(cliente_fail, "La autenticación fallida no devolvió None.")

    # --- PRUEBA 5: LÓGICA DE LUDOTECA (Cálculo de Costo) ---
    def test_5_ludoteca_calculo_costo(self):
        """Prueba el cálculo de duración y costo al finalizar la sesión forzando el tiempo."""
        juego = JuegoMesa.crear("Juego Ludoteca", "F", 1, 50.00, 10.00) # $10/hora
        
        # 1. Iniciar sesión (C)
        sesion = LudotecaSesion.iniciar_sesion(juego.id, TEST_VENDEDOR_ID)
        self.assertIsNotNone(sesion)
        
        # 2. ⚠️ FORZAR EL TIEMPO DE INICIO PARA SIMULAR 1.5 HORAS DE DURACIÓN
        
        # Obtener el momento actual (hora de finalización simulada)
        hora_fin_simulada = datetime.now()
        
        # Definir la duración deseada para la prueba (ej. 1.5 horas)
        duracion_simulada = timedelta(hours=1, minutes=30) 
        
        # Calcular el tiempo de inicio (simulado) restando la duración al tiempo actual
        hora_inicio_simulada = hora_fin_simulada - duracion_simulada
        
        # 3. Actualizar la instancia de Python con el tiempo de inicio manipulado
        # Esto asegura que el cálculo en el paso 4 siempre dé 1.5 horas.
        sesion.hora_inicio = hora_inicio_simulada 
        
        # Nota: Ya no necesitamos time.sleep(4)
        
        # 4. Finalizar sesión (U)
        sesion.finalizar_sesion()
        
        # 5. VERIFICACIONES FINALES
        
        # El cálculo de duración debe ser exactamente 1.5 horas
        self.assertEqual(sesion.duracion_horas, 1.50, "La duración calculada no es 1.5 horas exactas.") 
        
        # El precio debe ser 1.5 horas * $10/hr = $15.00
        self.assertEqual(sesion.precio_total, 15.00, "El precio total no se calculó correctamente.")
        self.assertTrue(sesion.hora_fin is not None)


# Ejecución de las pruebas
if __name__ == '__main__':
    unittest.main()