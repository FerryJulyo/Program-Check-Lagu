import sqlite3
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import threading
from queue import Queue
import re
import shutil
import csv
import string

db_path = None
supported_formats = ['.dat', '.mp4', '.vob', '.mpg']

class App:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        self.queue = Queue()
        self.running = False
        
    def setup_ui(self):
        self.root.title("Program Check Lagu VOD2 Ver. 20250801")
        self.root.geometry("800x650")
        
        # Variabel
        self.search_mode = tk.IntVar(value=1)
        
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
        
        # Mode pencarian
        frame_options = tk.Frame(self.root)
        frame_options.pack(fill="x", padx=5, pady=5)

        frame_radio = tk.LabelFrame(frame_options, text="Mode Pencarian")
        frame_radio.pack(side="left", fill="y", padx=5, pady=5)

        tk.Radiobutton(frame_radio, text="Lagu Belum", variable=self.search_mode, value=1).pack(anchor="w", padx=5, pady=2)
        tk.Radiobutton(frame_radio, text="Lagu Tidak Terpakai", variable=self.search_mode, value=2).pack(anchor="w", padx=5, pady=2)

        # Info format file
        frame_info = tk.LabelFrame(frame_options, text="Info Pencarian")
        frame_info.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # info_text = "Pencarian dilakukan pada:\n"
        # info_text += "• Drive D, E, F, dll (kecuali C)\n"
        # info_text += "• File di direktori root (tidak dalam folder)\n"
        # info_text += "• Format: DAT, MP4, VOB, MPG"
        
        # lbl_info = tk.Label(frame_info, text=info_text, justify="left")
        # lbl_info.pack(anchor="w", padx=5, pady=5)
        
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
    
    def get_available_drives(self):
        """Dapatkan semua drive yang tersedia kecuali C"""
        drives = []
        for letter in string.ascii_uppercase:
            if letter == 'C':  # Skip drive C
                continue
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives
    
    def get_root_files(self, drive_path):
        """Dapatkan file di root drive dengan format yang didukung"""
        root_files = []
        try:
            if os.path.exists(drive_path):
                for item in os.listdir(drive_path):
                    item_path = os.path.join(drive_path, item)
                    # Hanya ambil file (bukan folder) dengan ekstensi yang didukung
                    if os.path.isfile(item_path):
                        _, ext = os.path.splitext(item.lower())
                        if ext in supported_formats:
                            root_files.append(item)
        except PermissionError:
            # Skip drive yang tidak bisa diakses
            pass
        except Exception as e:
            print(f"Error accessing {drive_path}: {e}")
        
        return root_files
    
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
            args=(db_path, self.search_mode.get()),
            daemon=True
        )
        thread.start()
    
    def proses_data(self, db_path, mode):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Cek tabel song
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall()]
            if "song" not in tables:
                self.queue.put(("error", "Tabel 'song' tidak ditemukan."))
                return
            
            # Dapatkan semua drive yang tersedia
            available_drives = self.get_available_drives()
            if not available_drives:
                self.queue.put(("error", "Tidak ada drive yang tersedia untuk dicek."))
                return
                
            if mode == 1:  # Mode Cari Lagu Belum
                # Ambil semua data dari database
                query = "SELECT song_id, song_name, song_relative_path FROM song ORDER BY song_id"
                cursor.execute(query)
                rows = cursor.fetchall()
                
                db_songs = []
                for row in rows:
                    song_id, song_name, relative_path = row
                    self.queue.put(("add_db", (song_id, song_name)))
                    db_songs.append({
                        'id': song_id,
                        'name': song_name,
                        'relative_path': relative_path.strip() if relative_path else ''
                    })
                
                # Kumpulkan semua file dari drive
                all_drive_files = {}
                for drive in available_drives:
                    files = self.get_root_files(drive)
                    for file in files:
                        normalized_name = self.normalize_filename(file)
                        all_drive_files[normalized_name] = os.path.join(drive, file)
                
                missing_songs = []
                total = len(db_songs)
                processed = 0
                
                for song in db_songs:
                    song_id = str(song['id']) if song['id'] else ''
                    normalized_id = self.normalize_filename(song_id)
                    
                    # Cek apakah file ada di drive manapun
                    if normalized_id not in all_drive_files:
                        missing_songs.append((song['id'], song['name']))
                    
                    processed += 1
                    self.queue.put(("progress", (processed, total)))
                
                for song_id, song_name in missing_songs:
                    self.queue.put(("add_missing", (song_id, song_name)))
                
                self.queue.put(("result", f"Total DB: {total} | Missing: {len(missing_songs)} | Found: {total - len(missing_songs)}"))
                
            else:  # Mode Cari Lagu Tidak Terpakai
                # Tampilkan data dari database
                query = "SELECT song_id, song_name FROM song ORDER BY song_id"
                cursor.execute(query)
                rows = cursor.fetchall()
                for row in rows:
                    song_id, song_name = row
                    self.queue.put(("add_db", (song_id, song_name)))
                
                # Dapatkan semua song_id dari database
                cursor.execute("SELECT song_id FROM song")
                db_song_ids = set()
                for row in cursor.fetchall():
                    if row[0]:
                        normalized_id = self.normalize_filename(str(row[0]))
                        db_song_ids.add(normalized_id)
                
                # Hitung total file untuk progress
                total_files = 0
                for drive in available_drives:
                    total_files += len(self.get_root_files(drive))
                
                unused_files = []
                processed_files = 0
                
                self.queue.put(("progress", (0, total_files)))
                
                for drive in available_drives:
                    # Buat folder 'move' di setiap drive
                    move_path = os.path.join(drive, "move")
                    if not os.path.exists(move_path):
                        try:
                            os.makedirs(move_path)
                        except Exception as e:
                            print(f"Tidak bisa membuat folder move di {drive}: {e}")
                            continue
                    
                    files = self.get_root_files(drive)
                    
                    for file in files:
                        file_path = os.path.join(drive, file)
                        normalized_file = self.normalize_filename(file)

                        # Jika file ID tidak ada di database, maka file tidak terpakai
                        if normalized_file not in db_song_ids:
                            new_path = os.path.join(move_path, file)
                            try:
                                shutil.move(file_path, new_path)
                                unused_files.append((file, file_path, new_path))
                            except Exception as e:
                                unused_files.append((file, file_path, f"Gagal memindahkan: {str(e)}"))
                        
                        processed_files += 1
                        if processed_files % 5 == 0:
                            self.queue.put(("progress", (processed_files, total_files)))
                
                # Update progress terakhir
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
            # Gunakan encoding utf-8-sig untuk support karakter khusus dan BOM
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                
                # Tulis header
                headers = [self.tree_missing.heading(col)['text'] for col in self.tree_missing['columns']]
                writer.writerow(headers)
                
                # Tulis data dengan handling karakter khusus
                for item in self.tree_missing.get_children():
                    row = self.tree_missing.item(item)['values']
                    # Bersihkan dan normalisasi setiap nilai
                    cleaned_row = [
                        str(value).encode('utf-8', 'replace').decode('utf-8') 
                        if value else '' 
                        for value in row
                    ]
                    writer.writerow(cleaned_row)
            
            messagebox.showinfo("Sukses", f"File CSV berhasil disimpan di:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal menyimpan file CSV:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    try:
        root.iconbitmap("icon.ico")
    except:
        pass  # Icon tidak ditemukan, lanjutkan tanpa icon
    app = App(root)
    root.mainloop()