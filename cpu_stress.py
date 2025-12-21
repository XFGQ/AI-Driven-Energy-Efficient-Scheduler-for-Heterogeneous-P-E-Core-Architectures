"""CPU stress utility.
Usage:
    python cpu_stress.py --workers 4 --duration 30
If --duration is omitted the script runs until interrupted (Ctrl+C).
"""
import argparse
import multiprocessing as mp
import time
import math


def worker_run(stop_event):
    try:
        # Tight math loop to generate CPU load
        x = 0.0001
        while not stop_event.is_set():
            x += math.sqrt(x * 1.000001 + 0.0000001)
    except KeyboardInterrupt:
        return


def main(workers, duration):
    stop_event = mp.Event()
    procs = []
    for _ in range(workers):
        p = mp.Process(target=worker_run, args=(stop_event,))
        p.start()
        procs.append(p)
    try:
        if duration:
            time.sleep(duration)
            stop_event.set()
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
    finally:
        for p in procs:
            p.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lightweight CPU stress tool")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel workers (processes)")
    parser.add_argument("--duration", type=int, default=0, help="Duration in seconds (0 means until Ctrl+C)")
    args = parser.parse_args()
    dur = args.duration if args.duration > 0 else None
    print(f"Starting {args.workers} workers. Duration: {dur if dur else 'infinite (Ctrl+C to stop)'}")
    main(args.workers, dur)