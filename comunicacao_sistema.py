# comunicacao_sistema.py
# Versão corrigida do Sistema de Comunicação Baseado em Localização

import json
import socket
import threading
import time
import math
from datetime import datetime
from geopy.distance import geodesic
from typing import Dict, List, Tuple, Optional, Callable
import uuid
import queue


class User:
    def __init__(self, name: str, latitude: float, longitude: float,
                 communication_radius: float = 1.0):
        self.id = str(uuid.uuid4())
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.communication_radius = communication_radius
        self.status = "offline"
        self.contacts = []
        self.socket_port = None
        self.rpc_port = None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'communication_radius': self.communication_radius,
            'status': self.status,
            'contacts': self.contacts,
            'socket_port': self.socket_port,
            'rpc_port': self.rpc_port
        }

    def update_location(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

    def update_radius(self, radius: float):
        self.communication_radius = radius

    def set_status(self, status: str):
        self.status = status

    def add_contact(self, user_id: str):
        if user_id not in self.contacts:
            self.contacts.append(user_id)

    def distance_to(self, other_user) -> float:
        return geodesic(
            (self.latitude, self.longitude),
            (other_user.latitude, other_user.longitude)
        ).kilometers

    def is_in_communication_range(self, other_user) -> bool:
        distance = self.distance_to(other_user)
        return distance <= self.communication_radius


class CentralServer:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.lock = threading.Lock()

    def register_user(self, user: User) -> bool:
        with self.lock:
            if user.id not in self.users:
                self.users[user.id] = user
                self._update_contacts_for_all()
                return True
            return False

    def update_user_location(self, user_id: str, latitude: float, longitude: float):
        with self.lock:
            if user_id in self.users:
                self.users[user_id].update_location(latitude, longitude)
                self._update_contacts_for_all()

    def update_user_status(self, user_id: str, status: str):
        with self.lock:
            if user_id in self.users:
                self.users[user_id].set_status(status)

    def update_user_radius(self, user_id: str, radius: float):
        with self.lock:
            if user_id in self.users:
                self.users[user_id].update_radius(radius)
                self._update_contacts_for_all()

    def get_user(self, user_id: str) -> Optional[User]:
        with self.lock:
            return self.users.get(user_id)

    def get_all_users(self) -> Dict[str, User]:
        with self.lock:
            return self.users.copy()

    def _update_contacts_for_all(self):
        user_list = list(self.users.values())
        for user in user_list:
            new_contacts = []
            for other_user in user_list:
                if user.id != other_user.id and user.is_in_communication_range(other_user):
                    new_contacts.append(other_user.id)
            user.contacts = new_contacts


class SocketCommunicationServer:
    def __init__(self, user: User, central_server: CentralServer):
        self.user = user
        self.central_server = central_server
        self.server_socket = None
        self.running = False
        self.message_handler = None  # Handler para mensagens recebidas

    def set_message_handler(self, handler: Callable):
        """Define handler para processar mensagens recebidas"""
        self.message_handler = handler

    def start_server(self, port: int):
        self.user.socket_port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('localhost', port))
        self.server_socket.listen(5)
        self.running = True

        thread = threading.Thread(target=self._accept_connections)
        thread.daemon = True
        thread.start()

        print(f"Servidor socket iniciado na porta {port} para {self.user.name}")

    def _accept_connections(self):
        while self.running:
            try:
                if self.server_socket:
                    client_socket, address = self.server_socket.accept()
                    thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket,)
                    )
                    thread.daemon = True
                    thread.start()
            except:
                break

    def _handle_client(self, client_socket):
        try:
            data = client_socket.recv(1024).decode('utf-8')
            message_data = json.loads(data)

            response = {
                'status': 'received',
                'timestamp': datetime.now().isoformat(),
                'recipient': self.user.name,
                'message': message_data.get('message', '')
            }

            # Chamar handler personalizado se definido
            if self.message_handler:
                self.message_handler(
                    message_data.get('sender', 'Desconhecido'),
                    message_data.get('message', ''),
                    'socket'
                )
            else:
                # Fallback para console
                print(f"\n[MENSAGEM SÍNCRONA] {message_data.get('sender', 'Desconhecido')} -> {self.user.name}")
                print(f"Conteúdo: {message_data.get('message', '')}")

            client_socket.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            print(f"Erro ao processar mensagem socket: {e}")
        finally:
            client_socket.close()

    def send_message(self, target_user_id: str, message: str) -> bool:
        target_user = self.central_server.get_user(target_user_id)
        if not target_user or target_user.socket_port is None:
            return False

        if (target_user.status != "online" or
                not self.user.is_in_communication_range(target_user)):
            return False

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)  # Timeout de 5 segundos
            client_socket.connect(('localhost', target_user.socket_port))

            message_data = {
                'sender': self.user.name,
                'sender_id': self.user.id,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'type': 'synchronous'
            }

            client_socket.send(json.dumps(message_data).encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')
            client_socket.close()

            print(f"Mensagem socket enviada com sucesso para {target_user.name}")
            return True

        except Exception as e:
            print(f"Erro ao enviar mensagem socket: {e}")
            return False

    def stop_server(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass


import Pyro5.api


@Pyro5.api.expose
class RPCCommunicationService:
    def __init__(self, user: User, central_server: CentralServer):
        self.user = user
        self.central_server = central_server
        self.message_handler = None

    def set_message_handler(self, handler: Callable):
        """Define handler para processar mensagens recebidas"""
        self.message_handler = handler

    def send_synchronous_message(self, sender_id: str, message: str):
        sender = self.central_server.get_user(sender_id)
        if not sender:
            return {'status': 'error', 'message': 'Sender not found'}

        if (self.user.status == "online" and
                sender.is_in_communication_range(self.user)):

            # Chamar handler personalizado se definido
            if self.message_handler:
                self.message_handler(sender.name, message, 'rpc')
            else:
                # Fallback para console
                print(f"\n[MENSAGEM RPC] {sender.name} -> {self.user.name}")
                print(f"Conteúdo: {message}")

            return {
                'status': 'delivered',
                'timestamp': datetime.now().isoformat(),
                'recipient': self.user.name
            }
        else:
            return {
                'status': 'failed',
                'message': 'User offline or out of range'
            }

    def get_user_status(self):
        return {
            'name': self.user.name,
            'status': self.user.status,
            'location': (self.user.latitude, self.user.longitude)
        }


class RPCClient:
    def __init__(self, user: User, central_server: CentralServer):
        self.user = user
        self.central_server = central_server

    def send_message_to_user(self, target_user_id: str, message: str) -> bool:
        target_user = self.central_server.get_user(target_user_id)
        if not target_user or not target_user.rpc_port:
            return False

        if (target_user.status != "online" or
                not self.user.is_in_communication_range(target_user)):
            return False

        try:
            uri = f"PYRO:rpc_service@localhost:{target_user.rpc_port}"
            rpc_service = Pyro5.api.Proxy(uri)
            rpc_service._pyroTimeout = 5  # Timeout de 5 segundos

            result = rpc_service.send_synchronous_message(self.user.id, message)

            if result['status'] == 'delivered':
                print(f"Mensagem RPC enviada com sucesso para {target_user.name}")
                return True
            else:
                print(f"Falha ao entregar mensagem RPC: {result.get('message', '')}")
                return False

        except Exception as e:
            print(f"Erro na comunicação RPC: {e}")
            return False


import pika


class MOMCommunication:
    def __init__(self, user: User, central_server: CentralServer):
        self.user = user
        self.central_server = central_server
        self.connection = None
        self.channel = None
        self.consuming = False
        self.message_handler = None
        self.consume_thread = None

    def set_message_handler(self, handler: Callable):
        """Define handler para processar mensagens recebidas"""
        self.message_handler = handler

    def connect(self):
        try:
            # Tentar reconectar se a conexão estiver fechada
            if self.connection and not self.connection.is_closed:
                return True

            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost', heartbeat=600, blocked_connection_timeout=300)
            )
            self.channel = self.connection.channel()

            queue_name = f"user_{self.user.id}"
            self.channel.queue_declare(queue=queue_name, durable=True)

            return True
        except Exception as e:
            print(f"Erro ao conectar com RabbitMQ: {e}")
            return False

    def send_async_message(self, target_user_id: str, message: str) -> bool:
        try:
            if not self.channel or not self.connection or self.connection.is_closed:
                if not self.connect():
                    return False

            target_user = self.central_server.get_user(target_user_id)
            if not target_user:
                return False

            message_data = {
                'sender': self.user.name,
                'sender_id': self.user.id,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'type': 'asynchronous'
            }

            queue_name = f"user_{target_user_id}"
            self.channel.queue_declare(queue=queue_name, durable=True)

            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message_data),
                properties=pika.BasicProperties(delivery_mode=2)
            )

            print(f"Mensagem assíncrona enviada para {target_user.name}")
            return True

        except Exception as e:
            print(f"Erro ao enviar mensagem assíncrona: {e}")
            try:
                if self.connect():
                    return self.send_async_message(target_user_id, message)
            except:
                pass
            return False

    def start_consuming(self):
        if not self.connect():
            return

        queue_name = f"user_{self.user.id}"

        def callback(ch, method, properties, body):
            try:
                message_data = json.loads(body.decode('utf-8'))

                # Chamar handler personalizado se definido
                if self.message_handler:
                    self.message_handler(
                        message_data.get('sender', 'Desconhecido'),
                        message_data.get('message', ''),
                        'async'
                    )
                else:
                    # Fallback para console
                    print(f"\n[MENSAGEM ASSÍNCRONA] {message_data.get('sender', 'Desconhecido')} -> {self.user.name}")
                    print(f"Conteúdo: {message_data.get('message', '')}")
                    print(f"Enviada em: {message_data.get('timestamp', '')}")

                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Erro ao processar mensagem assíncrona: {e}")
                # Rejeitar mensagem em caso de erro para evitar loop infinito
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback
        )

        self.consuming = True

        def consume_loop():
            while self.consuming and self.connection and not self.connection.is_closed:
                try:
                    self.connection.process_data_events(time_limit=1)
                except Exception as e:
                    print(f"Erro no loop de consumo: {e}")
                    break

        self.consume_thread = threading.Thread(target=consume_loop)
        self.consume_thread.daemon = True
        self.consume_thread.start()

        print(f"Iniciado consumo de mensagens assíncronas para {self.user.name}")

    def stop_consuming(self):
        self.consuming = False
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except:
            pass


