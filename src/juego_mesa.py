from db_connection import get_conn


class JuegoMesa:
    """
    Representa un juego de mesa en el catálogo de la tienda.
    """

    def __init__(
        self, id_, titulo, fabricante, stock, precio_venta, precio_ludoteca_hora
    ):
        self.id = id_
        self.titulo = titulo
        self.fabricante = fabricante
        self.stock = stock
        self.precio_venta = precio_venta
        self.precio_ludoteca_hora = precio_ludoteca_hora

    def descripcion(self):
        """Ver el objeto."""
        return f"{self.titulo} por {self.fabricante} | Venta: ${self.precio_venta:.2f} | Ludoteca/hr: ${self.precio_ludoteca_hora:.2f} | Stock: {self.stock}"

    def reducir_stock(self, cantidad):
        """
        Reduce el stock del juego.
        """
        if self.stock < cantidad:
            raise Exception("Inventario insuficiente para la venta.")

        conn = get_conn()
        try:
            cur = conn.cursor()
            nuevo_stock = self.stock - cantidad
            query = "UPDATE juegos_mesa SET stock = %s WHERE id = %s"
            cur.execute(query, (nuevo_stock, self.id))
            conn.commit()
            self.stock = nuevo_stock
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error en la transacción de stock: {e}")
        finally:
            cur.close()
            conn.close()

    def aumentar_stock(self, cantidad):
        """
        Aumenta el stock del juego (en caso de devolucion o agregar mas stok).
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            nuevo_stock = self.stock + cantidad
            query = "UPDATE juegos_mesa SET stock = %s WHERE id = %s"
            cur.execute(query, (nuevo_stock, self.id))
            conn.commit()
            self.stock = nuevo_stock
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al aumentar el stock: {e}")
        finally:
            cur.close()
            conn.close()

    def modificar_datos(
        self,
        nuevo_titulo,
        nuevo_fabricante,
        nuevo_precio_venta,
        nuevo_precio_ludoteca_hora,
    ):
        """
        Permite actualizar todos los datos del juego .
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = """
            UPDATE juegos_mesa 
            SET titulo = %s, fabricante = %s, precio_venta = %s, precio_ludoteca_hora = %s 
            WHERE id = %s
            """
            cur.execute(
                query,
                (
                    nuevo_titulo,
                    nuevo_fabricante,
                    nuevo_precio_venta,
                    nuevo_precio_ludoteca_hora,
                    self.id,
                ),
            )
            conn.commit()

            self.titulo = nuevo_titulo
            self.fabricante = nuevo_fabricante
            self.precio_venta = nuevo_precio_venta
            self.precio_ludoteca_hora = nuevo_precio_ludoteca_hora

            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al modificar los datos del juego: {e}")
        finally:
            cur.close()
            conn.close()

    @classmethod
    def crear(cls, titulo, fabricante, stock, precio_venta, precio_ludoteca_hora):
        """
        Crea un nuevo juego de mesa en la BD.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = """
            INSERT INTO juegos_mesa (titulo, fabricante, stock, precio_venta, precio_ludoteca_hora) 
            VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(
                query, (titulo, fabricante, stock, precio_venta, precio_ludoteca_hora)
            )
            conn.commit()
            juego_id = cur.lastrowid
            return cls(
                juego_id, titulo, fabricante, stock, precio_venta, precio_ludoteca_hora
            )
        finally:
            cur.close()
            conn.close()

    @classmethod
    def listar_todos(cls):
        """
        Retorna una lista de todos los juegos de mesa.
        """
        conn = get_conn()
        juegos_lista = []
        try:
            cur = conn.cursor()
            query = "SELECT id, titulo, fabricante, stock, precio_venta, precio_ludoteca_hora FROM juegos_mesa ORDER BY titulo"
            cur.execute(query)
            rows = cur.fetchall()

            for r in rows:
                juegos_lista.append(
                    cls(r[0], r[1], r[2], r[3], float(r[4]), float(r[5]))
                )
            return juegos_lista
        finally:
            cur.close()
            conn.close()

    @classmethod
    def buscar_por_titulo(cls, titulo):
        """
        Busca un juego por titulo .
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = "SELECT id, titulo, fabricante, stock, precio_venta, precio_ludoteca_hora FROM juegos_mesa WHERE titulo = %s"
            cur.execute(query, (titulo,))
            r = cur.fetchone()
            if r:
                return cls(r[0], r[1], r[2], r[3], float(r[4]), float(r[5]))
            return None
        finally:
            cur.close()
            conn.close()

    @classmethod
    def buscar_por_id(cls, juego_id):
        """
        Busca un juego por su ID.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = "SELECT id, titulo, fabricante, stock, precio_venta, precio_ludoteca_hora FROM juegos_mesa WHERE id = %s"
            cur.execute(query, (juego_id,))
            r = cur.fetchone()
            if r:
                return cls(r[0], r[1], r[2], r[3], float(r[4]), float(r[5]))
            return None
        finally:
            cur.close()
            conn.close()

    @classmethod
    def eliminar(cls, juego_id):
        """
        Elimina un juego de la BD.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = "DELETE FROM juegos_mesa WHERE id = %s"
            cur.execute(query, (juego_id,))
            conn.commit()
            return True
        finally:
            cur.close()
            conn.close()
