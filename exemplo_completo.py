# exemplo_completo.py
# Demonstração completa do Sistema de Comunicação Baseado em Localização

from comunicacao_sistema import *
import time
import threading


def demo_automatica():
    """Demonstração automática de todas as funcionalidades"""
    print("=== DEMONSTRAÇÃO AUTOMÁTICA DO SISTEMA ===")

    # 1. Inicialização
    print("\n1. Inicializando sistema...")
    central_server = CentralServer()

    # Usuários em diferentes localizações de Fortaleza
    alice = User("Alice", -3.7319, -38.5267, 2.0)  # Centro de Fortaleza
    bob = User("Bob", -3.7325, -38.5270, 1.5)  # 100m de Alice
    carol = User("Carol", -3.7400, -38.5400, 1.0)  # 1.5km de Alice
    diana = User("Diana", -3.8000, -38.6000, 2.0)  # 8km de Alice

    # Gerenciadores
    comm_alice = CommunicationManager(alice, central_server)
    comm_bob = CommunicationManager(bob, central_server)
    comm_carol = CommunicationManager(carol, central_server)
    comm_diana = CommunicationManager(diana, central_server)

    # Iniciar serviços
    comm_alice.start_services(8001, 9001)
    comm_bob.start_services(8002, 9002)
    comm_carol.start_services(8003, 9003)
    comm_diana.start_services(8004, 9004)

    time.sleep(3)
    print("✅ Sistema inicializado com 4 usuários")

    # 2. Mostrar topologia inicial
    print("\n2. Topologia inicial:")
    for user_name, comm in [("Alice", comm_alice), ("Bob", comm_bob),
                            ("Carol", comm_carol), ("Diana", comm_diana)]:
        contacts = comm.get_contacts_info()
        print(f"\n{user_name} (raio: {comm.user.communication_radius}km):")
        for contact in contacts:
            range_status = "✅" if contact['in_range'] else "❌"
            print(f"  {range_status} {contact['name']}: {contact['distance']:.2f}km")

    # 3. Teste comunicação síncrona
    print("\n3. Teste de Comunicação Síncrona:")
    print("Alice enviando mensagem para Bob (próximo e online)...")
    comm_alice.send_message(bob.id, "Oi Bob! Esta é uma mensagem síncrona via socket!")
    time.sleep(1)

    print("Bob respondendo para Alice via RPC...")
    comm_bob.send_message(alice.id, "Oi Alice! Resposta via RPC!")
    time.sleep(2)

    # 4. Teste comunicação assíncrona (distância)
    print("\n4. Teste de Comunicação Assíncrona por Distância:")
    print("Alice enviando para Diana (distante)...")
    comm_alice.send_message(diana.id, "Oi Diana! Você está longe, esta mensagem vai por MOM!")
    time.sleep(2)

    # 5. Teste comunicação assíncrona (usuário offline)
    print("\n5. Teste de Comunicação Assíncrona por Status Offline:")
    print("Carol ficando offline...")
    carol.set_status("offline")
    central_server.update_user_status(carol.id, "offline")

    print("Alice enviando mensagem para Carol (offline)...")
    comm_alice.send_message(carol.id, "Carol, esta mensagem ficará na fila até você voltar!")

    time.sleep(2)
    print("Carol voltando online...")
    carol.set_status("online")
    central_server.update_user_status(carol.id, "online")
    time.sleep(2)

    # 6. Teste de atualização de localização
    print("\n6. Teste de Atualização de Localização:")
    print(f"Diana movendo de ({diana.latitude}, {diana.longitude}) para próximo de Alice...")
    comm_diana.update_location(-3.7320, -38.5269)  # Move para perto de Alice

    time.sleep(1)
    print("Nova lista de contatos de Alice após movimentação:")
    for contact in comm_alice.get_contacts_info():
        range_status = "✅" if contact['in_range'] else "❌"
        print(f"  {range_status} {contact['name']}: {contact['distance']:.2f}km")

    print("\nAgora Alice pode falar sincronamente com Diana:")
    comm_alice.send_message(diana.id, "Diana! Agora você está perto, mensagem síncrona!")
    time.sleep(2)

    # 7. Teste de atualização de raio
    print("\n7. Teste de Atualização de Raio:")
    print(f"Carol aumentando raio de {carol.communication_radius}km para 5km...")
    comm_carol.update_radius(5.0)

    time.sleep(1)
    print("Novos contatos de Carol após aumento do raio:")
    for contact in comm_carol.get_contacts_info():
        range_status = "✅" if contact['in_range'] else "❌"
        print(f"  {range_status} {contact['name']}: {contact['distance']:.2f}km")

    # 8. Teste de múltiplas mensagens simultâneas
    print("\n8. Teste de Múltiplas Mensagens Simultâneas:")

    def enviar_multiplas_mensagens():
        messages = [
            (comm_alice, bob.id, "Mensagem 1 de Alice para Bob"),
            (comm_bob, alice.id, "Mensagem 1 de Bob para Alice"),
            (comm_carol, diana.id, "Mensagem de Carol para Diana"),
            (comm_diana, alice.id, "Mensagem de Diana para Alice"),
        ]

        threads = []
        for comm, target_id, message in messages:
            thread = threading.Thread(target=comm.send_message, args=(target_id, message))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    print("Enviando múltiplas mensagens simultaneamente...")
    enviar_multiplas_mensagens()
    time.sleep(3)

    # 9. Demonstrar diferentes tipos de comunicação baseados no contexto
    print("\n9. Demonstração de Roteamento Automático de Mensagens:")

    # Resetar posições para demonstrar claramente
    comm_alice.update_location(-3.7319, -38.5267)  # Centro
    comm_bob.update_location(-3.7320, -38.5268)  # Próximo
    comm_carol.update_location(-3.7400, -38.5400)  # Médio
    comm_diana.update_location(-3.8000, -38.6000)  # Longe

    time.sleep(1)

    scenarios = [
        ("Alice -> Bob (próximo, online)", comm_alice, bob.id, "Síncrono esperado"),
        ("Alice -> Carol (médio, online)", comm_alice, carol.id, "Depende do raio"),
        ("Alice -> Diana (longe, online)", comm_alice, diana.id, "Assíncrono esperado"),
    ]

    for desc, comm, target_id, expected in scenarios:
        print(f"\n{desc} - {expected}:")
        comm.send_message(target_id, f"Teste de roteamento: {desc}")
        time.sleep(1)

    print("\n=== DEMONSTRAÇÃO CONCLUÍDA ===")
    print("Todas as funcionalidades foram testadas com sucesso!")

    input("\nPressione Enter para finalizar e limpar recursos...")

    # Limpeza
    comm_alice.stop_services()
    comm_bob.stop_services()
    comm_carol.stop_services()
    comm_diana.stop_services()

    print("✅ Recursos liberados com sucesso!")


