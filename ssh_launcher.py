import tkinter as tk
from tkinter import messagebox, simpledialog
import subprocess
import os
import json

class SSHCommandLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("SSH Command Launcher")
        self.root.geometry("600x400")

        # Список групп (по умолчанию)
        self.groups = []

        # Загрузка групп из файла (если есть)
        self.load_groups()

        # GUI элементы
        self.setup_ui()

        # Иконка приложения
        import sys
        if sys.platform == "win32":
            self.root.iconbitmap("dnevnik.ico")
        else:
            try:
                icon = tk.PhotoImage(file="dnevnik.png")
                self.root.tk.call('wm', 'iconphoto', self.root._w, icon)
            except:
                pass  # Если иконка не найдена, игнорируем ошибку

    def setup_ui(self):
        # Фрейм для списка команд
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        self.listbox = tk.Listbox(frame, width=80, height=15)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)

        # Кнопки
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Run", command=self.run_command).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Add Group", command=self.add_group).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edit", command=self.edit_item).pack(side=tk.LEFT, padx=5)  # Переименованная кнопка
        tk.Button(button_frame, text="Delete Group", command=self.delete_group).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Add Command", command=self.add_command_to_group).pack(side=tk.LEFT, padx=5)

        self.update_listbox()

    def update_listbox(self):
        """Обновляем список групп и команд в интерфейсе"""
        self.listbox.delete(0, tk.END)
        for group in self.groups:
            self.listbox.insert(tk.END, f"GROUP: {group['name']} → {group['host']}")
            for cmd in group["commands"]:
                self.listbox.insert(tk.END, f"  - {cmd['name']} → {cmd['command']}")

    def run_command(self):
        """Запуск выбранной команды или группы"""
        selected_index = self.listbox.curselection()
        if not selected_index:
            messagebox.showerror("Error", "No command or group selected!")
            return

        selected_item = self.get_selected_item(selected_index[0])

        if "host" in selected_item:  # Это группа
            host = selected_item["host"]
            self.execute_ssh_command(host)
        else:  # Это подкоманда
            group = self.find_group_for_command(selected_item)
            if group:
                host = group["host"]
                full_command = f"{host} -t \"sudo -i bash -c '{selected_item['command']}; exec bash'\""
                self.execute_ssh_command(full_command)

    def execute_ssh_command(self, command):
        """Выполнение SSH-команды в терминале"""
        try:
            print(f"Executing command: {command}")

            if os.name == "posix":  # Linux/macOS
                subprocess.Popen(["x-terminal-emulator", "-e", "bash", "-c", f"{command}; exec bash"])
            elif os.name == "nt":    # Windows
                subprocess.Popen(f"start cmd /k {command}", shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run command: {e}")

    def get_selected_item(self, index):
        """Возвращает выбранный элемент (группу или подкоманду)"""
        for group in self.groups:
            if index == 0:  # Первая строка — это группа
                return group
            index -= 1
            for cmd in group["commands"]:
                if index == 0:
                    return cmd
                index -= 1
        return None

    def find_group_for_command(self, command):
        """Находит группу, которой принадлежит команда"""
        for group in self.groups:
            if command in group["commands"]:
                return group
        return None

    def add_group(self):
        """Добавление новой группы"""
        name = simpledialog.askstring("Add Group", "Enter group name:")
        if not name:
            return

        host = simpledialog.askstring("Add Group", "Enter SSH host (e.g., ssh user@host -p22):")
        if not host:
            return

        self.groups.append({"name": name, "host": host, "commands": []})
        self.update_listbox()
        self.save_groups()

    def edit_item(self):
        """Редактирование выбранной группы или подгруппы"""
        selected_index = self.listbox.curselection()
        if not selected_index:
            messagebox.showerror("Error", "No item selected!")
            return

        selected_item = self.get_selected_item(selected_index[0])

        if "host" in selected_item:  # Это группа
            self.edit_group(selected_item)
        else:  # Это подгруппа
            group = self.find_group_for_command(selected_item)
            if group:
                self.edit_command(group, selected_item)
            else:
                messagebox.showerror("Error", "Failed to find group for the selected command!")

    def edit_group(self, group):
        """Редактирование группы"""
        new_name = simpledialog.askstring("Edit Group", "Enter new group name:", initialvalue=group["name"])
        if new_name is None:
            return

        new_host = simpledialog.askstring("Edit Group", "Enter new SSH host:", initialvalue=group["host"])
        if new_host is None:
            return

        group["name"] = new_name
        group["host"] = new_host
        self.update_listbox()
        self.save_groups()

    def edit_command(self, group, command):
        """Редактирование подгруппы (команды)"""
        new_name = simpledialog.askstring("Edit Command", "Enter new command name:", initialvalue=command["name"])
        if new_name is None:
            return

        new_command = simpledialog.askstring("Edit Command", "Enter new command:", initialvalue=command["command"])
        if new_command is None:
            return

        command["name"] = new_name
        command["command"] = new_command
        self.update_listbox()
        self.save_groups()

    def delete_group(self):
        """Удаление группы"""
        selected_index = self.listbox.curselection()
        if not selected_index:
            messagebox.showerror("Error", "No group selected!")
            return

        group = self.get_selected_item(selected_index[0])
        if "host" not in group:
            messagebox.showerror("Error", "Selected item is not a group!")
            return

        if messagebox.askyesno("Confirm", "Delete this group and all its commands?"):
            self.groups.remove(group)
            self.update_listbox()
            self.save_groups()

    def add_command_to_group(self):
        """Добавление команды в группу"""
        selected_index = self.listbox.curselection()
        if not selected_index:
            messagebox.showerror("Error", "No group selected!")
            return

        group = self.get_selected_item(selected_index[0])
        if "host" not in group:
            messagebox.showerror("Error", "Selected item is not a group!")
            return

        name = simpledialog.askstring("Add Command", "Enter command name:")
        if not name:
            return

        command = simpledialog.askstring("Add Command", "Enter command (e.g., sudo cat /etc/default/app.properties):")
        if not command:
            return

        group["commands"].append({"name": name, "command": command})
        self.update_listbox()
        self.save_groups()

    def save_groups(self):
        """Сохраняем группы в файл"""
        with open("groups.json", "w") as f:
            json.dump(self.groups, f)

    def load_groups(self):
        """Загружаем группы из файла (если есть)"""
        if os.path.exists("groups.json"):
            try:
                with open("groups.json", "r") as f:
                    self.groups = json.load(f)
            except:
                pass  # Файл битый, используем пустой список

if __name__ == "__main__":
    root = tk.Tk()
    app = SSHCommandLauncher(root)
    root.mainloop()