# main.pyw

import os
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import tkinter.font as tkfont


def clear_entry():
    entry_path.delete(0, tk.END)


def get_size(path):
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
        return size
    except Exception:
        return None


def set_size_unit(unit):
    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
    return units.get(unit.upper(), 1)


def calculate_size():
    path = entry_path.get().strip('"')
    unit = unit_var.get()
    if not path:
        messagebox.showerror("Error", "Por favor, seleccione un archivo.")
        return
    if unit not in ["B", "KB", "MB", "GB", "TB"]:
        messagebox.showerror(
            "Error", "Unidad no válida. Use una de las siguientes: B, KB, MB, GB, TB."
        )
        return
    size_in_bytes = get_size(path)
    if size_in_bytes is None:
        messagebox.showerror(
            "Error",
            "Archivo no encontrado o no se pudo leer. Verifique la ruta. \n\nImportante: No se puede ver el tamaño de una carpeta, unidad o servidor de red.",
        )
        return
    conversion_factor = set_size_unit(unit)
    size_converted = size_in_bytes / conversion_factor
    result_label.config(
        text=f"Tamaño aproximado del archivo:\n{size_converted:.2f} {unit}"
    )


def browse_file():
    filename = filedialog.askopenfilename()
    if filename:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, filename)


def show_file_content():
    path = entry_path.get().strip('"')
    text_area.delete(1.0, tk.END)
    if not path:
        messagebox.showerror("Error", "Por favor, seleccione un archivo.")
        return
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        text_area.insert(tk.END, content)
    except FileNotFoundError:
        messagebox.showerror(
            "Error",
            "No se encontró un archivo en la ruta especificada. Verifique la ruta.",
        )
    except Exception as e:
        messagebox.showerror("Error", "No se pudo leer el archivo: " + str(e))


def show_folder_tree(path):
    for item in tree.get_children():
        tree.delete(item)

    def insert_items(parent, abspath):
        try:
            for name in os.listdir(abspath):
                fullpath = os.path.join(abspath, name)
                isdir = os.path.isdir(fullpath)
                node = tree.insert(parent, "end", text=name, open=False)
                if isdir:
                    insert_items(node, fullpath)
        except Exception:
            pass

    insert_items("", path)


def show_file_or_folder():
    path = entry_path.get().strip('"')
    text_area.delete(1.0, tk.END)
    if not path:
        messagebox.showerror("Error", "Por favor, seleccione un archivo o carpeta.")
        return
    if os.path.isdir(path):
        tree_frame.grid(row=4, column=0, columnspan=4, sticky="nsew")
        text_area.grid_remove()
        show_folder_tree(path)
    else:
        tree_frame.grid_remove()
        text_area.grid(row=4, column=0, columnspan=4, padx=5, pady=10, sticky="nsew")
        show_file_content()


def get_folder_size(path, progress_callback=None):
    total_size = 0
    file_count = 0
    all_files = []
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                all_files.append(os.path.join(dirpath, f))
        total_files = len(all_files)
        for idx, fp in enumerate(all_files, 1):
            try:
                total_size += os.path.getsize(fp)
                file_count += 1
                if progress_callback and file_count % 100 == 0:
                    percent = (file_count / total_files) * 100 if total_files else 0
                    progress_callback(file_count, percent)
            except Exception:
                continue
        if progress_callback:
            progress_callback(file_count, 100)
        return total_size
    except Exception:
        return None


def get_best_unit(size_in_bytes):
    units = [("TB", 1024**4), ("GB", 1024**3), ("MB", 1024**2), ("KB", 1024), ("B", 1)]
    for unit, factor in units:
        if size_in_bytes >= factor:
            return unit, factor
    return "B", 1


def calculate_size_threaded():
    path = entry_path.get().strip('"')
    unit = unit_var.get()
    if not path:
        messagebox.showerror("Error", "Por favor, seleccione un archivo o carpeta.")
        return

    def update_progress(count, percent):
        progress_var.set(f"Archivos procesados: {count} ({percent:.1f}%)")

    def worker():
        if os.path.isdir(path):
            size_in_bytes = get_folder_size(path, update_progress)
        else:
            size_in_bytes = get_size(path)
            progress_var.set("100%")
        if size_in_bytes is None:
            messagebox.showerror(
                "Error",
                "Archivo o carpeta no encontrado o no se pudo leer. Verifique la ruta.",
            )
            progress_var.set("")
            return
        if unit == "Auto":
            best_unit, factor = get_best_unit(size_in_bytes)
        else:
            best_unit = unit
            factor = set_size_unit(unit)
        size_converted = size_in_bytes / factor
        result_label.config(
            text=f"Tamaño aproximado:\n{size_converted:.2f} {best_unit}"
        )
        progress_var.set("")

    threading.Thread(target=worker, daemon=True).start()


try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

root = tk.Tk()
root.title("Calculador de tamaño de archivo")

tk.Label(root, text="Ruta del archivo:").grid(
    row=0, column=0, padx=5, pady=5, sticky="e"
)
entry_path = tk.Entry(root, width=40)
entry_path.grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="Limpiar", command=clear_entry).grid(
    row=0, column=2, padx=5, pady=5
)
tk.Button(root, text="Examinar...", command=browse_file).grid(
    row=0, column=3, padx=5, pady=5
)


tk.Label(root, text="Unidad de tamaño:").grid(
    row=1, column=0, padx=5, pady=5, sticky="e"
)
unit_var = tk.StringVar(value="Auto")
unit_menu = tk.OptionMenu(root, unit_var, "Auto", "B", "KB", "MB", "GB", "TB")
unit_menu.grid(row=1, column=1, padx=5, pady=5, sticky="w")

tk.Button(root, text="Calcular tamaño", command=calculate_size_threaded).grid(
    row=2, column=1, padx=5, pady=10
)

tree_frame = tk.Frame(root)
tree = ttk.Treeview(tree_frame)
tree.pack(fill="both", expand=True)

tk.Button(root, text="Ver contenido", command=show_file_or_folder).grid(
    row=2, column=2, padx=5, pady=10
)

progress_var = tk.StringVar(value="")

bold_green_font = tkfont.Font(family="Arial", size=10, weight="bold")

progress_label = tk.Label(
    root, textvariable=progress_var, fg="#398D39", font=bold_green_font
)
progress_label.grid(row=3, column=0, columnspan=4, padx=5, pady=(10, 0), sticky="n")
result_label = tk.Label(root, text="", fg="blue")
result_label.grid(row=4, column=0, columnspan=4, padx=5, pady=(0, 10))

text_area = tk.Text(root, height=15, width=60, wrap="word")
text_area.grid(row=5, column=0, columnspan=4, padx=5, pady=10, sticky="nsew")

for i in range(4):
    root.grid_columnconfigure(i, weight=1)
for i in range(5):
    root.grid_rowconfigure(i, weight=1)

text_area.grid(row=5, column=0, columnspan=4, padx=5, pady=10, sticky="nsew")

root.mainloop()