class CommunicationManager:
    def __init__(self, user: User, central_server: CentralServer):
        self.user = user
        self.central_server = central_server
        self.socket_comm = SocketCommunicationServer(user, central_server)
        self.rpc_client = RPCClient(user, central_server)
        self.rpc_service = None
        self.mom_comm = MOMCommunication(user, central_server)
        self.rpc_daemon = None
        self.message_handlers = []  # Lista de handlers para mensagens recebidas

    def add_message_handler(self, handler: Callable):
        """Adiciona handler para mensagens recebidas"""
        self.message_handlers.append(handler)

    def _handle_received_message(self, sender: str, message: str, msg_type: str):
        """Processa mensagem recebida e chama todos os handlers"""
        for handler in self.message_handlers:
            try:
                handler(sender, message, msg_type)
            except Exception as e:
                print(f"Erro em message handler: {e}")

    def start_services(self, socket_port: int, rpc_port: int):
        # Configurar handlers para todos os tipos de comunicação
        self.socket_comm.set_message_handler(self._handle_received_message)
        self.mom_comm.set_message_handler(self._handle_received_message)

        # Iniciar servidor socket
        self.socket_comm.start_server(socket_port)

        # Iniciar serviço RPC
        self._start_rpc_service(rpc_port)

        # Conectar com MOM e iniciar consumo
        if self.mom_comm.connect():
            self.mom_comm.start_consuming()

        # Registrar usuário no servidor central
        self.central_server.register_user(self.user)

        # Marcar como online
        self.user.set_status("online")
        self.central_server.update_user_status(self.user.id, "online")

        print(f"\nServiços iniciados para {self.user.name}")
        print(f"Socket: porta {socket_port}")
        print(f"RPC: porta {rpc_port}")

    def _start_rpc_service(self, port: int):
        self.user.rpc_port = port

        def run_rpc_server():
            try:
                daemon = Pyro5.api.Daemon(host="localhost", port=port)
                self.rpc_service = RPCCommunicationService(self.user, self.central_server)
                self.rpc_service.set_message_handler(self._handle_received_message)
                uri = daemon.register(self.rpc_service, "rpc_service")

                print(f"Serviço RPC registrado: {uri}")
                daemon.requestLoop()
            except Exception as e:
                print(f"Erro no servidor RPC: {e}")

        thread = threading.Thread(target=run_rpc_server)
        thread.daemon = True
        thread.start()

    def send_message(self, target_user_id: str, message: str):
        target_user = self.central_server.get_user(target_user_id)
        if not target_user:
            print("Usuário de destino não encontrado")
            return

        # Verificar se deve usar comunicação síncrona ou assíncrona
        if (target_user.status == "online" and
                self.user.is_in_communication_range(target_user)):

            # Tentar socket primeiro, depois RPC
            success = self.socket_comm.send_message(target_user_id, message)
            if not success:
                success = self.rpc_client.send_message_to_user(target_user_id, message)

            if not success:
                print("Falha na comunicação síncrona, enviando assíncrona")
                self.mom_comm.send_async_message(target_user_id, message)
        else:
            # Comunicação assíncrona
            print("Usuário offline ou fora de alcance, enviando mensagem assíncrona")
            self.mom_comm.send_async_message(target_user_id, message)

    def update_location(self, latitude: float, longitude: float):
        self.user.update_location(latitude, longitude)
        self.central_server.update_user_location(self.user.id, latitude, longitude)
        print(f"Localização atualizada: ({latitude}, {longitude})")

    def update_radius(self, radius: float):
        self.user.update_radius(radius)
        self.central_server.update_user_radius(self.user.id, radius)
        print(f"Raio de comunicação atualizado: {radius} km")

    def get_contacts_info(self):
        contacts_info = []
        for contact_id in self.user.contacts:
            contact = self.central_server.get_user(contact_id)
            if contact:
                distance = self.user.distance_to(contact)
                contacts_info.append({
                    'name': contact.name,
                    'id': contact.id,
                    'status': contact.status,
                    'distance': round(distance, 2),
                    'in_range': self.user.is_in_communication_range(contact)
                })
        return contacts_info

    def stop_services(self):
        self.user.set_status("offline")
        self.central_server.update_user_status(self.user.id, "offline")
        self.socket_comm.stop_server()
        self.mom_comm.stop_consuming()


