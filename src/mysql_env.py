from db_connection import create_connection, close_connection


def crear_tablas(connection):
    querry_usuario = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(255) NOT NULL UNIQUE,
        role VARCHAR(50) NOT NULL DEFAULT 'cliente',
        password VARCHAR(64) NULL, -- Almacena el hash de la contraseña
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """

    querry_juegosmesa = """
    CREATE TABLE IF NOT EXISTS juegos_mesa (
        id INT AUTO_INCREMENT PRIMARY KEY,
        titulo VARCHAR(255) NOT NULL UNIQUE,
        fabricante VARCHAR(255) NULL,
        stock INT NOT NULL DEFAULT 0,
        precio_venta DECIMAL(10, 2) NOT NULL,       
        precio_ludoteca_hora DECIMAL(10, 2) NOT NULL, 
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """

    querry_ventas = """
    CREATE TABLE IF NOT EXISTS ventas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        cliente_id INT NOT NULL,
        juego_id INT NOT NULL,
        cantidad INT NOT NULL,
        precio_total DECIMAL(10, 2) NOT NULL, 
        fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (cliente_id) REFERENCES usuarios(id) 
            ON DELETE RESTRICT, 
        FOREIGN KEY (juego_id) REFERENCES juegos_mesa(id) 
            ON DELETE RESTRICT
    ) ENGINE=InnoDB;
    """

    querry_ludoteca = """
    CREATE TABLE IF NOT EXISTS ludoteca_sesiones (
        id INT AUTO_INCREMENT PRIMARY KEY,
        juego_id INT NOT NULL,
        vendedor_id INT NOT NULL,
        hora_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        hora_fin TIMESTAMP NULL,
        duracion_horas DECIMAL(5, 2) NULL, 
        precio_total DECIMAL(10, 2) NULL, 
        
        FOREIGN KEY (juego_id) REFERENCES juegos_mesa(id) ON DELETE RESTRICT,
        FOREIGN KEY (vendedor_id) REFERENCES usuarios(id) ON DELETE RESTRICT 
    ) ENGINE=InnoDB;
    """

    querry_sesiones = """
    CREATE TABLE IF NOT EXISTS ludoteca_participantes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sesion_id INT NOT NULL,
        usuario_id INT NOT NULL,
        
        FOREIGN KEY (sesion_id) REFERENCES ludoteca_sesiones(id) ON DELETE CASCADE,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT
    ) ENGINE=InnoDB;
    """

    cursor = connection.cursor()
    cursor.execute(querry_usuario)
    cursor.execute(querry_juegosmesa)
    cursor.execute(querry_ventas)
    cursor.execute(querry_ludoteca)
    cursor.execute(querry_sesiones)
    connection.commit()
    print("Tablas creadas exitosamente.")
    cursor.close()

    def insert_usuario(connection, nombre, role, password_hash):
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO usuarios (nombre, role, password)
        VALUES (%s, %s, %s);
        """
        cursor.execute(insert_query, (nombre, role, password_hash))
        connection.commit()
        print(f"Usuario '{nombre}' insertado exitosamente.")
        cursor.close()

    def get_usuario(connection, nombre):
        cursor = connection.cursor()
        select_query = """
        SELECT id, nombre, role, password, created_at
        FROM usuarios
        WHERE nombre = %s;
        """
        cursor.execute(select_query, (nombre,))
        usuario = cursor.fetchone()
        cursor.close()
        return usuario

    def insert_juego_mesa(connection, titulo, fabricante, stock, precio_venta, precio_ludoteca_hora):
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO juegos_mesa (titulo, fabricante, stock, precio_venta, precio_ludoteca_hora)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(
            insert_query,
            (titulo, fabricante, stock, precio_venta, precio_ludoteca_hora),
        )
        connection.commit()
        print(f"Juego de mesa '{titulo}' insertado exitosamente.")
        cursor.close()

    def get_juego_mesa(connection, titulo):
        cursor = connection.cursor()
        select_query = """
        SELECT id, titulo, fabricante, stock, precio, precio_ludoteca_hora, created_at
        FROM juegos_mesa
        WHERE titulo = %s;
        """
        cursor.execute(select_query, (titulo,))
        juego = cursor.fetchone()
        cursor.close()
        return juego

    def insertar_venta(connection, cliente_id, juego_id, cantidad, precio_total):
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO ventas (cliente_id, juego_id, cantidad, precio_total)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(insert_query, (cliente_id, juego_id, cantidad, precio_total))
        connection.commit()
        print(f"Venta registrada exitosamente para el cliente ID '{cliente_id}'.")
        cursor.close()

    def get_ventas(connection):
        cursor = connection.cursor()
        select_query = """
        SELECT id, cliente_id, juego_id, cantidad, precio_total, fecha_venta
        FROM ventas;
        """
        cursor.execute(select_query)
        ventas = cursor.fetchall()
        cursor.close()
        return ventas

    def insertar_ludoteca(
        connection, juego_id, vendedor_id, hora_fin, duracion_horas, precio_total
    ):
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO ludoteca_sesiones (juego_id, vendedor_id, hora_fin, duracion_horas, precio_total)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(
            insert_query,
            (juego_id, vendedor_id, hora_fin, duracion_horas, precio_total),
        )
        connection.commit()
        print(
            f"Sesión de ludoteca registrada exitosamente para el juego ID '{juego_id}'."
        )
        cursor.close()

    def get_ludoteca(connection):
        cursor = connection.cursor()
        select_query = """
        SELECT id, juego_id, vendedor_id, hora_inicio, hora_fin, duracion_horas, precio_total
        FROM ludoteca_sesiones;
        """
        cursor.execute(select_query)
        sesiones = cursor.fetchall()
        cursor.close()
        return sesiones

    def insertar_sesion_ludoteca(connection, sesion_id, usuario_id):
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO ludoteca_participantes (sesion_id, usuario_id)
        VALUES (%s, %s);
        """
        cursor.execute(insert_query, (sesion_id, usuario_id))
        connection.commit()
        print(f"Participante ID '{usuario_id}' agregado a la sesión ID '{sesion_id}'.")
        cursor.close()

    def get_participantes_sesion(connection, sesion_id):
        cursor = connection.cursor()
        select_query = """
        SELECT id, sesion_id, usuario_id
        FROM ludoteca_participantes
        WHERE sesion_id = %s;
        """
        cursor.execute(select_query, (sesion_id,))
        participantes = cursor.fetchall()
        cursor.close()
        return participantes


def main():
    connection = create_connection()
    if connection:
        crear_tablas(connection)
        close_connection(connection)


if __name__ == "__main__":
    main()