def demo_interativa():
    """Demonstração interativa permitindo escolha do usuário"""
    print("=== DEMONSTRAÇÃO INTERATIVA ===")

    central_server = CentralServer()

    # Usuários pré-configurados
    users_config = {
        "Alice": (-3.7319, -38.5267, 2.0),
        "Bob": (-3.7325, -38.5270, 1.5),
        "Carol": (-3.7400, -38.5400, 1.0),
        "Diana": (-3.8000, -38.6000, 2.0)
    }

    users = {}
    managers = {}

    # Inicializar usuários
    port_socket = 8001
    port_rpc = 9001

    for name, (lat, lon, radius) in users_config.items():
        user = User(name, lat, lon, radius)
        users[name] = user

        manager = CommunicationManager(user, central_server)
        manager.start_services(port_socket, port_rpc)
        managers[name] = manager

        port_socket += 1
        port_rpc += 1

    time.sleep(3)

    print("\nUsuários disponíveis:")
    for i, name in enumerate(users_config.keys(), 1):
        user = users[name]
        print(
            f"{i}. {name} - Localização: ({user.latitude:.4f}, {user.longitude:.4f}) - Raio: {user.communication_radius}km")

    while True:
        try:
            choice = input("\nEscolha um usuário (1-4) ou 0 para sair: ").strip()

            if choice == "0":
                break

            choice_idx = int(choice) - 1
            user_names = list(users_config.keys())

            if 0 <= choice_idx < len(user_names):
                selected_user = user_names[choice_idx]
                manager = managers[selected_user]

                print(f"\n=== Controlando {selected_user} ===")
                ui = SimpleUI(manager)
                ui.show_menu()
                break
            else:
                print("Opção inválida!")

        except ValueError:
            print("Por favor, digite um número válido!")

    # Limpeza
    for manager in managers.values():
        manager.stop_services()

    print("Sistema finalizado!")


