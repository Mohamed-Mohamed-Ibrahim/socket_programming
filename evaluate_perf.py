import socket
import time
import threading, numpy as np
import matplotlib.pyplot as plt
from my_client import client
import numpy as np

# Parameters
NUM_CLIENTS = 50  # Number of simulated clients
NUM_REQUESTS_PER_CLIENT = 10

# Store latency data
latencies = []

def client_task():

    for _ in range(NUM_REQUESTS_PER_CLIENT):
        start_time = time.time()
        client()
        end_time = time.time()
        
        latencies.append(end_time - start_time)

# Run clients in parallel
threads = []
for _ in range(NUM_CLIENTS):
    thread = threading.Thread(target=client_task)
    threads.append(thread)
    thread.start()

# Wait for all clients to finish
for thread in threads:
    thread.join()

# Calculate average latency for each number of requests
average_latency = sum(latencies) / len(latencies)

# Plot the latency data
plt.plot(range(len(latencies)), latencies, label="Latency per request")
plt.axhline(y=average_latency, color='r', linestyle='--', label="Average Latency")
plt.xlabel("Request Number")
plt.ylabel("Latency (seconds)")
plt.title("Latency vs. Number of Requests")
plt.legend()

plt.savefig("latency_vs_requests.png", format='png')  # You can change the format (e.g., 'jpg', 'pdf')

plt.show()
# print(latencies)
# print(average_latency)