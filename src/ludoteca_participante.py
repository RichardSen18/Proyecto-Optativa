from db_connection import get_conn

class LudotecaParticipante:
    """
    Representa un registro de que un Usuario participó en una Sesión de Ludoteca.
    """

    def __init__(self, id_, sesion_id, usuario_id):
        self.id = id_
        self.sesion_id = sesion_id
        self.usuario_id = usuario_id

    def descripcion(self):
        """Método para obtener una representación legible del registro."""
        return f"Participante ID {self.usuario_id} registrado en Sesión ID {self.sesion_id}"

   
    @classmethod
    def registrar_participante(cls, sesion_id, usuario_id):
        """
        Crea un nuevo registro de participación.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = """
            INSERT INTO ludoteca_participantes (sesion_id, usuario_id) 
            VALUES (%s, %s)
            """
            cur.execute(query, (sesion_id, usuario_id))
            conn.commit()
            participante_id = cur.lastrowid
            
            return cls(participante_id, sesion_id, usuario_id)
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al registrar participante en sesión: {e}")
        finally:
            cur.close()
            conn.close()

    @classmethod
    def listar_por_sesion(cls, sesion_id):
        """
        Muestra la lista de IDs de usuarios que participaron en una sesión.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = "SELECT usuario_id FROM ludoteca_participantes WHERE sesion_id = %s"
            cur.execute(query, (sesion_id,))
            rows = cur.fetchall()
        
            return [r[0] for r in rows] 
        except Exception as e:
            raise Exception(f"Error al listar participantes: {e}")
        finally:
            cur.close()
            conn.close()