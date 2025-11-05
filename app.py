from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import requests
import os
from datetime import datetime, date
from dotenv import load_dotenv
from stats_analyzer import StatsAnalyzer
from ensemble_predictor import EnsemblePredictor

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuração da API
API_KEY = os.getenv('FOOTBALL_API_KEY', 'f9c2bbc9a86c4c0b8a843cf67c364a0e')
API_BASE_URL = 'https://api.football-data.org/v4'

def init_db():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect('football.db')
    cursor = conn.cursor()
    
    # Tabela de jogos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY,
            home_team TEXT,
            away_team TEXT,
            date TEXT,
            home_goals INTEGER,
            away_goals INTEGER,
            competition TEXT,
            league_code TEXT
        )
    ''')
    
    # Tabela de estatísticas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_stats (
            id INTEGER PRIMARY KEY,
            team_name TEXT,
            goals_scored REAL,
            goals_conceded REAL,
            wins INTEGER,
            draws INTEGER,
            losses INTEGER,
            last_updated TEXT
        )
    ''')
    
    # Tabela de previsões
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY,
            game_id INTEGER,
            prediction_type TEXT,
            probability REAL,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/games', methods=['GET'])
def get_games():
    """Retorna jogos do dia das ligas específicas"""
    try:
        from data_collector import DataCollector
        collector = DataCollector()
        
        # Busca jogos de hoje das ligas específicas
        games = collector.get_today_matches()
        
        if games:
            return jsonify({
                'games': games,
                'total': len(games),
                'leagues': list(set([game['competition'] for game in games]))
            })
        else:
            return jsonify({
                'games': [],
                'message': 'Nenhum jogo encontrado hoje nas ligas: Premier League, La Liga, Serie A, Brasileirão, Liga Argentina'
            })
            
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar jogos: {str(e)}'}), 500

