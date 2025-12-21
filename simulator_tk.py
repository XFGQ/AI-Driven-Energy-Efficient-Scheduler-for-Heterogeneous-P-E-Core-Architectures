"""A minimal, standalone Tkinter simulator scaffold.
Usage:
    python simulator_tk.py
This file is a light demo and does not depend on model files; it has a placeholder decision function to be replaced by model inference.
"""
import tkinter as tk
from tkinter import ttk
import random
import threading
import time

class Task:
    def __init__(self, pid):
        self.pid = pid
        self.cpu_usage_pct = round(random.uniform(1, 100), 2)
        self.memory_mb = round(random.uniform(10, 1024), 2)
        self.estimated_time_s = round(random.expovariate(1/30), 2)

    def __str__(self):
        return f"PID:{self.pid} • CPU:{self.cpu_usage_pct}% • Est:{self.estimated_time_s}s"

class SimulatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Scheduler Simulator - Tkinter Demo")
        self.geometry("900x420")
        self._create_widgets()
        self.task_id = 2000
        self.running = False
        self.queue = []

    def _create_widgets(self):
        left = ttk.Frame(self, padding=8)
        left.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(left, text="Incoming Tasks").pack()
        self.queue_list = tk.Listbox(left, width=40, height=20)
        self.queue_list.pack()

        center = ttk.Frame(self, padding=8)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(center, text="AI Decision Engine").pack()
        self.decision_label = ttk.Label(center, text="Idle", font=(None, 14))
        self.decision_label.pack(pady=20)
        ttk.Button(center, text="Enqueue Random Task", command=self.enqueue_random).pack()
        ttk.Button(center, text="Start", command=self.start).pack(pady=4)
        ttk.Button(center, text="Stop", command=self.stop).pack()

        right = ttk.Frame(self, padding=8)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Label(right, text="P-Cores").pack()
        self.p_list = tk.Listbox(right, width=40, height=10)
        self.p_list.pack()
        ttk.Label(right, text="E-Cores").pack()
        self.e_list = tk.Listbox(right, width=40, height=10)
        self.e_list.pack()

    def enqueue_random(self):
        t = Task(self.task_id)
        self.task_id += 1
        self.queue.append(t)
        self.queue_list.insert(tk.END, str(t))

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self._main_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _ai_decision(self, task):
        # Placeholder: replace with model inference (e.g., load keras model and call predict)
        if task.cpu_usage_pct > 50 or task.estimated_time_s < 5:
            return 1
        return 0

    def _main_loop(self):
        while self.running:
            if self.queue:
                task = self.queue.pop(0)
                self.queue_list.delete(0)
                decision = self._ai_decision(task)
                self.decision_label.config(text=f"Assigning PID:{task.pid} → {'P' if decision==1 else 'E'}-core")
                if decision == 1:
                    self.p_list.insert(tk.END, f"{task.pid} • {task.cpu_usage_pct}%")
                else:
                    self.e_list.insert(tk.END, f"{task.pid} • {task.cpu_usage_pct}%")
            time.sleep(0.8)

if __name__ == "__main__":
    app = SimulatorApp()
    for _ in range(6):
        app.enqueue_random()
    app.mainloop()