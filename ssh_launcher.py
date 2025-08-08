import tkinter as tk
from tkinter import messagebox, simpledialog
import subprocess
import os

class SSHCommandLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("SSH Command Launcher")
        self.root.geometry("500x400")

        # Список команд (по умолчанию)
        self.commands = [
            {"name": "Connect to Server 1", "command": "ssh user@192.168.1.1"},
            {"name": "View Config", "command": "ssh user@192.168.1.1 'sudo cat /var/default/app.properties'"},
        ]

        # Загрузка команд из файла (если есть)
        self.load_commands()

        # GUI элементы
        self.setup_ui()

        import sys
        if sys.platform == "win32":
            self.root.iconbitmap("dnevnik.ico")
        else:
            icon = tk.PhotoImage(file="dnevnik.png")
            self.root.tk.call('wm', 'iconphoto', self.root._w, icon)

    def setup_ui(self):
        # Фрейм для списка команд
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        # Список команд (Listbox)
        self.listbox = tk.Listbox(frame, width=60, height=15)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH)

        # Скроллбар
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)

        # Обновляем список
        self.update_listbox()

        # Кнопки
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Run", command=self.run_command).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Add", command=self.add_command).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edit", command=self.edit_command).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete", command=self.delete_command).pack(side=tk.LEFT, padx=5)

    def update_listbox(self):
        """Обновляем список команд в интерфейсе"""
        self.listbox.delete(0, tk.END)
        for cmd in self.commands:
            self.listbox.insert(tk.END, f"{cmd['name']} → {cmd['command']}")

    def run_command(self):
        """Запуск выбранной команды в терминале"""
        selected_index = self.listbox.curselection()
        if not selected_index:
            messagebox.showerror("Error", "No command selected!")
            return

        selected_cmd = self.commands[selected_index[0]]["command"]

        # Запуск команды в новом терминале
        try:
            command = selected_cmd.replace("'", "'\"'\"'")
            if os.name == "posix":  # Linux/macOS
                subprocess.Popen(["x-terminal-emulator", "-e", "bash", "-c", f"{command}; exec bash"])
            elif os.name == "nt":    # Windows
                subprocess.Popen(f"start cmd /k {command}", shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run command: {e}")

    def add_command(self):
        """Добавление новой команды"""
        name = simpledialog.askstring("Add Command", "Enter command name:")
        if not name:
            return

        command = simpledialog.askstring("Add Command", "Enter command (e.g., ssh user@host):")
        if not command:
            return

        self.commands.append({"name": name, "command": command})
        self.update_listbox()
        self.save_commands()

    def edit_command(self):
        """Редактирование команды"""
        selected_index = self.listbox.curselection()
        if not selected_index:
            messagebox.showerror("Error", "No command selected!")
            return

        old_cmd = self.commands[selected_index[0]]

        new_name = simpledialog.askstring("Edit Command", "Enter new name:", initialvalue=old_cmd["name"])
        if new_name is None:
            return

        new_command = simpledialog.askstring("Edit Command", "Enter new command:", initialvalue=old_cmd["command"])
        if new_command is None:
            return

        self.commands[selected_index[0]] = {"name": new_name, "command": new_command}
        self.update_listbox()
        self.save_commands()

    def delete_command(self):
        """Удаление команды"""
        selected_index = self.listbox.curselection()
        if not selected_index:
            messagebox.showerror("Error", "No command selected!")
            return

        if messagebox.askyesno("Confirm", "Delete this command?"):
            del self.commands[selected_index[0]]
            self.update_listbox()
            self.save_commands()

    def save_commands(self):
        """Сохраняем команды в файл"""
        import json
        with open("commands.json", "w") as f:
            json.dump(self.commands, f)

    def load_commands(self):
        """Загружаем команды из файла (если есть)"""
        import json
        if os.path.exists("commands.json"):
            try:
                with open("commands.json", "r") as f:
                    self.commands = json.load(f)
            except:
                pass  # Файл битый, используем стандартные команды

if __name__ == "__main__":
    root = tk.Tk()
    app = SSHCommandLauncher(root)
    root.mainloop()