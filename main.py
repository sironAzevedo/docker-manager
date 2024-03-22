import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import docker
import threading


class DockerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Docker Manager")
        self.__center_window(self.root, 1500, 750)

        self.docker_client = docker.from_env()
        self.current_selected_container = None
        self.log_update_job = None

        self.setup_ui()

    def setup_ui(self):
        self.root.option_add('*tearOff', False)  # Impede que os menus sejam destacados

        # Definição de estilos para os widgets
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Tema padrão
        self.style.configure('TButton', padding=6)
        self.style.configure('TEntry', padding=6)
        self.style.configure('TCombobox', padding=6)
        self.style.configure('TLabel', padding=6)
        self.style.configure('TFrame', padding=6)

        # Gerenciamento de imagens docker
        self.image_frame = ttk.LabelFrame(self.root, text="Imagens Docker")
        self.image_frame.pack(fill=tk.BOTH, expand=True)

        # Frame para a lista de imagens e scrollbar
        self.image_list_scroll_frame = ttk.Frame(self.image_frame)
        self.image_list_scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.image_listbox = tk.Listbox(self.image_list_scroll_frame, height=6)
        self.image_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.image_scroll = ttk.Scrollbar(self.image_list_scroll_frame, orient=tk.VERTICAL,
                                          command=self.image_listbox.yview)
        self.image_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_listbox.config(yscrollcommand=self.image_scroll.set)

        self.image_listbox.bind('<<ListboxSelect>>', self.imagem_selection_changed)

        # Botões para ações de imagem
        self.image_action_frame = ttk.Frame(self.image_frame)
        self.image_action_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)

        # Frame para os botões de ação de imagem, agora posicionado abaixo do Listbox e Scrollbar
        self.pull_image_button = ttk.Button(self.image_action_frame, text='Puxar Imagem', command=self.pull_image)
        self.pull_image_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.build_container_button = ttk.Button(self.image_action_frame, text='Construir Container', state='disabled',
                                                 command=self.open_build_container_window)
        self.build_container_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.build_image_button = ttk.Button(self.image_action_frame, text='Construir Imagem', command=self.build_image)
        self.build_image_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.remove_image_button = ttk.Button(self.image_action_frame, text='Remover Imagem', command=self.remove_image)
        self.remove_image_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Layout adjustment
        self.container_frame = ttk.LabelFrame(self.root, text='Containers')
        self.container_frame.pack(fill=tk.BOTH, expand=False, side=tk.LEFT)

        # Container list

        self.container_list_frame = ttk.LabelFrame(self.container_frame)
        self.container_list_frame.pack(fill=tk.BOTH, expand=True)

        self.container_listbox = tk.Listbox(self.container_list_frame)
        self.container_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.container_scroll = ttk.Scrollbar(self.container_list_frame, orient=tk.VERTICAL,
                                              command=self.container_listbox.yview)
        self.container_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.container_listbox.config(yscrollcommand=self.container_scroll.set)

        # Container actions
        self.container_action_frame = ttk.Frame(self.container_frame)
        self.container_action_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)

        self.refresh_button = ttk.Button(self.container_action_frame, text="Refresh", command=self.refresh)
        self.refresh_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.start_button = ttk.Button(self.container_action_frame, text="Start", state='disabled',
                                       command=self.start_container)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.stop_button = ttk.Button(self.container_action_frame, text="Stop", state='disabled',
                                      command=self.stop_container)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.remove_button = ttk.Button(self.container_action_frame, text="Remove", state='disabled',
                                        command=self.remove_container)
        self.remove_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Log Text Frame
        self.log_frame = ttk.LabelFrame(self.root, text='Logs')
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Log Text Widget
        self.log_text = tk.Text(self.log_frame, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar for Log Text
        self.log_scroll = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=self.log_scroll.set)
        self.log_scroll.config(command=self.log_text.yview)

        self.container_listbox.bind('<<ListboxSelect>>', self.container_selection_changed)

        # Command execution frame
        self.cmd_frame = ttk.LabelFrame(self.root, text='Executar Comando')
        self.cmd_frame.pack(fill=tk.X, padx=5, pady=5)

        # Command entry
        self.cmd_entry = ttk.Entry(self.cmd_frame)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        # Execute command button
        self.cmd_button = ttk.Button(self.cmd_frame, text='Executar', command=self.execute_command)
        self.cmd_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.refresh()

    @staticmethod
    def __center_window(frame, width, height):
        ws = frame.winfo_screenwidth()
        hs = frame.winfo_screenheight()

        x = (ws / 2) - (width / 2)
        y = (hs / 2) - (height / 2)
        frame.geometry('%dx%d+%d+%d' % (width, height, x, y))

    def refresh(self):
        self.list_containers()
        self.refresh_images()

    def list_containers(self):
        self.container_listbox.delete(0, tk.END)
        for container in self.docker_client.containers.list(all=True):
            display_name = f"{container.name} ({'running' if container.status == 'running' else 'stopped'})"
            self.container_listbox.insert(tk.END, display_name)

    def show_logs(self, container_name):
        if self.check_container_exists(container_name):
            container = self.docker_client.containers.get(container_name)
            logs = container.logs(tail=100).decode('utf-8')
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, logs)
            self.schedule_log_update(container_name)

            self.log_text.see(tk.END)  # Rolagem automática para a parte inferior

    def schedule_log_update(self, container_name):
        # Cancela a atualização anterior se existir
        if self.log_update_job is not None:
            self.root.after_cancel(self.log_update_job)
        # Agenda a próxima atualização
        self.log_update_job = self.root.after(2000, lambda: self.show_logs(container_name))

    def start_container(self):
        try:
            selected_container = self.get_selected_container()
            if selected_container:
                selected_container.start()
                messagebox.showinfo("Success", "Container started successfully.")
                self.refresh()
                self.habilitar_botoes_container(selected_container.id)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def stop_container(self):
        try:
            selected_container = self.get_selected_container()
            if selected_container:
                selected_container.stop()
                messagebox.showinfo("Success", "Container stopped successfully.")
                self.refresh()
                self.habilitar_botoes_container(selected_container.id)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def remove_container(self):
        try:
            selected_container = self.get_selected_container()
            if selected_container:
                selected_container.remove()
                self.log_text.delete(0.0, tk.END)
                messagebox.showinfo("Success", "Container removed successfully.")
                self.refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

        # Nova função para tratar a mudança de seleção do container

    def imagem_selection_changed(self, event=None):
        selected = self.image_listbox.curselection()
        if selected:
            self.build_container_button.state(["!disabled"])
        else:
            self.build_container_button.state(["disabled"])

    def container_selection_changed(self, event=None):
        self.imagem_selection_changed(event)
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            container_name = event.widget.get(index).split()[0]
            if container_name != self.current_selected_container:
                self.current_selected_container = container_name
                self.show_logs(container_name)
                self.habilitar_botoes_container(container_name)

    def get_selected_container(self):
        selection = self.container_listbox.curselection()
        if selection:
            index = selection[0]
            container_name = self.container_listbox.get(index).split()[0]
            # Parar a atualização automática dos logs se um novo container for selecionado
            if container_name != self.current_selected_container:
                if self.log_update_job is not None:
                    self.root.after_cancel(self.log_update_job)
                    self.log_update_job = None
                self.current_selected_container = container_name
            return self.docker_client.containers.get(container_name)
        return None

    def execute_command(self):
        selected_container = self.get_selected_container()
        if selected_container is None:
            messagebox.showerror("Erro", "Nenhum container selecionado")
            return

        command = self.cmd_entry.get()
        if not command.strip():
            messagebox.showerror("Erro", "Comando vazio não é permitido")
            return

        try:
            exec_result = selected_container.exec_run(command)
            result = exec_result.output.decode('utf-8')
            self.log_text.delete(1.0, tk.END)  # Limpa os logs anteriores
            self.log_text.insert(tk.END, result)  # Mostra o resultado do comando
        except Exception as e:
            messagebox.showerror("Erro ao executar comando", str(e))

    def refresh_images(self):
        self.image_listbox.delete(0, tk.END)
        for image in self.docker_client.images.list():
            for tag in image.tags:
                self.image_listbox.insert(tk.END, tag)

    def pull_image(self):
        image_name = simpledialog.askstring("Puxar Imagem", "Nome da Imagem:")
        if image_name:

            # Chama a função para mostrar a janela de progresso
            progress_window = self.show_progress_window("Puxando imagem, por favor aguarde...")

            def worker():
                try:
                    self.docker_client.images.pull(image_name)

                    # Fecha a janela de progresso após a conclusão
                    progress_window.destroy()
                    self.refresh_images()
                    messagebox.showinfo("Sucesso", f"Imagem {image_name} puxada com sucesso.")
                except Exception as e:
                    # Fecha a janela de progresso após a conclusão
                    progress_window.destroy()

                    messagebox.showerror("Erro", str(e))

            # Inicia a thread
            threading.Thread(target=worker).start()

    def build_image(self):
        dockerfile_path = filedialog.askdirectory()
        image_tag = simpledialog.askstring("Construir Imagem", "Tag da Imagem:")
        if dockerfile_path and image_tag:
            try:
                image, _ = self.docker_client.images.build(path=dockerfile_path, tag=image_tag)
                messagebox.showinfo("Sucesso", f"Imagem {image_tag} construída com sucesso.")
                self.refresh_images()
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def remove_image(self):
        selected = self.image_listbox.curselection()
        if selected:
            image_tag = self.image_listbox.get(selected[0])
            try:
                self.docker_client.images.remove(image=image_tag)
                messagebox.showinfo("Sucesso", f"Imagem {image_tag} removida com sucesso.")
                self.refresh_images()
            except Exception as e:
                messagebox.showerror("Erro", str(e))
        else:
            messagebox.showwarning("Aviso", "Selecione uma imagem para remover.")

    def show_progress_window(self, mensagem: str):
        progress_window = tk.Toplevel()
        progress_window.title("Carregando...")
        self.__center_window(progress_window, 450, 100)
        progress_window.resizable(width=False, height=False)

        ttk.Label(progress_window, text=mensagem).pack(pady=20)
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
        progress_bar.pack(pady=10)
        progress_bar.start()

        return progress_window

    def open_build_container_window(self):
        self.build_window = tk.Toplevel()
        self.build_window.title("Construir Container")
        self.__center_window(self.build_window, 500, 300)
        self.build_window.resizable(width=False, height=False)

        # Imagem selecionada
        selected = self.image_listbox.curselection()
        image_tag = self.image_listbox.get(selected[0])

        tk.Label(self.build_window, text=f"Imagem: {image_tag}", font=('Arial', 12, 'bold')).pack(pady=(10, 0))

        # Nome do Container
        tk.Label(self.build_window, text="Nome do Container:").pack(pady=(40, 2))
        self.container_name_entry = tk.Entry(self.build_window)
        self.container_name_entry.pack(ipadx=60, ipady=3)

        # Porta
        tk.Label(self.build_window, text="Porta (formato host:container):").pack(pady=(10, 2))
        self.port_entry = tk.Entry(self.build_window)
        self.port_entry.pack(ipadx=60, ipady=3)

        # Networks
        tk.Label(self.build_window, text="Networks:").pack(pady=(10, 2))
        self.network_combobox = ttk.Combobox(self.build_window, state="readonly")
        self.network_combobox.pack(ipadx=60)

        # Preenche o combobox com as redes disponíveis
        self.fill_network_combobox()

        # Botão para construir o container  command= lambda: action(someNumber))
        ttk.Button(self.build_window, text="Construir", command=lambda: self.build_container(image_tag)).pack(
            pady=(30, 0))

    def fill_network_combobox(self):
        networks = self.get_available_networks()
        self.network_combobox['values'] = networks

    def get_available_networks(self):
        try:
            networks = self.docker_client.networks.list()
            network_names = [network.name for network in networks]
            return network_names
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def build_container(self, image_selected):
        try:
            container_name = self.container_name_entry.get()
            port = self.port_entry.get()
            network = self.network_combobox.get()

            self.docker_client.containers.run(image_selected, name=container_name,
                                              ports={port.split(':')[1]: port.split(':')[0]}, network=network,
                                              detach=True)
            self.list_containers()

            # Feche a janela após a criação
            self.build_window.destroy()

            messagebox.showinfo("Sucesso", f"Container {container_name} criado com sucesso.")
        except Exception as e:
            self.build_window.destroy()
            messagebox.showerror("Erro", str(e))

    def check_container_exists(self, container_name_or_id):
        try:
            self.docker_client.containers.get(container_name_or_id)
            return True
        except Exception as e:
            return False

    def habilitar_botoes_container(self, container_name):
        container = self.docker_client.containers.get(container_name)
        stats = container.attrs.get('State')
        if stats['Running']:
            self.start_button.state(["disabled"])
            self.stop_button.state(["!disabled"])
            self.remove_button.state(["disabled"])
        else:
            self.start_button.state(["!disabled"])
            self.stop_button.state(["disabled"])
            self.remove_button.state(["!disabled"])

        self.refresh()


def main():
    root = tk.Tk()
    app = DockerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
