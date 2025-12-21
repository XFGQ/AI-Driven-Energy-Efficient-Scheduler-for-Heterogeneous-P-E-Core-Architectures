import numpy as np

# Basit bir karar mekanizması simülasyonu (Örnek)
def ai_scheduler_decision(cpu_usage, memory_usage):
    # Bu normalde eğitilmiş bir model olacak
    # Şimdilik basit bir mantık: 
    # Yüksek CPU ve RAM isteyenler P-Core'a (1), diğerleri E-Core'a (0)
    score = (cpu_usage * 0.7) + (memory_usage * 0.3)
    return 1 if score > 50 else 0

# Test:
process_data = {"name": "Video Rendering", "cpu": 85, "mem": 70}
decision = ai_scheduler_decision(process_data["cpu"], process_data["mem"])

print(f"Görev: {process_data['name']} -> Atanan Çekirdek: {'P-Core' if decision == 1 else 'E-Core'}")