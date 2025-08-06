#!/usr/bin/env python3
"""
ESP32 BLE Latency Monitor
Captures latency data from ESP32 serial output and plots it in real-time using matplotlib.
"""

import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime, timedelta
import re
import argparse
import sys
import os
import csv

class LatencyMonitor:
    def __init__(self, port, baudrate=115200, max_points=100):
        self.port = port
        self.baudrate = baudrate
        self.max_points = max_points
        
        # Data storage for live plot (rolling window)
        self.timestamps = []
        self.latencies = []
        
        # Complete data storage for final graph and CSV
        self.all_timestamps = []
        self.all_latencies = []
        
        # Session info for file naming
        self.session_start = datetime.now()
        
        # Serial connection
        self.ser = None
        
        # Plot setup
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.line, = self.ax.plot([], [], 'b-', linewidth=2, label='BLE Latency')
        
        # Configure plot
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Latency (microseconds)')
        self.ax.set_title('ESP32 BLE Communication Latency')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        
        # Regex pattern to match latency output
        self.latency_pattern = re.compile(r'Latency: (\d+) microseconds')
        
    def connect_serial(self):
        """Connect to ESP32 via serial"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to serial port: {e}")
            return False
    
    def read_latency_data(self):
        """Read and parse latency data from serial"""
        if not self.ser or not self.ser.is_open:
            return None
            
        try:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                match = self.latency_pattern.match(line)
                if match:
                    latency = int(match.group(1))
                    timestamp = datetime.now()
                    return timestamp, latency
        except Exception as e:
            print(f"Error reading serial data: {e}")
        
        return None
    
    def update_plot(self, frame):
        """Update plot with new data (called by animation)"""
        # Read new data
        data = self.read_latency_data()
        if data:
            timestamp, latency = data
            
            # Add new data point to both live and complete storage
            self.timestamps.append(timestamp)
            self.latencies.append(latency)
            self.all_timestamps.append(timestamp)
            self.all_latencies.append(latency)
            
            # Keep only the last max_points for live display
            if len(self.timestamps) > self.max_points:
                self.timestamps.pop(0)
                self.latencies.pop(0)
            
            # Update plot data
            if self.timestamps:
                self.line.set_data(self.timestamps, self.latencies)
                
                # Update axis limits
                if len(self.timestamps) > 1:
                    time_range = self.timestamps[-1] - self.timestamps[0]
                    margin = timedelta(seconds=30)  # 30-second margin
                    
                    self.ax.set_xlim(self.timestamps[0] - margin, 
                                   self.timestamps[-1] + margin)
                
                # Auto-scale y-axis with some padding
                if self.latencies:
                    min_lat = min(self.latencies)
                    max_lat = max(self.latencies)
                    padding = (max_lat - min_lat) * 0.1 + 100  # 10% padding + 100µs
                    self.ax.set_ylim(max(0, min_lat - padding), max_lat + padding)
            
            # Print data to console
            print(f"{timestamp.strftime('%H:%M:%S')} - Latency: {latency} µs")
        
        return self.line,
    
    def save_data_to_csv(self):
        """Save all collected data to CSV file"""
        if not self.all_timestamps:
            print("No data to save")
            return None
            
        filename = f"latency_data_{self.session_start.strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Timestamp', 'Latency_Microseconds'])
                
                for timestamp, latency in zip(self.all_timestamps, self.all_latencies):
                    writer.writerow([timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'), latency])
            
            print(f"Data saved to: {filepath}")
            return filepath
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return None
    
    def create_final_graph(self):
        """Create and save a final static graph with all data"""
        if not self.all_timestamps:
            print("No data to plot")
            return None
            
        filename = f"latency_graph_{self.session_start.strftime('%Y-%m-%d_%H-%M-%S')}.png"
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            # Create a new figure for the final graph
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Plot all data points
            ax.plot(self.all_timestamps, self.all_latencies, 'b-', linewidth=1.5, 
                   marker='o', markersize=3, alpha=0.7, label='BLE Latency')
            
            # Add statistics to the plot
            if self.all_latencies:
                avg_latency = sum(self.all_latencies) / len(self.all_latencies)
                min_latency = min(self.all_latencies)
                max_latency = max(self.all_latencies)
                
                # Add horizontal lines for statistics
                ax.axhline(y=avg_latency, color='r', linestyle='--', alpha=0.7, 
                          label=f'Average: {avg_latency:.0f} µs')
                ax.axhline(y=min_latency, color='g', linestyle='--', alpha=0.7, 
                          label=f'Minimum: {min_latency} µs')
                ax.axhline(y=max_latency, color='orange', linestyle='--', alpha=0.7, 
                          label=f'Maximum: {max_latency} µs')
                
                # Add statistics text box
                stats_text = f'Session Stats:\nSamples: {len(self.all_latencies)}\n'
                stats_text += f'Duration: {(self.all_timestamps[-1] - self.all_timestamps[0]).total_seconds():.1f}s\n'
                stats_text += f'Avg: {avg_latency:.1f} µs\nMin: {min_latency} µs\nMax: {max_latency} µs'
                
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # Configure the plot
            ax.set_xlabel('Time', fontsize=12)
            ax.set_ylabel('Latency (microseconds)', fontsize=12)
            ax.set_title(f'ESP32 BLE Communication Latency - {self.session_start.strftime("%Y-%m-%d %H:%M:%S")}', 
                        fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right')
            
            # Format x-axis to show time nicely
            fig.autofmt_xdate()
            
            # Tight layout to prevent clipping
            plt.tight_layout()
            
            # Save the figure
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()  # Close to free memory
            
            print(f"Final graph saved to: {filepath}")
            return filepath
        except Exception as e:
            print(f"Error creating final graph: {e}")
            return None
    
    def start_monitoring(self):
        """Start the real-time monitoring"""
        if not self.connect_serial():
            sys.exit(1)
        
        print("Starting latency monitoring...")
        print("Waiting for ESP32 latency data...")
        print("Close the plot window to stop monitoring.\n")
        
        # Create animation
        ani = animation.FuncAnimation(
            self.fig, self.update_plot, interval=100, blit=False, cache_frame_data=False
        )
        
        try:
            plt.show()
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        finally:
            # Save data and create final graph when session ends
            print("\nSaving session data...")
            self.save_data_to_csv()
            self.create_final_graph()
            
            if self.ser:
                self.ser.close()
                print("Serial connection closed")
            
            print("Session complete!")

def list_serial_ports():
    """List available serial ports"""
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()
    print("Available serial ports:")
    for port in ports:
        print(f"  {port.device} - {port.description}")

def main():
    parser = argparse.ArgumentParser(description='Monitor ESP32 BLE latency in real-time')
    parser.add_argument('--port', '-p', type=str, 
                       help='Serial port (e.g., COM3 on Windows, /dev/ttyUSB0 on Linux)')
    parser.add_argument('--baudrate', '-b', type=int, default=115200,
                       help='Baud rate (default: 115200)')
    parser.add_argument('--max-points', '-m', type=int, default=100,
                       help='Maximum number of data points to display (default: 100)')
    parser.add_argument('--list-ports', '-l', action='store_true',
                       help='List available serial ports and exit')
    
    args = parser.parse_args()
    
    if args.list_ports:
        list_serial_ports()
        return
    
    if not args.port:
        print("Error: Please specify a serial port with --port")
        print("Use --list-ports to see available ports")
        list_serial_ports()
        sys.exit(1)
    
    # Create and start monitor
    monitor = LatencyMonitor(args.port, args.baudrate, args.max_points)
    monitor.start_monitoring()

if __name__ == "__main__":
    main()