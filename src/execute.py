import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from biblioteca import Biblioteca
from usuario import Usuario, hash_password  # si necesitas el hash
from libro import Libro

bib = Biblioteca()
current_user = None  # objeto Usuario autenticado

ADMIN_CODE = "admin"

# --------------------------
# Funciones de la aplicación
# --------------------------

def login_inicial():
    """Solicita credenciales al iniciar la aplicación.
     registrarse si el usuario no tiene cuenta: cliente, bibliotecario o admin.
    """
    global current_user

    # Preguntar si el usuario ya tiene cuenta
    tiene = messagebox.askyesno("Bienvenido", "¿Tienes una cuenta en el sistema?")
    if tiene is None:
        salir()
        return

    if not tiene:
        # Permitir registro público
        try:
            u = registrar_usuario_publico()
            if u:
                # auto-login con el usuario creado
                current_user = u
                lbl_help.config(text=f"Usuario conectado: {current_user.nombre} ({current_user.role})")
                ajustar_menu_por_rol()
                listar_libros()
                return
            else:
                # Si el usuario canceló el registro, volver a preguntar inicio de sesión
                messagebox.showinfo("Info", "Registro cancelado. Se solicitará inicio de sesión.")
        except Exception as e:
            messagebox.showerror("Error", f"Error durante el registro:\n{e}")

    # intentos iniciar sesión (3 intentos)
    for _ in range(3):
        login = simpledialog.askstring("Inicio de sesión", "Nombre de usuario:")
        if login is None:
            salir()
            return
        pwd = simpledialog.askstring("Inicio de sesión", "Contraseña:", show='*')
        if pwd is None:
            salir()
            return
        usuario = Usuario.autenticar(login.strip(), pwd)
        if usuario:
            current_user = usuario
            lbl_help.config(text=f"Usuario conectado: {current_user.nombre} ({current_user.role})")
            ajustar_menu_por_rol()
            listar_libros()
            return
        else:
            retry = messagebox.askretrycancel("Error", "Credenciales incorrectas. ¿Deseas intentar de nuevo?")
            if not retry:
                # dar opción para registrarse si no tiene cuenta
                want_reg = messagebox.askyesno("Registro", "¿Deseas registrarte ahora?")
                if want_reg:
                    try:
                        u = registrar_usuario_publico()
                        if u:
                            current_user = u
                            lbl_help.config(text=f"Usuario conectado: {current_user.nombre} ({current_user.role})")
                            ajustar_menu_por_rol()
                            listar_libros()
                            return
                    except Exception as e:
                        messagebox.showerror("Error", f"Error durante el registro:\n{e}")
                # si no se registra, seguir al siguiente intento (o salir si no quedan intentos)
    messagebox.showerror("Error", "Demasiados intentos fallidos. Saliendo.")
    salir()


def requiere_admin(func):
    """Decorador simple para funciones que requieren rol 'admin'."""
    def wrapper(*args, **kwargs):
        if current_user is None or current_user.role != 'admin':
            messagebox.showerror("Permisos", "Acción restringida: se requiere usuario admin.")
            return
        return func(*args, **kwargs)
    return wrapper


# Nueva función: registro público (sin requerir admin)
def registrar_usuario_publico():
    """Permite registrar un usuario desde la pantalla de inicio (roles: cliente, bibliotecario, admin).
    """
    nombre = simpledialog.askstring("Registrar usuario", "Nombre del usuario:")
    if not nombre:
        return None
    role = simpledialog.askstring("Registrar usuario", "Rol (cliente/bibliotecario/admin):", initialvalue="cliente")
    if role is None:
        return None
    role = role.strip().lower()

    if role == 'admin':
        code = simpledialog.askstring("Código de administrador", "Introduce el código secreto para el rol 'admin':", show='*')
        if code != ADMIN_CODE:
            messagebox.showerror("Código incorrecto", "Código de administrador incorrecto. No se puede crear la cuenta 'admin'.")
            return None

    if role not in ('cliente', 'bibliotecario', 'admin'):
        messagebox.showwarning("Rol inválido", "Rol inválido. Se usará 'cliente'.")
        role = 'cliente'
    pwd = simpledialog.askstring("Registrar usuario", "Contraseña (dejar vacío = sin contraseña):", show='*')
    # Crear usuario en la BD
    u = Usuario.crear(nombre.strip(), role, pwd)
    messagebox.showinfo("OK", f"Usuario registrado: {u.nombre} (id={u.id}, role={u.role})")
    return u


# --- Registro / modificación / eliminación (admin) ---

