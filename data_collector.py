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
        
        # IDs das ligas específicas
        self.leagues = {
            'Premier League': 'PL',
            'La Liga': 'PD', 
            'Serie A': 'SA',
            'Brasileirão': 'BSA',
            'Liga Argentina': 'PPL'
        }
    
    def collect_matches_by_leagues(self, days_back=30):
        """Coleta partidas das ligas específicas"""
        conn = sqlite3.connect('football.db')
        cursor = conn.cursor()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        total_matches = 0
        
        for league_name, league_code in self.leagues.items():
            try:
                response = requests.get(
                    f'{self.base_url}/competitions/{league_code}/matches',
                    headers=self.headers,
                    params={
                        'dateFrom': start_date.strftime('%Y-%m-%d'),
                        'dateTo': end_date.strftime('%Y-%m-%d')
                    }
                )
                
                if response.status_code == 200:
                    matches = response.json().get('matches', [])
                    
                    for match in matches:
                        cursor.execute('''
                            INSERT OR REPLACE INTO games 
                            (id, home_team, away_team, date, home_goals, away_goals, competition, league_code)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            match['id'],
                            match['homeTeam']['name'],
                            match['awayTeam']['name'],
                            match['utcDate'],
                            match['score']['fullTime']['home'] if match['status'] == 'FINISHED' else None,
                            match['score']['fullTime']['away'] if match['status'] == 'FINISHED' else None,
                            league_name,
                            league_code
                        ))
                    
                    total_matches += len(matches)
                    print(f"Coletadas {len(matches)} partidas da {league_name}")
                else:
                    print(f"Erro na API para {league_name}: {response.status_code}")
                    
            except Exception as e:
                print(f"Erro ao coletar {league_name}: {e}")
        
        conn.commit()
        conn.close()
        print(f"Total: {total_matches} partidas coletadas")
    
    def get_today_matches(self):
        """Busca jogos de hoje das ligas específicas"""
        today = datetime.now().strftime('%Y-%m-%d')
        all_matches = []
        
        for league_name, league_code in self.leagues.items():
            try:
                response = requests.get(
                    f'{self.base_url}/competitions/{league_code}/matches',
                    headers=self.headers,
                    params={
                        'dateFrom': today,
                        'dateTo': today
                    }
                )
                
                if response.status_code == 200:
                    matches = response.json().get('matches', [])
                    for match in matches:
                        all_matches.append({
                            'id': match['id'],
                            'homeTeam': match['homeTeam']['name'],
                            'awayTeam': match['awayTeam']['name'],
                            'date': match['utcDate'],
                            'competition': league_name,
                            'league_code': league_code,
                            'status': match['status']
                        })
                        
            except Exception as e:
                print(f"Erro ao buscar jogos de hoje da {league_name}: {e}")
        
        return all_matches
    
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
        self.collect_matches_by_leagues(days_back=7)  # Últimos 7 dias
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
    print("Fazendo coleta inicial das ligas específicas...")
    collector.collect_matches_by_leagues(days_back=90)
    collector.update_team_stats()
    
    # Inicia agendador
    run_scheduler()