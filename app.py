import sqlite3
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import string

db_path = None  # Menyimpan path database global

# Daftar kategori untuk checkbox
kategori_list = [
    "Indonesia", "Indonesia1", "English", "English1",
    "Mandarin", "Jepang", "Jepang2", "Jepang3",
    "Filipina", "India", "Korea", "Korea2",
    "Thailand", "Remix", "DVD", "DVD2"
]

# Pilih file database
def pilih_file():
    global db_path
    file_path = filedialog.askopenfilename(
        title="Pilih file database (.db)",
        filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
    )
    if file_path:
        db_path = file_path
        lbl_file.config(text=f"File dipilih: {file_path}")
    else:
        messagebox.showwarning("Peringatan", "Tidak ada file yang dipilih.")

# Proses data
def proses_data():
    global db_path
    if not db_path:
        messagebox.showwarning("Peringatan", "Pilih database terlebih dahulu.")
        return

    if not os.path.exists(db_path):
        messagebox.showerror("Error", f"File tidak ditemukan: {db_path}")
        return

    # Ambil pilihan kategori
    selected_categories = [cat for cat, var in kategori_vars.items() if var.get() == 1]
    if not selected_categories:
        messagebox.showwarning("Peringatan", "Pilih minimal 1 kategori.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Cek apakah tabel song ada
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    if "song" not in tables:
        messagebox.showwarning("Peringatan", "Tabel 'song' tidak ditemukan.")
        conn.close()
        return

    # Ambil data dari DB
    query = "SELECT song_id, song_name FROM song"
    if selected_categories:
        where_clauses = [f"song_relative_path LIKE '%{cat}%'" for cat in selected_categories]
        query += " WHERE " + " OR ".join(where_clauses)
    query += " ORDER BY song_id"

    cursor.execute(query)
    rows = cursor.fetchall()

    # Hapus data lama
    for i in tree_db.get_children():
        tree_db.delete(i)
    for i in tree_missing.get_children():
        tree_missing.delete(i)

    # Masukkan data DB
    db_song_names = []
    for row in rows:
        tree_db.insert("", tk.END, values=row)
        db_song_names.append(str(row[1]).strip())

    conn.close()

    # Cari file di seluruh drive (kecuali C:)
    found_files = []
    drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\") and d != "C"]

    for drive in drives:
        for kategori in selected_categories:
            kategori_path = os.path.join(drive, kategori)
            if os.path.exists(kategori_path):
                for root, dirs, files in os.walk(kategori_path):
                    for f in files:
                        found_files.append(os.path.splitext(f)[0])  # tanpa ekstensi

    # Cek yang hilang
    missing = [name for name in db_song_names if name not in found_files]

    # Masukkan ke tabel missing
    for name in missing:
        tree_missing.insert("", tk.END, values=(name,))

# ==== GUI ====
root = tk.Tk()
root.title("Database & File Checker")
root.geometry("1200x600")

# Frame atas
frame_top = tk.Frame(root)
frame_top.pack(fill="x", pady=5)

btn_pilih = tk.Button(frame_top, text="Pilih Database", command=pilih_file)
btn_pilih.pack(side="left", padx=5)

lbl_file = tk.Label(frame_top, text="Belum ada file dipilih", anchor="w")
lbl_file.pack(side="left", padx=5)

# Checkbox kategori
frame_check = tk.LabelFrame(root, text="Pilih Kategori Folder")
frame_check.pack(fill="x", padx=5, pady=5)

kategori_vars = {}
for idx, kategori in enumerate(kategori_list):
    var = tk.IntVar()
    kategori_vars[kategori] = var
    cb = tk.Checkbutton(frame_check, text=kategori, variable=var)
    cb.grid(row=idx // 4, column=idx % 4, sticky="w", padx=5, pady=2)

# Tombol proses
btn_proses = tk.Button(root, text="Proses", command=proses_data, bg="lightblue")
btn_proses.pack(pady=5)

# Frame tabel
frame_tables = tk.Frame(root)
frame_tables.pack(fill="both", expand=True)

# Frame kiri: database
frame_db = tk.LabelFrame(frame_tables, text="Data dari Database")
frame_db.pack(side="left", fill="both", expand=True, padx=5, pady=5)

scroll_y_db = ttk.Scrollbar(frame_db, orient="vertical")
scroll_y_db.pack(side="right", fill="y")
scroll_x_db = ttk.Scrollbar(frame_db, orient="horizontal")
scroll_x_db.pack(side="bottom", fill="x")

tree_db = ttk.Treeview(
    frame_db,
    columns=("song_id", "song_name"),
    show="headings",
    yscrollcommand=scroll_y_db.set,
    xscrollcommand=scroll_x_db.set
)
tree_db.heading("song_id", text="song_id")
tree_db.heading("song_name", text="song_name")
tree_db.column("song_id", width=80, anchor="center")
tree_db.column("song_name", width=300, anchor="w")
tree_db.pack(fill="both", expand=True)

scroll_y_db.config(command=tree_db.yview)
scroll_x_db.config(command=tree_db.xview)

# Frame kanan: missing files
frame_missing = tk.LabelFrame(frame_tables, text="Tidak ditemukan di folder")
frame_missing.pack(side="left", fill="both", expand=True, padx=5, pady=5)

scroll_y_missing = ttk.Scrollbar(frame_missing, orient="vertical")
scroll_y_missing.pack(side="right", fill="y")
scroll_x_missing = ttk.Scrollbar(frame_missing, orient="horizontal")
scroll_x_missing.pack(side="bottom", fill="x")

tree_missing = ttk.Treeview(
    frame_missing,
    columns=("song_name",),
    show="headings",
    yscrollcommand=scroll_y_missing.set,
    xscrollcommand=scroll_x_missing.set
)
tree_missing.heading("song_name", text="song_name")
tree_missing.column("song_name", width=300, anchor="w")
tree_missing.pack(fill="both", expand=True)

scroll_y_missing.config(command=tree_missing.yview)
scroll_x_missing.config(command=tree_missing.xview)

root.mainloop()
