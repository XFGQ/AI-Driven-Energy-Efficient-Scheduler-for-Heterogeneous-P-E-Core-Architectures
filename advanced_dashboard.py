import sys
import random
import numpy as np
import tensorflow as tf
import joblib
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QProgressBar, QFrame, QGridLayout)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# --- CONFIG ---
MODEL_PATH = 'advanced_scheduler_model.h5'
SCALER_PATH = 'advanced_scaler.pkl'

class SystemMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_data()
        self.init_ui()
        self.load_ai()
        
        # Timer for Real-Time Simulation
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_simulation_step)
        self.timer.start(1000) # Update every 1 second

    def init_data(self):
        self.total_energy_ai = 0
        self.total_energy_standard = 0
        self.history_ai = []
        self.history_std = []
        self.time_steps = []
        self.step_count = 0

    def init_ui(self):
        self.setWindowTitle("AI-Driven OS Scheduler | Heterogeneous Architecture Manager")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Header
        header = QLabel("⚡ Neural Network Scheduler & DVFS Controller")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #89b4fa; margin-bottom: 10px;")
        main_layout.addWidget(header)

        # 2. Main Dashboard Area
        dashboard_layout = QHBoxLayout()

        # LEFT PANEL: Incoming Task & AI Decision
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #313244; border-radius: 10px; padding: 10px;")
        left_layout = QVBoxLayout(left_panel)
        
        self.lbl_task = QLabel("No Active Task")
        self.lbl_task.setFont(QFont("Consolas", 12))
        self.lbl_task.setWordWrap(True)
        
        self.lbl_decision = QLabel("AI Decision: Pending...")
        self.lbl_decision.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.lbl_decision.setStyleSheet("color: #f9e2af;")

        left_layout.addWidget(QLabel("INCOMING TASK METRICS:"))
        left_layout.addWidget(self.lbl_task)
        left_layout.addWidget(self.lbl_decision)
        left_layout.addStretch()
        dashboard_layout.addWidget(left_panel, 1)

        # RIGHT PANEL: Cores Visualization
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #313244; border-radius: 10px; padding: 10px;")
        right_layout = QVBoxLayout(right_panel)
        
        # P-Core
        self.lbl_p = QLabel("🚀 Performance Core (P-Core)")
        self.bar_p = QProgressBar()
        self.bar_p.setStyleSheet("QProgressBar::chunk {background-color: #f38ba8;}")
        
        # E-Core
        self.lbl_e = QLabel("🌱 Efficiency Core (E-Core)")
        self.bar_e = QProgressBar()
        self.bar_e.setStyleSheet("QProgressBar::chunk {background-color: #a6e3a1;}")

        right_layout.addWidget(self.lbl_p)
        right_layout.addWidget(self.bar_p)
        right_layout.addWidget(self.lbl_e)
        right_layout.addWidget(self.bar_e)
        dashboard_layout.addWidget(right_panel, 1)

        main_layout.addLayout(dashboard_layout, 1)

        # 3. Statistics & Graph Area
        stats_frame = QFrame()
        stats_frame.setStyleSheet("background-color: #45475a; border-radius: 10px;")
        stats_layout = QHBoxLayout(stats_frame)

        # Text Stats
        self.lbl_stats = QLabel("Calculating Efficiency...")
        self.lbl_stats.setFont(QFont("Consolas", 11))
        stats_layout.addWidget(self.lbl_stats, 1)

        # Graph (Matplotlib)
        self.figure, self.ax = plt.subplots(figsize=(4, 2), dpi=100)
        self.figure.patch.set_facecolor('#45475a')
        self.ax.set_facecolor('#45475a')
        self.canvas = FigureCanvas(self.figure)
        stats_layout.addWidget(self.canvas, 2)

        main_layout.addWidget(stats_frame, 1)

    def load_ai(self):
        try:
            self.model = tf.keras.models.load_model(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
        except:
            print("Error: Train the model first!")
            sys.exit()

    def run_simulation_step(self):
        # 1. Simulate Incoming Task Metrics
        cpu = random.uniform(10, 100)
        ipc = random.uniform(0.5, 2.5)
        cache_miss = random.uniform(0, 100)
        temp = random.uniform(40, 90)

        # 2. AI Prediction
        features = np.array([[cpu, ipc, cache_miss, temp]])
        scaled_features = self.scaler.transform(features)
        
        # Multi-output prediction
        pred_core, pred_freq = self.model.predict(scaled_features, verbose=0)
        
        core_decision = 1 if pred_core[0][0] > 0.5 else 0 # 1=P, 0=E
        freq_decision = np.argmax(pred_freq[0]) # 0=Low, 1=Med, 2=High
        
        # 3. Energy Calculation (Simulated Physics)
        # Power = Base + (Load * CoreFactor * FreqFactor)
        # P-Core is expensive, E-Core is cheap. High Freq is expensive.
        
        # AI Energy
        core_factor_ai = 2.0 if core_decision == 1 else 0.8
        freq_factor_ai = [0.5, 1.0, 1.5][freq_decision]
        power_ai = (cpu * 0.1) * core_factor_ai * freq_factor_ai
        
        # Standard Scheduler Energy (Dumb Logic: Always P-Core for high load)
        core_factor_std = 2.0 if cpu > 50 else 0.8
        freq_factor_std = 1.5 # Standard usually runs high freq
        power_std = (cpu * 0.1) * core_factor_std * freq_factor_std

        # Update Totals
        self.total_energy_ai += power_ai
        self.total_energy_standard += power_std
        
        # 4. Update UI
        self.update_ui(cpu, ipc, cache_miss, temp, core_decision, freq_decision, power_ai, power_std)
        self.update_graph()

    def update_ui(self, cpu, ipc, cache, temp, core, freq, p_ai, p_std):
        freq_str = ["LOW", "MED", "HIGH"][freq]
        core_str = "P-CORE" if core == 1 else "E-CORE"
        
        # Task Info
        self.lbl_task.setText(
            f"CPU Load: {cpu:.1f}%\n"
            f"IPC: {ipc:.2f}\n"
            f"Cache Miss: {cache:.1f}%\n"
            f"Temp: {temp:.1f}°C"
        )
        
        # Decision Info
        color = "#f38ba8" if core == 1 else "#a6e3a1"
        self.lbl_decision.setText(f"Core: {core_str}\nFreq: {freq_str}")
        self.lbl_decision.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 16px;")

        # Progress Bars
        if core == 1:
            self.bar_p.setValue(int(cpu))
            self.bar_e.setValue(0)
        else:
            self.bar_e.setValue(int(cpu))
            self.bar_p.setValue(0)

        # Stats Text
        saving = ((self.total_energy_standard - self.total_energy_ai) / self.total_energy_standard) * 100
        self.lbl_stats.setText(
            f"⚡ Total Energy Consumed:\n"
            f"   Standard Scheduler: {self.total_energy_standard:.1f} J\n"
            f"   AI Scheduler:       {self.total_energy_ai:.1f} J\n"
            f"   --------------------------\n"
            f"   EFFICIENCY GAIN:    {saving:.1f}%"
        )

    def update_graph(self):
        self.step_count += 1
        self.time_steps.append(self.step_count)
        self.history_ai.append(self.total_energy_ai)
        self.history_std.append(self.total_energy_standard)

        # Keep graph clean (last 50 points)
        if len(self.time_steps) > 50:
            self.time_steps.pop(0)
            self.history_ai.pop(0)
            self.history_std.pop(0)

        self.ax.clear()
        self.ax.plot(self.time_steps, self.history_std, color='#f38ba8', linestyle='--', label='Standard')
        self.ax.plot(self.time_steps, self.history_ai, color='#a6e3a1', linewidth=2, label='AI-Driven')
        self.ax.legend(loc='upper left', fontsize='small')
        self.ax.set_title("Real-Time Energy Consumption (Lower is Better)", color='white', fontsize=10)
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.grid(True, linestyle=':', alpha=0.3)
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemMonitor()
    window.show()
    sys.exit(app.exec_())