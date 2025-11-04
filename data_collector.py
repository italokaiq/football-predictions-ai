import requests
import sqlite3
import schedule
import time
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class DataCollector:
    def __init__(self):
        self.api_key = os.getenv('FOOTBALL_API_KEY', 'your_api_key_here')
        self.base_url = 'https://api.football-data.org/v4'
        self.headers = {'X-Auth-Token': self.api_key}
    
    def collect_matches(self, days_back=30):
        """Coleta partidas dos últimos N dias"""
        conn = sqlite3.connect('football.db')
        cursor = conn.cursor()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        try:
            response = requests.get(
                f'{self.base_url}/matches',
                headers=self.headers,
                params={
                    'dateFrom': start_date.strftime('%Y-%m-%d'),
                    'dateTo': end_date.strftime('%Y-%m-%d'),
                    'status': 'FINISHED'
                }
            )
            
            if response.status_code == 200:
                matches = response.json().get('matches', [])
                
                for match in matches:
                    if match['status'] == 'FINISHED' and match['score']['fullTime']['home'] is not None:
                        cursor.execute('''
                            INSERT OR REPLACE INTO games 
                            (id, home_team, away_team, date, home_goals, away_goals, competition)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            match['id'],
                            match['homeTeam']['name'],
                            match['awayTeam']['name'],
                            match['utcDate'],
                            match['score']['fullTime']['home'],
                            match['score']['fullTime']['away'],
                            match['competition']['name']
                        ))
                
                conn.commit()
                print(f"Coletadas {len(matches)} partidas")
            else:
                print(f"Erro na API: {response.status_code}")
                
        except Exception as e:
            print(f"Erro ao coletar partidas: {e}")
        finally:
            conn.close()
    
    def update_team_stats(self):
        """Atualiza estatísticas dos times"""
        conn = sqlite3.connect('football.db')
        cursor = conn.cursor()
        
        # Busca todos os times únicos
        cursor.execute('''
            SELECT DISTINCT home_team FROM games
            UNION
            SELECT DISTINCT away_team FROM games
        ''')
        
        teams = [row[0] for row in cursor.fetchall()]
        
        for team in teams:
            # Estatísticas como mandante
            cursor.execute('''
                SELECT 
                    AVG(home_goals) as avg_goals_scored,
                    AVG(away_goals) as avg_goals_conceded,
                    SUM(CASE WHEN home_goals > away_goals THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN home_goals = away_goals THEN 1 ELSE 0 END) as draws,
                    SUM(CASE WHEN home_goals < away_goals THEN 1 ELSE 0 END) as losses
                FROM games 
                WHERE home_team = ? AND home_goals IS NOT NULL
            ''', (team,))
            
            home_stats = cursor.fetchone()
            
            # Estatísticas como visitante
            cursor.execute('''
                SELECT 
                    AVG(away_goals) as avg_goals_scored,
                    AVG(home_goals) as avg_goals_conceded,
                    SUM(CASE WHEN away_goals > home_goals THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN away_goals = home_goals THEN 1 ELSE 0 END) as draws,
                    SUM(CASE WHEN away_goals < home_goals THEN 1 ELSE 0 END) as losses
                FROM games 
                WHERE away_team = ? AND away_goals IS NOT NULL
            ''', (team,))
            
            away_stats = cursor.fetchone()
            
            # Combina estatísticas
            if home_stats[0] and away_stats[0]:
                avg_goals_scored = (home_stats[0] + away_stats[0]) / 2
                avg_goals_conceded = (home_stats[1] + away_stats[1]) / 2
                total_wins = (home_stats[2] or 0) + (away_stats[2] or 0)
                total_draws = (home_stats[3] or 0) + (away_stats[3] or 0)
                total_losses = (home_stats[4] or 0) + (away_stats[4] or 0)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO team_stats 
                    (team_name, goals_scored, goals_conceded, wins, draws, losses, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    team, avg_goals_scored, avg_goals_conceded,
                    total_wins, total_draws, total_losses,
                    datetime.now().isoformat()
                ))
        
        conn.commit()
        conn.close()
        print("Estatísticas dos times atualizadas")
    
    def daily_update(self):
        """Atualização diária automática"""
        print(f"Iniciando atualização diária - {datetime.now()}")
        self.collect_matches(days_back=7)  # Últimos 7 dias
        self.update_team_stats()
        print("Atualização concluída")

def run_scheduler():
    """Executa o agendador"""
    collector = DataCollector()
    
    # Agenda atualização diária às 6h
    schedule.every().day.at("06:00").do(collector.daily_update)
    
    print("Agendador iniciado. Pressione Ctrl+C para parar.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    collector = DataCollector()
    
    # Primeira coleta
    print("Fazendo coleta inicial...")
    collector.collect_matches(days_back=90)
    collector.update_team_stats()
    
    # Inicia agendador
    run_scheduler()