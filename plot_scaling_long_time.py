import os
import glob
import json
import re
import numpy as np
import matplotlib.pyplot as plt

# 1. Configuration
RESULTS_DIR = "./results/scalingLong"
TARGET_MODEL = "long-sta"  # <--- Dedicated script target
SWEEP_PARAM = "Y_THRESHOLD" # <--- The variable controlling the scale

data = {
    "mc": {},       
    "restart": {}   
}

print(f"Scanning for {TARGET_MODEL} data...")

# 2. Parse and Pool the Data
for filepath in glob.glob(os.path.join(RESULTS_DIR, "*.json")):
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            res = json.load(f)
        except json.JSONDecodeError:
            continue
            
    method = res.get("method")
    model_name = res.get("modelName", "")
    num_trials = res.get("numTrials", 0)
    
    # --- MODEL ISOLATION FILTER ---
    # If the file isn't our target model, skip it entirely
    if TARGET_MODEL not in model_name.lower():
        continue
        
    if method not in data or num_trials == 0:
        continue

    # --- EXTRACTING THE X-AXIS PARAMETER ---
    # We grab it directly from the constants dictionary instead of the filename
    constants = res.get("constants", {})
    scale_val = constants.get(SWEEP_PARAM)
    
    if scale_val is None:
        print(f"Skipping {filepath} (No {SWEEP_PARAM} found in constants)")
        continue
        
    # Convert to integer for clean sorting/plotting
    scale_val = int(scale_val)


    # --- POOLING MONTE CARLO ---
    if method == "mc":
        time = res.get("simElapsedSeconds", 0.0)
        if scale_val not in data["mc"]:
            data["mc"][scale_val] = {"time": 0.0}
        data["mc"][scale_val]["time"] += time

    # --- POOLING RESTART ---
    elif method == "restart":
        time = res.get("simElapsedSeconds", 0.0)
        if scale_val not in data["restart"]:
            data["restart"][scale_val] = {"time": 0.0}
        data["restart"][scale_val]["time"] += time

print("Calculating pooled global variances...")
x_vals = []
for scale_val in sorted(data["mc"].keys()):
    x_vals.append(scale_val)

plt.figure(figsize=(10, 6))

width = 2

plt.bar(
    [v - width/2 for v in x_vals], [data["restart"][scale_val]["time"] for scale_val in x_vals],
    color="#ff7f0e", label="RESTART Splitting", width=width
)

plt.bar(
    [v + width/2 for v in x_vals], [data["mc"][scale_val]["time"] for scale_val in x_vals],
    color="#1f77b4", label="Standard Monte Carlo", width=width
)

plt.yscale('log')
plt.xticks(sorted(data["restart"].keys() if data["restart"] else data["mc"].keys()))

plt.xlabel('Y Threshold', fontsize=12, fontweight='bold')
plt.ylabel('Elapsed Time (Seconds, Log Scale)', fontsize=12, fontweight='bold')
plt.title(f'Scaling Performance: {TARGET_MODEL.upper()} (Elapsed Time)', fontsize=14, fontweight='bold')

plt.grid(True, which="both", ls="--", alpha=0.4)
plt.legend(loc='upper left') 
plt.tight_layout()

# Save with a specific Chain filename
plt.savefig(f"{TARGET_MODEL}_scaling_simtime_plot.svg")
print(f"Success! Saved plot to '{TARGET_MODEL}_scaling_simtime_plot.svg'")
plt.show()
