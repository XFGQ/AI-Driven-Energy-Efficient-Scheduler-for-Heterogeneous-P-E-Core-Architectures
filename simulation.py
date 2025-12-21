import sys
import random
import numpy as np
import pandas as pd
import tensorflow as tf
import joblib
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

# --- AYARLAR ---
MODEL_PATH = 'scheduler_model.h5'
SCALER_PATH = 'scaler.pkl'

class SchedulerSimulation(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui() 
        self.load_ai_brain()
        
        # Simülasyon değişkenleri
        
        self.total_energy = 0
        self.total_tasks = 0
        self.p_core_tasks = 0
        self.e_core_tasks = 0

        # Zamanlayıcı (OS Clock) - Her 1.5 saniyede bir görev gelir
        self.timer = QTimer()
        self.timer.timeout.connect(self.generate_and_schedule_task)
        self.timer.start(1500) 

    def init_ui(self):
        self.setWindowTitle('AI-Driven Hybrid CPU Scheduler')
        self.setGeometry(100, 100, 800, 500)
        self.setStyleSheet("background-color: #2b2b2b; color: white;")

        layout = QVBoxLayout()

        # Başlık
        title = QLabel("AI-Driven Energy Management System")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # --- ÜST KISIM: Gelen Görev Bilgisi ---
        self.lbl_task_info = QLabel("Sistem Bekleniyor...")
        self.lbl_task_info.setFont(QFont("Consolas", 14))
        self.lbl_task_info.setStyleSheet("color: #00e5ff; border: 1px solid #444; padding: 10px;")
        layout.addWidget(self.lbl_task_info)

        # --- ORTA KISIM: Çekirdekler ---
        cores_layout = QHBoxLayout()

        # P-CORE (Performans)
        p_frame = QFrame()
        p_frame.setStyleSheet("background-color: #4a1414; border-radius: 10px; padding: 10px;")
        p_layout = QVBoxLayout()
        p_label = QLabel("🔥 PERFORMANCE CORE (P)")
        p_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.p_bar = QProgressBar()
        self.p_bar.setStyleSheet("QProgressBar::chunk { background-color: #ff3333; }")
        self.p_bar.setValue(0)
        p_layout.addWidget(p_label)
        p_layout.addWidget(self.p_bar)
        p_frame.setLayout(p_layout)
        cores_layout.addWidget(p_frame)

        # E-CORE (Verimlilik)
        e_frame = QFrame()
        e_frame.setStyleSheet("background-color: #144a1e; border-radius: 10px; padding: 10px;")
        e_layout = QVBoxLayout()
        e_label = QLabel("🌱 EFFICIENCY CORE (E)")
        e_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.e_bar = QProgressBar()
        self.e_bar.setStyleSheet("QProgressBar::chunk { background-color: #33ff66; }")
        self.e_bar.setValue(0)
        e_layout.addWidget(e_label)
        e_layout.addWidget(self.e_bar)
        e_frame.setLayout(e_layout)
        cores_layout.addWidget(e_frame)

        layout.addLayout(cores_layout)

        # --- ALT KISIM: İstatistikler ---
        stats_layout = QHBoxLayout()
        self.lbl_stats = QLabel("Tasks: 0 | P-Core: 0 | E-Core: 0")
        self.lbl_energy = QLabel("⚡ Energy Impact: 0 W")
        self.lbl_stats.setFont(QFont("Arial", 12))
        self.lbl_energy.setFont(QFont("Arial", 12, QFont.Bold))
        self.lbl_energy.setStyleSheet("color: #ffd700;")
        
        stats_layout.addWidget(self.lbl_stats)
        stats_layout.addWidget(self.lbl_energy)
        layout.addLayout(stats_layout)

        self.setLayout(layout)

    def load_ai_brain(self):
        try:
            self.model = tf.keras.models.load_model(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            print("AI Modeli Başarıyla Yüklendi!")
        except Exception as e:
            self.lbl_task_info.setText(f"HATA: Model yüklenemedi! ({e})")
            self.timer.stop()

    def generate_and_schedule_task(self):
        # 1. Rastgele Görev Oluştur
        cpu = random.uniform(5, 100)
        ram = random.uniform(5, 100)
        prio = random.randint(1, 10)
        
        task_name = f"Process_ID_{random.randint(1000, 9999)}"
        
        # 2. AI Tahmini İçin Veriyi Hazırla
        input_data = np.array([[cpu, ram, prio]])
        input_scaled = self.scaler.transform(input_data)
        
        # 3. Model Tahmini
        prediction_prob = self.model.predict(input_scaled, verbose=0)[0][0]
        decision = 1 if prediction_prob > 0.5 else 0 # 1: P-Core, 0: E-Core
        
        # 4. Arayüzü Güncelle
        self.update_simulation(task_name, cpu, ram, prio, decision)

    def update_simulation(self, name, cpu, ram, prio, decision):
        self.total_tasks += 1
        
        core_name = ""
        if decision == 1: # P-Core
            core_name = "P-CORE"
            self.p_core_tasks += 1
            # P-Core daha çok enerji harcar (Örnek: 15W)
            self.total_energy += 15 
            # Görsel efekt: Barı doldur
            new_val = min(100, self.p_bar.value() + int(cpu / 5))
            self.p_bar.setValue(new_val)
            self.e_bar.setValue(max(0, self.e_bar.value() - 5)) # Diğeri soğusun
        else: # E-Core
            core_name = "E-CORE"
            self.e_core_tasks += 1
            # E-Core az enerji harcar (Örnek: 4W)
            self.total_energy += 4
            # Görsel efekt
            new_val = min(100, self.e_bar.value() + int(cpu / 5))
            self.e_bar.setValue(new_val)
            self.p_bar.setValue(max(0, self.p_bar.value() - 5))

        # Metin Güncelleme
        info_text = f"GELEN GÖREV: {name}\nCPU: %{cpu:.1f} | RAM: %{ram:.1f} | Priority: {prio}\nKARAR: {core_name}"
        self.lbl_task_info.setText(info_text)
        
        # Renk Değişimi (Karara göre metin rengi)
        if decision == 1:
            self.lbl_task_info.setStyleSheet("color: #ff5555; border: 2px solid #ff5555; padding: 10px; font-size: 16px;")
        else:
            self.lbl_task_info.setStyleSheet("color: #55ff55; border: 2px solid #55ff55; padding: 10px; font-size: 16px;")

        self.lbl_stats.setText(f"Total Tasks: {self.total_tasks} | P-Core: {self.p_core_tasks} | E-Core: {self.e_core_tasks}")
        self.lbl_energy.setText(f"⚡ Est. Energy: {self.total_energy} Joules")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SchedulerSimulation()
    ex.show()
    sys.exit(app.exec_())