#!/usr/bin/env python3
"""
Ablation Study: SPECTRUM Pattern Mining vs Random Walks
Round robin rotation across datasets for the same epsilon before progressing.
Excludes epsilon=0.001. Appends to existing CSV.
"""

import os
import json
import glob
import re
import subprocess
import csv
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../.."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

DATASETS = ["family", "umls", "kinship", "imdb", "webkb"]
EPSILONS = [0.5, 0.1, 0.05, 0.01, 0.005]
CSV_FILE = os.path.join(SCRIPT_DIR, "SPECTRUM_RW_exp.csv")
FIELDNAMES = [
    "dataset", "version", "epsilon", "M",
    "random_walks",
    "data_loading_time_us",
    "fragment_creation_time_us",
    "fragments_found",
    "constrained_fragments_found",
    "normal_fragments_time_us",
    "cyclic_fragments_time_us",
    "total_rules",
    "end_to_end_time_us",
]

def read_info(dataset):
    info_file = glob.glob(os.path.join(DATA_DIR, dataset, "*.info"))[0]
    with open(info_file, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]
        preds = [l.split("(")[0] for l in lines]
    return list(set(preds))

def get_data_files(dataset):
    db_files = glob.glob(os.path.join(DATA_DIR, dataset, "*.db"))
    db_files = sorted([os.path.basename(f) for f in db_files if not f.endswith("_combined.db")])
    if len(db_files) > 1:
        combined_file = f"{dataset}_combined.db"
        return [combined_file.replace(".db", "")]
    return [f.replace(".db", "") for f in db_files]

def generate_config(dataset, preds, data_files, force_cyclic, variant):
    config = {
        "logic": "psl",
        "data_folder": f"data/{dataset}/",
        "info_file": f"data/{dataset}/{dataset}.info",
        "data_files": data_files,
        "targets": preds,
        "output_folder": os.path.join(SCRIPT_DIR, f"out_{variant}/"),
        "debug": False,
        "verbose": True,
        "force_cyclic": force_cyclic
    }
    config_file = os.path.join(SCRIPT_DIR, f"config_{dataset}_{variant}.json")
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)
    return config_file

def parse_log(stdout):
    res = {}
    for line in stdout.split('\n'):
        if "Duration(Data Loading)" in line:
            m = re.search(r'Duration\(Data Loading\) : (\d+)', line)
            if m: res["data_loading_time_us"] = m.group(1)
        elif "Max number of random walks" in line:
            m = re.search(r'Max number of random walks: (\d+)', line)
            if m: res["random_walks"] = m.group(1)
        elif "Duration(Fragment Creation)" in line:
            m = re.search(r'Duration\(Fragment Creation\) : (\d+)', line)
            if m: res["fragment_creation_time_us"] = m.group(1)
        elif " Fragments found" in line and "Constrained" not in line:
            m = re.search(r'(\d+) Fragments found', line)
            if m: res["fragments_found"] = m.group(1)
        elif "Constrained Fragments found" in line:
            m = re.search(r'(\d+) Constrained Fragments found', line)
            if m: res["constrained_fragments_found"] = m.group(1)
        elif "Duration(Normal Fragments)" in line:
            m = re.search(r'Duration\(Normal Fragments\) : (\d+)', line)
            if m: res["normal_fragments_time_us"] = m.group(1)
        elif "Duration(Cyclic Fragments)" in line:
            m = re.search(r'Duration\(Cyclic Fragments\) : (\d+)', line)
            if m: res["cyclic_fragments_time_us"] = m.group(1)
        elif "Total number of rules" in line:
            m = re.search(r'Total number of rules (\d+)', line)
            if m: res["total_rules"] = m.group(1)
        elif "Duration(main)" in line:
            m = re.search(r'Duration\(main\) : (\d+)', line)
            if m: res["end_to_end_time_us"] = m.group(1)
    return res

def run_experiment(binary, config_file, dataset, version_label, M, eps, writer, csv_fh):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {version_label} | {dataset} | eps={eps} | M={M}", flush=True)
    cmd = [binary, config_file, str(M), str(eps)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=7200, cwd=PROJECT_ROOT)
        out = proc.stdout
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT after 2h — skipping", flush=True)
        return False
    except subprocess.CalledProcessError as e:
        print(f"  ERROR: {e.stderr[:200]}", flush=True)
        out = (e.stdout or "") + "\n" + (e.stderr or "")

    parsed = parse_log(out)
    row = {
        "dataset": dataset,
        "version": version_label,
        "epsilon": eps,
        "M": M,
    }
    for field in FIELDNAMES:
        if field not in row:
            row[field] = parsed.get(field, "")
    writer.writerow(row)
    csv_fh.flush()
    print(f"  -> fragments={parsed.get('fragments_found','?')} "
          f"constrained={parsed.get('constrained_fragments_found','?')} "
          f"rules={parsed.get('total_rules','?')} "
          f"time={parsed.get('end_to_end_time_us','?')}us", flush=True)
    return True

def main():
    os.makedirs(os.path.join(SCRIPT_DIR, "out_SPECTRUM"), exist_ok=True)
    os.makedirs(os.path.join(SCRIPT_DIR, "out_RW"), exist_ok=True)

    completed_experiments = set()
    write_header = not os.path.exists(CSV_FILE)
    
    if not write_header:
        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    completed_experiments.add((row["dataset"], row["version"], float(row["epsilon"])))
                except:
                    pass

    csv_fh = open(CSV_FILE, "a" if not write_header else "w", newline="")
    # use append mode "a" if not writing header! Wait open("a")
    if not write_header:
        csv_fh = open(CSV_FILE, "a", newline="")
    else:
        csv_fh = open(CSV_FILE, "w", newline="")
        
    writer = csv.DictWriter(csv_fh, fieldnames=FIELDNAMES)
    if write_header:
        writer.writeheader()

    total = len(DATASETS) * len(EPSILONS) * 2
    done = len(completed_experiments)
    print(f"Found {done} completed experiments. Remaining: {total - done}")

    # Dataset presets (configs generated once)
    configs = {}
    Ms = {}
    for ds in DATASETS:
        preds = read_info(ds)
        data_files = get_data_files(ds)
        M = 20 * len(preds)
        if ds == "imdb": M = 200
        Ms[ds] = M
        config = generate_config(ds, preds, data_files, force_cyclic=True)
        config_rw = generate_config(ds, preds, data_files, force_cyclic=False, variant="rw")
        configs[ds] = {"SPECTRUM": config, "RW": config_rw}

    # Round Robin: Epsilon outside, Dataset inside
    for eps in EPSILONS:
        for ds in DATASETS:
            M = Ms[ds]
            
            # Run Version SPECTRUM
            if (ds, "SPECTRUM", eps) not in completed_experiments:
                binary = os.path.join(PROJECT_ROOT, "build", "SPECTRUM")
                if run_experiment(binary, configs[ds]["SPECTRUM"], ds, "SPECTRUM", M, eps, writer, csv_fh):
                    completed_experiments.add((ds, "SPECTRUM", eps))
                    done += 1
            
            # Run Version RW
            if (ds, "RW", eps) not in completed_experiments:
                binary_rw = os.path.join(PROJECT_ROOT, "build", "SPECTRUM_RW")
                if run_experiment(binary_rw, configs[ds]["RW"], ds, "RW", M, eps, writer, csv_fh):
                    completed_experiments.add((ds, "RW", eps))
                    done += 1

            print(f"  [{done}/{total} experiments total complete]\n", flush=True)

    csv_fh.close()
    print(f"\nAll intended experiments completed!")

if __name__ == "__main__":
    main()
