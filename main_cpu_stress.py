import multiprocessing
import time
import os

def worker():
     
    print(f"Core process {os.getpid()} ")
    while True:
        _ = 999999 * 999999

if __name__ == "__main__":
    # Çekirdek sayısı kadar işlem başlat
    num_cores = multiprocessing.cpu_count()
    print(f"WARNING: {num_cores} To stop CTRL+C yap.")
    print("STARTING CPU STRESS TEST... for 30 seconds")
    time.sleep(3)
    
    processes = []
    for _ in range(num_cores):
        p = multiprocessing.Process(target=worker)
        p.start()
        processes.append(p)
        
    try:
         time.sleep(30) 
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        for p in processes:
            p.terminate()
            p.join()
        print("Test over")