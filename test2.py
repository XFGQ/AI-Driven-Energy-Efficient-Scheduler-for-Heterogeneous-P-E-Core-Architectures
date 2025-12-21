import pandas as pd
import numpy as np

def generate_os_data(n_samples=1000):
    np.random.seed(42)
    
    # Özellikler (Features)
    cpu_usage = np.random.uniform(0, 100, n_samples)
    ram_usage = np.random.uniform(0, 100, n_samples)
    priority = np.random.randint(1, 11, n_samples) # 1: Düşük, 10: Kritik
    
    # Karar Mekanizması (Etiketleme Mantığı)
    # Eğer CPU > 60 VE Priority > 5 ise P-Core (1), değilse E-Core (0)
    # Biraz da rastgelelik (gürültü) ekleyelim ki AI gerçekten "öğrenmek" zorunda kalsın
    labels = []
    for i in range(n_samples):
        score = (cpu_usage[i] * 0.6) + (priority[i] * 4)
        if score > 50:
            labels.append(1) # Performance Core
        else:
            labels.append(0) # Efficiency Core
            
    df = pd.DataFrame({
        'cpu_usage': cpu_usage,
        'ram_usage': ram_usage,
        'priority': priority,
        'target_core': labels
    })
    
    df.to_csv('os_tasks_dataset.csv', index=False)
    print("Veri seti 'os_tasks_dataset.csv' olarak kaydedildi!")
    print(df.head())

if __name__ == "__main__":
    generate_os_data()