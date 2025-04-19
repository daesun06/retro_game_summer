import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV file
df = pd.read_csv('training_stats.csv')

# Create a figure with multiple subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# Plot 1: Scores over epochs
ax1.plot(df['Epoch'], df['AvgScore'], label='Average Score', color='blue')
ax1.plot(df['Epoch'], df['BestScore'], label='Best Score', color='green')
ax1.set_xlabel('Epoch')
ax1.set_ylabel('Score')
ax1.set_title('Training Scores over Time')
ax1.grid(True)
ax1.legend()

# Plot 2: Epsilon and States/Steps over epochs
ax2.plot(df['Epoch'], df['Epsilon'], label='Epsilon', color='red')
ax2.set_ylabel('Epsilon', color='red')
ax2.tick_params(axis='y', labelcolor='red')

# Create a twin axis for States/Steps
ax2_twin = ax2.twinx()
ax2_twin.plot(df['Epoch'], df['States/Steps'], label='States/Steps', color='purple')
ax2_twin.set_ylabel('States/Steps', color='purple')
ax2_twin.tick_params(axis='y', labelcolor='purple')

ax2.set_xlabel('Epoch')
ax2.set_title('Epsilon and States/Steps over Time')
ax2.grid(True)

# Add legends
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

# Adjust layout to prevent overlap
plt.tight_layout()

# Save the plot
plt.savefig('training_stats_plot.png')
plt.show()