import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV files
dqn_data = pd.read_csv('training_stats.csv')
q_data = pd.read_csv('training_stats_q.csv')

# Create figure with 3 subplots
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))
fig.suptitle('DQN vs Q-Learning Training Comparison', fontsize=16)

# Plot Average Score
ax1.plot(dqn_data['Epoch'], dqn_data['AvgScore'], label='DQN')
ax1.plot(q_data['Epoch'], q_data['AvgScore'], label='Q-Learning')
ax1.set_ylabel('Average Score')
ax1.set_xlabel('Epoch')
ax1.grid(True)
ax1.legend()
ax1.set_title('Average Score over Training')

# Plot Best Score
ax2.plot(dqn_data['Epoch'], dqn_data['BestScore'], label='DQN')
ax2.plot(q_data['Epoch'], q_data['BestScore'], label='Q-Learning')
ax2.set_ylabel('Best Score')
ax2.set_xlabel('Epoch')
ax2.grid(True)
ax2.legend()
ax2.set_title('Best Score over Training')

# Plot States/Steps
ax3.plot(dqn_data['Epoch'], dqn_data['States/Steps'], label='DQN')
ax3.plot(q_data['Epoch'], q_data['States/Steps'], label='Q-Learning')
ax3.set_ylabel('States/Steps')
ax3.set_xlabel('Epoch')
ax3.set_yscale('log')
ax3.grid(True)
ax3.legend()
ax3.set_title('States/Steps over Training')

# Adjust layout and save
plt.tight_layout()
plt.savefig('training_comparison.png')
plt.close()