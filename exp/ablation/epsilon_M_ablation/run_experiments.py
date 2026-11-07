import os
import json
import glob
import re
import subprocess
import csv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../.."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

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
        db_files = db_files[:-1]
        combined_file = f"{dataset}_combined.db"
        combined_path = os.path.join(DATA_DIR, dataset, combined_file)
        with open(combined_path, "wb") as wfd:
            for f in db_files:
                with open(os.path.join(DATA_DIR, dataset, f), "rb") as fd:
                    wfd.write(fd.read())
        return [combined_file.replace(".db", "")]
    
    return [f.replace(".db", "") for f in db_files]

def generate_config(dataset, preds, data_files):
    config = {
        "data_folder": f"data/{dataset}/",
        "info_file": f"data/{dataset}/{dataset}.info",
        "data_files": data_files,
        "targets": preds,
        "output_folder": os.path.join(SCRIPT_DIR, "out/"),
        "debug": False,
        "verbose": True,
        "force_cyclic": True
    }
    config_file = os.path.join(SCRIPT_DIR, f"config_{dataset}.json")
    with open(config_file, "w") as f:
        json.dump(config, f, indent=4)
    return config_file

def parse_log(stdout, dataset, exp_name, M, eps):
    # Regexes to capture metadata
    res = {
        "dataset": dataset,
        "experiment": exp_name,
        "M": M,
        "epsilon": eps,
        "data_loading_time_us": None,
        "random_walks": None,
        "fragment_creation_time_us": None,
        "fragments_found": None,
        "constrained_fragments_found": None,
        "normal_fragments_time_us": None,
        "cyclic_fragments_time_us": None,
        "total_rules": None,
        "end_to_end_time_us": None,
    }
    
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

def run_spectrum(config_file, dataset, exp_name, M, eps, writer):
    print(f"Running {dataset} | exp: {exp_name} | M: {M} | eps: {eps}")
    binary = os.path.join(PROJECT_ROOT, "build", "SPECTRUM")
    cmd = [binary, config_file, str(M), str(eps)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=PROJECT_ROOT)
        out = proc.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running {dataset} {exp_name}:")
        print(e.stderr)
        out = e.stdout + "\n" + e.stderr
        
    res = parse_log(out, dataset, exp_name, M, eps)
    writer.writerow(res)
    print(f" -> Rules found: {res.get('total_rules', 'ERROR')}")

def main():
    datasets = ["imdb", "webkb", "wn18rr"]
    ablation_datasets = ["imdb", "webkb", "wn18rr"]
    
    csv_filename = os.path.join(SCRIPT_DIR, "SPECTRUM_epsilon_M_ablation.csv")
    csv_file = open(csv_filename, "a", newline="")
    fieldnames = [
        "dataset", "experiment", "M", "epsilon", "data_loading_time_us", 
        "random_walks", "fragment_creation_time_us", "fragments_found", 
        "constrained_fragments_found", "normal_fragments_time_us", 
        "cyclic_fragments_time_us", "total_rules", "end_to_end_time_us"
    ]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    if os.path.getsize(csv_filename) == 0:
        writer.writeheader()
    
    # Make sure output directory exists
    os.makedirs(os.path.join(SCRIPT_DIR, "out"), exist_ok=True)
    
    for ds in datasets:
        preds = read_info(ds)
        data_files = get_data_files(ds)
        
        config_file = generate_config(ds, preds, data_files)
        
        heuristic_M = 20 * len(preds)
        base_eps = 0.01
        
        # 1. Base run for ALL datasets
        # run_spectrum(config_file, ds, "base", heuristic_M, base_eps, writer)
        # csv_file.flush()
        
        # 2. Ablation runs ONLY for the smallest 3
        if ds in ablation_datasets:
            print(f"--- Starting Ablations for {ds} ---")
            
            # M-ablation
            M_test = 1
            target_max_M = 16 * heuristic_M
            while True:
                run_spectrum(config_file, ds, f"M_ablation_{M_test}", M_test, base_eps, writer)
                if M_test >= target_max_M:
                    break
                M_test *= 2
                csv_file.flush()
                
            # eps-ablation
            # vary geometrically: 0.1, 0.05, 0.01, 0.005, 0.001
            eps_vals = [0.1, 0.05, 0.01, 0.005, 0.001]
            for e in eps_vals:
                if e == base_eps: 
                    continue # already ran base
                run_spectrum(config_file, ds, f"eps_ablation_{e}", heuristic_M, e, writer)
                csv_file.flush()
                
            print(f"--- Finished Ablations for {ds} ---")

    csv_file.close()
    print("All experiments completed!")

if __name__ == "__main__":
    main()
