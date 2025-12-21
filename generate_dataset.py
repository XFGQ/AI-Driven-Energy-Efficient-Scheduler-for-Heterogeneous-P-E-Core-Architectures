"""Generate a synthetic dataset of tasks for the scheduler.
Usage:
    python generate_dataset.py --out os_tasks_dataset.csv --rows 1000 --seed 42
"""
import argparse
import random
import csv

FIELDNAMES = ["cpu_usage_pct", "memory_mb", "context_switch_rate", "estimated_time_s", "target_core"]


def sample_row():
    # cpu usage: skewed distribution
    cpu = round(min(max(random.gauss(40, 30), 0.5), 100.0), 2)
    # memory: 10 MB - 2000 MB
    mem = round(max(random.gauss(200, 220), 1.0), 2)
    # context switch rate: 0 - 100
    cs = round(abs(random.gauss(2, 5)), 3)
    # estimated time (seconds)
    est = round(max(random.expovariate(1/30), 0.1), 2)
    # simple heuristic for label: heavy cpu => P-core
    target = 1 if cpu > 50 or est < 5 else 0
    return {"cpu_usage_pct": cpu, "memory_mb": mem, "context_switch_rate": cs, "estimated_time_s": est, "target_core": target}


def generate(out_file, rows=1000, seed=None):
    if seed is not None:
        random.seed(seed)
    with open(out_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for _ in range(rows):
            writer.writerow(sample_row())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic OS task dataset")
    parser.add_argument("--out", default="os_tasks_dataset.csv")
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    generate(args.out, rows=args.rows, seed=args.seed)
    print(f"Wrote {args.rows} rows to {args.out}")