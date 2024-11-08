import threading
import queue

# Function that will be run by each thread
def print_message(thread_id, q):
    q.put(f"Hello from thread {thread_id}")

# Create a queue to hold print messages
q = queue.Queue()

# Create and start threads
threads = []
for i in range(5):
    thread = threading.Thread(target=print_message, args=(i, q))
    threads.append(thread)
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()

# Now print all the messages collected in the queue
while not q.empty():
    print(q.get())
