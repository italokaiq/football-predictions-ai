import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class StatsAnalyzer:
    def __init__(self):
        self.conn = sqlite3.connect('football.db')
    
    def get_team_form(self, team_name, last_n_games=5):
        """Analisa forma recente do time"""
        query = '''
            SELECT home_goals, away_goals, 
                   CASE WHEN home_team = ? THEN 'home' ELSE 'away' END as venue
            FROM games 
            WHERE (home_team = ? OR away_team = ?) 
            AND home_goals IS NOT NULL
            ORDER BY date DESC 
            LIMIT ?
        '''
        
        df = pd.read_sql(query, self.conn, params=(team_name, team_name, team_name, last_n_games))
        
        if df.empty:
            return {'points': 0, 'goals_for': 0, 'goals_against': 0}
        
        points = 0
        goals_for = 0
        goals_against = 0
        
        for _, row in df.iterrows():
            if row['venue'] == 'home':
                gf, ga = row['home_goals'], row['away_goals']
            else:
                gf, ga = row['away_goals'], row['home_goals']
            
            goals_for += gf
            goals_against += ga
            
            if gf > ga:
                points += 3
            elif gf == ga:
                points += 1
        
        return {
            'points': points,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'avg_goals_for': goals_for / len(df),
            'avg_goals_against': goals_against / len(df)
        }
    
    def head_to_head(self, team1, team2, last_n=5):
        """Histórico de confrontos diretos"""
        query = '''
            SELECT home_team, away_team, home_goals, away_goals
            FROM games 
            WHERE ((home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?))
            AND home_goals IS NOT NULL
            ORDER BY date DESC 
            LIMIT ?
        '''
        
        df = pd.read_sql(query, self.conn, params=(team1, team2, team2, team1, last_n))
        
        if df.empty:
            return {'team1_wins': 0, 'draws': 0, 'team2_wins': 0, 'avg_goals': 2.5}
        
        team1_wins = team2_wins = draws = total_goals = 0
        
        for _, row in df.iterrows():
            hg, ag = row['home_goals'], row['away_goals']
            total_goals += hg + ag
            
            if row['home_team'] == team1:
                if hg > ag:
                    team1_wins += 1
                elif hg < ag:
                    team2_wins += 1
                else:
                    draws += 1
            else:
                if ag > hg:
                    team1_wins += 1
                elif ag < hg:
                    team2_wins += 1
                else:
                    draws += 1
        
        return {
            'team1_wins': team1_wins,
            'draws': draws,
            'team2_wins': team2_wins,
            'avg_goals': total_goals / len(df),
            'games_played': len(df)
        }
    
    def calculate_match_probabilities(self, home_team, away_team):
        """Calcula probabilidades baseadas em estatísticas"""
        
        # Forma recente
        home_form = self.get_team_form(home_team)
        away_form = self.get_team_form(away_team)
        
        # Confronto direto
        h2h = self.head_to_head(home_team, away_team)
        
        # Estatísticas gerais
        home_stats_query = "SELECT * FROM team_stats WHERE team_name = ?"
        away_stats_query = "SELECT * FROM team_stats WHERE team_name = ?"
        
        home_stats = pd.read_sql(home_stats_query, self.conn, params=(home_team,))
        away_stats = pd.read_sql(away_stats_query, self.conn, params=(away_team,))
        
        if home_stats.empty or away_stats.empty:
            return self._default_probabilities()
        
        # Cálculo de força dos times (0-100)
        home_strength = self._calculate_team_strength(home_stats.iloc[0], home_form, True)
        away_strength = self._calculate_team_strength(away_stats.iloc[0], away_form, False)
        
        # Probabilidades de resultado
        strength_diff = home_strength - away_strength
        
        # Ajuste baseado em vantagem de casa (+10 pontos)
        strength_diff += 10
        
        # Conversão para probabilidades
        if strength_diff > 20:
            home_win_prob = 0.65
            draw_prob = 0.20
            away_win_prob = 0.15
        elif strength_diff > 10:
            home_win_prob = 0.50
            draw_prob = 0.30
            away_win_prob = 0.20
        elif strength_diff > -10:
            home_win_prob = 0.35
            draw_prob = 0.30
            away_win_prob = 0.35
        elif strength_diff > -20:
            home_win_prob = 0.20
            draw_prob = 0.30
            away_win_prob = 0.50
        else:
            home_win_prob = 0.15
            draw_prob = 0.20
            away_win_prob = 0.65
        
        # Probabilidade de gols
        expected_goals = (home_form['avg_goals_for'] + away_form['avg_goals_against'] + 
                         away_form['avg_goals_for'] + home_form['avg_goals_against']) / 2
        
        # Ajuste com histórico H2H
        if h2h.get('games_played', 0) > 0:
            expected_goals = (expected_goals + h2h['avg_goals']) / 2
        
        over_2_5_prob = min(0.9, max(0.1, (expected_goals - 2.5) / 2 + 0.5))
        
        return {
            'home_win_prob': round(home_win_prob, 3),
            'draw_prob': round(draw_prob, 3),
            'away_win_prob': round(away_win_prob, 3),
            'over_2_5_prob': round(over_2_5_prob, 3),
            'expected_goals': round(expected_goals, 2),
            'home_strength': round(home_strength, 1),
            'away_strength': round(away_strength, 1),
            'confidence': self._calculate_confidence(h2h.get('games_played', 0), home_form['points'], away_form['points'])
        }
    
    def _calculate_team_strength(self, stats, form, is_home):
        """Calcula força do time (0-100)"""
        # Estatísticas gerais (40%)
        win_rate = stats['wins'] / max(1, stats['wins'] + stats['draws'] + stats['losses'])
        goal_diff = stats['goals_scored'] - stats['goals_conceded']
        
        general_strength = (win_rate * 50) + (min(20, max(-20, goal_diff)) + 20)
        
        # Forma recente (40%)
        form_strength = (form['points'] / 15) * 40  # Máximo 15 pontos em 5 jogos
        
        # Vantagem casa/fora (20%)
        venue_bonus = 20 if is_home else 10
        
        return min(100, general_strength * 0.4 + form_strength * 0.4 + venue_bonus * 0.2)
    
    def _calculate_confidence(self, h2h_games, home_form_points, away_form_points):
        """Calcula nível de confiança da previsão"""
        confidence_score = 0
        
        # Histórico H2H disponível
        if h2h_games >= 3:
            confidence_score += 30
        elif h2h_games >= 1:
            confidence_score += 15
        
        # Forma consistente
        if abs(home_form_points - away_form_points) > 6:
            confidence_score += 40
        elif abs(home_form_points - away_form_points) > 3:
            confidence_score += 20
        
        # Base
        confidence_score += 30
        
        if confidence_score >= 80:
            return 'Alta'
        elif confidence_score >= 60:
            return 'Média'
        else:
            return 'Baixa'
    
    def _default_probabilities(self):
        """Probabilidades padrão quando não há dados"""
        return {
            'home_win_prob': 0.40,
            'draw_prob': 0.30,
            'away_win_prob': 0.30,
            'over_2_5_prob': 0.50,
            'expected_goals': 2.5,
            'confidence': 'Baixa'
        }

if __name__ == "__main__":
    analyzer = StatsAnalyzer()
    
    # Teste com times de exemplo
    result = analyzer.calculate_match_probabilities('Real Madrid', 'Barcelona')
    print("Real Madrid vs Barcelona:")
    for key, value in result.items():
        print(f"  {key}: {value}")