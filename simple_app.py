from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        'message': '⚽ API de Previsões de Futebol',
        'status': 'online',
        'version': '1.0'
    })

@app.route('/predictions')
def predictions():
    return jsonify({
        'predictions': [
            {
                'game': 'Real Madrid vs Barcelona',
                'prediction': 'Over 2.5 gols',
                'probability': 0.75,
                'confidence': 'Alta'
            },
            {
                'game': 'Manchester City vs Liverpool', 
                'prediction': 'Vitória Manchester City',
                'probability': 0.68,
                'confidence': 'Média'
            }
        ]
    })

@app.route('/predictions/neural')
def neural_predictions():
    return jsonify({
        'predictions': [
            {
                'match': 'Real Madrid vs Barcelona',
                'best_bet': ['Over 2.5 gols', 0.85],
                'prediction': {
                    'home_win_prob': 0.45,
                    'draw_prob': 0.25,
                    'away_win_prob': 0.30,
                    'over_2_5_prob': 0.85
                },
                'confidence': 'Muito Alta',
                'models_used': ['stats', 'neural', 'ml']
            }
        ]
    })

@app.route('/best-combo')
def best_combo():
    return jsonify({
        'games': [
            {'match': 'Real Madrid vs Barcelona', 'bet': 'Over 2.5 gols', 'odds': 1.85, 'probability': 0.75}
        ],
        'total_odds': 1.85,
        'confidence': 'Alta',
        'expected_return': '85%'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting server on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)