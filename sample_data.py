import sqlite3
from datetime import datetime, timedelta
import random

def create_sample_data():
    """Cria dados de exemplo para testar o sistema"""
    conn = sqlite3.connect('football.db')
    cursor = conn.cursor()
    
    # Inicializa tabelas se não existirem
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
    
    # Times de exemplo
    teams = [
        'Real Madrid', 'Barcelona', 'Manchester City', 'Liverpool',
        'Bayern Munich', 'PSG', 'Chelsea', 'Arsenal',
        'Juventus', 'AC Milan', 'Atletico Madrid', 'Tottenham'
    ]
    
    # Gera jogos dos últimos 30 dias
    for i in range(100):
        home_team = random.choice(teams)
        away_team = random.choice([t for t in teams if t != home_team])
        
        # Gols baseados em probabilidades realistas
        home_goals = random.choices([0,1,2,3,4,5], weights=[10,25,30,20,10,5])[0]
        away_goals = random.choices([0,1,2,3,4], weights=[15,30,25,20,10])[0]
        
        game_date = datetime.now() - timedelta(days=random.randint(1, 30))
        
        cursor.execute('''
            INSERT OR IGNORE INTO games 
            (id, home_team, away_team, date, home_goals, away_goals, competition)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            1000 + i, home_team, away_team, game_date.isoformat(),
            home_goals, away_goals, 'Premier League'
        ))
    
    # Calcula estatísticas dos times
    for team in teams:
        # Como mandante
        cursor.execute('''
            SELECT AVG(home_goals), AVG(away_goals),
                   SUM(CASE WHEN home_goals > away_goals THEN 1 ELSE 0 END),
                   SUM(CASE WHEN home_goals = away_goals THEN 1 ELSE 0 END),
                   SUM(CASE WHEN home_goals < away_goals THEN 1 ELSE 0 END)
            FROM games WHERE home_team = ?
        ''', (team,))
        home_stats = cursor.fetchone()
        
        # Como visitante
        cursor.execute('''
            SELECT AVG(away_goals), AVG(home_goals),
                   SUM(CASE WHEN away_goals > home_goals THEN 1 ELSE 0 END),
                   SUM(CASE WHEN away_goals = home_goals THEN 1 ELSE 0 END),
                   SUM(CASE WHEN away_goals < home_goals THEN 1 ELSE 0 END)
            FROM games WHERE away_team = ?
        ''', (team,))
        away_stats = cursor.fetchone()
        
        # Combina estatísticas
        avg_goals = (home_stats[0] + away_stats[0]) / 2
        avg_conceded = (home_stats[1] + away_stats[1]) / 2
        wins = (home_stats[2] or 0) + (away_stats[2] or 0)
        draws = (home_stats[3] or 0) + (away_stats[3] or 0)
        losses = (home_stats[4] or 0) + (away_stats[4] or 0)
        
        cursor.execute('''
            INSERT OR REPLACE INTO team_stats 
            (team_name, goals_scored, goals_conceded, wins, draws, losses, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (team, avg_goals, avg_conceded, wins, draws, losses, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    print("Dados de exemplo criados com sucesso!")

if __name__ == "__main__":
    create_sample_data()