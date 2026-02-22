import customtkinter as ctk
import os
import sys
import subprocess
import json
import webbrowser
import ctypes
from tkinter import messagebox, filedialog

# === ФУНКЦИЯ ДЛЯ РАБОТЫ С ИКОНКОЙ В .EXE ===
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === НАСТРОЙКИ ВНЕШНЕГО ВИДА ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")
CONFIG_FILE = "launcher_config.json"

class WarningDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_bat, new_bat):
        super().__init__(parent)
        self.title("Внимание!")
        self.geometry("450x200")
        self.resizable(False, False)
        self.geometry(f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 100}")
        self.result = None 
        
        lbl = ctk.CTkLabel(self, text=f"Уже запущен процесс: {current_bat}\nВы хотите запустить: {new_bat}\n\nРекомендуется закрыть предыдущий батник.", font=ctk.CTkFont(size=14))
        lbl.pack(pady=20)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="Закрыть старый", command=lambda: self.set_result("close_and_run")).grid(row=0, column=0, padx=5)
        ctk.CTkButton(btn_frame, text="Запустить оба", fg_color="#D97706", hover_color="#B45309", command=lambda: self.set_result("run_both")).grid(row=0, column=1, padx=5)
        ctk.CTkButton(btn_frame, text="Отмена", fg_color="#DC2626", hover_color="#991B1B", command=lambda: self.set_result("cancel")).grid(row=0, column=2, padx=5)
        self.grab_set()

    def set_result(self, value):
        self.result = value
        self.destroy()

class ZapretApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Zapret Hub Launcher")
        self.geometry("700x600") # Слегка увеличили базовый размер
        self.minsize(600, 500)
        self.eval('tk::PlaceWindow . center')
        
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.current_process = None
        self.current_bat_name = None 
        self.zapret_path = "" 
        self.last_bat = ""       
        self.favorites = []      

        # Настройка сетки главного окна
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Контент (Setup или Main)
        self.grid_rowconfigure(1, weight=0) # Футер со ссылкой

        # Ссылка внизу
        self.link_label = ctk.CTkLabel(self, text="fork by SapTaLe", font=ctk.CTkFont(size=11, underline=True), 
                                       text_color="#666666", cursor="hand2")
        self.link_label.grid(row=1, column=0, pady=5)
        self.link_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/saptale/modernUI-zapret-discord-youtube"))
        self.link_label.bind("<Enter>", lambda e: self.link_label.configure(text_color="#BB86FC"))
        self.link_label.bind("<Leave>", lambda e: self.link_label.configure(text_color="#666666"))

        # Контейнеры
        self.setup_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")

        self.initialize_app()

    def load_config(self):
        default = {"zapret_path": "", "last_bat": "", "favorites": []}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict): default.update(data)
            except Exception: pass
        return default

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"zapret_path": self.zapret_path, "last_bat": self.last_bat, "favorites": self.favorites}, f, ensure_ascii=False, indent=4)

    def check_bats_exist(self, path):
        if not path or not os.path.exists(path): return False
        return any(f.endswith('.bat') for f in os.listdir(path))

    def initialize_app(self):
        config = self.load_config()
        self.zapret_path, self.last_bat, self.favorites = config["zapret_path"], config["last_bat"], config["favorites"]
        if self.check_bats_exist(self.zapret_path): self.show_main_screen()
        elif self.check_bats_exist(os.getcwd()):
            self.zapret_path = os.getcwd()
            self.save_config()
            self.show_main_screen()
        else: self.show_setup_screen()

    def show_setup_screen(self):
        self.main_frame.grid_forget()
        self.setup_frame.grid(row=0, column=0, sticky="nsew")
        for widget in self.setup_frame.winfo_children(): widget.destroy()
        
        container = ctk.CTkFrame(self.setup_frame, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(container, text="📁", font=ctk.CTkFont(size=60)).pack()
        ctk.CTkLabel(container, text="Конфигурации не найдены\nУкажите путь к папке Zapret", font=ctk.CTkFont(size=16)).pack(pady=20)
        ctk.CTkButton(container, text="Выбрать папку", height=40, command=self.browse_folder).pack()

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path and self.check_bats_exist(folder_path):
            self.zapret_path = folder_path
            self.save_config()
            self.show_main_screen()

    def show_main_screen(self):
        self.setup_frame.grid_forget()
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Сетка для главного экрана: Хаб (строка 0), Настройки (строка 1), Вкладки (строка 2)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1) # Вкладки забирают всё место

        # 0. Хаб
        hub_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        hub_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        ctk.CTkLabel(hub_frame, text="ХАБ ЗАПУСКА", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 0))
        self.status_label = ctk.CTkLabel(hub_frame, text="⚪ Ожидание", font=ctk.CTkFont(size=13))
        self.status_label.pack(pady=5)

        self.action_frame = ctk.CTkFrame(hub_frame, fg_color="transparent")
        self.action_frame.pack(pady=(0, 10))
        self.btn_stop = ctk.CTkButton(self.action_frame, text="⏹ Остановить", fg_color="#DC2626", hover_color="#991B1B", height=32, command=self.kill_current_process)
        self.btn_last = ctk.CTkButton(self.action_frame, text="", fg_color="#2563EB", hover_color="#1D4ED8", height=32, command=lambda: self.handle_launch(self.last_bat))

        # 1. Кнопка смены папки
        ctk.CTkButton(self.main_frame, text="⚙️ Сменить папку", fg_color="transparent", text_color="gray", font=ctk.CTkFont(size=12), command=self.show_setup_screen).grid(row=1, column=0, padx=20, sticky="e")

        # 2. Вкладки
        self.tabview = ctk.CTkTabview(self.main_frame, corner_radius=10)
        self.tabview.grid(row=2, column=0, padx=20, pady=(5, 10), sticky="nsew")
        
        self.refresh_tabs()
        self.update_hub_ui()

    def update_hub_ui(self):
        self.btn_stop.pack_forget()
        self.btn_last.pack_forget()
        if self.current_bat_name:
            self.status_label.configure(text=f"🟢 Работает: {self.current_bat_name}", text_color="#22C55E")
            self.btn_stop.pack(side="left", padx=5)
        else:
            self.status_label.configure(text="⚪ Ничего не запущено", text_color="gray")
            if self.last_bat and os.path.exists(os.path.join(self.zapret_path, self.last_bat)):
                self.btn_last.configure(text=f"↻ Запустить последний: {self.last_bat}")
                self.btn_last.pack(side="left", padx=5)

    def refresh_tabs(self):
        for tab in list(self.tabview._tab_dict.keys()): self.tabview.delete(tab)
        bat_files = [f for f in os.listdir(self.zapret_path) if f.endswith('.bat')]
        categories = {"⭐ ИЗБРАННОЕ": [], "ОСНОВНЫЕ": [], "АЛЬТЫ (ALT)": [], "FAKE TLS": [], "SIMPLE FAKE": [], "НЕОПРЕДЕЛЕНО": []}
        for fav in self.favorites:
            if fav in bat_files: categories["⭐ ИЗБРАННОЕ"].append(fav)
        for file in bat_files: categories[self.categorize_file(file)].append(file)

        for cat_name, files in categories.items():
            if files:
                self.tabview.add(cat_name)
                scroll = ctk.CTkScrollableFrame(self.tabview.tab(cat_name), fg_color="transparent")
                scroll.pack(fill="both", expand=True)
                for file in files:
                    row = ctk.CTkFrame(scroll, fg_color="transparent")
                    row.pack(fill="x", pady=2)
                    ctk.CTkButton(row, text=file, height=35, anchor="w", command=lambda f=file: self.handle_launch(f)).pack(side="left", fill="x", expand=True, padx=(0, 5))
                    is_fav = file in self.favorites
                    btn_fav = ctk.CTkButton(row, text="★" if is_fav else "☆", width=35, height=35, text_color="#F59E0B" if is_fav else "gray", fg_color="transparent", hover_color="#333333", font=ctk.CTkFont(size=18), command=lambda f=file: self.toggle_favorite(f))
                    btn_fav.pack(side="right")

    def toggle_favorite(self, bat_file):
        if bat_file in self.favorites: self.favorites.remove(bat_file)
        else: self.favorites.append(bat_file)
        self.save_config(); self.refresh_tabs()

    def categorize_file(self, filename):
        name = filename.upper()
        if "FAKE TLS" in name: return "FAKE TLS"
        if "SIMPLE FAKE" in name: return "SIMPLE FAKE"
        if "(ALT" in name: return "АЛЬТЫ (ALT)"
        if name in ["GENERAL.BAT", "SERVICE.BAT"]: return "ОСНОВНЫЕ"
        return "НЕОПРЕДЕЛЕНО"

    def handle_launch(self, bat_file):
        if self.current_bat_name:
            dialog = WarningDialog(self, self.current_bat_name, bat_file)
            self.wait_window(dialog)
            if dialog.result == "cancel" or dialog.result is None: return
            if dialog.result == "close_and_run": self.kill_current_process()
        self.start_new_process(bat_file)

    def start_new_process(self, bat_file):
        try:
            full = os.path.join(self.zapret_path, bat_file)
            self.current_process = subprocess.Popen(full, cwd=self.zapret_path, creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.current_bat_name = bat_file
            self.last_bat = bat_file
            self.save_config(); self.update_hub_ui()
        except Exception as e: messagebox.showerror("Ошибка", f"Ошибка запуска: {e}")

    def kill_current_process(self):
        if self.current_bat_name:
            try:
                subprocess.run('taskkill /F /IM winws.exe', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(f'taskkill /F /FI "WINDOWTITLE eq *{self.current_bat_name}*" /IM cmd.exe', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception: pass
        self.current_process = None; self.current_bat_name = None; self.update_hub_ui()

if __name__ == "__main__":
    try:
        myappid = 'saptale.zapretlauncher.modernui.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception: pass
    app = ZapretApp()
    app.mainloop()