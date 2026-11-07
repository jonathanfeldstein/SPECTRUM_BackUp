import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

csv_path = '[path to csv]'
df = pd.read_csv(csv_path)

time_cols = ['end_to_end_time_us']
for col in time_cols:
    df[col.replace('_us', '_s')] = df[col] / 1e6

out_dir = '[path to output dir]'
os.makedirs(out_dir, exist_ok=True)

datasets = df['dataset'].unique()

def plot_metric(metric, ylabel, title, filename):
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=df, x='epsilon', y=metric, hue='dataset', style='version', markers=True, dashes=False, errorbar=None)
    plt.xscale('log')
    if 'time' in metric:
        plt.yscale('log')
    plt.gca().invert_xaxis()
    plt.title(title)
    plt.xlabel('Epsilon (log scale, inverted)')
    plt.ylabel(ylabel)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, filename))
    plt.close()

plot_metric('end_to_end_time_s', 'End-to-End Time (seconds, log scale)', 'End-to-End Time vs Epsilon', 'end_to_end_time.png')
plot_metric('total_rules', 'Total Rules', 'Total Rules vs Epsilon', 'total_rules.png')
plot_metric('fragments_found', 'Fragments Found', 'Fragments Found vs Epsilon', 'fragments_found.png')