from usuario import Usuario
from juego_mesa import JuegoMesa
from venta import Venta
from ludoteca_sesion import LudotecaSesion
from ludoteca_participante import LudotecaParticipante

class Tienda:
    """
    Clase controladora central que gestiona la lógica de negocio de la tienda:
    Catálogo, Venta de Productos y Servicio de Ludoteca.
    """

    def __init__(self):
        pass

    def registrar_juego(self, titulo, fabricante, stock, precio_venta, precio_ludoteca_hora):
        """Crea un nuevo juego."""
        return JuegoMesa.crear(titulo, fabricante, stock, precio_venta, precio_ludoteca_hora)

    def buscar_juego(self, titulo):
        """Busca un juego por titulo."""
        return JuegoMesa.buscar_por_titulo(titulo)

    def listar_catalogo(self):
        """Lista todos los juegos."""
        return JuegoMesa.listar_todos()

    def modificar_juego_datos(self, juego_id, nuevo_titulo, nuevo_fabricante, nuevo_precio_venta, nuevo_precio_ludoteca_hora):
        """Modifica los datos descriptivos y precios de un juego."""
        juego = JuegoMesa.buscar_por_id(juego_id)
        if juego:
            return juego.modificar_datos(nuevo_titulo, nuevo_fabricante, nuevo_precio_venta, nuevo_precio_ludoteca_hora)
        raise Exception("Juego no encontrado para modificar.")
    
    def realizar_venta(self, cliente_id, titulo_juego, cantidad):
        """
        Registra una venta de un juego.
        """
        juego = self.buscar_juego(titulo_juego)
        if juego is None:
            raise Exception(f"Juego '{titulo_juego}' no encontrado para la venta.")
    
        return Venta.crear(cliente_id, juego.id, cantidad)
    
    def listar_ventas_cliente(self, cliente_id):
        """Lista las ventas realizadas por un cliente especifico."""
        return Venta.listar_por_cliente(cliente_id)
    
    def iniciar_sesion_juego(self, titulo_juego, vendedor_id):
        """
        Registra una nueva sesion de juego en la BD.
        """
        juego = self.buscar_juego(titulo_juego)
        if juego is None:
            raise Exception(f"Juego '{titulo_juego}' no encontrado para la ludoteca.")

        return LudotecaSesion.iniciar_sesion(juego.id, vendedor_id)

    def registrar_participante(self, sesion_id, nombre_usuario):
        """
        Agrega un usuario a una sesion de juego activa.
        """
        usuario = self.buscar_usuario(nombre_usuario)
        if usuario is None:
            raise Exception(f"Usuario '{nombre_usuario}' no encontrado para participar.")
        
        return LudotecaParticipante.registrar_participante(sesion_id, usuario.id)

    def finalizar_sesion_juego(self, sesion_id):
        """
        Finaliza una sesion, calcula la duracion y el costo total.
        """
        sesion = LudotecaSesion.buscar_por_id(sesion_id)
        if sesion is None:
            raise Exception("Sesión de juego no encontrada.")
            
        return sesion.finalizar_sesion()

    def obtener_participantes(self, sesion_id):
        """Obtiene la lista de IDs de usuarios que participaron en una sesion de juego."""
        return LudotecaParticipante.listar_por_sesion(sesion_id)

    
    def registrar_usuario(self, nombre, role, password):
        """CRUD: Crea un nuevo usuario."""
        return Usuario.crear(nombre, role, password)

    def buscar_usuario(self, nombre):
        """CRUD: Busca un usuario por nombre."""
        return Usuario.buscar_por_nombre(nombre)

    def listar_usuarios(self):
        """CRUD: Lista todos los usuarios."""
        return Usuario.listar_todos()
    
    def listar_sesiones(self):
        """Devuelve el historial completo de sesiones."""
        return LudotecaSesion.listar_todas()