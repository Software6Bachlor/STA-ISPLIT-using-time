import os
import glob
import json
import math

# --- CONFIGURATION ---
RESULTS_DIR = "./results/groundManu"

def calculate_manu_ground_truth():
    total_trials = 0
    total_hits = 0
    total_sim_time = 0.0
    files_processed = 0

    print(f"Scanning for ground truth files in {RESULTS_DIR}...")

    # 1. Loop files and pool raw hits/trials
    for filepath in glob.glob(os.path.join(RESULTS_DIR, "*.json")):
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                res = json.load(f)
            except json.JSONDecodeError:
                continue

        # Verify it's valid MC data
        method = res.get("method", "")
        num_trials = res.get("numTrials", 0)
        num_hits = res.get("numHits", 0)

        if method != "mc" or num_trials == 0:
            continue

        total_trials += num_trials
        total_hits += num_hits
        total_sim_time += res.get("simElapsedSeconds", 0.0)
        files_processed += 1

    if files_processed == 0:
        print("Error: No valid JSON files found in the target directory.")
        return

    # 2. Calculate Pooled Math
    p_hat = total_hits / total_trials
    
    # Standard MC Bernoulli Variance: p * (1 - p)
    variance = p_hat * (1.0 - p_hat)
    
    # 95% Confidence Interval Half-Width
    half_width = 1.96 * math.sqrt(variance / total_trials) if total_trials > 0 else 0.0

    # 3. Print Console Summary
    print("\n" + "="*40)
    print("      MANUFACTURING-STA GROUND TRUTH")
    print("="*40)
    print(f"Files Processed:      {files_processed}")
    print(f"Total Pooled Trials:  {total_trials:,}")
    print(f"Total Pooled Hits:    {total_hits:,}")
    print(f"Total Sim Time:       {(total_sim_time / 3600):.2f} hours")
    print("-" * 40)
    print(f"GROUND TRUTH (φ):     {p_hat:.6e}")
    print(f"HALF-WIDTH (ε):       {half_width:.6e}")
    print("="*40 + "\n")

    # 4. Save to JSON so you can copy/paste it later
    output_data = {
        "model": "manufacturing-sta",
        "ground_truth_phi": p_hat,
        "half_width": half_width,
        "total_trials": total_trials,
        "total_hits": total_hits,
        "total_sim_time_hours": total_sim_time / 3600
    }

    output_filename = "manufacturing-sta_ground_truth.json"
    with open(output_filename, "w", encoding='utf-8') as out_file:
        json.dump(output_data, out_file, indent=4)
        
    print(f"[✓] Saved precise data to {output_filename}")

if __name__ == "__main__":
    calculate_manu_ground_truth()