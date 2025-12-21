import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Dropout, BatchNormalization
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

# 1. Load Data
df = pd.read_csv('advanced_os_data.csv')

X = df[['cpu_load', 'ipc', 'cache_miss', 'temp']].values
y_core = df['target_core'].values
y_freq = df['target_freq'].values

# One-hot encode frequency (0, 1, 2)
y_freq_encoded = to_categorical(y_freq, num_classes=3)

# 2. Preprocessing
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_core_train, y_core_test, y_freq_train, y_freq_test = train_test_split(
    X_scaled, y_core, y_freq_encoded, test_size=0.2, random_state=42
)

# 3. Build Advanced Model (Functional API)
input_layer = Input(shape=(4,))

# Shared Layers (Feature Extraction)
x = Dense(64, activation='relu')(input_layer)
x = BatchNormalization()(x)
x = Dropout(0.2)(x)
x = Dense(32, activation='relu')(x)

# Head 1: Core Prediction (Binary Classification)
core_output = Dense(1, activation='sigmoid', name='core_output')(x)

# Head 2: Frequency Prediction (Multi-class Classification)
freq_output = Dense(3, activation='softmax', name='freq_output')(x)

# Combine
model = Model(inputs=input_layer, outputs=[core_output, freq_output])

# Compile
model.compile(
    optimizer='adam',
    loss={'core_output': 'binary_crossentropy', 'freq_output': 'categorical_crossentropy'},
    loss_weights={'core_output': 1.0, 'freq_output': 0.5}, # Prioritize core selection
    metrics={'core_output': 'accuracy', 'freq_output': 'accuracy'}
)

# 4. Train
print("Training Advanced Multi-Task Model...")
history = model.fit(
    X_train, 
    {'core_output': y_core_train, 'freq_output': y_freq_train},
    validation_data=(X_test, {'core_output': y_core_test, 'freq_output': y_freq_test}),
    epochs=30,
    batch_size=32,
    verbose=1
)

# 5. Save
model.save('advanced_scheduler_model.h5')
joblib.dump(scaler, 'advanced_scaler.pkl')
print("Advanced model saved successfully.")