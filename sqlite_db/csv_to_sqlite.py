import pandas as pd
import sqlite3

# 1. Cargar el archivo CSV
df = pd.read_csv('bk_excel_db/bk_ubicaciones.csv')  # Cambia la ruta al archivo real

# 2. Conectar (o crear) la base de datos SQLite
conn = sqlite3.connect('./supplier.db')  # Crea el archivo .db si no existe

# 3. Migrar el DataFrame a una tabla SQLite
df.to_sql('ubicaiones', conn, if_exists='replace', index=False)

# 4. Cerrar la conexión
conn.close()