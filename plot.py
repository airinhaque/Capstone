
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import numpy as np
import math
# Configuration
SERIAL_PORT = 'COM14'  # Change this to your Arduino port (COM3, COM4, etc. on Windows or /dev/ttyACM0, /dev/ttyUSB0 on Linux/Mac)
BAUD_RATE = 115200
WINDOW_SIZE = 500  # Number of data points to display

# Initialize serial connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
except Exception as e:
    print(f"Error connecting to serial port: {e}")
    print("Please check the port name and try again.")
    exit()

# Data storage
data = deque(maxlen=WINDOW_SIZE)
time_data = deque(maxlen=WINDOW_SIZE)
sample_count = 0

# Create figure and axis
fig, ax = plt.subplots(figsize=(12, 6))
line, = ax.plot([], [], 'r-', linewidth=1.5)
ax.set_ylim(0, 262144)  # 18-bit max value
ax.set_xlim(0, WINDOW_SIZE)
ax.set_xlabel('Sample Number', fontsize=12)
ax.set_ylabel('PPG Amplitude', fontsize=12)
ax.set_title('Live PPG Signal from MAX86916', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

# Text for displaying current value and heart rate estimate
value_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, 
                     verticalalignment='top', fontsize=10,
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

def init():
    line.set_data([], [])
    return line, value_text

def update(frame):
    global sample_count
    
    # Read data from serial
    try:
        if ser.in_waiting > 0:
            line_data = ser.readline().decode('utf-8').strip()
            
            # Skip non-numeric lines (like initialization messages)
            if line_data.replace('-', '').replace('.', '').isdigit():
                value = float(line_data)
                
                data.append(value)
                time_data.append(sample_count)
                sample_count += 1
                
                # Update plot
                if len(data) > 1:
                    line.set_data(list(time_data), list(data))
                    
                    # Auto-adjust y-axis based on data range
                    if len(data) > 10:
                        min_val = min(data)
                        max_val = max(data)
                        margin = (max_val - min_val) * 0.1
                        ax.set_ylim(min_val - margin, max_val + margin)
                    
                    # Update x-axis
                    if sample_count > WINDOW_SIZE:
                        ax.set_xlim(sample_count - WINDOW_SIZE, sample_count)
                    
                    # Update text with current value and simple HR estimate
                    current_val = math.log(int(value))
                    
                    # Simple peak detection for HR estimation
                    hr_estimate = estimate_heart_rate(list(data))
                    
                    value_text.set_text(f'Current Value: {current_val}\nHR Estimate: {hr_estimate} BPM')
    
    except Exception as e:
        print(f"Error reading data: {e}")
    
    return line, value_text

def estimate_heart_rate(data_list):
    """Simple heart rate estimation from peaks"""
    if len(data_list) < 50:
        return "..."
    
    # Find peaks
    data_array = np.array(data_list)
    threshold = np.mean(data_array) + 0.5 * np.std(data_array)
    
    peaks = []
    for i in range(1, len(data_array) - 1):
        if data_array[i] > threshold and data_array[i] > data_array[i-1] and data_array[i] > data_array[i+1]:
            peaks.append(i)
    
    # Calculate HR from peak intervals
    if len(peaks) > 2:
        intervals = np.diff(peaks)
        avg_interval = np.mean(intervals)
        # Assuming ~50 samples per second (20ms delay in Arduino code)
        hr = 60 / (avg_interval * 0.02)
        if 40 < hr < 200:  # Reasonable HR range
            return int(hr)
    
    return "..."

# Create animation
ani = animation.FuncAnimation(fig, update, init_func=init, 
                            interval=20, blit=True, cache_frame_data=False)

print("Plotting started. Close the plot window to exit.")
plt.tight_layout()
plt.show()

# Clean up
ser.close()
print("Serial connection closed.")