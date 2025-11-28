# usuario.py (Proyecto Tienda - Actualizado)
from db_connection import get_conn
import hashlib

def hash_password(password: str):
    if password is None:
        return None
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

class Usuario:
    def __init__(self, id_, nombre, role, password_hash=None):
        self.id = id_
        self.nombre = nombre
        self.role = role
        self.password_hash = password_hash

    def descripcion(self):
        return f"{self.nombre} ({self.role})"

    @classmethod
    def crear(cls, nombre, role, password):
        conn = get_conn()
        try:
            cur = conn.cursor()
            # Hashear contraseña
            pwd_hash = hash_password(password)
            
            query = "INSERT INTO usuarios (nombre, role, password) VALUES (%s, %s, %s)"
            cur.execute(query, (nombre, role, pwd_hash))
            conn.commit()
            
            usuario_id = cur.lastrowid
            return cls(usuario_id, nombre, role, pwd_hash)
        finally:
            cur.close()
            conn.close()

    @classmethod
    def buscar_por_nombre(cls, nombre):
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = "SELECT id, nombre, role, password FROM usuarios WHERE nombre = %s"
            cur.execute(query, (nombre,))
            r = cur.fetchone()
            if r:
                return cls(r[0], r[1], r[2], r[3])
            return None
        finally:
            cur.close()
            conn.close()

    @classmethod
    def autenticar(cls, nombre, password):
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = "SELECT id, nombre, role, password FROM usuarios WHERE nombre = %s"
            cur.execute(query, (nombre,))
            r = cur.fetchone()
            
            if r:
                stored_hash = r[3]
                if hash_password(password) == stored_hash:
                    return cls(r[0], r[1], r[2], stored_hash)
            return None
        finally:
            cur.close()
            conn.close()

    @classmethod
    def listar_todos(cls):
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, role, password FROM usuarios ORDER BY nombre")
            rows = cur.fetchall()
            return [cls(r[0], r[1], r[2], r[3]) for r in rows]
        finally:
            cur.close()
            conn.close()

    @classmethod
    def actualizar(cls, id_usuario, nuevo_nombre, nuevo_role, nueva_password=None):
        """Actualiza los datos de un usuario."""
        conn = get_conn()
        try:
            cur = conn.cursor()
            if nueva_password:
                pwd_hash = hash_password(nueva_password)
                query = "UPDATE usuarios SET nombre=%s, role=%s, password=%s WHERE id=%s"
                cur.execute(query, (nuevo_nombre, nuevo_role, pwd_hash, id_usuario))
            else:
                query = "UPDATE usuarios SET nombre=%s, role=%s WHERE id=%s"
                cur.execute(query, (nuevo_nombre, nuevo_role, id_usuario))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al actualizar usuario: {e}")
        finally:
            cur.close()
            conn.close()

    @classmethod
    def eliminar(cls, id_usuario):
        """Elimina un usuario por ID."""
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM usuarios WHERE id = %s", (id_usuario,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al eliminar usuario: {e}")
        finally:
            cur.close()
            conn.close()