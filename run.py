#!/usr/bin/env python3
"""
Script principal para executar o sistema de previsões de futebol
"""

import os
import sys
import threading
import time
from app import app, init_db
from data_collector import DataCollector
from ml_predictor import FootballPredictor

def setup_system():
    """Configuração inicial do sistema"""
    print("🚀 Iniciando sistema de previsões de futebol...")
    
    # Inicializa banco de dados
    print("📊 Inicializando banco de dados...")
    init_db()
    
    # Verifica se há dados
    import sqlite3
    conn = sqlite3.connect('football.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM games')
    game_count = cursor.fetchone()[0]
    conn.close()
    
    if game_count == 0:
        print("📥 Coletando dados iniciais...")
        collector = DataCollector()
        collector.collect_matches_by_leagues(days_back=30)
        collector.update_team_stats()
        
        print("🤖 Treinando modelos ML...")
        predictor = FootballPredictor()
        predictor.train_models()
        
        print("🧠 Treinando rede neural...")
        from neural_predictor import NeuralPredictor
        neural = NeuralPredictor()
        neural.train_models()
    
    print("✅ Sistema configurado com sucesso!")

def run_data_collector():
    """Executa o coletor de dados em thread separada"""
    from data_collector import run_scheduler
    run_scheduler()

if __name__ == "__main__":
    # Configuração inicial
    setup_system()
    
    # Inicia coletor de dados em background
    collector_thread = threading.Thread(target=run_data_collector, daemon=True)
    collector_thread.start()
    
    print("🌐 Iniciando servidor Flask...")
    print("📡 API disponível em: http://localhost:5000")
    print("📋 Endpoints:")
    print("   - GET /games - Jogos do dia")
    print("   - GET /stats/<team> - Estatísticas")
    print("   - GET /predictions - Previsões estatísticas")
    print("   - GET /predictions/neural - Previsões IA (Ensemble)")
    print("   - GET /analyze/<home>/<away> - Análise estatística")
    print("   - GET /analyze/neural/<home>/<away> - Análise IA")
    print("   - GET /best-combo - Melhor combinação")
    
    # Inicia servidor Flask
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Servidor Flask iniciado na porta {port}")
    app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)