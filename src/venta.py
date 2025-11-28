from db_connection import get_conn
from juego_mesa import JuegoMesa


class Venta:
    """
    Representa una transacción de compra de un juego de mesa.
    """

    def __init__(self, id_, cliente_id, juego_id, cantidad, precio_total, fecha_venta):
        self.id = id_
        self.cliente_id = cliente_id
        self.juego_id = juego_id
        self.cantidad = cantidad
        self.precio_total = precio_total
        self.fecha_venta = fecha_venta

    def descripcion(self):
        """Método para obtener una representación legible del objeto Venta."""
        return f"Venta ID {self.id} | Cliente {self.cliente_id} compró {self.cantidad} del Juego {self.juego_id} por ${self.precio_total:.2f}"

    @classmethod
    def crear(cls, cliente_id, juego_id, cantidad):
        """
        Crea un nuevo registro de venta.
        """
        conn = get_conn()

        juego = JuegoMesa.buscar_por_id(juego_id)
        if juego is None:
            raise Exception("Juego no encontrado en el catálogo. Venta cancelada.")

        precio_unitario = juego.precio_venta
        precio_total = cantidad * precio_unitario

        try:
            cur = conn.cursor()
            
            if juego.stock < cantidad:
                raise Exception("Inventario insuficiente para la venta.")
            
            nuevo_stock = juego.stock - cantidad
            cur.execute("UPDATE juegos_mesa SET stock = %s WHERE id = %s", (nuevo_stock, juego_id))
            
            query = """
            INSERT INTO ventas (cliente_id, juego_id, cantidad, precio_total) 
            VALUES (%s, %s, %s, %s)
            """
            cur.execute(query, (cliente_id, juego_id, cantidad, precio_total))
            
            conn.commit()

            venta_id = cur.lastrowid
            return cls(venta_id, cliente_id, juego_id, cantidad, precio_total, "Ahora")

        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al registrar la venta: {e}")

        finally:
            cur.close()
            conn.close()

    @classmethod
    def buscar_por_id(cls, venta_id):
        """
        Busca una venta por su ID.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = "SELECT id, cliente_id, juego_id, cantidad, precio_total, fecha_venta FROM ventas WHERE id = %s"
            cur.execute(query, (venta_id,))
            r = cur.fetchone()
            if r:
                return cls(r[0], r[1], r[2], r[3], float(r[4]), r[5])
            return None
        finally:
            cur.close()
            conn.close()

    @classmethod
    def listar_por_cliente(cls, cliente_id):
        """
        Retorna todas las ventas realizadas por un cliente.
        """
        conn = get_conn()
        ventas_lista = []
        try:
            cur = conn.cursor()
            query = "SELECT id, cliente_id, juego_id, cantidad, precio_total, fecha_venta FROM ventas WHERE cliente_id = %s ORDER BY fecha_venta DESC"
            cur.execute(query, (cliente_id,))
            rows = cur.fetchall()

            for r in rows:
                ventas_lista.append(cls(r[0], r[1], r[2], r[3], float(r[4]), r[5]))

            return ventas_lista
        finally:
            cur.close()
            conn.close()

    @classmethod
    def eliminar(cls, venta_id):
        """
        Elimina un registro de venta y devuelve el stock.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()

            # Obtener los detalles de la venta antes de eliminar
            cur.execute(
                "SELECT juego_id, cantidad FROM ventas WHERE id = %s", (venta_id,)
            )
            r = cur.fetchone()
            if not r:
                return False

            juego_id, cantidad = r[0], r[1]

            # Eliminar la venta
            query = "DELETE FROM ventas WHERE id = %s"
            cur.execute(query, (venta_id,))
            conn.commit()

            # Aumentar el stock (por si se elimina por error)
            juego = JuegoMesa.buscar_por_id(juego_id)
            if juego:
                juego.aumentar_stock(cantidad)

            return True

        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al eliminar la venta: {e}")

        finally:
            cur.close()
            conn.close()
