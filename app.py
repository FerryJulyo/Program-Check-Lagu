import sqlite3
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import threading
from queue import Queue
import re
import shutil
import csv

db_path = None
server_location = ""
kategori_list = [
    "Indonesia", "Indonesia1", "English", "English1",
    "Mandarin", "Jepang", "Jepang2", "Jepang3",
    "Filipina", "India", "Korea", "Korea2",
    "Thailand", "Remix", "DVD", "DVD2"
]

class App:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        self.queue = Queue()
        self.running = False
        
    def setup_ui(self):
        self.root.title("Program Check Lagu Ver. 20250801")
        self.root.geometry("800x650")
        
        # Variabel
        self.search_mode = tk.IntVar(value=1)
        self.kategori_vars = {k: tk.IntVar() for k in kategori_list}
        
        # Frame atas
        frame_top = tk.Frame(self.root)
        frame_top.pack(fill="x", pady=5)
        
        # Pilih database
        frame_db = tk.Frame(frame_top)
        frame_db.pack(side="left", fill="x", expand=True)
        
        btn_pilih = tk.Button(frame_db, text="Pilih Database", command=self.pilih_file)
        btn_pilih.pack(side="left", padx=5)
        
        self.lbl_file = tk.Label(frame_db, text="Belum ada file dipilih", anchor="w")
        self.lbl_file.pack(side="left", padx=5)
        
        # Input server
        frame_server = tk.Frame(frame_top)
        frame_server.pack(side="right", fill="x")
        
        lbl_server = tk.Label(frame_server, text="Lokasi Server:")
        lbl_server.pack(side="left", padx=5)
        
        self.entry_server = tk.Entry(frame_server, width=30)
        self.entry_server.pack(side="left", padx=5)
        self.entry_server.insert(0, "\\\\192.168.1.11")
        
        # Mode pencarian
        frame_options = tk.Frame(self.root)
        frame_options.pack(fill="x", padx=5, pady=5)

        frame_radio = tk.LabelFrame(frame_options, text="Mode Pencarian")
        frame_radio.pack(side="left", fill="y", padx=5, pady=5)

        tk.Radiobutton(frame_radio, text="Lagu Belum", variable=self.search_mode, value=1).pack(anchor="w", padx=5, pady=2)
        tk.Radiobutton(frame_radio, text="Lagu Tidak Terpakai", variable=self.search_mode, value=2).pack(anchor="w", padx=5, pady=2)

        # Kategori
        frame_check = tk.LabelFrame(frame_options, text="Pilih Kategori Folder")
        frame_check.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Hitung jumlah kolom untuk 3 baris
        total_kategori = len(kategori_list)
        cols_per_row = (total_kategori + 2) // 3  # Pembulatan ke atas untuk 3 baris

        for idx, kategori in enumerate(kategori_list):
            cb = tk.Checkbutton(frame_check, text=kategori, variable=self.kategori_vars[kategori])
            cb.grid(row=idx // cols_per_row, column=idx % cols_per_row, sticky="w", padx=5, pady=2)
        
        # Tombol proses
        self.btn_proses = tk.Button(self.root, text="Proses", command=self.start_processing, bg="lightblue")
        self.btn_proses.pack(pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=5)
        
        # Label hasil
        self.lbl_result = tk.Label(self.root, text="", fg="blue", font=("Arial", 10, "bold"))
        self.lbl_result.pack(pady=2)
        
        # Frame tombol download (awalnya disembunyikan)
        self.frame_download = tk.Frame(self.root)
        self.btn_download = tk.Button(self.frame_download, text="Download CSV", command=self.download_csv)
        self.btn_download.pack(side="left", padx=5)
        self.btn_open_folder = tk.Button(self.frame_download, text="Buka Folder Output", command=self.open_output_folder)
        self.btn_open_folder.pack(side="left", padx=5)
        
        # Frame tabel
        frame_tables = tk.Frame(self.root)
        frame_tables.pack(fill="both", expand=True)
        
        # Tabel database
        frame_db = tk.LabelFrame(frame_tables, text="Data dari Database")
        frame_db.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        scroll_y_db = ttk.Scrollbar(frame_db, orient="vertical")
        scroll_y_db.pack(side="right", fill="y")
        scroll_x_db = ttk.Scrollbar(frame_db, orient="horizontal")
        scroll_x_db.pack(side="bottom", fill="x")
        
        self.tree_db = ttk.Treeview(frame_db, columns=("song_id", "song_name"), show="headings",
                                  yscrollcommand=scroll_y_db.set, xscrollcommand=scroll_x_db.set)
        self.tree_db.heading("song_id", text="song_id")
        self.tree_db.heading("song_name", text="song_name")
        self.tree_db.column("song_id", width=80, anchor="center")
        self.tree_db.column("song_name", width=300, anchor="w")
        self.tree_db.pack(fill="both", expand=True)
        
        scroll_y_db.config(command=self.tree_db.yview)
        scroll_x_db.config(command=self.tree_db.xview)
        
        # Tabel hasil
        frame_missing = tk.LabelFrame(frame_tables, text="Output")
        frame_missing.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        scroll_y_missing = ttk.Scrollbar(frame_missing, orient="vertical")
        scroll_y_missing.pack(side="right", fill="y")
        scroll_x_missing = ttk.Scrollbar(frame_missing, orient="horizontal")
        scroll_x_missing.pack(side="bottom", fill="x")
        
        self.tree_missing = ttk.Treeview(frame_missing, columns=("col1", "col2"), show="headings",
                                       yscrollcommand=scroll_y_missing.set, xscrollcommand=scroll_x_missing.set)
        self.tree_missing.heading("col1", text="")
        self.tree_missing.heading("col2", text="")
        self.tree_missing.column("col1", width=80, anchor="w")
        self.tree_missing.column("col2", width=500, anchor="w")
        self.tree_missing.pack(fill="both", expand=True)
        
        scroll_y_missing.config(command=self.tree_missing.yview)
        scroll_x_missing.config(command=self.tree_missing.xview)
        
        # Cek queue secara berkala
        self.root.after(100, self.process_queue)
    
    def normalize_filename(self, filename):
        """Normalize filename untuk perbandingan"""
        # Hapus ekstensi
        name = os.path.splitext(filename)[0]
        # Ambil hanya bagian ID (angka + huruf di awal)
        match = re.match(r'^(\d+[A-Za-z]*)', name)
        if match:
            return match.group(1).upper()
        return name.upper()
    
    def pilih_file(self):
        global db_path
        file_path = filedialog.askopenfilename(
            title="Pilih file database (.db)",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        if file_path:
            db_path = file_path
            self.lbl_file.config(text=f"File dipilih: {file_path}")
    
    def start_processing(self):
        if self.running:
            return
            
        # Validasi input
        if not db_path:
            messagebox.showwarning("Peringatan", "Pilih database terlebih dahulu.")
            return
            
        if not os.path.exists(db_path):
            messagebox.showerror("Error", f"File tidak ditemukan: {db_path}")
            return
            
        server_location = self.entry_server.get().strip()
        if not server_location:
            messagebox.showwarning("Peringatan", "Masukkan lokasi server terlebih dahulu.")
            return
            
        selected_categories = [cat for cat, var in self.kategori_vars.items() if var.get() == 1]
        if not selected_categories:
            messagebox.showwarning("Peringatan", "Pilih minimal 1 kategori.")
            return
            
        # Reset UI
        for i in self.tree_db.get_children():
            self.tree_db.delete(i)
        for i in self.tree_missing.get_children():
            self.tree_missing.delete(i)
            
        self.progress["value"] = 0
        self.btn_proses.config(state="disabled")
        self.frame_download.pack_forget()  # Sembunyikan tombol download
        self.running = True
        
        # Jalankan di thread terpisah
        thread = threading.Thread(
            target=self.proses_data,
            args=(db_path, server_location, selected_categories, self.search_mode.get()),
            daemon=True
        )
        thread.start()
    
    def proses_data(self, db_path, server_location, selected_categories, mode):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            check_path = os.path.join(server_location, "Indonesia")

            # 2️⃣ Cek apakah path bisa diakses
            if not os.path.exists(check_path):
                messagebox.showwarning("Koneksi Gagal", f"Tidak dapat mengakses server")
                return  # Stop proses

            # Cek tabel song
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall()]
            if "song" not in tables:
                self.queue.put(("error", "Tabel 'song' tidak ditemukan."))
                return
                
            if mode == 1:  # Mode Cari Lagu Belum
                query = "SELECT song_id, song_name, song_relative_path FROM song WHERE " + \
                        " OR ".join([f"song_relative_path LIKE '%{cat}%'" for cat in selected_categories]) + \
                        " ORDER BY song_id"
                
                cursor.execute(query)
                rows = cursor.fetchall()
                total = len(rows)
                
                db_songs = []
                for row in rows:
                    song_id, song_name, relative_path = row
                    self.queue.put(("add_db", (song_id, song_name)))
                    db_songs.append({
                        'id': song_id,
                        'name': song_name,
                        'relative_path': relative_path.strip() if relative_path else ''
                    })
                
                missing_songs = []
                processed = 0
                
                for song in db_songs:
                    relative_path = song['relative_path']
                    if not relative_path:
                        missing_songs.append((song['id'], song['name']))
                        continue
                        
                    if relative_path.startswith('\\'):
                        relative_path = relative_path[1:]
                    
                    full_path = os.path.join(server_location, relative_path)
                    
                    if not os.path.exists(full_path):
                        missing_songs.append((song['id'], song['name']))
                    
                    processed += 1
                    self.queue.put(("progress", (processed, total)))
                
                for song_id, song_name in missing_songs:
                    self.queue.put(("add_missing", (song_id, song_name)))
                
                self.queue.put(("result", f"Total: {total} | Missing: {len(missing_songs)} | Found: {total - len(missing_songs)}"))
                
            else:  # Mode Cari Lagu Tidak Terpakai
                # Tampilkan data dari database
                query_select = "SELECT song_id, song_name, song_relative_path FROM song WHERE " + \
                        " OR ".join([f"song_relative_path LIKE '%{cat}%'" for cat in selected_categories]) + \
                        " ORDER BY song_id"
                
                cursor.execute(query_select)
                rows = cursor.fetchall()
                for row in rows:
                    song_id, song_name, _ = row
                    self.queue.put(("add_db", (song_id, song_name)))
                
                # Dapatkan semua song_id dari database untuk kategori yang dipilih
                query_ids = "SELECT song_id FROM song WHERE " + \
                        " OR ".join([f"song_relative_path LIKE '%{cat}%'" for cat in selected_categories])
                
                cursor.execute(query_ids)
                db_song_ids = set()
                for row in cursor.fetchall():
                    if row[0]:
                        # Normalize song_id dari database
                        normalized_id = self.normalize_filename(str(row[0]))
                        db_song_ids.add(normalized_id)
                
                unused_files = []
                total_files = 0
                processed_files = 0
                
                # Hitung total file hanya di folder utama (tanpa subfolder)
                for kategori in selected_categories:
                    search_path = os.path.join(server_location, kategori)
                    if os.path.exists(search_path):
                        # Hanya file di folder utama, bukan subfolder
                        total_files += len([f for f in os.listdir(search_path) 
                                        if os.path.isfile(os.path.join(search_path, f))])
                
                # Kirim progress 0% di awal
                self.queue.put(("progress", (0, total_files)))
                
                for kategori in selected_categories:
                    search_path = os.path.join(server_location, kategori)
                    move_path = os.path.join(search_path, "move")

                    if not os.path.exists(search_path):
                        continue

                    # Buat folder 'move' jika belum ada
                    if not os.path.exists(move_path):
                        os.makedirs(move_path)
                        
                    # Hanya proses file di folder utama, tidak termasuk subfolder
                    for file in os.listdir(search_path):
                        file_path = os.path.join(search_path, file)
                        if not os.path.isfile(file_path):
                            continue

                        # Normalize nama file untuk perbandingan
                        normalized_file = self.normalize_filename(file)

                        # Jika file ID tidak ada di database, maka file tidak terpakai
                        if normalized_file not in db_song_ids:
                            # Pindahkan file ke folder 'move'
                            new_path = os.path.join(move_path, file)
                            try:
                                shutil.move(file_path, new_path)
                                unused_files.append((file, file_path, new_path))  # Simpan path lama dan baru
                            except Exception as e:
                                unused_files.append((file, file_path, f"Gagal memindahkan: {str(e)}"))
                        
                        processed_files += 1
                        # Update progress setiap file
                        if processed_files % 5 == 0:  # Update lebih sering untuk feedback visual
                            self.queue.put(("progress", (processed_files, total_files)))
                
                # Pastikan progress terakhir di-update
                self.queue.put(("progress", (processed_files, total_files)))
                
                # Tampilkan file yang tidak terpakai
                for file_name, old_path, new_path in unused_files:
                    display_text = f"{old_path} -> {new_path}"
                    self.queue.put(("add_missing", (file_name, display_text)))
                
                self.queue.put(("result", f"Total File Tidak Terpakai: {len(unused_files)}")) 

        except Exception as e:
            self.queue.put(("error", str(e)))
        finally:
            conn.close()
            self.queue.put(("done", None))
    
    def process_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                
                if msg_type == "add_db":
                    self.tree_db.insert("", tk.END, values=data)
                elif msg_type == "add_missing":
                    self.tree_missing.insert("", tk.END, values=data)
                    # Tampilkan tombol download jika ada data di tree_missing
                    if not self.frame_download.winfo_ismapped():
                        self.frame_download.pack(pady=5)
                elif msg_type == "progress":
                    processed, total = data
                    if total > 0:
                        self.progress["value"] = (processed / total) * 100
                elif msg_type == "result":
                    self.lbl_result.config(text=data)
                elif msg_type == "error":
                    messagebox.showerror("Error", data)
                elif msg_type == "done":
                    self.btn_proses.config(state="normal")
                    self.running = False
                    self.progress["value"] = 100
                    
        except:
            pass
            
        self.root.after(100, self.process_queue)
    
    def download_csv(self):
        # Minta lokasi penyimpanan file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Simpan Output sebagai CSV"
        )
        
        if not file_path:
            return  # User membatalkan
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Tulis header
                headers = [self.tree_missing.heading(col)['text'] for col in self.tree_missing['columns']]
                writer.writerow(headers)
                
                # Tulis data
                for item in self.tree_missing.get_children():
                    row = self.tree_missing.item(item)['values']
                    writer.writerow(row)
            
            messagebox.showinfo("Sukses", f"File CSV berhasil disimpan di:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan file CSV:\n{str(e)}")
    
    def open_output_folder(self):
        # Buka folder output (folder 'move' di kategori pertama yang dipilih)
        selected_categories = [cat for cat, var in self.kategori_vars.items() if var.get() == 1]
        if not selected_categories:
            return
            
        server_location = self.entry_server.get().strip()
        if not server_location:
            return
            
        first_category = selected_categories[0]
        move_path = os.path.join(server_location, first_category, "move")
        
        if os.path.exists(move_path):
            os.startfile(move_path)
        else:
            messagebox.showinfo("Info", f"Folder output tidak ditemukan:\n{move_path}")

if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap("icon.ico")
    app = App(root)
    root.mainloop()