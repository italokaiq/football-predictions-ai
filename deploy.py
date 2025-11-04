#!/usr/bin/env python3
"""
Script para preparar e fazer deploy da aplicação
"""

import os
import subprocess
import sys

def setup_production():
    """Prepara aplicação para produção"""
    print("🚀 Preparando para deploy...")
    
    # Cria dados de exemplo se não existirem
    if not os.path.exists('football.db'):
        print("📊 Criando dados de exemplo...")
        subprocess.run([sys.executable, 'sample_data.py'])
        
        print("🤖 Treinando modelos...")
        subprocess.run([sys.executable, 'ml_predictor.py'])
        subprocess.run([sys.executable, 'neural_predictor.py'])
    
    print("✅ Aplicação pronta para produção!")

def deploy_heroku():
    """Deploy no Heroku"""
    print("🌐 Deploy no Heroku...")
    
    commands = [
        "git init",
        "git add .",
        "git commit -m 'Deploy inicial'",
        "heroku create football-predictions-ai",
        "git push heroku main"
    ]
    
    for cmd in commands:
        print(f"Executando: {cmd}")
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Erro: {result.stderr}")
            return False
    
    print("✅ Deploy no Heroku concluído!")
    return True

def deploy_railway():
    """Deploy no Railway"""
    print("🚂 Deploy no Railway...")
    
    commands = [
        "railway login",
        "railway init",
        "railway up"
    ]
    
    for cmd in commands:
        print(f"Executando: {cmd}")
        subprocess.run(cmd.split())
    
    print("✅ Deploy no Railway concluído!")

def create_docker():
    """Cria Dockerfile"""
    dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python sample_data.py
RUN python ml_predictor.py
RUN python neural_predictor.py

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    print("🐳 Dockerfile criado!")

def main():
    print("⚽ Deploy do Sistema de Previsões de Futebol")
    print("=" * 50)
    
    setup_production()
    create_docker()
    
    print("\n🚀 Opções de Deploy:")
    print("1. Heroku (gratuito)")
    print("2. Railway (gratuito)")
    print("3. Vercel (frontend)")
    print("4. Docker local")
    
    choice = input("\nEscolha uma opção (1-4): ")
    
    if choice == "1":
        deploy_heroku()
    elif choice == "2":
        deploy_railway()
    elif choice == "3":
        print("📱 Para Vercel:")
        print("1. Instale: npm i -g vercel")
        print("2. Execute: vercel --prod")
    elif choice == "4":
        print("🐳 Para Docker:")
        print("1. docker build -t football-ai .")
        print("2. docker run -p 5000:5000 football-ai")

if __name__ == "__main__":
    main()