import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load data
df = pd.read_csv('results.csv')

# Clean data
df['total_rules'] = pd.to_numeric(df['total_rules'], errors='coerce')
df = df.dropna(subset=['total_rules']) # drop failed runs
numeric_cols = ['M', 'epsilon', 'data_loading_time_us', 'random_walks', 'fragment_creation_time_us',
                'fragments_found', 'constrained_fragments_found', 'normal_fragments_time_us',
                'cyclic_fragments_time_us', 'total_rules', 'end_to_end_time_us']
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col])

# Convert time from microseconds to seconds for readability
df['end_to_end_time_sec'] = df['end_to_end_time_us'] / 1e6
df['fragment_creation_time_sec'] = df['fragment_creation_time_us'] / 1e6

# Aesthetic settings
sns.set_theme(style="whitegrid", context="paper", font_scale=1.5)
palette = sns.color_palette("Set2")

datasets = ['umls', 'kinship', 'family', 'imdb', 'webkb', 'wn18rr']

# 1. M-ablation data
# Filter for eps == 0.01 and dataset in small datasets
df_M = df[(df['epsilon'] == 0.01) & (df['dataset'].isin(datasets))].copy()
df_base = df[(df['experiment'] == 'base') & (df['dataset'].isin(datasets))].copy()

# 2. Epsilon-ablation data
# For each dataset, find the base M
df_eps_list = []
for ds in datasets:
    base_M = df[(df['dataset'] == ds) & (df['experiment'] == 'base')]['M'].values[0]
    df_eps_list.append(df[(df['dataset'] == ds) & (df['M'] == base_M)])
df_eps = pd.concat(df_eps_list)

# Function to save plot
def save_plot(filename):
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()

# Plotting M-Ablation
# A. Rules vs M
plt.figure(figsize=(8, 6))
sns.lineplot(data=df_M, x='M', y='total_rules', hue='dataset', marker='o', palette=palette)
plt.xscale('log', base=2)
plt.title('Total Rules Discovered vs M (Epsilon = 0.01)')
plt.xlabel('M (Number of Targets / Extracted Rules)')
plt.ylabel('Total Rules')
save_plot('ablation_M_rules.png')

# B. End-to-end Time vs M
plt.figure(figsize=(8, 6))
sns.lineplot(data=df_M, x='M', y='end_to_end_time_sec', hue='dataset', marker='o', palette=palette)
sns.scatterplot(data=df_base, x='M', y='end_to_end_time_sec', marker='*', color='red', s=200, zorder=10, label='Heuristic: M = 20 * |num predicate types|')
plt.xscale('log', base=2)
plt.yscale('log')
plt.title('End-to-End Runtime vs M (Epsilon = 0.01)')
plt.xlabel('M')
plt.ylabel('Runtime (Seconds)')
save_plot('ablation_M_time.png')

# C. Random Walks vs M
plt.figure(figsize=(8, 6))
sns.lineplot(data=df_M, x='M', y='random_walks', hue='dataset', marker='o', palette=palette)
plt.xscale('log', base=2)
plt.yscale('log')
plt.title('Number of Random Walks vs M (Epsilon = 0.01)')
plt.xlabel('M')
plt.ylabel('Random Walks')
save_plot('ablation_M_walks.png')

# D. Fragments Found vs M
plt.figure(figsize=(8, 6))
sns.lineplot(data=df_M, x='M', y='fragments_found', hue='dataset', marker='o', palette=palette)
plt.xscale('log', base=2)
plt.title('Discovered Fragments vs M (Epsilon = 0.01)')
plt.xlabel('M')
plt.ylabel('Unique Fragments Found')
save_plot('ablation_M_fragments.png')

# Plotting Epsilon-Ablation
# A. Rules vs Epsilon
plt.figure(figsize=(8, 6))
sns.lineplot(data=df_eps, x='epsilon', y='total_rules', hue='dataset', marker='s', palette=palette)
plt.xscale('log')
plt.gca().invert_xaxis() # smaller epsilon -> more walks
plt.title('Total Rules vs Epsilon (Fixed Heuristic M)')
plt.xlabel('Epsilon (Reversed log scale)')
plt.ylabel('Total Rules')
save_plot('ablation_eps_rules.png')

# B. End-to-end Time vs Epsilon
plt.figure(figsize=(8, 6))
sns.lineplot(data=df_eps, x='epsilon', y='end_to_end_time_sec', hue='dataset', marker='s', palette=palette)
plt.xscale('log')
plt.yscale('log')
plt.gca().invert_xaxis()
plt.title('End-to-End Runtime vs Epsilon (Fixed Heuristic M)')
plt.xlabel('Epsilon (Reversed log scale)')
plt.ylabel('Runtime (Seconds)')
save_plot('ablation_eps_time.png')

# C. Random Walks vs Epsilon
plt.figure(figsize=(8, 6))
sns.lineplot(data=df_eps, x='epsilon', y='random_walks', hue='dataset', marker='s', palette=palette)
plt.xscale('log')
plt.yscale('log')
plt.gca().invert_xaxis()
plt.title('Number of Random Walks vs Epsilon (Fixed Heuristic M)')
plt.xlabel('Epsilon (Reversed log scale)')
plt.ylabel('Random Walks')
save_plot('ablation_eps_walks.png')

# D. Constrained Fragments vs Epsilon
plt.figure(figsize=(8, 6))
sns.lineplot(data=df_eps, x='epsilon', y='constrained_fragments_found', hue='dataset', marker='s', palette=palette)
plt.xscale('log')
plt.gca().invert_xaxis()
plt.title('Constrained Fragments vs Epsilon (Fixed Heuristic M)')
plt.xlabel('Epsilon (Reversed log scale)')
plt.ylabel('Constrained Fragments Found')
save_plot('ablation_eps_constrained_fragments.png')

print("All plots generated successfully.")

