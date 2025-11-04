import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import sqlite3
import pickle
from datetime import datetime

class FootballPredictor:
    def __init__(self):
        self.model_goals = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model_result = RandomForestClassifier(n_estimators=100, random_state=42)
        
    def prepare_features(self, home_team, away_team):
        """Prepara features para previsão"""
        conn = sqlite3.connect('football.db')
        
        # Busca estatísticas dos times
        home_stats = pd.read_sql('''
            SELECT * FROM team_stats WHERE team_name = ?
        ''', conn, params=(home_team,))
        
        away_stats = pd.read_sql('''
            SELECT * FROM team_stats WHERE team_name = ?
        ''', conn, params=(away_team,))
        
        conn.close()
        
        if home_stats.empty or away_stats.empty:
            return None
            
        # Cria features
        features = [
            home_stats['goals_scored'].iloc[0],
            home_stats['goals_conceded'].iloc[0],
            home_stats['wins'].iloc[0],
            away_stats['goals_scored'].iloc[0],
            away_stats['goals_conceded'].iloc[0],
            away_stats['wins'].iloc[0]
        ]
        
        return np.array(features).reshape(1, -1)
    
    def train_models(self):
        """Treina os modelos com dados históricos"""
        conn = sqlite3.connect('football.db')
        
        # Busca dados históricos
        games_df = pd.read_sql('''
            SELECT g.*, 
                   hs.goals_scored as home_avg_goals,
                   hs.goals_conceded as home_avg_conceded,
                   hs.wins as home_wins,
                   as_.goals_scored as away_avg_goals,
                   as_.goals_conceded as away_avg_conceded,
                   as_.wins as away_wins
            FROM games g
            JOIN team_stats hs ON g.home_team = hs.team_name
            JOIN team_stats as_ ON g.away_team = as_.team_name
            WHERE g.home_goals IS NOT NULL
        ''', conn)
        
        conn.close()
        
        if games_df.empty:
            print("Não há dados suficientes para treinar")
            return
        
        # Prepara features
        X = games_df[['home_avg_goals', 'home_avg_conceded', 'home_wins', 
                     'away_avg_goals', 'away_avg_conceded', 'away_wins']]
        
        # Target para gols (over/under 2.5)
        y_goals = (games_df['home_goals'] + games_df['away_goals'] > 2.5).astype(int)
        
        # Target para resultado (0=away, 1=draw, 2=home)
        y_result = np.where(games_df['home_goals'] > games_df['away_goals'], 2,
                           np.where(games_df['home_goals'] < games_df['away_goals'], 0, 1))
        
        # Treina modelos
        if len(X) > 10:  # Mínimo de dados
            X_train, X_test, y_goals_train, y_goals_test = train_test_split(X, y_goals, test_size=0.2)
            X_train, X_test, y_result_train, y_result_test = train_test_split(X, y_result, test_size=0.2)
            
            self.model_goals.fit(X_train, y_goals_train)
            self.model_result.fit(X_train, y_result_train)
            
            # Avalia modelos
            goals_acc = accuracy_score(y_goals_test, self.model_goals.predict(X_test))
            result_acc = accuracy_score(y_result_test, self.model_result.predict(X_test))
            
            print(f"Acurácia Over/Under: {goals_acc:.2f}")
            print(f"Acurácia Resultado: {result_acc:.2f}")
            
            # Salva modelos
            with open('model_goals.pkl', 'wb') as f:
                pickle.dump(self.model_goals, f)
            with open('model_result.pkl', 'wb') as f:
                pickle.dump(self.model_result, f)
    
    def predict_match(self, home_team, away_team):
        """Faz previsão para uma partida"""
        features = self.prepare_features(home_team, away_team)
        
        if features is None:
            return None
        
        try:
            # Carrega modelos se existirem
            with open('model_goals.pkl', 'rb') as f:
                self.model_goals = pickle.load(f)
            with open('model_result.pkl', 'rb') as f:
                self.model_result = pickle.load(f)
        except FileNotFoundError:
            print("Modelos não encontrados. Treine primeiro.")
            return None
        
        # Previsões
        goals_prob = self.model_goals.predict_proba(features)[0]
        result_prob = self.model_result.predict_proba(features)[0]
        
        predictions = {
            'over_2_5_prob': goals_prob[1] if len(goals_prob) > 1 else 0.5,
            'home_win_prob': result_prob[2] if len(result_prob) > 2 else 0.33,
            'draw_prob': result_prob[1] if len(result_prob) > 1 else 0.33,
            'away_win_prob': result_prob[0] if len(result_prob) > 0 else 0.33
        }
        
        return predictions

if __name__ == "__main__":
    predictor = FootballPredictor()
    predictor.train_models()