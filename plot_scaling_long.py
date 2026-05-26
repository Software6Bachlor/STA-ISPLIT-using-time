import os
import glob
import json
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
        num_hits = res.get("numHits", 0)
        if scale_val not in data["mc"]:
            data["mc"][scale_val] = {"hits": 0, "trials": 0}
        
        data["mc"][scale_val]["hits"] += num_hits
        data["mc"][scale_val]["trials"] += num_trials

    # --- POOLING RESTART ---
    elif method == "restart":
        raw_list = res.get("weightedHitsList") or []
        
        # Pad with zeros if the engine only saved non-zero hits
        zeros_to_add = num_trials - len(raw_list)
        if zeros_to_add > 0:
            raw_list.extend([0.0] * zeros_to_add)
            
        if scale_val not in data["restart"]:
            data["restart"][scale_val] = {"Y_list": [], "total_trials": 0}
            
        data["restart"][scale_val]["Y_list"].extend(raw_list)
        data["restart"][scale_val]["total_trials"] += num_trials

print("Calculating pooled global variances...")

plot_data = {"mc": {"x": [], "y": [], "yerr": []}, "restart": {"x": [], "y": [], "yerr": []}}

# 3. Calculate Math
for x_val in sorted(data["mc"].keys()):
    hits = data["mc"][x_val]["hits"]
    M = data["mc"][x_val]["trials"]
    
    p_hat = hits / M
    variance = p_hat * (1 - p_hat) 
    hw = 1.96 * np.sqrt(variance / M) if M > 0 else 0
    
    plot_data["mc"]["x"].append(x_val)
    plot_data["mc"]["y"].append(p_hat)
    plot_data["mc"]["yerr"].append(hw)

for x_val in sorted(data["restart"].keys()):
    Y_mega_list = np.array(data["restart"][x_val]["Y_list"])
    M = data["restart"][x_val]["total_trials"]
    
    p_hat = np.sum(Y_mega_list) / M
    variance = np.var(Y_mega_list, ddof=1) if M > 1 else 0
    hw = 1.96 * np.sqrt(variance / M) if M > 0 else 0
    
    plot_data["restart"]["x"].append(x_val)
    plot_data["restart"]["y"].append(p_hat)
    
    # Asymmetric clamping to protect the log scale
    lower_err = hw if (p_hat - hw) > 0 else p_hat 
    plot_data["restart"]["yerr"].append([lower_err, hw])

# 4. Generate the Plot
plt.figure(figsize=(10, 6))

plt.errorbar(
    plot_data["restart"]["x"], plot_data["restart"]["y"], 
    yerr=[[err[0] for err in plot_data["restart"]["yerr"]], [err[1] for err in plot_data["restart"]["yerr"]]], 
    fmt='o-', color="#ff7f0e", label="RESTART Splitting", 
    capsize=5, capthick=1.5, elinewidth=1.5, markersize=7
)

if plot_data["mc"]["x"]: # Only plot MC if data exists
    plt.errorbar(
        plot_data["mc"]["x"], plot_data["mc"]["y"], 
        yerr=plot_data["mc"]["yerr"], 
        fmt='s-', color="#1f77b4", label="Standard Monte Carlo", 
        capsize=5, capthick=1.5, elinewidth=1.5, markersize=7
    )

plt.yscale('log')

# Automatically format X-ticks based on the Y_THRESHOLD values found
plt.xticks(sorted(data["restart"].keys() if data["restart"] else data["mc"].keys()))

plt.xlabel('Y Threshold', fontsize=12, fontweight='bold')
plt.ylabel('Probability of Failure (Log Scale)', fontsize=12, fontweight='bold')
plt.title(f'Scaling Performance: {TARGET_MODEL.upper()} (95% CI Error Bars)', fontsize=14, fontweight='bold')

plt.grid(True, which="both", ls="--", alpha=0.4)
plt.legend(loc='best') 
plt.tight_layout()

# Save with a specific Long-STA filename
plt.savefig(f"{TARGET_MODEL}_scaling_plot.svg")
print(f"Success! Saved plot to '{TARGET_MODEL}_scaling_plot.svg'")
plt.show()