@app.route('/stats/<team_name>', methods=['GET'])
def get_team_stats(team_name):
    """Retorna estatísticas de um time"""
    conn = sqlite3.connect('football.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM team_stats WHERE team_name = ?
    ''', (team_name,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return jsonify({
            'team': result[1],
            'goals_scored': result[2],
            'goals_conceded': result[3],
            'wins': result[4],
            'draws': result[5],
            'losses': result[6]
        })
    else:
        return jsonify({'error': 'Time não encontrado'}), 404

@app.route('/predictions/neural', methods=['GET'])
def get_neural_predictions():
    """Retorna previsões usando ensemble de modelos IA"""
    ensemble = EnsemblePredictor()
    
    try:
        predictions = ensemble.get_best_predictions()
        return jsonify({
            'predictions': predictions,
            'model_type': 'Ensemble (Stats + Neural + ML)',
            'total_matches': len(predictions)
        })
    except Exception as e:
        return jsonify({'error': f'Erro no ensemble: {str(e)}'}), 500

@app.route('/predictions', methods=['GET'])
def get_predictions():
    """Retorna previsões baseadas nos jogos reais das ligas específicas"""
    try:
        from data_collector import DataCollector
        analyzer = StatsAnalyzer()
        collector = DataCollector()
        
        # Busca jogos de hoje das ligas específicas
        today_games = collector.get_today_matches()
        
        predictions = []
        
        # Se não há jogos hoje, usa jogos de exemplo das ligas
        if not today_games:
            sample_matches = [
                ('Manchester City', 'Liverpool', 'Premier League'),
                ('Real Madrid', 'Barcelona', 'La Liga'),
                ('Juventus', 'Inter Milan', 'Serie A'),
                ('Flamengo', 'Palmeiras', 'Brasileirão'),
                ('Boca Juniors', 'River Plate', 'Liga Argentina')
            ]
            
            for home_team, away_team, league in sample_matches:
                probs = analyzer.calculate_match_probabilities(home_team, away_team)
                
                # Melhor aposta baseada nas probabilidades
                best_bet = 'Over 2.5 gols' if probs['over_2_5_prob'] > 0.6 else 'Under 2.5 gols'
                best_prob = probs['over_2_5_prob'] if probs['over_2_5_prob'] > 0.6 else (1 - probs['over_2_5_prob'])
                
                if probs['home_win_prob'] > best_prob:
                    best_bet = f'Vitória {home_team}'
                    best_prob = probs['home_win_prob']
                elif probs['away_win_prob'] > best_prob:
                    best_bet = f'Vitória {away_team}'
                    best_prob = probs['away_win_prob']
                
                predictions.append({
                    'game': f'{home_team} vs {away_team}',
                    'league': league,
                    'prediction': best_bet,
                    'probability': round(best_prob, 3),
                    'confidence': probs['confidence'],
                    'expected_goals': probs['expected_goals'],
                    'home_win': probs['home_win_prob'],
                    'draw': probs['draw_prob'],
                    'away_win': probs['away_win_prob'],
                    'over_2_5': probs['over_2_5_prob']
                })
        else:
            # Usa jogos reais de hoje
            for game in today_games[:5]:  # Limita a 5 jogos
                probs = analyzer.calculate_match_probabilities(game['homeTeam'], game['awayTeam'])
                
                best_bet = 'Over 2.5 gols' if probs['over_2_5_prob'] > 0.6 else 'Under 2.5 gols'
                best_prob = probs['over_2_5_prob'] if probs['over_2_5_prob'] > 0.6 else (1 - probs['over_2_5_prob'])
                
                if probs['home_win_prob'] > best_prob:
                    best_bet = f'Vitória {game["homeTeam"]}'
                    best_prob = probs['home_win_prob']
                elif probs['away_win_prob'] > best_prob:
                    best_bet = f'Vitória {game["awayTeam"]}'
                    best_prob = probs['away_win_prob']
                
                predictions.append({
                    'game': f'{game["homeTeam"]} vs {game["awayTeam"]}',
                    'league': game['competition'],
                    'prediction': best_bet,
                    'probability': round(best_prob, 3),
                    'confidence': probs['confidence'],
                    'expected_goals': probs['expected_goals'],
                    'home_win': probs['home_win_prob'],
                    'draw': probs['draw_prob'],
                    'away_win': probs['away_win_prob'],
                    'over_2_5': probs['over_2_5_prob']
                })
        
        return jsonify({
            'predictions': predictions,
            'leagues_covered': ['Premier League', 'La Liga', 'Serie A', 'Brasileirão', 'Liga Argentina']
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar previsões: {str(e)}'}), 500

@app.route('/analyze/neural/<home_team>/<away_team>', methods=['GET'])
def analyze_match_neural(home_team, away_team):
    """Análise com ensemble de modelos IA"""
    ensemble = EnsemblePredictor()
    
    try:
        prediction = ensemble.predict_match_ensemble(home_team, away_team)
        
        return jsonify({
            'match': f'{home_team} vs {away_team}',
            'ensemble_prediction': prediction,
            'recommendation': {
                'best_bet': ensemble._determine_best_bet(prediction),
                'confidence': prediction.get('ensemble_confidence', 'Baixa'),
                'models_used': prediction.get('models_used', [])
            }
        })
    except Exception as e:
        return jsonify({'error': f'Erro na análise neural: {str(e)}'}), 500

@app.route('/analyze/<home_team>/<away_team>', methods=['GET'])
def analyze_match(home_team, away_team):
    """Análise detalhada de uma partida específica"""
    analyzer = StatsAnalyzer()
    
    try:
        analysis = analyzer.calculate_match_probabilities(home_team, away_team)
        
        # Adiciona forma recente
        home_form = analyzer.get_team_form(home_team)
        away_form = analyzer.get_team_form(away_team)
        h2h = analyzer.head_to_head(home_team, away_team)
        
        detailed_analysis = {
            'match': f'{home_team} vs {away_team}',
            'probabilities': analysis,
            'team_forms': {
                'home': home_form,
                'away': away_form
            },
            'head_to_head': h2h,
            'recommendation': {
                'primary': 'Over 2.5 gols' if analysis['over_2_5_prob'] > 0.6 else f'Vitória {home_team}' if analysis['home_win_prob'] > 0.5 else 'Empate',
                'confidence': analysis['confidence'],
                'risk_level': 'Baixo' if analysis['confidence'] == 'Alta' else 'Médio'
            }
        }
        
        return jsonify(detailed_analysis)
        
    except Exception as e:
        return jsonify({'error': f'Erro na análise: {str(e)}'}), 500

@app.route('/')
def home():
    return jsonify({
        'message': '⚽ API de Previsões de Futebol',
        'status': 'online',
        'endpoints': ['/predictions', '/predictions/neural', '/best-combo']
    })

@app.route('/best-combo', methods=['GET'])
def get_best_combo():
    """Retorna a melhor combinação do dia baseada em análise estatística"""
    analyzer = StatsAnalyzer()
    
    matches = [
        ('Real Madrid', 'Barcelona'),
        ('Manchester City', 'Liverpool'),
        ('Bayern Munich', 'PSG')
    ]
    
    best_bets = []
    total_prob = 1.0
    
    for home_team, away_team in matches:
        probs = analyzer.calculate_match_probabilities(home_team, away_team)
        
        # Seleciona aposta com maior probabilidade e confiança
        bets = [
            ('Over 2.5 gols', probs['over_2_5_prob'], 1.75),
            (f'Vitória {home_team}', probs['home_win_prob'], 2.10),
            ('Empate', probs['draw_prob'], 3.20),
            (f'Vitória {away_team}', probs['away_win_prob'], 2.80)
        ]
        
        # Filtra apostas com probabilidade > 50% e confiança alta/média
        good_bets = [(bet, prob, odds) for bet, prob, odds in bets 
                    if prob > 0.45 and probs['confidence'] in ['Alta', 'Média']]
        
        if good_bets:
            best_bet = max(good_bets, key=lambda x: x[1])  # Maior probabilidade
            best_bets.append({
                'match': f'{home_team} vs {away_team}',
                'bet': best_bet[0],
                'probability': round(best_bet[1], 3),
                'odds': best_bet[2],
                'confidence': probs['confidence']
            })
            total_prob *= best_bet[1]
    
    if best_bets:
        total_odds = 1
        for bet in best_bets:
            total_odds *= bet['odds']
        
        combo = {
            'games': best_bets,
            'total_odds': round(total_odds, 2),
            'combined_probability': round(total_prob, 3),
            'confidence': 'Alta' if total_prob > 0.3 else 'Média' if total_prob > 0.15 else 'Baixa',
            'expected_return': f'{round((total_odds - 1) * 100)}%',
            'risk_level': 'Baixo' if len(best_bets) <= 2 else 'Médio' if len(best_bets) <= 3 else 'Alto'
        }
    else:
        combo = {
            'message': 'Nenhuma combinação segura encontrada hoje',
            'games': [],
            'total_odds': 0,
            'confidence': 'Baixa'
        }
    
    return jsonify(combo)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Iniciando servidor na porta {port}")
    
    # Configuração para produção
    import os
    if os.environ.get('RENDER'):
        from werkzeug.serving import WSGIRequestHandler
        WSGIRequestHandler.protocol_version = "HTTP/1.1"
    
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)