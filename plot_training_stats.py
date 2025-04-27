import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV files
q_data = pd.read_csv('training_stats_q.csv')
dqn_data = pd.read_csv('training_stats.csv')

# Create figure with three subplots
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))

# Plot Steps/States comparison with log scale
ax1.plot(q_data['Epoch'], q_data['States/Steps'], label='Q-Learning', color='blue')
ax1.plot(dqn_data['Epoch'], dqn_data['States/Steps'], label='DQN', color='red')
ax1.set_xlabel('Epoch')
ax1.set_ylabel('States/Steps (log scale)')
ax1.set_title('States/Steps Comparison: Q-Learning vs DQN')
ax1.set_yscale('log')  # Set log scale for y-axis
ax1.legend()
ax1.grid(True)

# Plot Average Score comparison
ax2.plot(q_data['Epoch'], q_data['AvgScore'], label='Q-Learning', color='blue')
ax2.plot(dqn_data['Epoch'], dqn_data['AvgScore'], label='DQN', color='red')
ax2.set_xlabel('Epoch')
ax2.set_ylabel('Average Score')
ax2.set_title('Average Score Comparison: Q-Learning vs DQN')
ax2.legend()
ax2.grid(True)

# Plot Best Score comparison
ax3.plot(q_data['Epoch'], q_data['BestScore'], label='Q-Learning', color='blue')
ax3.plot(dqn_data['Epoch'], dqn_data['BestScore'], label='DQN', color='red')
ax3.set_xlabel('Epoch')
ax3.set_ylabel('Best Score')
ax3.set_title('Best Score Comparison: Q-Learning vs DQN')
ax3.legend()
ax3.grid(True)

# Adjust layout to prevent overlap
plt.tight_layout()

# Save the figure
plt.savefig('training_comparison.png')
plt.close()