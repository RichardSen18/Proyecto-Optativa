import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Asegurar importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tienda import Tienda
from usuario import Usuario

# --- Variables Globales ---
tienda = Tienda()
current_user = None
ADMIN_CODE = "admin"  # Código secreto para registrarse como admin

# Variables de la interfaz (se inicializan más abajo)
root = None
lb_output = None
lbl_help = None
menubar = None
menu_usuarios = None
menu_catalogo = None
menu_acciones = None

# --------------------------
# Funciones de Utilidad para Formularios
# --------------------------


def centrar_ventana(ventana, ancho=400, alto=300):
    """Centra una ventana Toplevel en la pantalla."""
    ventana.update_idletasks()
    x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
    y = (ventana.winfo_screenheight() // 2) - (alto // 2)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


# --------------------------
# Funciones de Sesión y Registro
# --------------------------


def login_inicial():
    """Flujo de inicio."""
    global current_user

    # Intenta asegurar que exista admin
    try:
        if not tienda.buscar_usuario("admin"):
            tienda.registrar_usuario("admin", "administrador", "admin123")
    except:
        pass

    tiene = messagebox.askyesno("Bienvenido", "¿Tienes una cuenta en el sistema?")
    if tiene is None:
        salir()
        return

    if not tiene:
        # Usamos el nuevo formulario unificado
        u = registrar_usuario_publico()
        if u:
            current_user = u
            actualizar_interfaz_login()
            return
        else:
            messagebox.showinfo(
                "Info", "Registro cancelado. Se solicitará inicio de sesión."
            )

    # Loop de intentos de login
    for _ in range(3):
        # Formulario rápido de login (Nombre y Pass en una sola ventana)
        datos_login = popup_login()
        if not datos_login:  # Si cierra la ventana o cancela
            salir()
            return

        usuario = Usuario.autenticar(datos_login["nombre"], datos_login["password"])
        if usuario:
            current_user = usuario
            actualizar_interfaz_login()
            return
        else:
            retry = messagebox.askretrycancel(
                "Error", "Credenciales incorrectas. ¿Deseas intentar de nuevo?"
            )
            if not retry:
                want_reg = messagebox.askyesno("Registro", "¿Deseas registrarte ahora?")
                if want_reg:
                    u = registrar_usuario_publico()
                    if u:
                        current_user = u
                        actualizar_interfaz_login()
                        return

    messagebox.showerror("Error", "Demasiados intentos fallidos. Saliendo.")
    salir()


def popup_login():
    """Muestra un pequeño formulario para login (Usuario y Contraseña juntos)."""
    login_data = {}

    top = tk.Toplevel(root)
    top.title("Iniciar Sesión")
    centrar_ventana(top, 300, 150)
    top.transient(root)
    top.grab_set()  # Bloquea la ventana principal

    tk.Label(top, text="Usuario:").grid(row=0, column=0, padx=10, pady=10)
    e_user = tk.Entry(top)
    e_user.grid(row=0, column=1, padx=10, pady=10)
    e_user.focus()

    tk.Label(top, text="Contraseña:").grid(row=1, column=0, padx=10, pady=10)
    e_pass = tk.Entry(top, show="*")
    e_pass.grid(row=1, column=1, padx=10, pady=10)

    def confirmar():
        user = e_user.get().strip()
        pwd = e_pass.get()
        if user and pwd:
            login_data["nombre"] = user
            login_data["password"] = pwd
            top.destroy()
        else:
            messagebox.showwarning("Datos", "Complete ambos campos.", parent=top)

    tk.Button(top, text="Entrar", command=confirmar).grid(
        row=2, column=0, columnspan=2, pady=10
    )
    top.bind("<Return>", lambda event: confirmar())

    root.wait_window(top)  # Espera a que se cierre
    return login_data if login_data else None


def actualizar_interfaz_login():
    """Actualiza etiquetas y menús tras login exitoso."""
    lbl_help.config(
        text=f"Usuario conectado: {current_user.nombre} ({current_user.role})"
    )
    ajustar_menu_por_rol()
    listar_catalogo()


def registrar_usuario_publico():
    """
    Formulario unificado para registrar usuario.
    """
    resultado = {}

    top = tk.Toplevel(root)
    top.title("Registro de Usuario")
    centrar_ventana(top, 350, 250)
    top.transient(root)
    top.grab_set()

    # Campos
    tk.Label(top, text="Nombre Usuario:").grid(
        row=0, column=0, padx=10, pady=5, sticky="e"
    )
    e_nombre = tk.Entry(top)
    e_nombre.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(top, text="Contraseña:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
    e_pass = tk.Entry(top, show="*")
    e_pass.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(top, text="Rol:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
    combo_rol = ttk.Combobox(
        top, values=["cliente", "vendedor", "administrador"], state="readonly"
    )
    combo_rol.current(0)  # Default cliente
    combo_rol.grid(row=2, column=1, padx=10, pady=5)

    tk.Label(top, text="Cód. Admin (si aplica):").grid(
        row=3, column=0, padx=10, pady=5, sticky="e"
    )
    e_code = tk.Entry(top, show="*")  # Opcional
    e_code.grid(row=3, column=1, padx=10, pady=5)

    def guardar():
        nombre = e_nombre.get().strip()
        pwd = e_pass.get()
        rol = combo_rol.get()
        code = e_code.get().strip()

        if not nombre or not pwd:
            messagebox.showwarning(
                "Faltan datos", "Nombre y contraseña son obligatorios.", parent=top
            )
            return

        # Validación Admin
        if rol == "administrador" and code != ADMIN_CODE:
            messagebox.showerror(
                "Error", "Código de administrador incorrecto.", parent=top
            )
            return

        try:
            # Intentar crear
            u = tienda.registrar_usuario(nombre, rol, pwd)
            messagebox.showinfo(
                "Éxito", f"Usuario '{u.nombre}' registrado.", parent=top
            )
            resultado["user"] = u
            top.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar:\n{e}", parent=top)

    btn = tk.Button(top, text="Registrar", command=guardar, bg="#dddddd")
    btn.grid(row=4, column=0, columnspan=2, pady=15)

    root.wait_window(top)  # Esperar a que termine el formulario
    return resultado.get("user")


def salir():
    if root:
        root.destroy()
    sys.exit(0)


def requiere_rol(roles_permitidos):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if current_user is None or current_user.role not in roles_permitidos:
                messagebox.showerror(
                    "Permisos", "No tienes permiso para realizar esta acción."
                )
                return
            return func(*args, **kwargs)

        return wrapper

    return decorator


# --------------------------
# Funciones de Gestión: USUARIOS (Admin)
# --------------------------


@requiere_rol(["administrador"])
def registrar_usuario_admin():
    registrar_usuario_publico()


@requiere_rol(["administrador"])
def modificar_usuario():
    """Formulario unificado para modificar usuario."""
    nombre_busqueda = simpledialog.askstring(
        "Buscar", "Nombre del usuario a modificar:"
    )
    if not nombre_busqueda:
        return

    usr = tienda.buscar_usuario(nombre_busqueda.strip())
    if usr is None:
        messagebox.showwarning("No encontrado", "Usuario no encontrado.")
        return

    # Formulario con datos precargados
    top = tk.Toplevel(root)
    top.title(f"Modificar: {usr.nombre}")
    centrar_ventana(top, 350, 250)

    tk.Label(top, text="Nuevo Nombre:").grid(
        row=0, column=0, padx=10, pady=5, sticky="e"
    )
    e_nom = tk.Entry(top)
    e_nom.insert(0, usr.nombre)
    e_nom.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(top, text="Nuevo Rol:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
    c_rol = ttk.Combobox(
        top, values=["cliente", "vendedor", "administrador"], state="readonly"
    )
    c_rol.set(usr.role)
    c_rol.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(top, text="Nueva Contraseña:").grid(
        row=2, column=0, padx=10, pady=5, sticky="e"
    )
    tk.Label(top, text="(Dejar vacío para mantener)").grid(
        row=3, column=0, columnspan=2, text_color="gray", font=("Arial", 8)
    )
    e_pass = tk.Entry(top, show="*")
    e_pass.grid(row=2, column=1, padx=10, pady=5)

    def guardar_cambios():
        nn = e_nom.get().strip()
        nr = c_rol.get()
        np = e_pass.get()

        if not nn:
            messagebox.showwarning(
                "Error", "El nombre no puede estar vacío", parent=top
            )
            return

        try:
            Usuario.actualizar(usr.id, nn, nr, np if np else None)
            messagebox.showinfo("Éxito", "Usuario actualizado.", parent=top)
            top.destroy()
            listar_usuarios()
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al actualizar: {e}", parent=top)

    tk.Button(top, text="Guardar Cambios", command=guardar_cambios).grid(
        row=4, column=0, columnspan=2, pady=15
    )


@requiere_rol(["administrador"])
def eliminar_usuario():
    nombre = simpledialog.askstring(
        "Eliminar usuario", "Nombre del usuario a eliminar:"
    )
    if not nombre:
        return

    usr = tienda.buscar_usuario(nombre.strip())
    if usr is None:
        messagebox.showwarning("No encontrado", "Usuario no encontrado.")
        return

    if messagebox.askyesno(
        "Confirmar", f"¿Eliminar al usuario '{usr.nombre}' (ID: {usr.id})?"
    ):
        try:
            Usuario.eliminar(usr.id)
            messagebox.showinfo("OK", "Usuario eliminado.")
            listar_usuarios()
        except Exception as e:
            # Convertimos el error a texto para buscar el código 1451
            error_str = str(e)
            if "1451" in error_str:
                messagebox.showerror(
                    "No se puede eliminar",
                    f"El usuario '{usr.nombre}' tiene historial de ventas o sesiones.\n\n"
                    "No se puede eliminar porque perderías el registro financiero.",
                )
            else:
                messagebox.showerror("Error", f"Error al eliminar: {e}")


# --------------------------
# Funciones de Gestión: CATÁLOGO (Admin)
# --------------------------


@requiere_rol(["administrador"])
def registrar_juego():
    """
    NUEVO FORMULARIO: Todos los campos en una sola ventana.
    """
    top = tk.Toplevel(root)
    top.title("Registrar Nuevo Juego")
    centrar_ventana(top, 400, 300)
    top.transient(root)  # Mantiene la ventana encima de la principal

    # --- Widgets del Formulario ---
    labels = [
        "Título:",
        "Fabricante:",
        "Stock Inicial:",
        "Precio Venta ($):",
        "Precio Ludoteca ($/h):",
    ]
    entries = {}

    for i, label_text in enumerate(labels):
        tk.Label(top, text=label_text).grid(
            row=i, column=0, padx=15, pady=8, sticky="e"
        )
        entry = tk.Entry(top)
        entry.grid(row=i, column=1, padx=15, pady=8)
        entries[label_text] = entry

    # Función interna para guardar
    def guardar_juego():
        # Obtener valores
        t = entries["Título:"].get().strip()
        f = entries["Fabricante:"].get().strip()
        s_str = entries["Stock Inicial:"].get()
        pv_str = entries["Precio Venta ($):"].get()
        pl_str = entries["Precio Ludoteca ($/h):"].get()

        # Validaciones
        if not t or not f:
            messagebox.showwarning(
                "Faltan datos", "Título y Fabricante son obligatorios.", parent=top
            )
            return

        try:
            s = int(s_str)
            pv = float(pv_str)
            pl = float(pl_str)
        except ValueError:
            messagebox.showerror(
                "Error de formato",
                "Stock debe ser entero.\nPrecios deben ser números.",
                parent=top,
            )
            return

        # Guardar en BD
        try:
            j = tienda.registrar_juego(t, f, s, pv, pl)
            messagebox.showinfo(
                "Éxito", f"Juego '{j.titulo}' registrado correctamente.", parent=top
            )
            top.destroy()  # Cerrar formulario
            listar_catalogo()  # Actualizar lista
        except Exception as e:
            messagebox.showerror(
                "Error BD", f"No se pudo registrar el juego:\n{e}", parent=top
            )

    # Botón Guardar
    btn_save = tk.Button(
        top, text="Guardar Juego", command=guardar_juego, bg="#e1e1e1", width=20
    )
    btn_save.grid(row=len(labels), column=0, columnspan=2, pady=20)


@requiere_rol(["administrador"])
def eliminar_juego():
    titulo = simpledialog.askstring("Eliminar Juego", "Título del juego a eliminar:")
    if not titulo:
        return

    juego = tienda.buscar_juego(titulo.strip())
    if not juego:
        messagebox.showwarning("Error", "Juego no encontrado.")
        return

    if messagebox.askyesno("Confirmar", f"¿Eliminar '{juego.titulo}'?"):
        try:
            from juego_mesa import JuegoMesa

            JuegoMesa.eliminar(juego.id)
            messagebox.showinfo("OK", "Juego eliminado.")
            listar_catalogo()
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")


# --------------------------
# Funciones de Gestión: TRANSACCIONES (Vendedor/Admin/Cliente)
# --------------------------


@requiere_rol(["administrador", "vendedor", "cliente"])
def realizar_venta():
    """Formulario unificado para venta."""
    top = tk.Toplevel(root)
    top.title("Nueva Venta")
    centrar_ventana(top, 350, 200)

    # Campos
    tk.Label(top, text="Título del Juego:").grid(
        row=0, column=0, padx=10, pady=10, sticky="e"
    )
    e_titulo = tk.Entry(top)
    e_titulo.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(top, text="Cantidad:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
    e_cant = tk.Entry(top)
    e_cant.insert(0, "1")
    e_cant.grid(row=1, column=1, padx=10, pady=10)

    e_cliente = None
    # Si es vendedor/admin, mostrar campo para elegir cliente
    if current_user.role in ["administrador", "vendedor"]:
        tk.Label(top, text="Cliente (Usuario):").grid(
            row=2, column=0, padx=10, pady=10, sticky="e"
        )
        e_cliente = tk.Entry(top)
        e_cliente.grid(row=2, column=1, padx=10, pady=10)

    def procesar_venta():
        tit = e_titulo.get().strip()
        try:
            cant = int(e_cant.get())
            if cant <= 0:
                raise ValueError
        except:
            messagebox.showerror("Error", "Cantidad inválida.", parent=top)
            return

        cliente_id = current_user.id
        # Lógica para vendedor seleccionando otro cliente
        if e_cliente:
            cli_nom = e_cliente.get().strip()
            if cli_nom:
                c = tienda.buscar_usuario(cli_nom)
                if c:
                    cliente_id = c.id
                else:
                    messagebox.showerror("Error", "Cliente no encontrado.", parent=top)
                    return

        try:
            venta = tienda.realizar_venta(cliente_id, tit, cant)
            messagebox.showinfo(
                "Venta Exitosa",
                f"Total: ${venta.precio_total}\n{venta.descripcion()}",
                parent=top,
            )
            top.destroy()
            listar_catalogo()
        except Exception as e:
            messagebox.showerror("Error", f"Error en venta: {e}", parent=top)

    tk.Button(top, text="Confirmar Venta", command=procesar_venta, bg="#dddddd").grid(
        row=3, column=0, columnspan=2, pady=15
    )


@requiere_rol(["administrador", "vendedor"])
def iniciar_ludoteca():
    # Para ludoteca es simple (Título y primer participante), se puede dejar o hacer form.
    # Haremos un form simple para coherencia.
    top = tk.Toplevel(root)
    top.title("Ludoteca: Iniciar")
    centrar_ventana(top, 350, 180)

    tk.Label(top, text="Juego:").grid(row=0, column=0, padx=10, pady=10)
    e_juego = tk.Entry(top)
    e_juego.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(top, text="Participante Inicial:").grid(row=1, column=0, padx=10, pady=10)
    e_part = tk.Entry(top)
    e_part.grid(row=1, column=1, padx=10, pady=10)

    def iniciar():
        tit = e_juego.get().strip()
        par = e_part.get().strip()
        if not tit:
            return

        try:
            sesion = tienda.iniciar_sesion_juego(tit, current_user.id)
            msg = f"Sesión iniciada ID: {sesion.id}"

            if par:
                tienda.registrar_participante(sesion.id, par)
                msg += f"\nParticipante {par} agregado."

            messagebox.showinfo("OK", msg, parent=top)
            top.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"{e}", parent=top)

    tk.Button(top, text="Iniciar Sesión", command=iniciar).grid(
        row=2, column=0, columnspan=2, pady=10
    )


@requiere_rol(["administrador", "vendedor"])
def finalizar_ludoteca():
    sid = simpledialog.askstring("Ludoteca", "ID de sesión a finalizar:")
    if not sid:
        return
    try:
        tienda.finalizar_sesion_juego(int(sid))
        from ludoteca_sesion import LudotecaSesion

        s = LudotecaSesion.buscar_por_id(int(sid))
        messagebox.showinfo(
            "Finalizada",
            f"Sesión {s.id} terminada.\nDuración: {s.duracion_horas}h\nTotal a pagar: ${s.precio_total}",
        )
    except Exception as e:
        messagebox.showerror("Error", f"Error finalizar: {e}")


# --------------------------
# Listados
# --------------------------
def listar_catalogo():
    if lb_output:
        lb_output.delete(0, tk.END)
        lb_output.insert(tk.END, "--- CATÁLOGO ---")
        try:
            items = tienda.listar_catalogo()
            for i in items:
                lb_output.insert(
                    tk.END,
                    f"[{i.id}] {i.titulo} | Stock: {i.stock} | ${i.precio_venta}",
                )
        except Exception as e:
            lb_output.insert(tk.END, f"Error: {e}")


def listar_usuarios():
    if lb_output:
        lb_output.delete(0, tk.END)
        lb_output.insert(tk.END, "--- USUARIOS ---")
        try:
            items = tienda.listar_usuarios()
            for i in items:
                lb_output.insert(tk.END, f"[{i.id}] {i.nombre} ({i.role})")
        except Exception as e:
            lb_output.insert(tk.END, f"Error: {e}")


def listar_sesiones_ludoteca():
    """Muestra el historial de sesiones y sus participantes."""
    if lb_output:
        lb_output.delete(0, tk.END)
        lb_output.insert(tk.END, "--- HISTORIAL DE LUDOTECA ---")
        try:
            # 1. Obtenemos todas las sesiones
            sesiones = tienda.listar_sesiones()
            
            if not sesiones:
                lb_output.insert(tk.END, "No hay sesiones registradas.")
                return

            for s in sesiones:
                # 2. Para cada sesión, buscamos sus participantes
                ids_participantes = tienda.obtener_participantes(s.id)
                participantes_str = ", ".join(map(str, ids_participantes)) if ids_participantes else "Ninguno"
                
                # 3. Definimos el estado (Activa o Finalizada)
                estado = "ACTIVA" if s.hora_fin is None else f"Finalizada (${s.precio_total})"
                
                # 4. Formateamos el texto para la lista
                texto = f"[ID: {s.id}] Juego ID: {s.juego_id} | {estado} | Participantes IDs: [{participantes_str}]"
                lb_output.insert(tk.END, texto)
                
        except Exception as e:
            lb_output.insert(tk.END, f"Error al listar sesiones: {e}")

# --------------------------
# Configuración GUI
# --------------------------


def ajustar_menu_por_rol():
    if not current_user:
        return

    state_admin = "normal" if current_user.role == "administrador" else "disabled"
    state_vend = (
        "normal" if current_user.role in ["administrador", "vendedor"] else "disabled"
    )

    if menu_usuarios:
        menu_usuarios.entryconfig("Registrar usuario", state=state_admin)
        menu_usuarios.entryconfig("Modificar usuario", state=state_admin)
        menu_usuarios.entryconfig("Eliminar usuario", state=state_admin)
        menu_usuarios.entryconfig("Listar usuarios", state=state_admin)

    if menu_catalogo:
        menu_catalogo.entryconfig("Registrar juego", state=state_admin)
        menu_catalogo.entryconfig("Eliminar juego", state=state_admin)

    if menu_acciones:
        menu_acciones.entryconfig("Iniciar Sesión Ludoteca", state=state_vend)
        menu_acciones.entryconfig("Finalizar Sesión Ludoteca", state=state_vend)
        # state_vend si prefieres  = restringe
        # state "normal" para todos 
        menu_acciones.entryconfig("Ver Historial Ludoteca", state="normal")
        

root = tk.Tk()
root.title("Gestión Tienda y Ludoteca")
root.geometry("800x500")

menubar = tk.Menu(root)

# Menú Usuarios
menu_usuarios = tk.Menu(menubar, tearoff=0)
menu_usuarios.add_command(label="Registrar usuario", command=registrar_usuario_admin)
menu_usuarios.add_command(label="Modificar usuario", command=modificar_usuario)
menu_usuarios.add_command(label="Eliminar usuario", command=eliminar_usuario)
menu_usuarios.add_separator()
menu_usuarios.add_command(label="Listar usuarios", command=listar_usuarios)
menubar.add_cascade(label="Usuarios (Admin)", menu=menu_usuarios)

# Menú Catálogo
menu_catalogo = tk.Menu(menubar, tearoff=0)
menu_catalogo.add_command(label="Registrar juego", command=registrar_juego)
menu_catalogo.add_command(label="Eliminar juego", command=eliminar_juego)
menu_catalogo.add_separator()
menu_catalogo.add_command(label="Ver Catálogo", command=listar_catalogo)
menubar.add_cascade(label="Catálogo", menu=menu_catalogo)

# Menú Acciones
menu_acciones = tk.Menu(menubar, tearoff=0)
menu_acciones.add_command(label="Comprar Juego", command=realizar_venta)
menu_acciones.add_separator()
menu_acciones.add_command(label="Iniciar Sesión Ludoteca", command=iniciar_ludoteca)
menu_acciones.add_command(label="Finalizar Sesión Ludoteca", command=finalizar_ludoteca)
menu_acciones.add_separator() # Separador visual
menu_acciones.add_command(label="Ver Historial Ludoteca", command=listar_sesiones_ludoteca) # <--- NUEVA LÍNEA
menubar.add_cascade(label="Acciones", menu=menu_acciones)

# Menú Sistema
menu_sys = tk.Menu(menubar, tearoff=0)
menu_sys.add_command(label="Salir", command=salir)
menubar.add_cascade(label="Sistema", menu=menu_sys)

root.config(menu=menubar)

# UI Principal
frame_top = ttk.Frame(root, padding=10)
frame_top.pack(fill=tk.BOTH, expand=True)

lb_output = tk.Listbox(frame_top, font=("Consolas", 10))
lb_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
sb = ttk.Scrollbar(frame_top, orient=tk.VERTICAL, command=lb_output.yview)
sb.pack(side=tk.RIGHT, fill=tk.Y)
lb_output.config(yscrollcommand=sb.set)

lbl_help = ttk.Label(root, text="Iniciando sistema...", relief=tk.SUNKEN, anchor=tk.W)
lbl_help.pack(side=tk.BOTTOM, fill=tk.X)

# Arrancar
root.after(100, login_inicial)
root.mainloop()