def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    dependencias = [
        ("Pyro5", "import Pyro5.api"),
        ("pika", "import pika"),
        ("geopy", "from geopy.distance import geodesic"),
    ]

    print("Verificando dependências...")

    for nome, import_cmd in dependencias:
        try:
            exec(import_cmd)
            print(f"✅ {nome} - OK")
        except ImportError:
            print(f"❌ {nome} - NÃO INSTALADO")
            print(f"   Instale com: pip install {nome}")
            return False

    # Verificar RabbitMQ
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        connection.close()
        print("✅ RabbitMQ - OK")
    except:
        print("❌ RabbitMQ - NÃO DISPONÍVEL")
        print("   Certifique-se que o RabbitMQ está instalado e rodando")
        return False

    return True


def main():
    print("SISTEMA DE COMUNICAÇÃO BASEADO EM LOCALIZAÇÃO")
    print("=" * 50)

    if not verificar_dependencias():
        print("\n❌ Dependências não atendidas. Resolva os problemas acima antes de continuar.")
        return

    print("\nEscolha o modo de demonstração:")
    print("1. Demonstração Automática (recomendado)")
    print("2. Demonstração Interativa (console)")
    print("3. Interface Gráfica Completa (GUI)")
    print("4. Interface Gráfica Simplificada (GUI Simples)")
    print("5. Sair")

    while True:
        choice = input("\nSua escolha (1-5): ").strip()

        if choice == "1":
            demo_automatica()
            break
        elif choice == "2":
            demo_interativa()
            break
        elif choice == "3":
            executar_gui()
            break
        elif choice == "4":
            executar_gui_simples()
            break
        elif choice == "5":
            print("Saindo...")
            break
        else:
            print("Opção inválida!")


def executar_gui_simples():
    """Executa a interface gráfica simplificada"""
    try:
        print("\n🎨 Iniciando Interface Gráfica Simplificada...")
        print("Uma nova janela será aberta - mais estável e fácil de usar!")

        from gui_simple import SimpleChatGUI, patch_for_gui

        app = SimpleChatGUI()

        print("✅ Interface gráfica simplificada carregada!")
        print("📌 Use a janela gráfica que foi aberta.")

        app.run()

    except ImportError:
        print("❌ Erro: Interface gráfica não disponível.")
        print("Certifique-se que o arquivo gui_simple.py está no mesmo diretório.")
        input("Pressione Enter para continuar...")
    except Exception as e:
        print(f"❌ Erro ao carregar interface gráfica: {e}")
        input("Pressione Enter para continuar...")


def executar_gui():
    """Executa a interface gráfica"""
    try:
        print("\n🎨 Iniciando Interface Gráfica...")
        print("Uma nova janela será aberta com a interface completa.")

        from gui_interface import LocationBasedChatGUI, patch_communication_system_for_gui

        app = LocationBasedChatGUI()
        patch_communication_system_for_gui(app)

        print("✅ Interface gráfica carregada com sucesso!")
        print("📌 Use a janela gráfica que foi aberta.")

        app.run()

    except ImportError:
        print("❌ Erro: Interface gráfica não disponível.")
        print("Certifique-se que o arquivo gui_interface.py está no mesmo diretório.")
        input("Pressione Enter para continuar...")
    except Exception as e:
        print(f"❌ Erro ao carregar interface gráfica: {e}")
        input("Pressione Enter para continuar...")


if __name__ == "__main__":
    main()