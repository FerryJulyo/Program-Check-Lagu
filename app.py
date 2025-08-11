import sqlite3
import tkinter as tk
from tkinter import filedialog
import os

# Fungsi untuk memilih file
def pilih_file():
    root = tk.Tk()
    root.withdraw()  # Sembunyikan window utama
    file_path = filedialog.askopenfilename(
        title="Pilih file database (.db)",
        filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
    )
    return file_path

# Fungsi untuk membaca isi database
def baca_database(db_path):
    if not os.path.exists(db_path):
        print("File tidak ditemukan:", db_path)
        return
    
    # Koneksi ke database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ambil semua nama tabel
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    if not tables:
        print("Tidak ada tabel di database.")
        return

    for table_name in tables:
        print(f"\n=== Tabel: {table_name[0]} ===")
        cursor.execute(f"SELECT * FROM {table_name[0]}")
        rows = cursor.fetchall()

        if rows:
            for row in rows:
                print(row)
        else:
            print("(Tabel kosong)")

    conn.close()

# Main program
if __name__ == "__main__":
    file_db = pilih_file()
    if file_db:
        print(f"File dipilih: {file_db}")
        baca_database(file_db)
    else:
        print("Tidak ada file yang dipilih.")
