import sqlite3
import tkinter as tk
from tkinter import filedialog
import os

# Pilih file database
def pilih_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Pilih file database (.db)",
        filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
    )
    return file_path

# Tampilkan struktur & isi tabel song
def tampilkan_song(db_path):
    if not os.path.exists(db_path):
        print("File tidak ditemukan:", db_path)
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Cek daftar tabel
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]

    if "song" not in tables:
        print("Tabel 'song' tidak ditemukan di database.")
        conn.close()
        return

    # Tampilkan struktur tabel song
    print("\n=== Struktur tabel 'song' ===")
    cursor.execute("PRAGMA table_info(song);")
    struktur = cursor.fetchall()
    print("CID | Nama Kolom | Tipe Data | NotNull | Default | PrimaryKey")
    print("-" * 70)
    for col in struktur:
        print(" | ".join(str(item) for item in col))

    # Tampilkan isi tabel song
    print("\n=== Data dari tabel 'song' ===")
    cursor.execute("SELECT * FROM song")
    rows = cursor.fetchall()

    # if rows:
    #     col_names = [desc[0] for desc in cursor.description]
    #     print(" | ".join(col_names))
    #     print("-" * 50)
    #     for row in rows:
    #         print(" | ".join(str(item) for item in row))
    # else:
    #     print("(Tabel 'song' kosong)")

    conn.close()

if __name__ == "__main__":
    file_db = pilih_file()
    if file_db:
        print(f"File dipilih: {file_db}")
        tampilkan_song(file_db)
    else:
        print("Tidak ada file yang dipilih.")
