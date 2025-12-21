import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

# 1. Veri Setini Yükle
print("Veri seti yükleniyor...")
df = pd.read_csv('os_tasks_dataset.csv')

# Girdiler (X) ve Hedef (y)
X = df[['cpu_usage', 'ram_usage', 'priority']] # Bu özelliklere bakacak
y = df['target_core'] # 0 veya 1 tahmin etmeye çalışacak

# 2. Veriyi Hazırla (Normalizasyon)
# Yapay zeka 0-100 arası sayıları sevmez, onları 0-1 arasına sıkıştırıyoruz.
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Veriyi Eğitim (%80) ve Test (%20) olarak ayır
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# 3. Sinir Ağı Modelini Kur (The Architecture)
model = Sequential([
    # Giriş Katmanı + İlk Gizli Katman (16 Nöron)
    Dense(16, activation='relu', input_shape=(3,)),
    # İkinci Gizli Katman (8 Nöron) - Daha karmaşık ilişkileri öğrenir
    Dense(8, activation='relu'),
    # Çıkış Katmanı (1 Nöron) - Sonuç 0 ile 1 arasında bir olasılık olacak
    Dense(1, activation='sigmoid')
])

# Modeli Derle
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
 
# 4. Modeli Eğit
print("Model eğitimi başlıyor...")
model.fit(X_train, y_train, epochs=20, batch_size=10, verbose=1)

# 5. Başarımı Test Et
loss, accuracy = model.evaluate(X_test, y_test)
print(f"\nModel Başarısı (Accuracy): %{accuracy * 100:.2f}")

# 6. Modeli ve Scaler'ı Kaydet (Simülasyonda kullanacağız)
model.save('scheduler_model.h5')
joblib.dump(scaler, 'scaler.pkl')

print("Model ve ölçekleyici kaydedildi! Simülasyona hazır.")


#İşte yapay zeka modelini eğiten ve kaydeden kod (train_model.py):
#Bu Kod Ne Yapıyor? (Hocaya Anlatırken Kullanacağın Teknik Detaylar)
#
 #   Normalizasyon (StandardScaler): CPU kullanımı %90 iken Priority (Öncelik) değeri 5 olabilir. Biri büyük biri küçük sayı olunca yapay zekanın kafası karışır. Hepsini aynı matematiksel düzleme indiriyoruz.

  #  Hidden Layers (Gizli Katmanlar): Kodda gördüğün Dense(16) ve Dense(8) kısımları. Burada model, CPU yüksek ama RAM düşükse ne yapması gerektiğini "öğreniyor".

   # Sigmoid Fonksiyonu: Çıkış katmanında kullandık. Bu fonksiyon bize 0 ile 1 arasında bir sayı verir.

    #    Sonuç 0.5'ten küçükse -> Efficiency Core (E)

     #   Sonuç 0.5'ten büyükse -> Performance Core (P)
     #training