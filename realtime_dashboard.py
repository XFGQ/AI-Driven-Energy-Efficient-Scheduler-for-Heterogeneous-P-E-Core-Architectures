import sys
import random
import numpy as np
import tensorflow as tf
import joblib
import psutil  # <--- YENİ KÜTÜPHANE: Gerçek donanım verisi için
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QProgressBar, QFrame)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# --- CONFIG ---
MODEL_PATH = 'advanced_scheduler_model.h5'
SCALER_PATH = 'advanced_scaler.pkl'

class RealTimeMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_data()
        self.init_ui()
        self.load_ai()
        
        # Gerçek zamanlı izleme için Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_realtime_step)
        self.timer.start(1000) # Her 1 saniyede bir güncelle

    def init_data(self):
        self.total_energy_ai = 0
        self.total_energy_standard = 0
        self.history_ai = []
        self.history_std = []
        self.time_steps = []
        self.step_count = 0

    def init_ui(self):
        self.setWindowTitle("AI-Driven OS Scheduler | REAL-TIME HARDWARE MONITOR")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("background-color: #1a1b26; color: #a9b1d6;") # Tema: Tokyo Night

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Başlık
        header = QLabel("⚡ LIVE HARDWARE AI SCHEDULER")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #7aa2f7; margin-bottom: 10px;")
        main_layout.addWidget(header)

        # 2. Dashboard Paneli
        dashboard_layout = QHBoxLayout()

        # SOL PANEL: Gerçek Veriler
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #24283b; border-radius: 10px; padding: 10px;")
        left_layout = QVBoxLayout(left_panel)
        
        self.lbl_hardware = QLabel("Reading Sensors...")
        self.lbl_hardware.setFont(QFont("Consolas", 12))
        self.lbl_hardware.setStyleSheet("color: #9ece6a;") # Yeşilimsi
        
        self.lbl_decision = QLabel("AI Decision: Pending...")
        self.lbl_decision.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.lbl_decision.setStyleSheet("color: #e0af68;")

        left_layout.addWidget(QLabel("YOUR SYSTEM METRICS (LIVE):"))
        left_layout.addWidget(self.lbl_hardware)
        left_layout.addWidget(self.lbl_decision)
        left_layout.addStretch()
        dashboard_layout.addWidget(left_panel, 1)

        # SAĞ PANEL: Çekirdek Simülasyonu
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #24283b; border-radius: 10px; padding: 10px;")
        right_layout = QVBoxLayout(right_panel)
        
        # P-Core
        self.lbl_p = QLabel("🚀 Performance Core Assignment")
        self.bar_p = QProgressBar()
        self.bar_p.setStyleSheet("QProgressBar::chunk {background-color: #f7768e;}") # Kırmızımsı
        
        # E-Core
        self.lbl_e = QLabel("🌱 Efficiency Core Assignment")
        self.bar_e = QProgressBar()
        self.bar_e.setStyleSheet("QProgressBar::chunk {background-color: #9ece6a;}") # Yeşil

        right_layout.addWidget(self.lbl_p)
        right_layout.addWidget(self.bar_p)
        right_layout.addWidget(self.lbl_e)
        right_layout.addWidget(self.bar_e)
        dashboard_layout.addWidget(right_panel, 1)

        main_layout.addLayout(dashboard_layout, 1)

        # 3. İstatistik ve Grafik
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: #414868; border-radius: 10px;")
        stats_layout = QHBoxLayout(stats_frame)

        self.lbl_stats = QLabel("Calculating Efficiency...")
        self.lbl_stats.setFont(QFont("Consolas", 11))
        stats_layout.addWidget(self.lbl_stats, 1)

        # Grafik
        self.figure, self.ax = plt.subplots(figsize=(4, 2), dpi=100)
        self.figure.patch.set_facecolor('#414868')
        self.ax.set_facecolor('#414868')
        self.canvas = FigureCanvas(self.figure)
        stats_layout.addWidget(self.canvas, 2)

        main_layout.addWidget(stats_frame, 1)

    def load_ai(self):
        try:
            self.model = tf.keras.models.load_model(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
        except:
            print("HATA: Önce train_advanced_model.py çalıştırılmalı!")
            sys.exit()

    def run_realtime_step(self):
        # --- 1. GERÇEK SİSTEM VERİLERİNİ OKU ---
        real_cpu = psutil.cpu_percent()
        real_ram = psutil.virtual_memory().percent
        
        # IPC ve Cache Miss gibi verileri Python ile doğrudan okumak zordur (Root yetkisi gerekir).
        # Bu yüzden gerçek CPU yüküne dayalı mantıklı bir tahmin (Heuristic) yapıyoruz:
        
        # Eğer CPU çok yoğunsa, IPC genelde yüksektir.
        estimated_ipc = 0.5 + (real_cpu / 100.0) * 2.0 + random.uniform(-0.2, 0.2)
        
        # RAM kullanımı çoksa, Cache Miss ihtimali artar.
        estimated_cache_miss = (real_ram * 0.8) + random.uniform(0, 10)
        
        # Sıcaklık tahmini (CPU yüküne göre)
        estimated_temp = 40 + (real_cpu * 0.5)

        # --- 2. AI TAHMİNİ ---
        features = np.array([[real_cpu, estimated_ipc, estimated_cache_miss, estimated_temp]])
        scaled_features = self.scaler.transform(features)
        
        pred_core, pred_freq = self.model.predict(scaled_features, verbose=0)
        
        core_decision = 1 if pred_core[0][0] > 0.5 else 0 # 1=P, 0=E
        freq_decision = np.argmax(pred_freq[0]) # 0=Low, 1=Med, 2=High
        
        # --- 3. ENERJİ HESAPLAMA (Simüle Edilmiş Fizik) ---
        # AI Enerjisi
        core_factor_ai = 2.0 if core_decision == 1 else 0.8
        freq_factor_ai = [0.5, 1.0, 1.5][freq_decision]
        power_ai = (real_cpu * 0.1) * core_factor_ai * freq_factor_ai
        
        # Standart Scheduler (Kural Tabanlı - Aptal) Enerjisi
        # Standart scheduler genelde %40 yükü geçerse hemen P-Core açar
        core_factor_std = 2.0 if real_cpu > 40 else 0.8
        power_std = (real_cpu * 0.1) * core_factor_std * 1.5 

        # Toplamları Güncelle
        self.total_energy_ai += power_ai
        self.total_energy_standard += power_std
        
        # --- 4. ARAYÜZÜ GÜNCELLE ---
        self.update_ui(real_cpu, real_ram, estimated_ipc, estimated_temp, 
                       core_decision, freq_decision)
        self.update_graph()

    def update_ui(self, cpu, ram, ipc, temp, core, freq):
        freq_str = ["LOW", "MED", "HIGH"][freq]
        core_str = "P-CORE" if core == 1 else "E-CORE"
        
        # Donanım Bilgisi
        self.lbl_hardware.setText(
            f"REAL CPU LOAD: {cpu:.1f}%\n"
            f"REAL RAM USAGE: {ram:.1f}%\n"
            f"Est. IPC: {ipc:.2f} | Temp: {temp:.1f}°C"
        )
        
        # Karar Bilgisi
        color = "#f7768e" if core == 1 else "#9ece6a"
        self.lbl_decision.setText(f"AI Assigns: {core_str}\nSet Freq: {freq_str}")
        self.lbl_decision.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 16px;")

        # Barlar
        if core == 1:
            self.bar_p.setValue(int(cpu))
            self.bar_e.setValue(0)
        else:
            self.bar_e.setValue(int(cpu))
            self.bar_p.setValue(0)

        # İstatistikler
        diff = self.total_energy_standard - self.total_energy_ai
        saving = (diff / self.total_energy_standard) * 100 if self.total_energy_standard > 0 else 0
        
        self.lbl_stats.setText(
            f"⚡ ENERGY CONSUMPTION (Simulated):\n"
            f"   Std. Scheduler: {self.total_energy_standard:.1f} J\n"
            f"   AI Scheduler:   {self.total_energy_ai:.1f} J\n"
            f"   SAVINGS:        {saving:.1f}%"
        )

    def update_graph(self):
        self.step_count += 1
        self.time_steps.append(self.step_count)
        self.history_ai.append(self.total_energy_ai)
        self.history_std.append(self.total_energy_standard)

        if len(self.time_steps) > 50:
            self.time_steps.pop(0)
            self.history_ai.pop(0)
            self.history_std.pop(0)

        self.ax.clear()
        self.ax.plot(self.time_steps, self.history_std, color='#f7768e', linestyle='--', label='Standard')
        self.ax.plot(self.time_steps, self.history_ai, color='#9ece6a', linewidth=2, label='AI-Driven')
        self.ax.legend(loc='upper left', fontsize='small')
        self.ax.set_title("Real-Time Energy Impact", color='white', fontsize=10)
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.grid(True, linestyle=':', alpha=0.3)
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RealTimeMonitor()
    window.show()
    sys.exit(app.exec_())