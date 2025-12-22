import sys
import time
import psutil
import numpy as np
import tensorflow as tf
import joblib
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QLabel, QProgressBar, QFrame, QPushButton, 
                             QTabWidget, QScrollArea, QTextEdit, QLCDNumber)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import multiprocessing

# --- AYARLAR ---
MODEL_PATH = 'advanced_scheduler_model.h5'
SCALER_PATH = 'advanced_scaler.pkl'

# --- STRESS TEST İŞÇİSİ (GLOBAL FONKSİYON) ---
def stress_worker():
    while True:
        _ = 999999 * 999999

# --- ARKA PLAN VERİ İŞÇİSİ ---
class DataWorker(QThread):
    data_signal = pyqtSignal(dict) 

    def __init__(self, model, scaler):
        super().__init__()
        self.model = model
        self.scaler = scaler
        self.running = True
        self.stress_processes = [] 

    def run(self):
        while self.running:
            try:
                cpu_percents = psutil.cpu_percent(interval=0.5, percpu=True)
                ram = psutil.virtual_memory()
                
                core_data = []
                total_power_ai = 0
                total_power_std = 0
                
                for cpu_load in cpu_percents:
                    # Simülasyon Verileri
                    ipc = 0.5 + (cpu_load / 100.0) * 2.5
                    cache_miss = (ram.percent * 0.5) + (cpu_load * 0.3)
                    temp = 35 + (cpu_load * 0.55) 
                    
                    # AI Tahmini
                    features = np.array([[cpu_load, ipc, cache_miss, temp]])
                    scaled = self.scaler.transform(features)
                    p_core, p_freq = self.model.predict(scaled, verbose=0)
                    
                    is_p_core = p_core[0][0] > 0.5
                    freq_idx = np.argmax(p_freq[0]) 
                    
                    voltage = 0.8 + (freq_idx * 0.2)
                    frequency = 1.8 + (freq_idx * 1.2) if is_p_core else 1.2 + (freq_idx * 0.6)
                    
                    # Enerji (Watt)
                    p_ai = (cpu_load * 0.1) * (2.0 if is_p_core else 0.8) * voltage
                    p_std = (cpu_load * 0.1) * (2.0 if cpu_load > 40 else 0.8) * 1.2
                    
                    total_power_ai += p_ai
                    total_power_std += p_std
                    
                    core_data.append({
                        'load': cpu_load,
                        'temp': temp,
                        'is_p': is_p_core,
                        'freq_val': frequency,
                        'ipc': ipc
                    })

                data_packet = {
                    'cores': core_data,
                    'ram_percent': ram.percent,
                    'ram_used': ram.used / (1024**3),
                    'ram_total': ram.total / (1024**3),
                    'power_ai': total_power_ai,
                    'power_std': total_power_std
                }
                
                self.data_signal.emit(data_packet)
                
            except Exception as e:
                print(f"Worker Error: {e}")

    def start_stress(self):
        if not self.stress_processes:
            num_cores = multiprocessing.cpu_count()
            for _ in range(num_cores):
                p = multiprocessing.Process(target=stress_worker)
                p.start()
                self.stress_processes.append(p)

    def stop_stress(self):
        if self.stress_processes:
            for p in self.stress_processes:
                p.terminate()
                p.join()
            self.stress_processes = []

    def stop(self):
        self.running = False
        self.stop_stress()
        self.wait()

