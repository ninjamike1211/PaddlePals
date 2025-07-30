import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import numpy as np
import datetime
import signal
import sys

# Serial setup
ser = serial.Serial('COM3', 115200)
ser.flush()

# Constants
threshold = 0.70
max_live_points = 300

# Live plot buffers
times = deque(maxlen=max_live_points)
speeds = deque(maxlen=max_live_points)
swing_flags = deque(maxlen=max_live_points)

# Full session buffers (for saving)
full_times = []
full_speeds = []
full_swings = []

# Setup live plot
fig, ax = plt.subplots()
line, = ax.plot([], [], label='Swing Speed')
threshold_line = ax.axhline(y=threshold, color='r', linestyle='--', label='Threshold')
scatter = ax.scatter([], [], color='green', label='Detected Swings', zorder=5)

ax.set_xlim(0, max_live_points)
ax.set_ylim(0, 2)
ax.set_xlabel("Time (index)")
ax.set_ylabel("Swing Speed (m/s)")
ax.set_title("Real-Time Swing Speed")
ax.legend()
plt.tight_layout()

# Function to update live plot
def update(frame):
    while ser.in_waiting:
        try:
            line_raw = ser.readline().decode('utf-8').strip()
            parts = line_raw.split(',')
            if len(parts) >= 3:
                time_ms = int(parts[0])
                speed = float(parts[1])
                is_swing = parts[2] == "1"

                # Live plot storage
                times.append(time_ms)
                speeds.append(speed)
                swing_flags.append(is_swing)

                # Full storage
                full_times.append(time_ms)
                full_speeds.append(speed)
                full_swings.append(is_swing)

        except Exception as e:
            print(f"Error parsing line: {e}")
            continue

    # Update line
    line.set_data(range(len(speeds)), speeds)

    # Update scatter points
    # Replace the original scatter.set_offsets() line with this:
    scatter_data = np.array([
        (i, s) for i, (s, flag) in enumerate(zip(speeds, swing_flags)) if flag
    ])
    if len(scatter_data) == 0:
        scatter_data = np.empty((0, 2))  # Ensure 2D array when empty

    scatter.set_offsets(scatter_data)

    ax.set_xlim(0, max(len(speeds), max_live_points))
    return line, scatter

# Save and close logic
def save_and_exit(sig=None, frame=None):
    print("\nExiting and saving full session graph...")

    fig2, ax2 = plt.subplots()
    ax2.plot(full_times, full_speeds, label='Swing Speed')
    ax2.axhline(y=threshold, color='r', linestyle='--', label='Threshold')

    # Plot detected swings
    swing_x = [t for t, s in zip(full_times, full_swings) if s]
    swing_y = [v for v, s in zip(full_speeds, full_swings) if s]
    ax2.scatter(swing_x, swing_y, color='green', label='Detected Swings', zorder=5)

    ax2.set_title("Full Session Swing Speed")
    ax2.set_xlabel("Time (ms)")
    ax2.set_ylabel("Swing Speed (m/s)")
    ax2.legend()
    plt.tight_layout()

    # Save with timestamp
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"swing_graph_{now}.png"
    plt.savefig(filename)
    print(f"Saved as {filename}")

    ser.close()
    plt.close('all')
    sys.exit(0)

# Handle Ctrl+C and regular closing
signal.signal(signal.SIGINT, save_and_exit)
fig.canvas.mpl_connect('close_event', save_and_exit)

# Start animation
ani = animation.FuncAnimation(fig, update, interval=100)
plt.show()
