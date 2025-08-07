# gui_interface.py
# Interface Gráfica CORRIGIDA para o Sistema de Comunicação Baseado em Localização

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
import time
from datetime import datetime
from comunicacao_sistema import *


class LauncherGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema de Comunicação Baseada em Localização")
        self.root.geometry("800x500")
        self.central_server = CentralServer()
        self.users = {}
        self.managers = {}
        self.setup_main_window()

    def setup_main_window(self):
        frame = tk.Frame(self.root, bg="#2c3e50")
        frame.pack(fill=tk.BOTH, expand=True)
        title = ttk.Label(frame, text="🌍 Sistema de Comunicação Baseada em Localização",
                          font=('Arial', 16, 'bold'), background="#2c3e50", foreground="#ecf0f1")
        title.pack(pady=(40, 20))
        ttk.Button(frame, text="🆕 Criar Novo Usuário", command=self.create_new_user).pack(pady=10)
        ttk.Button(frame, text="👥 Selecionar Usuário Existente", command=self.select_existing_user).pack(pady=10)
        ttk.Button(frame, text="🎮 Demo com Usuários Pré-configurados", command=self.setup_demo_users).pack(pady=10)
        ttk.Button(frame, text="❌ Sair", command=self.root.quit).pack(pady=10)

    def create_new_user(self):
        dialog = UserCreationDialog(self.root)
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            name, lat, lon, radius = dialog.result
            if any(u.name == name for u in self.users.values()):
                messagebox.showerror("Erro", f"Usuário '{name}' já existe!")
                return
            user = User(name, lat, lon, radius)
            self.users[user.id] = user
            comm_manager = CommunicationManager(user, self.central_server)
            port_socket = 8001 + len(self.managers)
            port_rpc = 9001 + len(self.managers)
            comm_manager.start_services(port_socket, port_rpc)
            self.managers[user.id] = comm_manager
            self.open_user_window(user)

    def select_existing_user(self):
        if not self.users:
            messagebox.showinfo("Info", "Nenhum usuário criado ainda.")
            return
        dialog = UserSelectionDialog(self.root, list(self.users.values()))
        self.root.wait_window(dialog.dialog)
        if dialog.selected_user:
            self.open_user_window(dialog.selected_user)

    def setup_demo_users(self):
        demo_users_config = {
            "Alice": (-3.7319, -38.5267, 2.0),
            "Bob": (-3.7325, -38.5270, 1.5),
            "Carol": (-3.7400, -38.5400, 3.0),
            "Diana": (-3.8000, -38.6000, 2.0)
        }
        for name, (lat, lon, radius) in demo_users_config.items():
            if name not in [u.name for u in self.users.values()]:
                user = User(name, lat, lon, radius)
                self.users[user.id] = user
                comm_manager = CommunicationManager(user, self.central_server)
                port_socket = 8001 + len(self.managers)
                port_rpc = 9001 + len(self.managers)
                comm_manager.start_services(port_socket, port_rpc)
                self.managers[user.id] = comm_manager
        time.sleep(2)
        for user in self.users.values():
            self.open_user_window(user)

    def open_user_window(self, user):
        comm_manager = self.managers[user.id]
        UserChatWindow(self.root, user, comm_manager)

    def run(self):
        self.root.mainloop()


