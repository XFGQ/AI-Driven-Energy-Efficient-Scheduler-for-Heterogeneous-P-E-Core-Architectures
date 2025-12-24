import pandas as pd
import numpy as np

def calculate_optimal_configuration(cpu_load, ipc, cache_miss, temp):
    """
    Complex logic to determine ground truth for training.
    
    Logic:
    1. Thermal Throttling: If Temp > 85, force E-Core + Low Freq.
    2. Memory Bound (High Cache Miss): E-Core (waiting for RAM anyway).
    3. Compute Bound (High IPC + High Load): P-Core + High Freq.
    4. Idle/Background: E-Core + Low Freq.
    """
    # Defaults
    target_core = 0 # 0: E-Core, 1: P-Core
    target_freq = 0 # 0: Low, 1: Med, 2: High

    if temp > 85:
        return 0, 0 # Emergency throttling

    if cache_miss > 70: 
        # Memory bound task, high freq wastes power waiting for memory
        target_core = 0
        target_freq = 1
    elif cpu_load > 70 and ipc > 1.5:
        # Heavy compute task
        target_core = 1
        target_freq = 2
    elif cpu_load > 40:
        target_core = 1
        target_freq = 1
    else:
        # Background task
        target_core = 0
        target_freq = 0
        
    return target_core, target_freq

def generate_complex_dataset(n_samples=5000):
    np.random.seed(42)
    
    # Feature Generation
    cpu_loads = np.random.uniform(0, 100, n_samples)
    ipcs = np.random.uniform(0.2, 3.0, n_samples) # Instructions Per Cycle
    cache_misses = np.random.uniform(0, 100, n_samples) # Cache Miss Rate %
    temps = np.random.uniform(30, 95, n_samples) # CPU Temperature
    
    data = []
    
    for i in range(n_samples):
        core, freq = calculate_optimal_configuration(
            cpu_loads[i], ipcs[i], cache_misses[i], temps[i]
        )
        data.append([cpu_loads[i], ipcs[i], cache_misses[i], temps[i], core, freq])
        
    columns = ['cpu_load', 'ipc', 'cache_miss', 'temp', 'target_core', 'target_freq']
    df = pd.DataFrame(data, columns=columns)
    
    df.to_csv('advanced_os_data.csv', index=False)
    print(f"Generated {n_samples} complex samples. Saved to 'advanced_os_data.csv'.")
    print(df.head())

if __name__ == "__main__":
    generate_complex_dataset()