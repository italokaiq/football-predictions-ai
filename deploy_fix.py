#!/usr/bin/env python3
"""
Script simplificado para deploy no Render
"""

import os
from app import app, init_db

if __name__ == "__main__":
    print("🚀 Iniciando sistema simplificado...")
    
    # Inicializa apenas o banco
    init_db()
    
    # Popula com dados de exemplo se necessário
    import sqlite3
    conn = sqlite3.connect('football.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM games')
    game_count = cursor.fetchone()[0]
    
    if game_count == 0:
        print("📊 Populando dados de exemplo...")
        from sample_data import populate_sample_data
        populate_sample_data()
    
    conn.close()
    
    print("✅ Sistema pronto!")
    
    # Inicia servidor
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)