class UserChatWindow:
    def __init__(self, parent, user, comm_manager):
        self.current_user = user
        self.comm_manager = comm_manager
        # Garante que ao abrir, se usuário está online, começa consumir MOM
        if self.current_user.status == "online" and hasattr(self.comm_manager, "mom_comm"):
            try:
                self.comm_manager.mom_comm.start_consuming()
            except Exception as e:
                print(f"Erro ao iniciar consumo MOM: {e}")
        self.root = tk.Toplevel(parent)
        self.root.title(f"Chat - {user.name}")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2c3e50')
        self.setup_chat_window()

        # CORREÇÃO PRINCIPAL: Registrar handler para mensagens recebidas
        self.comm_manager.add_message_handler(self._handle_received_message)

    def _handle_received_message(self, sender: str, message: str, msg_type: str):
        """Handler para processar mensagens recebidas - THREAD SAFE"""

        def update_gui():
            type_map = {
                'socket': 'received',
                'rpc': 'received',
                'async': 'received'
            }
            gui_msg_type = type_map.get(msg_type, 'received')
            suffix = " (Assíncrona)" if msg_type == 'async' else ""
            self.add_message_to_chat(f"{message}{suffix}", sender, gui_msg_type)

        # Executar na thread da GUI
        self.root.after(0, update_gui)

    def setup_chat_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.create_header(main_frame)
        content_frame = tk.Frame(main_frame, bg='#2c3e50')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.create_chat_area(content_frame)
        self.create_control_panel(content_frame)
        self.start_updates()

    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg='#34495e', relief=tk.RAISED, bd=2)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        info_frame = tk.Frame(header_frame, bg='#34495e')
        info_frame.pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Label(info_frame, text=f"👤 {self.current_user.name}",
                  font=('Arial', 14, 'bold'), background='#34495e', foreground='#e74c3c').pack(anchor=tk.W)
        location_text = f"📍 ({self.current_user.latitude:.4f}, {self.current_user.longitude:.4f})"
        ttk.Label(info_frame, text=location_text, background='#34495e', foreground='#ecf0f1').pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"📡 Raio: {self.current_user.communication_radius} km",
                  background='#34495e', foreground='#ecf0f1').pack(anchor=tk.W)
        status_color = '#27ae60' if self.current_user.status == 'online' else '#e74c3c'
        ttk.Label(info_frame, text=f"🔴 Status: {self.current_user.status.upper()}",
                  background='#34495e', foreground=status_color).pack(anchor=tk.W)

        # Botões do header
        btn_frame = tk.Frame(header_frame, bg='#34495e')
        btn_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        ttk.Button(btn_frame, text="📍 Atualizar Localização",
                   command=self.update_location).pack(pady=2)
        ttk.Button(btn_frame, text="📡 Atualizar Raio",
                   command=self.update_radius).pack(pady=2)
        ttk.Button(btn_frame, text="🔴 Trocar Status", command=self.toggle_status).pack(pady=2)

    def create_chat_area(self, parent):
        chat_frame = tk.Frame(parent, bg='#34495e', relief=tk.RAISED, bd=2)
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        ttk.Label(chat_frame, text="💬 Chat",
                  font=('Arial', 12, 'bold'), background='#34495e', foreground='#ecf0f1').pack(pady=10)
        self.chat_area = scrolledtext.ScrolledText(
            chat_frame, height=20, width=50, bg='#ecf0f1', fg='#2c3e50',
            font=('Consolas', 10), wrap=tk.WORD, state=tk.DISABLED
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        input_frame = tk.Frame(chat_frame, bg='#34495e')
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.message_entry = tk.Entry(
            input_frame, font=('Arial', 11), bg='#ecf0f1', fg='#2c3e50'
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', self.send_message_event)
        ttk.Button(input_frame, text="Enviar", command=self.send_message).pack(side=tk.RIGHT)

    def create_control_panel(self, parent):
        control_frame = tk.Frame(parent, bg='#34495e', relief=tk.RAISED, bd=2)
        control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        ttk.Label(control_frame, text="👥 Contatos",
                  font=('Arial', 12, 'bold'), background='#34495e', foreground='#ecf0f1').pack(pady=10)
        contacts_frame = tk.Frame(control_frame, bg='#34495e')
        contacts_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        self.contacts_listbox = tk.Listbox(
            contacts_frame, height=12, font=('Arial', 10), bg='#ecf0f1',
            fg='#2c3e50', selectbackground='#3498db'
        )
        self.contacts_listbox.pack(fill=tk.BOTH, expand=True)
        self.contacts_listbox.bind('<Double-Button-1>', self.select_contact_for_message)
        self.contacts_listbox.bind('<ButtonRelease-1>', self.on_contact_select)
        contact_info_frame = tk.Frame(control_frame, bg='#34495e')
        contact_info_frame.pack(fill=tk.X, padx=10, pady=10)
        self.contact_info_label = tk.Label(
            contact_info_frame, text="Selecione um contato", bg='#34495e',
            fg='#ecf0f1', font=('Arial', 9), wraplength=200, justify=tk.LEFT
        )
        self.contact_info_label.pack()
        ttk.Label(control_frame, text="⚡ Ações Rápidas",
                  font=('Arial', 12, 'bold'), background='#34495e', foreground='#ecf0f1').pack(pady=(20, 10))
        actions_frame = tk.Frame(control_frame, bg='#34495e')
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(actions_frame, text="🔄 Atualizar Contatos",
                   command=self.update_contacts).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="📊 Ver Estatísticas",
                   command=self.show_statistics).pack(fill=tk.X, pady=2)
        ttk.Button(actions_frame, text="🧪 Enviar Teste",
                   command=self.send_test_messages).pack(fill=tk.X, pady=2)

    def send_message_event(self, event):
        self.send_message()

    def send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return
        selection = self.contacts_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um contato primeiro!")
            return
        selected_index = selection[0]
        contacts = self.comm_manager.get_contacts_info()
        if selected_index < len(contacts):
            contact = contacts[selected_index]
            self.add_message_to_chat(
                f"{message}",
                f"Você ➜ {contact['name']}",
                "sent"
            )
            self.message_entry.delete(0, tk.END)
            threading.Thread(
                target=self.comm_manager.send_message,
                args=(contact['id'], message),
                daemon=True
            ).start()
        else:
            messagebox.showerror("Erro", "Contato inválido!")

    def select_contact_for_message(self, event):
        self.message_entry.focus()

    def on_contact_select(self, event):
        self.update_contact_info()

    def update_contacts(self):
        if not self.contacts_listbox.winfo_exists():
            return
        selection = self.contacts_listbox.curselection()
        selected_contact_name = None
        if selection:
            selected_index = selection[0]
            contacts = self.comm_manager.get_contacts_info()
            if selected_index < len(contacts):
                selected_contact_name = contacts[selected_index]['name']
        contacts = self.comm_manager.get_contacts_info()
        self.contacts_listbox.delete(0, tk.END)
        for contact in contacts:
            status_icon = "🟢" if contact['status'] == 'online' else "🔴"
            range_icon = "📡" if contact['in_range'] else "📵"
            display_text = f"{status_icon} {contact['name']} {range_icon} ({contact['distance']:.2f}km)"
            self.contacts_listbox.insert(tk.END, display_text)
        if selected_contact_name:
            for idx, contact in enumerate(contacts):
                if contact['name'] == selected_contact_name:
                    self.contacts_listbox.select_set(idx)
                    self.contacts_listbox.event_generate('<<ListboxSelect>>')
                    break

    def update_contact_info(self):
        if not self.contacts_listbox.winfo_exists():
            return
        selection = self.contacts_listbox.curselection()
        if not selection:
            self.contact_info_label.config(text="Selecione um contato")
            return
        contacts = self.comm_manager.get_contacts_info()
        selected_index = selection[0]
        if selected_index < len(contacts):
            contact = contacts[selected_index]
            info_text = f"""Nome: {contact['name']}
Status: {contact['status'].upper()}
Distância: {contact['distance']:.2f} km
No alcance: {'Sim' if contact['in_range'] else 'Não'}
Tipo de comunicação: {'Síncrona' if contact['status'] == 'online' and contact['in_range'] else 'Assíncrona'}"""
            self.contact_info_label.config(text=info_text)
        else:
            self.contact_info_label.config(text="Contato inválido")

    def add_message_to_chat(self, message, sender="Sistema", msg_type="info"):
        # Verificar se a janela ainda existe
        if not self.chat_area.winfo_exists():
            return

        # Evitar duplicar mensagens do próprio usuário
        if msg_type == "received" and sender == self.current_user.name:
            return

        self.chat_area.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "sent": "#2980b9", "received": "#27ae60", "system": "#f39c12",
            "error": "#e74c3c", "info": "#8e44ad"
        }
        prefix_map = {"sent": "➤", "received": "⬅", "system": "ℹ", "error": "⚠", "info": "📢"}
        prefix = prefix_map.get(msg_type, "•")
        color = colors.get(msg_type, "#2c3e50")
        self.chat_area.insert(tk.END, f"[{timestamp}] ")
        start_pos = self.chat_area.index(tk.INSERT)
        self.chat_area.insert(tk.END, f"{prefix} {sender}: {message}\n")
        end_pos = self.chat_area.index(tk.INSERT)
        tag_name = f"msg_{msg_type}_{timestamp}_{hash(sender + message)}"
        self.chat_area.tag_add(tag_name, start_pos, end_pos)
        self.chat_area.tag_config(tag_name, foreground=color, font=('Consolas', 10, 'bold'))
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    def show_statistics(self):
        contacts = self.comm_manager.get_contacts_info()
        online_contacts = sum(1 for c in contacts if c['status'] == 'online')
        in_range_contacts = sum(1 for c in contacts if c['in_range'])
        sync_available = sum(1 for c in contacts if c['status'] == 'online' and c['in_range'])
        stats_text = f"""📊 ESTATÍSTICAS DO USUÁRIO {self.current_user.name}

👥 Contatos totais: {len(contacts)}
🟢 Contatos online: {online_contacts}
📡 Contatos no alcance: {in_range_contacts}
⚡ Comunicação síncrona disponível: {sync_available}
📬 Comunicação assíncrona necessária: {len(contacts) - sync_available}

📍 Localização atual: ({self.current_user.latitude:.4f}, {self.current_user.longitude:.4f})
📡 Raio de comunicação: {self.current_user.communication_radius} km
🔴 Status: {self.current_user.status.upper()}"""
        messagebox.showinfo("Estatísticas", stats_text)

    def send_test_messages(self):
        def run():
            contacts = self.comm_manager.get_contacts_info()
            if not contacts:
                self.root.after(0, lambda: messagebox.showinfo("Info", "Nenhum contato disponível para teste."))
                return
            test_message = f"Mensagem de teste enviada em {datetime.now().strftime('%H:%M:%S')}"
            for contact in contacts:
                self.comm_manager.send_message(contact['id'], test_message)
                msg_type = "síncrona" if contact['status'] == 'online' and contact['in_range'] else "assíncrona"
                self.root.after(0, self.add_message_to_chat,
                                f"Teste {msg_type} para {contact['name']}",
                                "Sistema", "info")
            self.root.after(0, lambda: messagebox.showinfo("Teste Completo",
                                                           f"Mensagens de teste enviadas para {len(contacts)} contatos!"))

        threading.Thread(target=run, daemon=True).start()

    def update_location(self):
        dialog = LocationUpdateDialog(self.root, self.current_user)
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            lat, lon = dialog.result
            self.comm_manager.update_location(lat, lon)
            self.setup_chat_window()  # Recriar interface para mostrar nova localização
            self.add_message_to_chat(f"Localização atualizada para ({lat:.4f}, {lon:.4f})", "Sistema", "info")

    def update_radius(self):
        radius = simpledialog.askfloat("Atualizar Raio",
                                       "Novo raio de comunicação (km):",
                                       initialvalue=self.current_user.communication_radius,
                                       minvalue=0.1, maxvalue=50.0)
        if radius:
            self.comm_manager.update_radius(radius)
            self.setup_chat_window()  # Recriar interface para mostrar novo raio
            self.add_message_to_chat(f"Raio de comunicação atualizado para {radius} km", "Sistema", "info")

    def toggle_status(self):
        new_status = "offline" if self.current_user.status == "online" else "online"
        self.current_user.set_status(new_status)
        self.comm_manager.central_server.update_user_status(self.current_user.id, new_status)
        # >>>> INÍCIO: Reinicia o consumo da fila MOM quando voltar online
        if new_status == "online":
            try:
                if hasattr(self.comm_manager, "mom_comm"):
                    self.comm_manager.mom_comm.start_consuming()
            except Exception as e:
                print(f"Erro ao reiniciar consumo MOM: {e}")
        # <<<< FIM
        self.setup_chat_window()
        self.add_message_to_chat(
            f"Status alterado para {new_status.upper()}",
            "Sistema",
            "system"
        )

    def start_updates(self):
        def update_loop():
            while True:
                try:
                    if self.current_user and self.comm_manager and self.root.winfo_exists():
                        self.root.after(0, self.update_contacts)
                        self.root.after(0, self.update_contact_info)
                    else:
                        break
                    time.sleep(3)  # Reduzido para 3 segundos para melhor responsividade
                except Exception as e:
                    print(f"Erro no loop de atualização: {e}")
                    break

        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
        self.update_contacts()


