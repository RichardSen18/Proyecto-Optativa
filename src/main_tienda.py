# main_tienda.py

import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Importación de clases
from tienda import Tienda
from usuario import Usuario, hash_password
from juego_mesa import JuegoMesa

# --- Variables Globales y Controladores ---
tienda = Tienda() 
current_user = None  
ADMIN_CODE = "admin"
root = tk.Tk()
notebook = ttk.Notebook(root) # El contenedor de pestañas
lbl_status = None # Para mostrar el estado y el usuario
output_listbox = None # La Listbox para mostrar resultados
tab_widgets = {} # Diccionario para almacenar widgets de pestañas


# --------------------------
# Lógica de Permisos (Decoradores)
# --------------------------

def requiere_admin(func):
    """Restringe la función al rol 'admin'."""
    def wrapper(*args, **kwargs):
        if current_user is None or current_user.role != 'admin':
            messagebox.showerror("Permisos", "Acción solo disponible para administradores.")
            return
        return func(*args, **kwargs)
    return wrapper

def requiere_vendedor(func):
    """Restringe la función a roles 'admin' o 'vendedor'."""
    def wrapper(*args, **kwargs):
        if current_user is None or current_user.role not in ('admin', 'vendedor'):
            messagebox.showerror("Permisos", "Acción solo disponible para vendedores/admin.")
            return
        return func(*args, **kwargs)
    return wrapper


# --------------------------
# Funciones de LISTADO y UTILIDAD
# --------------------------

def log_output(message, clear=False):
    """Limpia o añade un mensaje a la Listbox de resultados."""
    if output_listbox:
        if clear:
            output_listbox.delete(0, tk.END)
        output_listbox.insert(tk.END, message)
        output_listbox.see(tk.END)

def listar_juegos_catalogo():
    """Muestra el catálogo en la pestaña principal."""
    try:
        juegos = tienda.listar_catalogo()
        log_output("--- Catálogo Actual ---", clear=True)
        if not juegos:
            log_output("No hay juegos registrados.")
            return
        for j in juegos:
            log_output(f"  [{j.id}] {j.titulo} | Stock: {j.stock} | Venta: ${j.precio_venta:.2f} | Ludoteca: ${j.precio_ludoteca_hora:.2f}/hr")
    except Exception as e:
        messagebox.showerror("Error", f"Error al listar juegos:\n{e}")

# --------------------------
# Lógica de Transacciones (Conectada a la GUI)
# --------------------------

@requiere_vendedor
def ejecutar_venta():
    """Ejecuta la venta de un producto."""
    # (Usar variables de entrada de la GUI en lugar de simpledialog, pero simplificamos con simpledialog)
    cliente_nombre = simpledialog.askstring("Venta", "Nombre del Cliente:")
    juego_titulo = simpledialog.askstring("Venta", "Título del Juego:")
    cantidad = simpledialog.askinteger("Venta", "Cantidad:", initialvalue=1)

    if cliente_nombre and juego_titulo and cantidad is not None:
        try:
            cliente = tienda.buscar_usuario(cliente_nombre)
            if cliente is None:
                messagebox.showerror("Error", "Cliente no encontrado.")
                return

            venta = tienda.realizar_venta(cliente.id, juego_titulo, cantidad)
            messagebox.showinfo("Venta Exitosa", f"Venta ID {venta.id} completada. Total: ${venta.precio_total:.2f}")
            listar_juegos_catalogo() # Refrescar stock
        except Exception as e:
            messagebox.showerror("Error de Venta", f"Fallo en la transacción:\n{e}")


@requiere_vendedor
def ejecutar_iniciar_sesion():
    """Inicia una sesión de juego en la ludoteca."""
    juego_titulo = simpledialog.askstring("Ludoteca", "Título del Juego a Jugar:")
    
    if juego_titulo:
        try:
            # Current user (vendedor) inicia la sesión
            sesion = tienda.iniciar_sesion_juego(juego_titulo.strip(), current_user.id)
            
            # Flujo para registrar participantes
            participantes_nombres = simpledialog.askstring("Participantes", "Nombres de los participantes (separados por coma):")
            if participantes_nombres:
                for nombre in [n.strip() for n in participantes_nombres.split(',')]:
                    tienda.registrar_participante(sesion.id, nombre)
            
            messagebox.showinfo("Sesión Iniciada", f"Sesión ID {sesion.id} iniciada para {juego_titulo}.")
            listar_sesiones_activas()

        except Exception as e:
            messagebox.showerror("Error de Ludoteca", f"Fallo al iniciar sesión:\n{e}")