# Interface de usuário simples (mesma do original)
class SimpleUI:
    def __init__(self, communication_manager: CommunicationManager):
        self.comm_manager = communication_manager

    def show_menu(self):
        while True:
            print(f"\n=== {self.comm_manager.user.name} ===")
            print("1. Enviar mensagem")
            print("2. Ver contatos")
            print("3. Atualizar localização")
            print("4. Atualizar raio de comunicação")
            print("5. Ver informações do usuário")
            print("0. Sair")

            choice = input("Escolha uma opção: ").strip()

            if choice == "1":
                self._send_message_interface()
            elif choice == "2":
                self._show_contacts()
            elif choice == "3":
                self._update_location_interface()
            elif choice == "4":
                self._update_radius_interface()
            elif choice == "5":
                self._show_user_info()
            elif choice == "0":
                self.comm_manager.stop_services()
                break
            else:
                print("Opção inválida!")

    def _send_message_interface(self):
        contacts = self.comm_manager.get_contacts_info()
        if not contacts:
            print("Nenhum contato disponível")
            return

        print("\nContatos disponíveis:")
        for i, contact in enumerate(contacts):
            status_icon = "🟢" if contact['status'] == 'online' else "🔴"
            range_icon = "📡" if contact['in_range'] else "📵"
            print(f"{i + 1}. {contact['name']} {status_icon} {range_icon} ({contact['distance']} km)")

        try:
            choice = int(input("Selecione um contato (número): ")) - 1
            if 0 <= choice < len(contacts):
                target_contact = contacts[choice]
                message = input("Digite sua mensagem: ")
                self.comm_manager.send_message(target_contact['id'], message)
            else:
                print("Contato inválido!")
        except ValueError:
            print("Entrada inválida!")

    def _show_contacts(self):
        contacts = self.comm_manager.get_contacts_info()
        if not contacts:
            print("Nenhum contato no alcance")
            return

        print("\n=== CONTATOS ===")
        for contact in contacts:
            status = "ONLINE" if contact['status'] == 'online' else "OFFLINE"
            in_range = "Dentro do alcance" if contact['in_range'] else "Fora do alcance"
            print(f"• {contact['name']} - {status} - {contact['distance']} km - {in_range}")

    def _update_location_interface(self):
        try:
            lat = float(input("Nova latitude: "))
            lon = float(input("Nova longitude: "))
            self.comm_manager.update_location(lat, lon)
        except ValueError:
            print("Coordenadas inválidas!")

    def _update_radius_interface(self):
        try:
            radius = float(input("Novo raio de comunicação (km): "))
            if radius > 0:
                self.comm_manager.update_radius(radius)
            else:
                print("Raio deve ser maior que zero!")
        except ValueError:
            print("Valor inválido!")

    def _show_user_info(self):
        user = self.comm_manager.user
        print(f"\n=== INFORMAÇÕES DO USUÁRIO ===")
        print(f"Nome: {user.name}")
        print(f"Status: {user.status}")
        print(f"Localização: ({user.latitude}, {user.longitude})")
        print(f"Raio de comunicação: {user.communication_radius} km")
        print(f"Número de contatos: {len(user.contacts)}")


