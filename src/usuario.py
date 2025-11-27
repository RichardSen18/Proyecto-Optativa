from db_connection import get_conn
import hashlib

# --- Función de utilidad para hashing ---

def hash_password(password: str) -> str:
    """
    Calcula el hash SHA-256 de una contraseña.
    """
    if password is None:
        return None
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

class Usuario:
    """
    Los posibles usuarios del sistema (cliente, vendedor o administrador).
    """
    def __init__(self, id_, nombre, role='cliente'):
        self.id = id_
        self.nombre = nombre
        self.role = role

    def descripcion(self):
        """Método para obtener una representación legible del objeto Usuario."""
        return f"Usuario ID {self.id} | Nombre: {self.nombre} | Rol: {self.role}"


    @classmethod
    def crear(cls, nombre, role='cliente', password=None):
        """
        Crea un nuevo registro de usuario.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            pwd_hash = hash_password(password) if password else None
            
            query = "INSERT INTO usuarios (nombre, role, password) VALUES (%s, %s, %s)"
            cur.execute(query, (nombre, role, pwd_hash))
            conn.commit()
            uid = cur.lastrowid
            return cls(uid, nombre, role)
        except Exception as e:
            conn.rollback()
            if 'Duplicate entry' in str(e):
                raise Exception(f"El nombre de usuario '{nombre}' ya existe.")
            raise Exception(f"Error al crear usuario: {e}")
        finally:
            cur.close()
            conn.close()

    @classmethod
    def listar_todos(cls):
        """
        Mostrar todos los usuarios.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, role FROM usuarios ORDER BY nombre")
            rows = cur.fetchall()
            return [cls(r[0], r[1], r[2]) for r in rows]
        finally:
            cur.close()
            conn.close()

    @classmethod
    def buscar_por_nombre(cls, nombre):
        """
        Buscra un usuario por su nombre.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, role FROM usuarios WHERE nombre = %s", (nombre,))
            r = cur.fetchone()
            return cls(r[0], r[1], r[2]) if r else None
        finally:
            cur.close()
            conn.close()
            
    @classmethod
    def buscar_por_id(cls, id_):
        """
        Bsucar un usuario por su ID.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, role FROM usuarios WHERE id = %s", (id_,))
            r = cur.fetchone()
            return cls(r[0], r[1], r[2]) if r else None
        finally:
            cur.close()
            conn.close()
            
    @classmethod
    def autenticar(cls, nombre, password):
        """
        Verificar credenciales de los usuarios
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, role, password FROM usuarios WHERE nombre = %s", (nombre,))
            r = cur.fetchone()
            if not r:
                return None # Usuario no encontrado

            stored_hash = r[3]
            
            if stored_hash is not None and hash_password(password) == stored_hash:
                return cls(r[0], r[1], r[2])
            return None # Contraseña incorrecta o sin hash
        finally:
            cur.close()
            conn.close()

    @classmethod
    def modificar_role(cls, id_, nuevo_role):
        """
        Modificar el rol de un usuario.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = "UPDATE usuarios SET role = %s WHERE id = %s"
            cur.execute(query, (nuevo_role, id_))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al modificar el rol del usuario: {e}")
        finally:
            cur.close()
            conn.close()
            
    @classmethod
    def eliminar(cls, id_):
        """
        Elimina un usuario por su ID.
        """
        conn = get_conn()
        try:
            cur = conn.cursor()
            query = "DELETE FROM usuarios WHERE id = %s"
            cur.execute(query, (id_,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error al eliminar el usuario: {e}")
        finally:
            cur.close()
            conn.close()