import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load data
df = pd.read_csv('rw_ablation_results.csv')

# Drop webkb
df = df[df['dataset'] != 'webkb']

# Clean data
df['total_rules'] = pd.to_numeric(df['total_rules'], errors='coerce')
df = df.dropna(subset=['total_rules']) # drop failed runs

# Map version names
df['version'] = df['version'].replace({
    'v1_pattern_mining': 'SPECTRUM',
    'v2_random_walks': 'Random Walks'
})

numeric_cols = ['epsilon', 'end_to_end_time_us', 'random_walks', 'fragments_found', 'constrained_fragments_found', 'total_rules']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col])

# Convert time from microseconds to seconds for readability
df['end_to_end_time_sec'] = df['end_to_end_time_us'] / 1e6

# Aesthetic settings
sns.set_theme(style="whitegrid", context="paper", font_scale=1.5)

# Function to save plot
def save_plot(filename):
    # Adjust legend position to avoid overlapping with data
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()

# Plotting Epsilon-Ablation

# A. Rules vs Epsilon
plt.figure(figsize=(10, 6))
sns.lineplot(data=df, x='epsilon', y='total_rules', hue='dataset', style='version', markers=True)
plt.xscale('log')
plt.gca().invert_xaxis() # smaller epsilon -> more walks
plt.title('Total Rules vs Epsilon')
plt.xlabel('Epsilon (Reversed log scale)')
plt.ylabel('Total Rules')
save_plot('rw_ablation_eps_rules.png')

# B. End-to-end Time vs Epsilon
plt.figure(figsize=(10, 6))
sns.lineplot(data=df, x='epsilon', y='end_to_end_time_sec', hue='dataset', style='version', markers=True)
plt.xscale('log')
plt.yscale('log')
plt.gca().invert_xaxis()
plt.title('End-to-End Runtime vs Epsilon')
plt.xlabel('Epsilon (Reversed log scale)')
plt.ylabel('Runtime (Seconds)')
save_plot('rw_ablation_eps_time.png')

# C. Fragments Found vs Epsilon
plt.figure(figsize=(10, 6))
sns.lineplot(data=df, x='epsilon', y='fragments_found', hue='dataset', style='version', markers=True)
plt.xscale('log')
plt.gca().invert_xaxis()
plt.title('Unique Fragments vs Epsilon')
plt.xlabel('Epsilon (Reversed log scale)')
plt.ylabel('Unique Fragments Found')
save_plot('rw_ablation_eps_fragments.png')

# D. Constrained Fragments vs Epsilon
plt.figure(figsize=(10, 6))
sns.lineplot(data=df, x='epsilon', y='constrained_fragments_found', hue='dataset', style='version', markers=True)
plt.xscale('log')
plt.gca().invert_xaxis()
plt.title('Constrained Fragments vs Epsilon')
plt.xlabel('Epsilon (Reversed log scale)')
plt.ylabel('Constrained Fragments Found')
save_plot('rw_ablation_eps_constrained_fragments.png')

print("All plots generated successfully.")
