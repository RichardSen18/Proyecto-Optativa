from db_connection import get_conn

class LudotecaParticipante:
    """
    Representa un registro de que un Usuario participo en una Sesion de Ludoteca.
    """

    def __init__(self, id_, sesion_id, usuario_id):
        self.id = id_
        self.sesion_id = sesion_id
        self.usuario_id = usuario_id

    def descripcion(self):
        """Método para obtener una representacion legible del registro."""
        return f"Participante ID {self.usuario_id} registrado en Sesion ID {self.sesion_id}"

   
    @classmethod
    def registrar_participante(cls, sesion_id, usuario_id):
        """
        Crea un nuevo registro de participacion.
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
            raise Exception(f"Error al registrar participante en sesion: {e}")
        finally:
            cur.close()
            conn.close()

    @classmethod
    def listar_por_sesion(cls, sesion_id):
        """
        Muestra la lista de IDs de usuarios que participaron en una sesion.
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