@requiere_admin
def registrar_usuario():
    nombre = simpledialog.askstring("Registrar usuario", "Nombre del usuario:")
    if not nombre:
        return
    role = simpledialog.askstring("Registrar usuario", "Rol (admin/bibliotecario):", initialvalue="bibliotecario")
    pwd = simpledialog.askstring("Registrar usuario", "Contraseña:", show='*')
    try:
        u = bib.registrar_usuario(nombre.strip()) if role is None and pwd is None else None
        # Si se pasó role/ pwd usamos Usuario.crear directamente
        if u is None:
            u = Usuario.crear(nombre.strip(), role.strip() if role else 'bibliotecario', pwd)
        messagebox.showinfo("OK", f"Usuario registrado: {u.nombre} (id={u.id})")
        listar_usuarios()
    except Exception as e:
        messagebox.showerror("Error", f"Error al registrar usuario:\n{e}")

@requiere_admin
def modificar_usuario():
    nombre = simpledialog.askstring("Modificar usuario", "Nombre del usuario a modificar:")
    if not nombre:
        return
    usr = bib.buscar_usuario(nombre.strip())
    if usr is None:
        messagebox.showwarning("No encontrado", "Usuario no encontrado.")
        return
    nuevo_nombre = simpledialog.askstring("Modificar usuario", "Nuevo nombre:", initialvalue=usr.nombre)
    nuevo_role = simpledialog.askstring("Modificar usuario", "Nuevo rol (admin/bibliotecario):", initialvalue=usr.role)
    nueva_pwd = simpledialog.askstring("Modificar usuario", "Nueva contraseña (vacío = sin cambio):", show='*')
    try:
        conn = __import__('db_connection').get_conn()
        cur = conn.cursor()
        if nueva_pwd:
            from usuario import hash_password
            cur.execute("UPDATE usuarios SET nombre=%s, role=%s, password=%s WHERE id=%s",
                        (nuevo_nombre.strip(), nuevo_role.strip(), hash_password(nueva_pwd), usr.id))
        else:
            cur.execute("UPDATE usuarios SET nombre=%s, role=%s WHERE id=%s",
                        (nuevo_nombre.strip(), nuevo_role.strip(), usr.id))
        conn.commit()
        cur.close()
        conn.close()
        messagebox.showinfo("OK", "Usuario modificado.")
        listar_usuarios()
    except Exception as e:
        messagebox.showerror("Error", f"Error al modificar usuario:\n{e}")

@requiere_admin
def eliminar_usuario():
    nombre = simpledialog.askstring("Eliminar usuario", "Nombre del usuario a eliminar:")
    if not nombre:
        return
    usr = bib.buscar_usuario(nombre.strip())
    if usr is None:
        messagebox.showwarning("No encontrado", "Usuario no encontrado.")
        return
    if messagebox.askyesno("Confirmar", f"¿Eliminar al usuario '{usr.nombre}' (id={usr.id})?"):
        try:
            conn = __import__('db_connection').get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM usuarios WHERE id = %s", (usr.id,))
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("OK", "Usuario eliminado.")
            listar_usuarios()
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar usuario:\n{e}")

@requiere_admin
def registrar_libro():
    titulo = simpledialog.askstring("Registrar libro", "Título del libro:")
    if not titulo:
        return
    autor = simpledialog.askstring("Registrar libro", "Autor del libro:")
    if not autor:
        return
    try:
        l = bib.registrar_libro(titulo.strip(), autor.strip())
        messagebox.showinfo("OK", f"Libro registrado: {l.titulo} (id={l.id})")
        listar_libros()
    except Exception as e:
        messagebox.showerror("Error", f"Error al registrar libro:\n{e}")

@requiere_admin
def modificar_libro():
    titulo = simpledialog.askstring("Modificar libro", "Título del libro a modificar:")
    if not titulo:
        return
    lib = bib.buscar_libro(titulo.strip())
    if lib is None:
        messagebox.showwarning("No encontrado", "Libro no encontrado.")
        return
    nuevo_titulo = simpledialog.askstring("Modificar libro", "Nuevo título:", initialvalue=lib.titulo)
    nuevo_autor = simpledialog.askstring("Modificar libro", "Nuevo autor:", initialvalue=lib.autor)
    try:
        conn = __import__('db_connection').get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE libros SET titulo=%s, autor=%s WHERE id=%s", (nuevo_titulo.strip(), nuevo_autor.strip(), lib.id))
        conn.commit()
        cur.close()
        conn.close()
        messagebox.showinfo("OK", "Libro modificado.")
        listar_libros()
    except Exception as e:
        messagebox.showerror("Error", f"Error al modificar libro:\n{e}")