# --- ANA DASHBOARD ---
class UltimateDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_models()
        self.init_ui()
        self.start_worker()
        self.add_log("System initialized. Waiting for task scheduler...")

    def load_models(self):
        try:
            self.model = tf.keras.models.load_model(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
        except:
            print("Model dosyaları eksik!")
            sys.exit()

    def init_ui(self):
        self.setWindowTitle("AI-OS Scheduler | Advanced Control Center")
        self.setGeometry(50, 50, 1400, 900)
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1b26; }
            QLabel { color: #a9b1d6; font-family: 'Segoe UI'; }
            QProgressBar { border: 1px solid #414868; border-radius: 4px; background-color: #24283b; }
            QProgressBar::chunk { background-color: #7aa2f7; }
            QTabWidget::pane { border: 1px solid #414868; }
            QTabBar::tab { background: #24283b; color: white; padding: 10px; }
            QTabBar::tab:selected { background: #414868; }
            QPushButton { background-color: #7aa2f7; color: #1a1b26; font-weight: bold; border-radius: 5px; padding: 8px; }
            QPushButton:hover { background-color: #bb9af7; }
            QPushButton#stop_btn { background-color: #f7768e; color: white; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # --- SOL TARAF (CORE GRID + GRAFİKLER) ---
        left_layout = QVBoxLayout()
        header = QLabel("HETEROGENEOUS CORE ARCHITECTURE MAP")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setStyleSheet("color: #7dcfff; letter-spacing: 2px;")
        left_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: transparent;")
        grid_container = QWidget()
        grid_container.setStyleSheet("background-color: transparent;")
        self.core_grid = QGridLayout(grid_container)
        self.core_widgets = []
        
        self.cpu_count = psutil.cpu_count(logical=True)
        for i in range(self.cpu_count):
            widget = self.create_core_card(i)
            self.core_grid.addWidget(widget, i // 4, i % 4)
            self.core_widgets.append(widget)
            
        scroll.setWidget(grid_container)
        left_layout.addWidget(scroll)
        
        # Grafikler
        self.tabs = QTabWidget()
        self.tabs.setFixedHeight(250)
        
        self.fig_power, self.ax_power = plt.subplots(figsize=(5, 2))
        self.fig_power.patch.set_facecolor('#1a1b26')
        self.ax_power.set_facecolor('#24283b')
        self.canvas_power = FigureCanvas(self.fig_power)
        self.tabs.addTab(self.canvas_power, "⚡ Power Consumption (W)")
        
        self.fig_eff, self.ax_eff = plt.subplots(figsize=(5, 2))
        self.fig_eff.patch.set_facecolor('#1a1b26')
        self.ax_eff.set_facecolor('#24283b')
        self.canvas_eff = FigureCanvas(self.fig_eff)
        self.tabs.addTab(self.canvas_eff, "🌱 Energy Savings (%)")

        left_layout.addWidget(self.tabs)
        main_layout.addLayout(left_layout, 7)

        # --- SAĞ TARAF (RAM + POWER + LOGS) ---
        right_layout = QVBoxLayout()
        
        # 1. RAM
        ram_frame = QFrame()
        ram_frame.setStyleSheet("background-color: #24283b; border-radius: 10px; padding: 15px;")
        ram_vbox = QVBoxLayout(ram_frame)
        ram_vbox.addWidget(QLabel("MEMORY (RAM) USAGE"))
        self.ram_bar = QProgressBar()
        self.ram_bar.setFixedHeight(20)
        self.ram_lbl = QLabel("0 GB / 0 GB")
        self.ram_lbl.setAlignment(Qt.AlignRight)
        ram_vbox.addWidget(self.ram_bar)
        ram_vbox.addWidget(self.ram_lbl)
        right_layout.addWidget(ram_frame)

        # 2. POWER
        power_frame = QFrame()
        power_frame.setStyleSheet("background-color: #24283b; border-radius: 10px; padding: 15px; margin-top: 10px;")
        power_vbox = QVBoxLayout(power_frame)
        
        lbl_pwr_title = QLabel("POWER CONSUMPTION")
        lbl_pwr_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_pwr_title.setStyleSheet("color: white;")
        power_vbox.addWidget(lbl_pwr_title)
        
        lcd_layout = QHBoxLayout()
        self.lcd_power = QLCDNumber()
        self.lcd_power.setDigitCount(4)
        self.lcd_power.setStyleSheet("color: #e0af68; border: none;")
        self.lcd_power.setFixedHeight(60)
        
        lbl_unit = QLabel("W")
        lbl_unit.setFont(QFont("Segoe UI", 24, QFont.Bold))
        lbl_unit.setStyleSheet("color: #e0af68; margin-left: 5px;")
        lbl_unit.setAlignment(Qt.AlignBottom)
        
        lcd_layout.addWidget(self.lcd_power)
        lcd_layout.addWidget(lbl_unit)
        power_vbox.addLayout(lcd_layout)
        right_layout.addWidget(power_frame)

        # 3. BUTTONS (Sadece Stress Test Kaldı)
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet("background-color: #414868; border-radius: 10px; padding: 5px; margin-top: 10px;")
        ctrl_vbox = QVBoxLayout(ctrl_frame)
        
        self.btn_stress = QPushButton(" START STRESS TEST")
        self.btn_stress.setFixedHeight(50)
        self.btn_stress.clicked.connect(self.toggle_stress)
        ctrl_vbox.addWidget(self.btn_stress)
        right_layout.addWidget(ctrl_frame)

        # 4. KERNEL LOGS (Embedded - Yeni Kısım)
        log_frame = QFrame()
        log_frame.setStyleSheet("background-color: #0f0f14; border-radius: 10px; padding: 5px; margin-top: 10px;")
        log_layout = QVBoxLayout(log_frame)
        
        log_title = QLabel("> SYSTEM KERNEL LOGS")
        log_title.setFont(QFont("Consolas", 10, QFont.Bold))
        log_title.setStyleSheet("color: #9ece6a;")
        log_layout.addWidget(log_title)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("border: none; background-color: transparent; color: #9ece6a; font-family: Consolas; font-size: 11px;")
        log_layout.addWidget(self.log_area)
        
        right_layout.addWidget(log_frame, 2) # 2 birim yer kaplasın (esnek)

        main_layout.addLayout(right_layout, 3)

        self.history_ai = [0] * 50
        self.history_std = [0] * 50
        self.history_saving = [0] * 50

    def create_core_card(self, index):
        frame = QFrame()
        frame.setStyleSheet("background-color: #1f2335; border-radius: 8px; border: 1px solid #2f354b;")
        layout = QVBoxLayout(frame)
        
        top_row = QHBoxLayout()
        name_lbl = QLabel(f"CORE {index}")
        name_lbl.setFont(QFont("Consolas", 10, QFont.Bold))
        type_lbl = QLabel("IDLE")
        type_lbl.setObjectName("type_lbl") 
        type_lbl.setFont(QFont("Arial", 8, QFont.Bold))
        top_row.addWidget(name_lbl)
        top_row.addStretch()
        top_row.addWidget(type_lbl)
        layout.addLayout(top_row)
        
        bar = QProgressBar()
        bar.setFixedHeight(10)
        bar.setTextVisible(False)
        bar.setObjectName("load_bar")
        layout.addWidget(bar)
        
        details = QGridLayout()
        details.addWidget(QLabel("Freq:"), 0, 0)
        freq_val = QLabel("0.0 GHz")
        freq_val.setObjectName("freq_val")
        details.addWidget(freq_val, 0, 1)
        
        details.addWidget(QLabel("Temp:"), 0, 2)
        temp_val = QLabel("0°C")
        temp_val.setObjectName("temp_val")
        details.addWidget(temp_val, 0, 3)
        
        details.addWidget(QLabel("IPC:"), 1, 0)
        ipc_val = QLabel("0.00")
        ipc_val.setObjectName("ipc_val")
        details.addWidget(ipc_val, 1, 1)

        layout.addLayout(details)
        
        frame.layout_refs = {
            'type': type_lbl,
            'bar': bar,
            'freq': freq_val,
            'temp': temp_val,
            'ipc': ipc_val,
            'frame': frame
        }
        return frame

    def start_worker(self):
        self.worker = DataWorker(self.model, self.scaler)
        self.worker.data_signal.connect(self.update_dashboard)
        self.worker.start()

    def add_log(self, message):
        """Logları sağ alttaki ekrana yazar"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        # Otomatik aşağı kaydır
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def update_dashboard(self, data):
        # Core Update
        for i, core_data in enumerate(data['cores']):
            widgets = self.core_widgets[i].layout_refs
            
            widgets['bar'].setValue(int(core_data['load']))
            widgets['freq'].setText(f"{core_data['freq_val']:.1f} GHz")
            widgets['temp'].setText(f"{int(core_data['temp'])}°C")
            widgets['ipc'].setText(f"{core_data['ipc']:.2f}")
            
            if core_data['is_p']:
                widgets['type'].setText("P-CORE")
                widgets['type'].setStyleSheet("color: #f7768e; background-color: #2a1b1b; padding: 2px;")
                widgets['frame'].setStyleSheet("background-color: #2a1b1b; border: 1px solid #f7768e; border-radius: 8px;")
                widgets['bar'].setStyleSheet("QProgressBar::chunk { background-color: #f7768e; }")
            else:
                widgets['type'].setText("E-CORE")
                widgets['type'].setStyleSheet("color: #9ece6a; background-color: #1b2a1b; padding: 2px;")
                widgets['frame'].setStyleSheet("background-color: #1b2a1b; border: 1px solid #9ece6a; border-radius: 8px;")
                widgets['bar'].setStyleSheet("QProgressBar::chunk { background-color: #9ece6a; }")

        self.ram_bar.setValue(int(data['ram_percent']))
        self.ram_lbl.setText(f"{data['ram_used']:.1f} GB / {data['ram_total']:.1f} GB")
        self.lcd_power.display(int(data['power_ai']))

        self.update_graphs(data['power_ai'], data['power_std'])
        
        # Sadece kritik olaylarda log bas (Çok hızlı akmasın)
        if data['power_ai'] > 120 and (int(time.time()) % 2 == 0): 
            self.add_log(f"HIGH LOAD! Power Spike: {int(data['power_ai'])}W - Tuning Frequencies...")

    def update_graphs(self, ai_pow, std_pow):
        self.history_ai.append(ai_pow)
        self.history_std.append(std_pow)
        self.history_ai.pop(0)
        self.history_std.pop(0)
        
        saving = 0
        if std_pow > 0:
            saving = ((std_pow - ai_pow) / std_pow) * 100
        self.history_saving.append(saving)
        self.history_saving.pop(0)

        self.ax_power.clear()
        self.ax_power.plot(self.history_std, color='#f7768e', linestyle='--', label='Standard OS')
        self.ax_power.plot(self.history_ai, color='#9ece6a', label='AI-Driven')
        self.ax_power.legend(loc='upper left', fontsize=8)
        self.ax_power.grid(True, alpha=0.2)
        self.ax_power.tick_params(colors='white')
        self.canvas_power.draw()
        
        self.ax_eff.clear()
        self.ax_eff.plot(self.history_saving, color='#7dcfff', label='Energy Savings (%)')
        self.ax_eff.fill_between(range(50), self.history_saving, color='#7dcfff', alpha=0.3)
        self.ax_eff.set_ylim(-10, 100)
        self.ax_eff.grid(True, alpha=0.2)
        self.ax_eff.tick_params(colors='white')
        self.canvas_eff.draw()

    def toggle_stress(self):
        if self.btn_stress.text() == "🔥 START STRESS TEST":
            self.worker.start_stress()
            self.btn_stress.setText("⏹ STOP STRESS TEST")
            self.btn_stress.setObjectName("stop_btn")
            self.btn_stress.setStyleSheet("background-color: #f7768e; color: white;")
            self.add_log("WARNING: USER INITIATED STRESS TEST. CPU LOAD 100%")
        else:
            self.worker.stop_stress()
            self.btn_stress.setText("🔥 START STRESS TEST")
            self.btn_stress.setObjectName("")
            self.btn_stress.setStyleSheet("background-color: #7aa2f7; color: #1a1b26;")
            self.add_log("Stress test terminated. Returning to IDLE state.")

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    window = UltimateDashboard()
    window.show()
    sys.exit(app.exec_())