@requiere_vendedor
def ejecutar_finalizar_sesion():
    """Finaliza una sesión y calcula el costo."""
    sesion_id = simpledialog.askinteger("Finalizar Ludoteca", "ID de la Sesión a finalizar:")
    
    if sesion_id is not None:
        try:
            sesion = tienda.finalizar_sesion_juego(sesion_id)
            participantes_ids = tienda.obtener_participantes(sesion_id)

            messagebox.showinfo("Sesión Finalizada", 
                                f"Sesión ID {sesion_id} terminada.\n"
                                f"Duración: {sesion.duracion_horas:.2f} hrs\n"
                                f"Costo Total: ${sesion.precio_total:.2f}")
            listar_sesiones_activas()

        except Exception as e:
            messagebox.showerror("Error de Ludoteca", f"Fallo al finalizar sesión:\n{e}")

def listar_sesiones_activas():
    """Función simulada para listar sesiones (requeriría un método en LudotecaSesion)."""
    log_output("--- Sesiones Activas (Simulado) ---", clear=True)
    log_output("Consulte la BD o implemente un método 'listar_activas' en LudotecaSesion.")

# --------------------------
# Funciones de Login (Mantenidas del original)
# --------------------------

# (Debes incluir aquí la función login_inicial completa de tu código original,
# así como registrar_usuario_publico y la función salir).

def login_inicial():
    """Simulación simple de login para el ejemplo."""
    global current_user
    try:
        # Intenta autenticar un usuario de prueba pre-creado
        admin_auth = Usuario.autenticar("AdminTest", ADMIN_CODE)
        if admin_auth:
            current_user = admin_auth
            messagebox.showinfo("Login Simulado", f"Conectado como {current_user.nombre} ({current_user.role})")
        else:
             # Si no hay admin, crear uno (solo para la demostración)
            Usuario.crear("AdminTest", "admin", ADMIN_CODE)
            current_user = Usuario.autenticar("AdminTest", ADMIN_CODE)
            messagebox.showinfo("Info", "AdminTest creado y conectado. ¡INICIA EL PROYECTO!")

        ajustar_interfaz_por_rol()
        listar_juegos_catalogo()

    except Exception as e:
        messagebox.showerror("Error Fatal", f"Error al intentar autenticar/crear usuario de prueba:\n{e}")
        root.after(100, salir)

def registrar_usuario_publico():
    """Permite registrar un usuario (simplificado)."""
    # (No implementado en esta versión modular)
    messagebox.showinfo("Info", "Use el botón 'Admin' -> 'Registrar Usuario' después de iniciar sesión.")
    return None

def ajustar_interfaz_por_rol():
    """Ajusta el estado de los botones y pestañas según el rol."""
    rol = current_user.role if current_user else ''
    lbl_status.config(text=f"Conectado como: {current_user.nombre} ({rol})")
    
    # Habilitar/Deshabilitar pestañas
    if rol == 'admin':
        notebook.tab(0, state='normal')
        notebook.tab(1, state='normal')
        notebook.tab(2, state='normal')
    elif rol == 'vendedor':
        notebook.tab(0, state='normal')
        notebook.tab(1, state='normal')
        notebook.tab(2, state='normal')
    else: # Cliente o no autenticado
        notebook.tab(0, state='normal') # Catálogo visible
        notebook.tab(1, state='disabled')
        notebook.tab(2, state='disabled')

# --------------------------
# Definición de la GUI (Tkinter)
# --------------------------