@requiere_admin
def eliminar_libro():
    titulo = simpledialog.askstring("Eliminar libro", "Título del libro a eliminar:")
    if not titulo:
        return
    lib = bib.buscar_libro(titulo.strip())
    if lib is None:
        messagebox.showwarning("No encontrado", "Libro no encontrado.")
        return
    if messagebox.askyesno("Confirmar", f"¿Eliminar el libro '{lib.titulo}' (id={lib.id})?"):
        try:
            conn = __import__('db_connection').get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM libros WHERE id = %s", (lib.id,))
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("OK", "Libro eliminado.")
            listar_libros()
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar libro:\n{e}")

# --- Listados / Prestamos (bibliotecario y admin) ---

def listar_usuarios():
    try:
        usuarios = bib.listar_usuarios()
        lb_output.delete(0, tk.END)
        if not usuarios:
            lb_output.insert(tk.END, "No hay usuarios registrados.")
            return
        lb_output.insert(tk.END, "Usuarios:")
        for u in usuarios:
            lb_output.insert(tk.END, f"  [{u.id}] {u.nombre} — {getattr(u, 'role', 'bibliotecario')}")
    except Exception as e:
        messagebox.showerror("Error", f"Error al listar usuarios:\n{e}")

def listar_libros():
    try:
        libros = bib.listar_libros()
        lb_output.delete(0, tk.END)
        if not libros:
            lb_output.insert(tk.END, "No hay libros registrados.")
            return
        lb_output.insert(tk.END, "Libros:")
        for l in libros:
            status = "Disponible" if l.disponible else "Prestado"
            lb_output.insert(tk.END, f"  [{l.id}] {l.titulo} — {l.autor} ({status})")
    except Exception as e:
        messagebox.showerror("Error", f"Error al listar libros:\n{e}")

def prestar_libro():
    if current_user is None:
        messagebox.showerror("Permisos", "Debe iniciar sesión.")
        return
    nombre = simpledialog.askstring("Prestar libro", "Nombre del usuario que toma el libro:")
    if not nombre:
        return
    titulo = simpledialog.askstring("Prestar libro", "Título del libro:")
    if not titulo:
        return
    try:
        msg = bib.prestar_libro(titulo.strip(), nombre.strip())
        messagebox.showinfo("Resultado", msg)
        listar_libros()
    except Exception as e:
        messagebox.showerror("Error", f"Error al prestar libro:\n{e}")

def devolver_libro():
    if current_user is None:
        messagebox.showerror("Permisos", "Debe iniciar sesión.")
        return
    nombre = simpledialog.askstring("Devolver libro", "Nombre del usuario que devuelve el libro:")
    if not nombre:
        return
    titulo = simpledialog.askstring("Devolver libro", "Título del libro:")
    if not titulo:
        return
    try:
        msg = bib.devolver_libro(titulo.strip(), nombre.strip())
        messagebox.showinfo("Resultado", msg)
        listar_libros()
    except Exception as e:
        messagebox.showerror("Error", f"Error al devolver libro:\n{e}")

def obtener_libros_prestados():
    if current_user is None:
        messagebox.showerror("Permisos", "Debe iniciar sesión.")
        return
    
    if current_user.role == 'cliente':
        nombre = current_user.nombre
    else:
        nombre = simpledialog.askstring("Libros prestados", "Nombre del usuario:")
        if not nombre:
            return
            
    try:
        if current_user.role == 'cliente':
            usuario = current_user
        else:
            usuario = bib.buscar_usuario(nombre.strip())
        
        if usuario is None:
            messagebox.showwarning("No encontrado", "Usuario no encontrado.")
            return
            
        libros = usuario.obtener_libros_prestados()
        lb_output.delete(0, tk.END)
        
        if current_user.role == 'cliente':
             lb_output.insert(tk.END, f"Tus libros prestados ({usuario.nombre}):")
        else:
             lb_output.insert(tk.END, f"Libros prestados a {usuario.nombre}:")
        
        if not libros:
            lb_output.insert(tk.END, "  (No tiene libros prestados)")
            return
        for l in libros:
            lb_output.insert(tk.END, f"  [{l.id}] {l.titulo} — {l.autor}")
            
    except Exception as e:
        messagebox.showerror("Error", f"Error al obtener libros prestados:\n{e}")

def salir():
    root.destroy()
    sys.exit(0)