def main():
    # Servidor central compartilhado
    central_server = CentralServer()

    print("=== SISTEMA DE COMUNICAÇÃO BASEADO EM LOCALIZAÇÃO (CORRIGIDO) ===")
    print("Criando usuários de exemplo...")

    # Criar usuários de exemplo
    user1 = User("Alice", -3.7319, -38.5267, 2.0)  # Fortaleza
    user2 = User("Bob", -3.7350, -38.5200, 1.5)  # Próximo a Alice
    user3 = User("Carol", -3.8000, -38.6000, 1.0)  # Mais distante

    # Criar gerenciadores de comunicação
    comm_manager1 = CommunicationManager(user1, central_server)
    comm_manager2 = CommunicationManager(user2, central_server)
    comm_manager3 = CommunicationManager(user3, central_server)

    # Iniciar serviços
    comm_manager1.start_services(8001, 9001)
    comm_manager2.start_services(8002, 9002)
    comm_manager3.start_services(8003, 9003)

    # Aguardar inicialização
    time.sleep(2)

    print("\nSistema iniciado! Usuários:")
    print("1. Alice (Fortaleza: -3.7319, -38.5267)")
    print("2. Bob (Próximo: -3.7350, -38.5200)")
    print("3. Carol (Distante: -3.8000, -38.6000)")

    # Interface interativa
    print("\nEscolha um usuário para interagir:")
    print("1 - Alice")
    print("2 - Bob")
    print("3 - Carol")

    choice = input("Escolha (1-3): ").strip()

    if choice == "1":
        ui = SimpleUI(comm_manager1)
    elif choice == "2":
        ui = SimpleUI(comm_manager2)
    elif choice == "3":
        ui = SimpleUI(comm_manager3)
    else:
        print("Escolha inválida!")
        return

    ui.show_menu()


if __name__ == "__main__":
    main()