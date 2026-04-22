import sqlite3

conn = sqlite3.connect('data/database.db')
cursor = conn.cursor()

# Tablo oluşturma SQL'ini göster
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='appointments'")
result = cursor.fetchone()

print("=== APPOINTMENTS TABLE CREATE SQL ===")
print(result[0])

conn.close()