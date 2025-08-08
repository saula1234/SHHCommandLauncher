import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import os
import json

class SSHCommandLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("SSH Мастер")
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

        # Создаем Treeview
        self.tree = ttk.Treeview(frame, columns=("Details"), show="tree")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Добавляем скроллбар
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Настройка стилей
        style = ttk.Style()
        style.configure("Group.Treeview", font=("Arial", 12, "bold"), foreground="blue")
        style.configure("Command.Treeview", font=("Arial", 10))

        # Кнопки
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Открыть", command=self.run_command).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Добавить группу", command=self.add_group).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Редактировать", command=self.edit_item).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Удалить", command=self.delete_group).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Добавить комманду", command=self.add_command_to_group).pack(side=tk.LEFT, padx=5)

        # Обновляем Treeview
        self.update_treeview()

    def update_treeview(self):
        """Обновляем Treeview с группами и командами"""
        # Очищаем Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Добавляем группы и команды
        for group in self.groups:
            group_id = self.tree.insert("", "end", text=f"{group['name']}", values=[group['host']], tags=("group",))
            for cmd in group["commands"]:
                self.tree.insert(group_id, "end", text=f"{cmd['name']}", values=[cmd['command']], tags=("command",))

        # Применяем теги для стилей
        self.tree.tag_configure("group", font=("Arial", 12, "bold"), foreground="blue")
        self.tree.tag_configure("command", font=("Arial", 10))

    def run_command(self):
        """Запуск выбранной команды или группы"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No command or group selected!")
            return

        item = self.tree.item(selected_item)
        if item["values"]:  # Это группа (у групп есть значение host)
            host = item["values"][0]
            self.execute_ssh_command(host)
        else:  # Это подкоманда
            group = self.find_group_for_command(item)
            if group:
                host = group["host"]
                full_command = f"{host} -t \"sudo -i bash -c '{item['values'][0]}; exec bash'\""
                self.execute_ssh_command(full_command)

    def find_group_for_command(self, item):
        """Находим группу, которой принадлежит команда"""
        for group in self.groups:
            for cmd in group["commands"]:
                if cmd["name"] == item["text"] and cmd["command"] == item["values"][0]:
                    return group
        return None

    def load_groups(self):
        """Загружаем группы из файла (если есть)"""
        if os.path.exists("groups.json"):
            try:
                with open("groups.json", "r") as f:
                    self.groups = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load groups: {e}")
                self.groups = []  # В случае ошибки используем пустой список

    def save_groups(self):
        """Сохраняем группы в файл"""
        try:
            with open("groups.json", "w") as f:
                json.dump(self.groups, f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save groups: {e}")

    def add_group(self):
        """Добавление новой группы"""
        name = simpledialog.askstring("Add Group", "Enter group name:")
        if not name:
            return

        host = simpledialog.askstring("Add Group", "Enter SSH host (e.g., ssh user@host -p22):")
        if not host:
            return

        self.groups.append({"name": name, "host": host, "commands": []})
        self.update_treeview()
        self.save_groups()

    def edit_item(self):
        """Редактирование выбранной группы или подгруппы"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No item selected!")
            return

        item = self.tree.item(selected_item)
        if item["values"]:  # Это группа (у групп есть значение host)
            self.edit_group(item)
        else:  # Это подкоманда
            group = self.find_group_for_command(item)
            if group:
                self.edit_command(group, item)
            else:
                messagebox.showerror("Error", "Failed to find group for the selected command!")

    def edit_group(self, item):
        """Редактирование группы"""
        group_name = item["text"]
        new_name = simpledialog.askstring("Edit Group", "Enter new group name:", initialvalue=group_name)
        if new_name is None:
            return

        new_host = simpledialog.askstring("Edit Group", "Enter new SSH host:", initialvalue=item["values"][0])
        if new_host is None:
            return

        for group in self.groups:
            if group["name"] == group_name:
                group["name"] = new_name
                group["host"] = new_host
                break

        self.update_treeview()
        self.save_groups()

    def edit_command(self, group, item):
        """Редактирование подгруппы (команды)"""
        new_name = simpledialog.askstring("Edit Command", "Enter new command name:", initialvalue=item["text"])
        if new_name is None:
            return

        new_command = simpledialog.askstring("Edit Command", "Enter new command:", initialvalue=item["values"][0])
        if new_command is None:
            return

        for cmd in group["commands"]:
            if cmd["name"] == item["text"] and cmd["command"] == item["values"][0]:
                cmd["name"] = new_name
                cmd["command"] = new_command
                break

        self.update_treeview()
        self.save_groups()

    def delete_group(self):
        """Удаление группы"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No group selected!")
            return

        item = self.tree.item(selected_item)
        if item["values"]:  # Это группа (у групп есть значение host)
            group_name = item["text"]
            self.groups = [g for g in self.groups if g["name"] != group_name]
        else:  # Это подкоманда
            group = self.find_group_for_command(item)
            if group:
                group["commands"] = [
                    cmd for cmd in group["commands"]
                    if cmd["name"] != item["text"] or cmd["command"] != item["values"][0]
                ]

        self.update_treeview()
        self.save_groups()

    def add_command_to_group(self):
        """Добавление команды в группу"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No group selected!")
            return

        item = self.tree.item(selected_item)
        if not item["values"]:  # Это подкоманда, а не группа
            messagebox.showerror("Error", "Selected item is not a group!")
            return

        group_name = item["text"]
        group = next((g for g in self.groups if g["name"] == group_name), None)
        if not group:
            messagebox.showerror("Error", "Failed to find group!")
            return

        name = simpledialog.askstring("Add Command", "Enter command name:")
        if not name:
            return

        command = simpledialog.askstring("Add Command", "Enter command (e.g., sudo cat /etc/default/app.properties):")
        if not command:
            return

        group["commands"].append({"name": name, "command": command})
        self.update_treeview()
        self.save_groups()

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


if __name__ == "__main__":
    root = tk.Tk()
    app = SSHCommandLauncher(root)
    root.mainloop()