def crear_interfaz_modular():
    global lbl_status, output_listbox
    root.title("Tienda de Juegos de Mesa (POO & CRUD)")
    root.geometry("1000x650")
    
    # Frame de Estado Superior
    frame_status = ttk.Frame(root, padding="10 10 10 0")
    frame_status.pack(fill='x')
    lbl_status = ttk.Label(frame_status, text="Iniciando...", font=('Arial', 12, 'bold'))
    lbl_status.pack(side='left', expand=True)
    ttk.Button(frame_status, text="Salir", command=salir).pack(side='right')

    # Contenedor de Pestañas (Notebook)
    notebook.pack(pady=10, padx=10, expand=True, fill="both")
    
    # --- PESTAÑA 1: CATÁLOGO y Admin ---
    tab_catalogo = ttk.Frame(notebook, padding="10")
    notebook.add(tab_catalogo, text='Catálogo / Admin')
    crear_tab_catalogo(tab_catalogo)

    # --- PESTAÑA 2: VENTAS ---
    tab_ventas = ttk.Frame(notebook, padding="10")
    notebook.add(tab_ventas, text='Ventas')
    crear_tab_ventas(tab_ventas)

    # --- PESTAÑA 3: LUDOTECA ---
    tab_ludoteca = ttk.Frame(notebook, padding="10")
    notebook.add(tab_ludoteca, text='Ludoteca')
    crear_tab_ludoteca(tab_ludoteca)
    
    # Listbox de Salida Global (Para mostrar Catálogo, Logs, etc.)
    frame_output_list = ttk.Frame(root, padding="10 0 10 10")
    frame_output_list.pack(fill='both', expand=True)
    output_listbox = tk.Listbox(frame_output_list, height=10, font=('Consolas', 10))
    output_listbox.pack(fill='both', expand=True)
    
    # Iniciar la aplicación
    root.after(100, login_inicial)
    root.mainloop()


# --- DEFINICIÓN DE PESTAÑAS ---

def crear_tab_catalogo(tab):
    """Pestaña para ver el catálogo y registrar/modificar juegos (Admin)."""
    
    # Botones de Acciones CRUD
    ttk.Button(tab, text="Refrescar Catálogo", command=listar_juegos_catalogo).pack(pady=5, fill='x')
    ttk.Separator(tab, orient='horizontal').pack(pady=10, fill='x')
    ttk.Label(tab, text="Gestión de Productos (Admin):", font=('Arial', 10, 'bold')).pack(pady=5, anchor='w')
    
    frame_crud = ttk.Frame(tab)
    frame_crud.pack(pady=5, fill='x')
    
    ttk.Button(frame_crud, text="1. Registrar Nuevo Juego", command=registrar_juego).pack(side='left', padx=5, expand=True)
    ttk.Button(frame_crud, text="2. Modificar Datos", command=modificar_juego).pack(side='left', padx=5, expand=True)
    ttk.Button(frame_crud, text="3. Eliminar Juego", command=eliminar_juego).pack(side='left', padx=5, expand=True)
    
    ttk.Separator(tab, orient='horizontal').pack(pady=10, fill='x')
    
    ttk.Button(tab, text="Registrar Usuario (Admin)", command=lambda: registrar_usuario(root)).pack(pady=5, fill='x')
    
    # Muestra el catálogo al cargar la pestaña
    root.after(200, listar_juegos_catalogo)

def crear_tab_ventas(tab):
    """Pestaña para realizar ventas (Vendedor)."""
    
    ttk.Label(tab, text="Venta de Productos:", font=('Arial', 14, 'bold')).pack(pady=10)
    
    # Botón Principal de Venta
    ttk.Button(tab, text="FINALIZAR VENTA (REDUCIR STOCK)", command=ejecutar_venta, 
               style='Accent.TButton').pack(pady=20, ipadx=20, ipady=10, fill='x')

    ttk.Label(tab, text="Historial (Opcional):", font=('Arial', 10, 'bold')).pack(pady=5, anchor='w')
    ttk.Button(tab, text="Listar Mis Ventas", command=lambda: messagebox.showinfo("Pendiente", "Implementar Listado de Ventas")).pack(pady=5, fill='x')

def crear_tab_ludoteca(tab):
    """Pestaña para el servicio de juego por hora (Vendedor)."""
    
    ttk.Label(tab, text="Servicio de Ludoteca por Hora:", font=('Arial', 14, 'bold')).pack(pady=10)
    
    # Botón para iniciar la sesión
    ttk.Button(tab, text="1. INICIAR SESIÓN DE JUEGO", command=ejecutar_iniciar_sesion, 
               style='Accent.TButton').pack(pady=10, ipady=5, fill='x')
               
    ttk.Button(tab, text="2. FINALIZAR SESIÓN (Calcular Costo)", command=ejecutar_finalizar_sesion, 
               style='Accent.TButton').pack(pady=10, ipady=5, fill='x')

# --------------------------
# Arranque
# --------------------------

if __name__ == "__main__":
    # La aplicación debe usar un theme moderno si es posible
    style = ttk.Style()
    style.theme_use('vista') # o 'clam' si tienes problemas
    style.configure('Accent.TButton', background='darkgreen', foreground='white')
    
    crear_interfaz_modular()