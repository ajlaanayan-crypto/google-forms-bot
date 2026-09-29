import customtkinter as ctk
import requests
import threading
import time
import random
import string

# Theme and colors
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
COLOR_CYAN = "#00f3ff"
COLOR_PURPLE = "#8a2be2"
COLOR_BG = "#1e1e2f"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
]

CITIES = ["New York", "London", "Tokyo", "Paris", "Berlin", "Sydney", "Dubai", "Mumbai", "Toronto", "Singapore", "Los Angeles", "Rome", "Seoul"]

class FloatingButton(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.default_fg = kwargs.get('fg_color', ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        self.hover_fg = kwargs.get('hover_color', ctk.ThemeManager.theme["CTkButton"]["hover_color"])
        
    def on_enter(self, event):
        self.configure(border_color=COLOR_CYAN, border_width=2)
        
    def on_leave(self, event):
        self.configure(border_color="transparent", border_width=0)


class AntigravityApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Antigravity Form Bot")
        self.geometry("900x650")
        self.configure(fg_color=COLOR_BG)
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.is_running = False
        self.bot_thread = None
        self.total_submissions = 0
        
        self.create_left_panel()
        self.create_right_panel()

    def create_left_panel(self):
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        title = ctk.CTkLabel(self.left_frame, text="⚙️ CONFIGURATION", font=("Inter", 20, "bold"), text_color=COLOR_CYAN)
        title.pack(pady=(0, 20), anchor="w")
        
        self.url_entry = ctk.CTkEntry(self.left_frame, placeholder_text="Google Form POST URL (ends with formResponse)", width=350)
        self.url_entry.pack(pady=5, anchor="w")
        
        self.name_id_entry = ctk.CTkEntry(self.left_frame, placeholder_text="Name Entry ID (e.g. entry.123456)", width=350)
        self.name_id_entry.pack(pady=5, anchor="w")

        self.gender_id_entry = ctk.CTkEntry(self.left_frame, placeholder_text="Gender Entry ID", width=350)
        self.gender_id_entry.pack(pady=5, anchor="w")

        self.place_id_entry = ctk.CTkEntry(self.left_frame, placeholder_text="Place Entry ID", width=350)
        self.place_id_entry.pack(pady=5, anchor="w")

        self.other_id_entry = ctk.CTkEntry(self.left_frame, placeholder_text="Other/Dummy Entry ID", width=350)
        self.other_id_entry.pack(pady=5, anchor="w")
        
        names_label = ctk.CTkLabel(self.left_frame, text="Name List (One per line):", font=("Inter", 14), text_color=COLOR_PURPLE)
        names_label.pack(pady=(15, 5), anchor="w")
        
        self.names_textbox = ctk.CTkTextbox(self.left_frame, width=350, height=150)
        self.names_textbox.pack(pady=5, anchor="w")
        
        self.loop_switch = ctk.CTkSwitch(self.left_frame, text="Loop Names Infinitely", progress_color=COLOR_CYAN)
        self.loop_switch.pack(pady=15, anchor="w")
        
        self.start_btn = FloatingButton(self.left_frame, text="START SEQUENCE", fg_color=COLOR_PURPLE, hover_color="#6a1b9a", command=self.start_bot)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = FloatingButton(self.left_frame, text="ABORT", fg_color="#ff3366", hover_color="#cc0033", command=self.stop_bot)
        self.stop_btn.pack(side="left", padx=5)
        
    def create_right_panel(self):
        self.right_frame = ctk.CTkFrame(self, fg_color="#2a2a3f", corner_radius=15)
        self.right_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        dash_title = ctk.CTkLabel(self.right_frame, text="🛸 LIVE DASHBOARD", font=("Inter", 24, "bold"), text_color=COLOR_CYAN)
        dash_title.pack(pady=(30, 20))
        
        self.total_label = ctk.CTkLabel(self.right_frame, text="TOTAL SUBMISSIONS: 0", font=("Inter", 18, "bold"), text_color="white")
        self.total_label.pack(pady=10)
        
        self.current_name_label = ctk.CTkLabel(self.right_frame, text="CURRENT TARGET: NONE", font=("Inter", 16), text_color=COLOR_PURPLE)
        self.current_name_label.pack(pady=10)
        
        self.countdown_label = ctk.CTkLabel(self.right_frame, text="00:10", font=("Inter", 64, "bold"), text_color=COLOR_CYAN)
        self.countdown_label.pack(pady=40)
        
        self.log_textbox = ctk.CTkTextbox(self.right_frame, width=350, height=200, fg_color="#1e1e2f", text_color="#a0a0b0")
        self.log_textbox.pack(pady=10)
        self.log_textbox.insert("0.0", "System idle...\n")
        
    def log(self, message):
        # We need to make sure UI updates happen in a thread-safe way, 
        # customtkinter is mostly thread safe but it's best to handle properly if issues arise.
        # Standard insert is usually okay for simple logs.
        self.log_textbox.insert("end", f"> {message}\n")
        self.log_textbox.see("end")
        
    def start_bot(self):
        if self.is_running:
            return
            
        url = self.url_entry.get().strip()
        names_text = self.names_textbox.get("1.0", "end").strip()
        
        if not url or not names_text:
            self.log("ERROR: URL and Names are required.")
            return
            
        self.names_list = [n.strip() for n in names_text.split('\n') if n.strip()]
        self.original_names = list(self.names_list)
        
        if not self.names_list:
            self.log("ERROR: Name list is empty.")
            return
            
        self.is_running = True
        self.log("Sequence Initiated...")
        self.start_btn.configure(state="disabled")
        self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        if self.is_running:
            self.is_running = False
            self.log("ABORT SIGNAL RECEIVED. Stopping...")
            self.start_btn.configure(state="normal")
            
    def bot_loop(self):
        url = self.url_entry.get().strip()
        n_id = self.name_id_entry.get().strip()
        g_id = self.gender_id_entry.get().strip()
        p_id = self.place_id_entry.get().strip()
        o_id = self.other_id_entry.get().strip()
        
        while self.is_running:
            if not self.names_list:
                if self.loop_switch.get() == 1:
                    self.log("List ended. Looping back...")
                    self.names_list = list(self.original_names)
                else:
                    self.log("List completed. Sequence stopped.")
                    break
                    
            current_name = self.names_list.pop(0)
            self.current_name_label.configure(text=f"CURRENT TARGET: {current_name}")
            
            # Countdown
            for i in range(10, 0, -1):
                if not self.is_running:
                    break
                self.countdown_label.configure(text=f"00:{i:02d}")
                time.sleep(1)
                
            if not self.is_running:
                break
                
            self.countdown_label.configure(text="00:00")
            self.log(f"Submitting: {current_name}")
            
            # Prepare Payload
            payload = {}
            if n_id: payload[n_id] = current_name
            if g_id: payload[g_id] = random.choice(["Male", "Female"])
            if p_id: payload[p_id] = random.choice(CITIES)
            if o_id: payload[o_id] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            headers = {
                "User-Agent": random.choice(USER_AGENTS)
            }
            
            try:
                if url.endswith('viewform'):
                    url = url.replace('viewform', 'formResponse')
                response = requests.post(url, data=payload, headers=headers)
                
                # Google forms formResponse returns 200 on success
                if response.status_code in [200, 201]:
                    self.total_submissions += 1
                    self.total_label.configure(text=f"TOTAL SUBMISSIONS: {self.total_submissions}")
                    self.log("Status: SUCCESS (200)")
                else:
                    self.log(f"Status: FAILED ({response.status_code})")
            except Exception as e:
                self.log(f"Error: {e}")
                
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.countdown_label.configure(text="00:10")

if __name__ == "__main__":
    app = AntigravityApp()
    app.mainloop()
