#!/usr/bin/env python3
"""
Script para testar as funcionalidades das ligas específicas
"""

import requests
import json
from data_collector import DataCollector

def test_leagues():
    """Testa a coleta de dados das ligas específicas"""
    print("🧪 Testando Sistema de Ligas Específicas")
    print("=" * 50)
    
    collector = DataCollector()
    
    # Testa busca de jogos de hoje
    print("\n📅 Buscando jogos de hoje...")
    games = collector.get_today_matches()
    
    if games:
        print(f"✅ Encontrados {len(games)} jogos:")
        for game in games:
            print(f"  🏆 {game['competition']}: {game['homeTeam']} vs {game['awayTeam']}")
    else:
        print("ℹ️  Nenhum jogo encontrado hoje")
    
    # Testa API endpoints
    print("\n🌐 Testando endpoints da API...")
    
    base_url = "http://localhost:5000"
    
    endpoints = [
        ("/games", "Jogos de hoje"),
        ("/predictions", "Previsões estatísticas"),
        ("/predictions/neural", "Previsões IA")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {description}: OK")
                
                if endpoint == "/games":
                    games_count = len(data.get('games', []))
                    leagues = data.get('leagues', [])
                    print(f"   📊 {games_count} jogos, {len(leagues)} ligas")
                    
                elif endpoint == "/predictions":
                    preds = data.get('predictions', [])
                    leagues_covered = data.get('leagues_covered', [])
                    print(f"   📊 {len(preds)} previsões")
                    print(f"   🏆 Ligas: {', '.join(leagues_covered)}")
                    
            else:
                print(f"❌ {description}: Erro {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {description}: Erro de conexão - {e}")
    
    print("\n🎯 Teste concluído!")

if __name__ == "__main__":
    test_leagues()