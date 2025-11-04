#!/usr/bin/env python3
"""
Script para iniciar o sistema completo (Backend + Frontend)
"""

import subprocess
import threading
import time
import os
import sys

def start_backend():
    """Inicia o servidor Flask"""
    print("🚀 Iniciando backend Flask...")
    subprocess.run([sys.executable, "run.py"])

def start_frontend():
    """Inicia o servidor React"""
    print("🌐 Iniciando frontend React...")
    os.chdir("frontend")
    
    # Instala dependências se necessário
    if not os.path.exists("node_modules"):
        print("📦 Instalando dependências do React...")
        subprocess.run(["npm", "install"])
    
    # Inicia servidor React
    subprocess.run(["npm", "start"])

def main():
    print("⚽ Iniciando Sistema Completo de Previsões de Futebol")
    print("=" * 60)
    
    # Inicia backend em thread separada
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Aguarda backend inicializar
    print("⏳ Aguardando backend inicializar...")
    time.sleep(5)
    
    # Inicia frontend
    try:
        start_frontend()
    except KeyboardInterrupt:
        print("\n🛑 Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar frontend: {e}")
        print("💡 Certifique-se de ter o Node.js instalado")

if __name__ == "__main__":
    main()