class UserCreationDialog:
    def __init__(self, parent):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Criar Novo Usuário")
        self.dialog.geometry("500x650")
        self.dialog.configure(bg='#34495e')
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.geometry("+{}+{}".format(
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.dialog, bg='#34495e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        tk.Label(main_frame,
                 text="👤 Criar Novo Usuário",
                 font=('Arial', 14, 'bold'),
                 bg='#34495e',
                 fg='#ecf0f1').pack(pady=(0, 20))
        tk.Label(main_frame, text="Nome:", bg='#34495e', fg='#ecf0f1').pack(anchor=tk.W)
        self.name_entry = tk.Entry(main_frame, font=('Arial', 11))
        self.name_entry.pack(fill=tk.X, pady=(0, 10))
        coord_frame = tk.Frame(main_frame, bg='#34495e')
        coord_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(coord_frame,
                 text="📍 Coordenadas do Google Maps (copie e cole diretamente):",
                 bg='#34495e', fg='#e74c3c', font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        gmaps_frame = tk.Frame(coord_frame, bg='#34495e')
        gmaps_frame.pack(fill=tk.X, pady=(5, 15))
        tk.Label(gmaps_frame, text="Cole aqui (ex: -3.744207283155359, -38.53564217314052):",
                 bg='#34495e', fg='#ecf0f1').pack(anchor=tk.W)
        self.gmaps_entry = tk.Entry(gmaps_frame, font=('Arial', 11), bg='#f8f9fa')
        self.gmaps_entry.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(gmaps_frame, text="📋 Usar Coordenadas do Google Maps",
                   command=self.parse_gmaps_coordinates).pack()
        separator = tk.Frame(coord_frame, height=2, bg='#7f8c8d')
        separator.pack(fill=tk.X, pady=10)
        tk.Label(coord_frame, text="OU Digite Manualmente:",
                 bg='#34495e', fg='#f39c12', font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        manual_frame = tk.Frame(coord_frame, bg='#34495e')
        manual_frame.pack(fill=tk.X, pady=5)
        lat_frame = tk.Frame(manual_frame, bg='#34495e')
        lat_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(lat_frame, text="Latitude:", bg='#34495e', fg='#ecf0f1').pack(side=tk.LEFT)
        self.lat_entry = tk.Entry(lat_frame, font=('Arial', 11))
        self.lat_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        self.lat_entry.insert(0, "-3.7319")
        lon_frame = tk.Frame(manual_frame, bg='#34495e')
        lon_frame.pack(fill=tk.X)
        tk.Label(lon_frame, text="Longitude:", bg='#34495e', fg='#ecf0f1').pack(side=tk.LEFT)
        self.lon_entry = tk.Entry(lon_frame, font=('Arial', 11))
        self.lon_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        self.lon_entry.insert(0, "-38.5267")
        tk.Label(main_frame, text="Raio de Comunicação (km):", bg='#34495e', fg='#ecf0f1').pack(anchor=tk.W,
                                                                                                pady=(15, 0))
        self.radius_entry = tk.Entry(main_frame, font=('Arial', 11))
        self.radius_entry.pack(fill=tk.X, pady=(0, 20))
        self.radius_entry.insert(0, "2.0")
        btn_frame = tk.Frame(main_frame, bg='#34495e')
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Criar", command=self.create_user).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Cancelar", command=self.cancel).pack(side=tk.LEFT)

    def parse_gmaps_coordinates(self):
        gmaps_text = self.gmaps_entry.get().strip()
        if not gmaps_text:
            messagebox.showwarning("Aviso", "Cole as coordenadas do Google Maps primeiro!")
            return
        try:
            coords = gmaps_text.replace(' ', '').split(',')
            if len(coords) != 2:
                raise ValueError("Formato inválido")
            lat = float(coords[0])
            lon = float(coords[1])
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise ValueError("Coordenadas fora do range válido")
            self.lat_entry.delete(0, tk.END)
            self.lat_entry.insert(0, str(lat))
            self.lon_entry.delete(0, tk.END)
            self.lon_entry.insert(0, str(lon))
            messagebox.showinfo("Sucesso", f"Coordenadas aplicadas:\nLatitude: {lat}\nLongitude: {lon}")
        except ValueError as e:
            messagebox.showerror("Erro",
                                 "Formato inválido!\n\n" +
                                 "Formato esperado: latitude, longitude\n" +
                                 "Exemplo: -3.744207283155359, -38.53564217314052\n\n" +
                                 "Como copiar do Google Maps:\n" +
                                 "1. Clique com botão direito no local\n" +
                                 "2. Clique no primeiro item (coordenadas)\n" +
                                 "3. Cole aqui")

    def create_user(self):
        try:
            name = self.name_entry.get().strip()
            lat = float(self.lat_entry.get())
            lon = float(self.lon_entry.get())
            radius = float(self.radius_entry.get())
            if not name:
                messagebox.showerror("Erro", "Nome é obrigatório!")
                return
            if radius <= 0:
                messagebox.showerror("Erro", "Raio deve ser maior que zero!")
                return
            self.result = (name, lat, lon, radius)
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Erro", "Valores numéricos inválidos!")

    def cancel(self):
        self.dialog.destroy()


class UserSelectionDialog:
    def __init__(self, parent, users):
        self.selected_user = None
        self.users = users
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Selecionar Usuário")
        self.dialog.geometry("500x400")
        self.dialog.configure(bg='#34495e')
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.dialog, bg='#34495e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        tk.Label(main_frame,
                 text="👥 Selecionar Usuário Existente",
                 font=('Arial', 14, 'bold'),
                 bg='#34495e',
                 fg='#ecf0f1').pack(pady=(0, 20))
        self.users_listbox = tk.Listbox(
            main_frame,
            font=('Arial', 11),
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        self.users_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        for user in self.users:
            display_text = f"{user.name} - ({user.latitude:.4f}, {user.longitude:.4f}) - {user.communication_radius}km"
            self.users_listbox.insert(tk.END, display_text)
        btn_frame = tk.Frame(main_frame, bg='#34495e')
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Selecionar", command=self.select_user).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Cancelar", command=self.cancel).pack(side=tk.LEFT)

    def select_user(self):
        selection = self.users_listbox.curselection()
        if selection:
            self.selected_user = self.users[selection[0]]
            self.dialog.destroy()
        else:
            messagebox.showwarning("Aviso", "Selecione um usuário!")

    def cancel(self):
        self.dialog.destroy()


class LocationUpdateDialog:
    def __init__(self, parent, user):
        self.result = None
        self.user = user
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Atualizar Localização")
        self.dialog.geometry("500x500")
        self.dialog.configure(bg='#34495e')
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.create_widgets()

    def create_widgets(self):
        canvas = tk.Canvas(self.dialog, bg='#34495e', borderwidth=0, highlightthickness=0)
        scroll_y = tk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        main_frame = tk.Frame(canvas, bg='#34495e')
        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        tk.Label(main_frame,
                 text=f"📍 Atualizar Localização - {self.user.name}",
                 font=('Arial', 14, 'bold'),
                 bg='#34495e',
                 fg='#ecf0f1').pack(pady=(20, 20))

        # Localização atual
        current_frame = tk.Frame(main_frame, bg='#2c3e50', relief=tk.RAISED, bd=1)
        current_frame.pack(fill=tk.X, pady=(0, 15), padx=20)
        tk.Label(current_frame,
                 text="📍 Localização Atual:",
                 font=('Arial', 10, 'bold'),
                 bg='#2c3e50',
                 fg='#f39c12').pack(pady=5)
        current_coords = f"{self.user.latitude}, {self.user.longitude}"
        tk.Label(current_frame,
                 text=f"Coordenadas: {current_coords}",
                 bg='#2c3e50',
                 fg='#ecf0f1').pack()

        # Google Maps input
        gmaps_frame = tk.Frame(main_frame, bg='#e74c3c', relief=tk.RAISED, bd=2)
        gmaps_frame.pack(fill=tk.X, pady=(0, 15), padx=20)
        tk.Label(gmaps_frame,
                 text="🗺️ GOOGLE MAPS - Copie e Cole Diretamente",
                 font=('Arial', 11, 'bold'),
                 bg='#e74c3c',
                 fg='white').pack(pady=5)
        self.gmaps_entry = tk.Entry(gmaps_frame, font=('Arial', 12), bg='white', fg='black')
        self.gmaps_entry.pack(fill=tk.X, padx=10, pady=5)
        self.gmaps_entry.insert(0, f"{self.user.latitude}, {self.user.longitude}")
        ttk.Button(gmaps_frame,
                   text="📋 Aplicar Coordenadas do Google Maps",
                   command=self.parse_gmaps_coordinates).pack(pady=(0, 10))

        # Manual input
        manual_frame = tk.Frame(main_frame, bg='#34495e')
        manual_frame.pack(fill=tk.X, pady=(0, 15), padx=20)
        tk.Label(manual_frame,
                 text="✏️ Edição Manual:",
                 font=('Arial', 10, 'bold'),
                 bg='#34495e',
                 fg='#f39c12').pack(anchor=tk.W)
        lat_frame = tk.Frame(manual_frame, bg='#34495e')
        lat_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(lat_frame, text="Latitude:", bg='#34495e', fg='#ecf0f1').pack(side=tk.LEFT)
        self.lat_entry = tk.Entry(lat_frame, font=('Arial', 11))
        self.lat_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        self.lat_entry.insert(0, str(self.user.latitude))
        lon_frame = tk.Frame(manual_frame, bg='#34495e')
        lon_frame.pack(fill=tk.X)
        tk.Label(lon_frame, text="Longitude:", bg='#34495e', fg='#ecf0f1').pack(side=tk.LEFT)
        self.lon_entry = tk.Entry(lon_frame, font=('Arial', 11))
        self.lon_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        self.lon_entry.insert(0, str(self.user.longitude))

        # Quick locations
        quick_frame = tk.Frame(main_frame, bg='#27ae60', relief=tk.RAISED, bd=1)
        quick_frame.pack(fill=tk.X, pady=(0, 15), padx=20)
        tk.Label(quick_frame,
                 text="⚡ Localizações Rápidas de Fortaleza:",
                 font=('Arial', 10, 'bold'),
                 bg='#27ae60',
                 fg='white').pack(pady=5)
        quick_locations = [
            ("🏛️ Centro", -3.7319, -38.5267),
            ("🏖️ Iracema", -3.7183, -38.5120),
            ("🛍️ Iguatemi", -3.7414, -38.4935),
            ("✈️ Aeroporto", -3.7761, -38.5329),
            ("🏫 UFC", -3.7441, -38.5742),
            ("🏖️ Futuro", -3.7324, -38.4758)
        ]
        btn_frame1 = tk.Frame(quick_frame, bg='#27ae60')
        btn_frame1.pack(pady=(0, 5))
        btn_frame2 = tk.Frame(quick_frame, bg='#27ae60')
        btn_frame2.pack(pady=(0, 10))
        for i, (name, lat, lon) in enumerate(quick_locations):
            frame = btn_frame1 if i < 3 else btn_frame2
            btn = tk.Button(frame,
                            text=name,
                            font=('Arial', 9),
                            bg='white',
                            fg='#27ae60',
                            command=lambda l=lat, lo=lon: self.set_quick_location(l, lo))
            btn.pack(side=tk.LEFT, padx=2)

        # Buttons
        btn_frame = tk.Frame(main_frame, bg='#34495e')
        btn_frame.pack(fill=tk.X, pady=(10, 20), padx=20)
        ttk.Button(btn_frame, text="✅ Atualizar", command=self.update_location).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="❌ Cancelar", command=self.cancel).pack(side=tk.LEFT)

    def parse_gmaps_coordinates(self):
        gmaps_text = self.gmaps_entry.get().strip()
        if not gmaps_text:
            messagebox.showwarning("Aviso", "Digite as coordenadas primeiro!")
            return
        try:
            clean_text = gmaps_text.replace(' ', '').replace('°', '').replace('′', '').replace('″', '')
            coords = clean_text.split(',')
            if len(coords) != 2:
                raise ValueError("Formato deve ser: latitude, longitude")
            lat = float(coords[0])
            lon = float(coords[1])
            if not (-90 <= lat <= 90):
                raise ValueError(f"Latitude {lat} está fora do range válido (-90 a 90)")
            if not (-180 <= lon <= 180):
                raise ValueError(f"Longitude {lon} está fora do range válido (-180 a 180)")
            self.lat_entry.delete(0, tk.END)
            self.lat_entry.insert(0, str(lat))
            self.lon_entry.delete(0, tk.END)
            self.lon_entry.insert(0, str(lon))
            messagebox.showinfo("✅ Sucesso",
                                f"Coordenadas processadas com sucesso!\n\n" +
                                f"📍 Latitude: {lat}\n" +
                                f"📍 Longitude: {lon}\n\n" +
                                f"Clique em 'Atualizar' para aplicar.")
        except ValueError as e:
            messagebox.showerror("❌ Erro", f"Não foi possível processar as coordenadas!\n\nErro: {str(e)}")

    def set_quick_location(self, lat, lon):
        self.lat_entry.delete(0, tk.END)
        self.lat_entry.insert(0, str(lat))
        self.lon_entry.delete(0, tk.END)
        self.lon_entry.insert(0, str(lon))

    def update_location(self):
        try:
            lat = float(self.lat_entry.get())
            lon = float(self.lon_entry.get())
            self.result = (lat, lon)
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Erro", "Coordenadas inválidas!")

    def cancel(self):
        self.dialog.destroy()


def main():
    """Função principal da GUI corrigida"""
    try:
        # Verificar dependências
        import Pyro5.api
        import pika
        from geopy.distance import geodesic

        # Testar RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        connection.close()

    except ImportError as e:
        messagebox.showerror("Erro", f"Dependência não encontrada: {e}\nInstale com: pip install -r requirements.txt")
        return
    except Exception as e:
        messagebox.showerror("Erro", f"RabbitMQ não está rodando: {e}\nInicie o RabbitMQ primeiro.")
        return

    # Criar e executar GUI
    app = LauncherGUI()
    app.run()


if __name__ == "__main__":
    main()