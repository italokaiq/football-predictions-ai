from app import app, init_db
import os

# Inicializa banco na primeira execução
init_db()

# Cria dados se não existirem
import sqlite3
conn = sqlite3.connect('football.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM games')
game_count = cursor.fetchone()[0]
conn.close()

if game_count == 0:
    from sample_data import create_sample_data
    create_sample_data()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)