def ajustar_menu_por_rol():
    """Habilita/deshabilita opciones del menú según el rol del usuario actual."""
    if current_user is None:
        # deshabilitar todo por seguridad
        acciones_menu.entryconfig("Registrar usuario", state="disabled")
        acciones_menu.entryconfig("Registrar libro", state="disabled")
        # ... deshabilitar o habilitar entradas manualmente
        return

    if current_user.role == 'admin':
        # Admin: habilitar todo
        acciones_menu.entryconfig("Registrar usuario", state="normal")
        acciones_menu.entryconfig("Modificar usuario", state="normal")
        acciones_menu.entryconfig("Eliminar usuario", state="normal")
        acciones_menu.entryconfig("Registrar libro", state="normal")
        acciones_menu.entryconfig("Modificar libro", state="normal")
        acciones_menu.entryconfig("Eliminar libro", state="normal")
        acciones_menu.entryconfig("Prestar libro", state="normal")
        acciones_menu.entryconfig("Devolver libro", state="normal")
        acciones_menu.entryconfig("Mostrar usuarios", state="normal")
        acciones_menu.entryconfig("Mostrar libros", state="normal")
        acciones_menu.entryconfig("Obtener libros prestados (usuario)", state="normal")
    else:
        # Bibliotecario o cliente: permisos limitados
        acciones_menu.entryconfig("Registrar usuario", state="disabled")
        acciones_menu.entryconfig("Modificar usuario", state="disabled")
        acciones_menu.entryconfig("Eliminar usuario", state="disabled")
        acciones_menu.entryconfig("Registrar libro", state="disabled")
        acciones_menu.entryconfig("Modificar libro", state="disabled")
        acciones_menu.entryconfig("Eliminar libro", state="disabled")
        # bibliotecario puede prestar/devolver; cliente solo listar y ver sus prestamos
        if current_user.role == 'bibliotecario':
            acciones_menu.entryconfig("Prestar libro", state="normal")
            acciones_menu.entryconfig("Devolver libro", state="normal")
            acciones_menu.entryconfig("Mostrar usuarios", state="normal")
            acciones_menu.entryconfig("Mostrar libros", state="normal")
            acciones_menu.entryconfig("Obtener libros prestados (usuario)", state="normal")
        else:  # cliente
            acciones_menu.entryconfig("Prestar libro", state="disabled")
            acciones_menu.entryconfig("Devolver libro", state="disabled")
            acciones_menu.entryconfig("Mostrar usuarios", state="disabled")
            acciones_menu.entryconfig("Mostrar libros", state="normal")
            acciones_menu.entryconfig("Obtener libros prestados (usuario)", state="normal")
root = tk.Tk()
root.title("Biblioteca - Interfaz gráfica")
root.geometry("800x480")
root.minsize(700, 420)

# Menú principal
menubar = tk.Menu(root)

# Menú "Acciones" con las opciones
acciones_menu = tk.Menu(menubar, tearoff=0)
acciones_menu.add_command(label="Registrar usuario", command=registrar_usuario)
acciones_menu.add_command(label="Modificar usuario", command=modificar_usuario)
acciones_menu.add_command(label="Eliminar usuario", command=eliminar_usuario)
acciones_menu.add_separator()
acciones_menu.add_command(label="Registrar libro", command=registrar_libro)
acciones_menu.add_command(label="Modificar libro", command=modificar_libro)
acciones_menu.add_command(label="Eliminar libro", command=eliminar_libro)
acciones_menu.add_separator()
acciones_menu.add_command(label="Mostrar usuarios", command=listar_usuarios)
acciones_menu.add_command(label="Mostrar libros", command=listar_libros)
acciones_menu.add_separator()
acciones_menu.add_command(label="Prestar libro", command=prestar_libro)
acciones_menu.add_command(label="Devolver libro", command=devolver_libro)
acciones_menu.add_separator()
acciones_menu.add_command(label="Obtener libros prestados (usuario)", command=obtener_libros_prestados)
menubar.add_cascade(label="Acciones", menu=acciones_menu)

# Menú "Archivo" con Salir
archivo_menu = tk.Menu(menubar, tearoff=0)
archivo_menu.add_command(label="Salir", command=salir)
menubar.add_cascade(label="Archivo", menu=archivo_menu)

root.config(menu=menubar)

# Frame principal para salida / resultados
frame_output = ttk.Frame(root, padding=(12, 12))
frame_output.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

lbl_output = ttk.Label(frame_output, text="Salida", font=("Segoe UI", 12, "bold"))
lbl_output.pack(anchor="w")

# Listbox con scrollbar para mostrar resultados
frame_list = ttk.Frame(frame_output)
frame_list.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

sb = ttk.Scrollbar(frame_list, orient=tk.VERTICAL)
lb_output = tk.Listbox(frame_list, yscrollcommand=sb.set, font=("Consolas", 10))
sb.config(command=lb_output.yview)
sb.pack(side=tk.RIGHT, fill=tk.Y)
lb_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Mensaje de ayuda inferior
lbl_help = ttk.Label(frame_output, text="Iniciando...", font=("Segoe UI", 9))
lbl_help.pack(anchor="w", pady=(8, 0))

# Al iniciar, pedir login
root.after(100, login_inicial)

root.mainloop()