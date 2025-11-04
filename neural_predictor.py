import numpy as np
import pandas as pd
import sqlite3
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import pickle
import os
from datetime import datetime

class NeuralPredictor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model_goals = None
        self.model_result = None
        self.feature_names = [
            'home_avg_goals', 'home_avg_conceded', 'home_wins', 'home_form_points',
            'away_avg_goals', 'away_avg_conceded', 'away_wins', 'away_form_points',
            'h2h_home_wins', 'h2h_draws', 'h2h_away_wins', 'h2h_avg_goals',
            'home_strength', 'away_strength', 'strength_diff'
        ]
    
    def create_advanced_features(self):
        """Cria features avançadas para a rede neural"""
        conn = sqlite3.connect('football.db')
        
        # Query complexa para extrair features
        query = '''
        SELECT 
            g.id,
            g.home_team,
            g.away_team,
            g.home_goals,
            g.away_goals,
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
        '''
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty:
            return None, None, None, None
        
        # Features básicas
        features = df[['home_avg_goals', 'home_avg_conceded', 'home_wins',
                      'away_avg_goals', 'away_avg_conceded', 'away_wins']].copy()
        
        # Features derivadas
        features['home_goal_diff'] = features['home_avg_goals'] - features['home_avg_conceded']
        features['away_goal_diff'] = features['away_avg_goals'] - features['away_avg_conceded']
        features['goal_diff_advantage'] = features['home_goal_diff'] - features['away_goal_diff']
        
        # Força dos times (normalizada)
        features['home_strength'] = (features['home_wins'] * 3 + features['home_goal_diff']) / 10
        features['away_strength'] = (features['away_wins'] * 3 + features['away_goal_diff']) / 10
        features['strength_diff'] = features['home_strength'] - features['away_strength']
        
        # Vantagem de casa
        features['home_advantage'] = 1
        
        # Targets
        total_goals = df['home_goals'] + df['away_goals']
        y_goals = (total_goals > 2.5).astype(int)
        
        # Resultado: 0=away win, 1=draw, 2=home win
        y_result = np.where(df['home_goals'] > df['away_goals'], 2,
                           np.where(df['home_goals'] < df['away_goals'], 0, 1))
        
        return features.values, y_goals.values, y_result, total_goals.values
    
    def build_neural_network(self, input_dim, output_dim, task_type='classification'):
        """Constrói rede neural otimizada"""
        model = keras.Sequential([
            layers.Dense(128, activation='relu', input_shape=(input_dim,)),
            layers.Dropout(0.3),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.1),
        ])
        
        if task_type == 'classification':
            if output_dim == 1:
                model.add(layers.Dense(1, activation='sigmoid'))
                model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
            else:
                model.add(layers.Dense(output_dim, activation='softmax'))
                model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        else:
            model.add(layers.Dense(1, activation='linear'))
            model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        return model
    
    def train_models(self):
        """Treina os modelos de rede neural"""
        print("Criando features avançadas...")
        X, y_goals, y_result, y_total_goals = self.create_advanced_features()
        
        if X is None:
            print("Não há dados suficientes para treinar")
            return
        
        print(f"Treinando com {len(X)} amostras...")
        
        # Normaliza features
        X_scaled = self.scaler.fit_transform(X)
        
        # Divide dados
        X_train, X_test, y_goals_train, y_goals_test = train_test_split(
            X_scaled, y_goals, test_size=0.2, random_state=42
        )
        X_train_r, X_test_r, y_result_train, y_result_test = train_test_split(
            X_scaled, y_result, test_size=0.2, random_state=42
        )
        
        # Modelo para Over/Under
        print("Treinando modelo Over/Under...")
        self.model_goals = self.build_neural_network(X.shape[1], 1, 'classification')
        
        early_stopping = keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)
        
        self.model_goals.fit(
            X_train, y_goals_train,
            epochs=100,
            batch_size=32,
            validation_split=0.2,
            callbacks=[early_stopping],
            verbose=0
        )
        
        # Modelo para Resultado
        print("Treinando modelo de Resultado...")
        self.model_result = self.build_neural_network(X.shape[1], 3, 'classification')
        
        self.model_result.fit(
            X_train_r, y_result_train,
            epochs=100,
            batch_size=32,
            validation_split=0.2,
            callbacks=[early_stopping],
            verbose=0
        )
        
        # Avalia modelos
        goals_acc = self.model_goals.evaluate(X_test, y_goals_test, verbose=0)[1]
        result_acc = self.model_result.evaluate(X_test_r, y_result_test, verbose=0)[1]
        
        print(f"Acurácia Over/Under: {goals_acc:.3f}")
        print(f"Acurácia Resultado: {result_acc:.3f}")
        
        # Salva modelos
        self.model_goals.save('neural_model_goals.h5')
        self.model_result.save('neural_model_result.h5')
        
        with open('scaler.pkl', 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print("Modelos salvos com sucesso!")
    
    def load_models(self):
        """Carrega modelos treinados"""
        try:
            self.model_goals = keras.models.load_model('neural_model_goals.h5')
            self.model_result = keras.models.load_model('neural_model_result.h5')
            
            with open('scaler.pkl', 'rb') as f:
                self.scaler = pickle.load(f)
            
            return True
        except:
            return False
    
    def prepare_match_features(self, home_team, away_team):
        """Prepara features para uma partida específica"""
        conn = sqlite3.connect('football.db')
        
        # Busca estatísticas dos times
        home_query = "SELECT * FROM team_stats WHERE team_name = ?"
        away_query = "SELECT * FROM team_stats WHERE team_name = ?"
        
        home_stats = pd.read_sql(home_query, conn, params=(home_team,))
        away_stats = pd.read_sql(away_query, conn, params=(away_team,))
        
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
        
        # Features derivadas
        home_goal_diff = features[0] - features[1]
        away_goal_diff = features[3] - features[4]
        
        features.extend([
            home_goal_diff,
            away_goal_diff,
            home_goal_diff - away_goal_diff,
            (features[2] * 3 + home_goal_diff) / 10,  # home_strength
            (features[5] * 3 + away_goal_diff) / 10,  # away_strength
            ((features[2] * 3 + home_goal_diff) - (features[5] * 3 + away_goal_diff)) / 10,  # strength_diff
            1  # home_advantage
        ])
        
        return np.array(features).reshape(1, -1)
    
    def predict_match(self, home_team, away_team):
        """Faz previsão usando rede neural"""
        if not self.load_models():
            print("Modelos não encontrados. Treine primeiro.")
            return None
        
        features = self.prepare_match_features(home_team, away_team)
        if features is None:
            return None
        
        # Normaliza features
        features_scaled = self.scaler.transform(features)
        
        # Previsões
        goals_prob = self.model_goals.predict(features_scaled, verbose=0)[0][0]
        result_probs = self.model_result.predict(features_scaled, verbose=0)[0]
        
        return {
            'over_2_5_prob': float(goals_prob),
            'under_2_5_prob': float(1 - goals_prob),
            'away_win_prob': float(result_probs[0]),
            'draw_prob': float(result_probs[1]),
            'home_win_prob': float(result_probs[2]),
            'confidence': 'Alta' if max(result_probs) > 0.6 else 'Média' if max(result_probs) > 0.4 else 'Baixa',
            'model_type': 'Neural Network'
        }

if __name__ == "__main__":
    predictor = NeuralPredictor()
    predictor.train_models()
    
    # Teste
    result = predictor.predict_match('Real Madrid', 'Barcelona')
    if result:
        print("\nPrevisão Neural Network:")
        for key, value in result.items():
            print(f"  {key}: {value}")