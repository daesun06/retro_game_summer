import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read both CSV files
dqn_df = pd.read_csv('/home/daesun/repos/retro_game_summer/training_stats.csv')
q_df = pd.read_csv('/home/daesun/repos/retro_game_summer/training_stats_q.csv')

# Create figure and subplots
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))

# Plot Average Score
ax1.plot(dqn_df['Epoch'], dqn_df['AvgScore'], label='DQN')
ax1.plot(q_df['Epoch'], q_df['AvgScore'], label='Q-Learning')
ax1.set_ylabel('Average Score')
ax1.set_xlabel('Epoch')
ax1.grid(True)
ax1.legend()
ax1.set_title('Average Score over Training')

# Plot Best Score
ax2.plot(dqn_df['Epoch'], dqn_df['BestScore'], label='DQN')
ax2.plot(q_df['Epoch'], q_df['BestScore'], label='Q-Learning')
ax2.set_ylabel('Best Score')
ax2.set_xlabel('Epoch')
ax2.grid(True)
ax2.legend()
ax2.set_title('Best Score over Training')

# Plot States/Steps
ax3.plot(dqn_df['Epoch'], dqn_df['States/Steps'], label='DQN')
ax3.plot(q_df['Epoch'], q_df['States/Steps'], label='Q-Learning')
ax3.set_ylabel('States/Steps')
ax3.set_xlabel('Epoch')
ax3.set_yscale('log')
ax3.grid(True)
ax3.legend()
ax3.set_title('States/Steps over Training (Log Scale)')

# Adjust layout
plt.tight_layout()

# Save the figure
plt.savefig('training_comparison1.png')
plt.close()