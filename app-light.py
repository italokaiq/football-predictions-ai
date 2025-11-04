from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import requests
import os
from datetime import datetime, date
from dotenv import load_dotenv
from stats_analyzer import StatsAnalyzer

load_dotenv()

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv('FOOTBALL_API_KEY', 'your_api_key_here')
API_BASE_URL = 'https://api.football-data.org/v4'

def init_db():
    conn = sqlite3.connect('football.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY,
            home_team TEXT,
            away_team TEXT,
            date TEXT,
            home_goals INTEGER,
            away_goals INTEGER,
            competition TEXT
        )
    ''')
    
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
    
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return jsonify({
        'message': '⚽ API de Previsões de Futebol',
        'version': '1.0',
        'endpoints': ['/predictions', '/predictions/neural', '/best-combo']
    })

@app.route('/predictions', methods=['GET'])
def get_predictions():
    analyzer = StatsAnalyzer()
    
    sample_matches = [
        ('Real Madrid', 'Barcelona'),
        ('Manchester City', 'Liverpool'),
        ('Bayern Munich', 'PSG'),
        ('Chelsea', 'Arsenal')
    ]
    
    predictions = []
    
    for home_team, away_team in sample_matches:
        try:
            probs = analyzer.calculate_match_probabilities(home_team, away_team)
            
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
                'prediction': best_bet,
                'probability': round(best_prob, 3),
                'confidence': probs['confidence'],
                'expected_goals': probs['expected_goals'],
                'home_win': probs['home_win_prob'],
                'draw': probs['draw_prob'],
                'away_win': probs['away_win_prob'],
                'over_2_5': probs['over_2_5_prob']
            })
        except:
            predictions.append({
                'game': f'{home_team} vs {away_team}',
                'prediction': 'Over 2.5 gols',
                'probability': 0.65,
                'confidence': 'Média'
            })
    
    return jsonify({'predictions': predictions})

@app.route('/predictions/neural', methods=['GET'])
def get_neural_predictions():
    # Versão simplificada sem TensorFlow
    return get_predictions()

@app.route('/best-combo', methods=['GET'])
def get_best_combo():
    combo = {
        'games': [
            {'match': 'Real Madrid vs Barcelona', 'bet': 'Over 2.5 gols', 'odds': 1.85, 'probability': 0.75},
            {'match': 'Manchester City vs Liverpool', 'bet': 'Vitória Manchester City', 'odds': 2.10, 'probability': 0.68}
        ],
        'total_odds': 3.89,
        'combined_probability': 0.51,
        'confidence': 'Alta',
        'expected_return': '289%',
        'risk_level': 'Médio'
    }
    
    return jsonify(combo)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)