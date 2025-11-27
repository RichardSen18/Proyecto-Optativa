from db_connection import get_conn
from datetime import datetime, timedelta
from juego_mesa import JuegoMesa


class LudotecaSesion:
    """
    Gestiona el encabezado de una sesión de juego en la ludoteca.
    Su lógica principal es calcular el costo al finalizar.
    """

    def __init__(
        self,
        id_,
        juego_id,
        vendedor_id,
        hora_inicio,
        hora_fin,
        duracion_horas,
        precio_total,
    ):
        self.id = id_
        self.juego_id = juego_id
        self.vendedor_id = vendedor_id
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.duracion_horas = duracion_horas
        self.precio_total = precio_total

    def descripcion(self):
        """
        Metodo para obtener una representacion legible del objeto.
        """
        estado = "Activa" if not self.hora_fin else "Finalizada"
        return f"Sesión ID {self.id} | Juego ID {self.juego_id} | Inicio: {self.hora_inicio} | Estado: {estado}"

    @classmethod
    def iniciar_sesion(cls, juego_id, vendedor_id):
        """
        Registra el inicio de una nueva sesion de juego.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = """
            INSERT INTO ludoteca_sesiones (juego_id, vendedor_id) 
            VALUES (%s, %s)
            """
            cur.execute(query, (juego_id, vendedor_id))
            conn.commit()
            sesion_id = cur.lastrowid

            # Obtener la hora de inicio de la BD para la instancia
            cur.execute(
                "SELECT hora_inicio FROM ludoteca_sesiones WHERE id = %s", (sesion_id,)
            )
            hora_inicio = cur.fetchone()[0]

            return cls(sesion_id, juego_id, vendedor_id, hora_inicio, None, None, None)
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al iniciar la sesión de ludoteca: {e}")
        finally:
            cur.close()
            conn.close()

    @classmethod
    def buscar_por_id(cls, sesion_id):
        """
        Busca una sesión por su ID.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = "SELECT id, juego_id, vendedor_id, hora_inicio, hora_fin, duracion_horas, precio_total FROM ludoteca_sesiones WHERE id = %s"
            cur.execute(query, (sesion_id,))
            r = cur.fetchone()
            if r:
                return cls(r[0], r[1], r[2], r[3], r[4], r[5], r[6])
            return None
        finally:
            cur.close()
            conn.close()


    def finalizar_sesion(self):
        """
        Registra la hora de fin calcula el costo total y actualiza la BD.
        """
        if self.hora_fin:
            raise Exception("La sesión ya ha sido finalizada.")

        conn = get_conn()

        # Obtengo el precio por hora del juego
        juego = JuegoMesa.buscar_por_id(self.juego_id)
        if juego is None:
            raise Exception("Juego de la sesión no encontrado en el catálogo.")

        precio_por_hora = juego.precio_ludoteca_hora

        try:
            # Obtener  la hora actual (simulando NOW())
            hora_fin_bd = datetime.now()
            duracion: timedelta = hora_fin_bd - self.hora_inicio

            # Convertir a horas y redondear
            duracion_horas = round(duracion.total_seconds() / 3600, 2)
            precio_total = round(duracion_horas * precio_por_hora, 2)

            cur = conn.cursor()
            query = """
            UPDATE ludoteca_sesiones 
            SET hora_fin = %s, duracion_horas = %s, precio_total = %s 
            WHERE id = %s
            """
            cur.execute(query, (hora_fin_bd, duracion_horas, precio_total, self.id))
            conn.commit()

            self.hora_fin = hora_fin_bd
            self.duracion_horas = duracion_horas
            self.precio_total = precio_total
            return True

        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al finalizar la sesión: {e}")
        finally:
            cur.close()
            conn.close()

    @classmethod
    def eliminar(cls, sesion_id):
        """
        Elimina un registro de sesion.
        Nota: La BD debe manejar la eliminación de participantes relacionados (CASCADE).
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = "DELETE FROM ludoteca_sesiones WHERE id = %s"
            cur.execute(query, (sesion_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al eliminar la sesión: {e}")
        finally:
            cur.close()
            conn.close()
