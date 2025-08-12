import sqlite3
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import string

db_path = None  # Menyimpan path database global
server_location = ""  # Menyimpan lokasi server

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
    global db_path, server_location
    if not db_path:
        messagebox.showwarning("Peringatan", "Pilih database terlebih dahulu.")
        return

    if not os.path.exists(db_path):
        messagebox.showerror("Error", f"File tidak ditemukan: {db_path}")
        return

    # Ambil lokasi server dari input
    server_location = entry_server.get().strip()
    if not server_location:
        messagebox.showwarning("Peringatan", "Masukkan lokasi server terlebih dahulu.")
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

    # Hapus data lama
    for i in tree_db.get_children():
        tree_db.delete(i)
    for i in tree_missing.get_children():
        tree_missing.delete(i)

    if search_mode.get() == 1:  # Mode Cari Lagu Belum
        # Ambil data dari DB termasuk song_relative_path
        query = "SELECT song_id, song_name, song_relative_path FROM song"
        where_clauses = [f"song_relative_path LIKE '%{cat}%'" for cat in selected_categories]
        query += " WHERE " + " OR ".join(where_clauses)
        query += " ORDER BY song_id"

        cursor.execute(query)
        rows = cursor.fetchall()

        # Masukkan data DB dan siapkan data untuk pengecekan
        db_songs = []
        for row in rows:
            song_id, song_name, relative_path = row
            tree_db.insert("", tk.END, values=(song_id, song_name))
            db_songs.append({
                'id': song_id,
                'name': song_name,
                'relative_path': relative_path.strip() if relative_path else ''
            })

        missing_songs = []
        
        for song in db_songs:
            relative_path = song['relative_path']
            if not relative_path:
                missing_songs.append((song['id'], song['name']))
                continue
                
            # Hapus backslash di awal jika ada
            if relative_path.startswith('\\'):
                relative_path = relative_path[1:]
            
            # Gabungkan dengan path server
            full_path = os.path.join(server_location, relative_path)
            
            if not os.path.exists(full_path):
                missing_songs.append((song['id'], song['name']))

        # Masukkan ke tabel missing
        for song_id, song_name in missing_songs:
            tree_missing.insert("", tk.END, values=(song_id, song_name))
        
        # Update label dengan informasi hasil
        lbl_result.config(text=f"Total: {len(db_songs)} | Missing: {len(missing_songs)} | Found: {len(db_songs) - len(missing_songs)}")

    else:  # Mode Cari Lagu Tidak Terpakai
        # Dapatkan semua path dari database untuk kategori yang dipilih
        query = "SELECT song_relative_path FROM song WHERE "
        where_clauses = []
        for cat in selected_categories:
            # Cari path yang mengandung nama kategori
            where_clauses.append(f"song_relative_path LIKE '%{cat}%'")
        query += " OR ".join(where_clauses)
        
        cursor.execute(query)
        db_paths = set()
        for row in cursor.fetchall():
            if row[0]:  # Jika path tidak NULL
                # Normalisasi path: lowercase dan ganti backslash dengan forward slash
                normalized_path = row[0].strip().lower().replace('\\', '/')
                db_paths.add(normalized_path)
        
        unused_files = []
        
        for kategori in selected_categories:
            search_path = os.path.join(server_location, kategori)
            
            if not os.path.exists(search_path):
                continue
                
            for root_dir, _, files in os.walk(search_path):
                for file in files:
                    full_path = os.path.join(root_dir, file)
                    # Dapatkan path relatif terhadap server location
                    rel_path = os.path.relpath(full_path, server_location).replace('\\', '/').lower()
                    
                    # Cek apakah path ada di database
                    if rel_path not in db_paths:
                        unused_files.append((file, full_path))
        
        # Tampilkan hasil
        for file_name, file_path in unused_files:
            tree_missing.insert("", tk.END, values=(file_name, file_path))
        
        lbl_result.config(text=f"Total File Tidak Terpakai: {len(unused_files)}")

    conn.close()

