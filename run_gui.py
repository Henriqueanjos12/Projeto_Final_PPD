# run_gui.py
# Execução simplificada da interface gráfica

import tkinter as tk
from tkinter import messagebox
import sys
import os


def check_dependencies():
    """Verifica dependências antes de executar"""
    try:
        import Pyro5.api
        import pika
        from geopy.distance import geodesic

        # Testar RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        connection.close()

        return True, "Todas as dependências OK!"

    except ImportError as e:
        return False, f"Dependência não encontrada: {e}\n\nSolução:\npip install -r requirements.txt"
    except Exception as e:
        return False, f"RabbitMQ não está rodando: {e}\n\nSoluções:\n1. sudo systemctl start rabbitmq-server (Linux)\n2. brew services start rabbitmq (Mac)\n3. docker run -d --name rabbitmq -p 5672:5672 rabbitmq:3 (Docker)"


def main():
    """Execução principal"""
    print("🚀 Iniciando Interface Gráfica do Sistema de Comunicação...")

    # Verificar dependências
    deps_ok, deps_msg = check_dependencies()

    if not deps_ok:
        # Criar janela simples de erro
        root = tk.Tk()
        root.withdraw()  # Esconder janela principal

        messagebox.showerror("Erro de Dependências", deps_msg)
        print(f"❌ {deps_msg}")
        return

    print("✅ Dependências verificadas com sucesso!")

    # Importar e executar GUI
    try:
        from gui_interface import LocationBasedChatGUI, patch_communication_system_for_gui

        print("🎨 Carregando interface gráfica...")

        app = LocationBasedChatGUI()
        patch_communication_system_for_gui(app)

        print("🎉 Interface carregada! Iniciando aplicação...")
        app.run()

    except ImportError:
        print("❌ Erro: Arquivo gui_interface.py não encontrado!")
        print("Certifique-se que todos os arquivos estão no mesmo diretório.")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")


if __name__ == "__main__":
    main()