# ==== GUI ====
root = tk.Tk()
root.title("Database & File Checker")
root.geometry("800x600")
search_mode = tk.IntVar()
search_mode.set(1)

# Frame atas
frame_top = tk.Frame(root)
frame_top.pack(fill="x", pady=5)

# Frame untuk pilih database dan server location
frame_db_selection = tk.Frame(frame_top)
frame_db_selection.pack(fill="x", pady=5)

# Bagian kiri: pilih database
frame_db_left = tk.Frame(frame_db_selection)
frame_db_left.pack(side="left", fill="x", expand=True)

btn_pilih = tk.Button(frame_db_left, text="Pilih Database", command=pilih_file)
btn_pilih.pack(side="left", padx=5)

lbl_file = tk.Label(frame_db_left, text="Belum ada file dipilih", anchor="w")
lbl_file.pack(side="left", padx=5)

# Bagian kanan: input server location
frame_db_right = tk.Frame(frame_db_selection)
frame_db_right.pack(side="right", fill="x")

lbl_server = tk.Label(frame_db_right, text="Lokasi Server (LAN):")
lbl_server.pack(side="left", padx=5)

entry_server = tk.Entry(frame_db_right, width=30)
entry_server.pack(side="left", padx=5)
entry_server.insert(0, "\\\\192.168.1.11")  # Contoh format path server

# Frame untuk opsi pencarian (radio button dan checkbox dalam satu baris)
frame_options = tk.Frame(root)
frame_options.pack(fill="x", padx=5, pady=5)

# Frame radio button di sebelah kiri
frame_radio = tk.LabelFrame(frame_options, text="Mode Pencarian")
frame_radio.pack(side="left", fill="y", padx=5, pady=5)

rb_missing = tk.Radiobutton(
    frame_radio, 
    text="Cari Lagu Belum", 
    variable=search_mode, 
    value=1
)
rb_missing.pack(anchor="w", padx=5, pady=2)

rb_unused = tk.Radiobutton(
    frame_radio, 
    text="Cari Lagu Tidak Terpakai", 
    variable=search_mode, 
    value=2
)
rb_unused.pack(anchor="w", padx=5, pady=2)

# Frame checkbox kategori di sebelah kanan
frame_check = tk.LabelFrame(frame_options, text="Pilih Kategori Folder")
frame_check.pack(side="left", fill="both", expand=True, padx=5, pady=5)

kategori_vars = {}
for idx, kategori in enumerate(kategori_list):
    var = tk.IntVar()
    kategori_vars[kategori] = var
    cb = tk.Checkbutton(frame_check, text=kategori, variable=var)
    cb.grid(row=idx // 8, column=idx % 8, sticky="w", padx=5, pady=2)

# Tombol proses
btn_proses = tk.Button(root, text="Proses", command=proses_data, bg="lightblue")
btn_proses.pack(pady=5)

# Label hasil
lbl_result = tk.Label(root, text="", fg="blue", font=("Arial", 10, "bold"))
lbl_result.pack(pady=2)

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
frame_missing = tk.LabelFrame(frame_tables, text="Output")
frame_missing.pack(side="left", fill="both", expand=True, padx=5, pady=5)

scroll_y_missing = ttk.Scrollbar(frame_missing, orient="vertical")
scroll_y_missing.pack(side="right", fill="y")
scroll_x_missing = ttk.Scrollbar(frame_missing, orient="horizontal")
scroll_x_missing.pack(side="bottom", fill="x")

# Ubah konfigurasi tree_missing
tree_missing = ttk.Treeview(
    frame_missing,
    columns=("col1", "col2"),
    show="headings",
    yscrollcommand=scroll_y_missing.set,
    xscrollcommand=scroll_x_missing.set
)
tree_missing.heading("col1", text="Nama File")
tree_missing.heading("col2", text="Lokasi")
tree_missing.column("col1", width=200, anchor="w")
tree_missing.column("col2", width=400, anchor="w")
tree_missing.pack(fill="both", expand=True)

scroll_y_missing.config(command=tree_missing.yview)
scroll_x_missing.config(command=tree_missing.xview)

root.mainloop()