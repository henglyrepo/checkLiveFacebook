import os
import time
import requests
import threading

def check_live(uids, completed_uids, lock, live_count, die_count, total_count, live_uids, die_uids):
    for index, uid in enumerate(uids, start=0):
        try:
            response = requests.get(f"https://graph.facebook.com/{uid}/picture?redirect=0", timeout=25)
            data = response.json()
            
            url = data['data']['url']
            
            if "static.xx" in url:
                print(f"{index}: {uid}, : Die")
                with lock:
                    die_count[0] += 1
                    die_uids.append(uid)
            elif "scontent" in url:
                print(f"{index}: {uid}, : Live")
                with lock:
                    live_count[0] += 1
                    live_uids.append(uid)
            else:
                print(f"{index}: {uid}, : Unknown")
            
            with lock:
                total_count[0] += 1

        except Exception as e:
            print(f"{index}: {uid}, : Error - {e}")
        
        # Acquire the lock to update the completed UIDs count
        with lock:
            completed_uids[0] += 1
            
            # Check if all UIDs have been processed
            if completed_uids[0] == len(uids):
                # Notify other threads to stop
                completion_event.set()

# Get the absolute path of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Specify the file path relative to the script's directory
file_path = os.path.join(script_dir, "./acc-check-live/acc.txt")

# Check if the file exists
if not os.path.isfile(file_path):
    print(f"File '{file_path}' not found.")
    exit()

# Read UIDs from the text file
with open(file_path, "r") as file:
    uids = file.read().splitlines()

# Split the UIDs into batches of 5
batch_size = 10
uid_batches = [uids[i:i+batch_size] for i in range(0, len(uids), batch_size)]

# Create an event to track completion
completion_event = threading.Event()

# Create a lock for thread safety
lock = threading.Lock()

# Create and start threads for each UID batch
threads = []
completed_uids = [0]  # Shared variable to track completed UIDs count
live_count = [0]      # Shared variable to track live UIDs count
die_count = [0]       # Shared variable to track dead UIDs count
total_count = [0]     # Shared variable to track total UIDs count
live_uids = []        # List to store live UIDs
die_uids = []         # List to store dead UIDs

for batch in uid_batches:
    thread = threading.Thread(target=check_live, args=(batch, completed_uids, lock, live_count, die_count, total_count, live_uids, die_uids))
    thread.start()
    threads.append(thread)
    # Sleep for 2 seconds between batches
    time.sleep(2)

# Wait for completion event or all threads to finish
completion_event.wait()

# Wait for all threads to finish
for thread in threads:
    thread.join()


# Print the counts of live and dead UIDs
print(f"Live UIDs: {live_count[0]}")
print(f"Dead UIDs: {die_count[0]}")
print(f"Total UIDs: {total_count[0]}")

# Write live UIDs to "live.txt"
with open("./acc-check-live/live.txt", "w") as live_file:
    live_file.write("\n".join(live_uids))

# Write dead UIDs to "die.txt"
with open("./acc-check-live/die.txt", "w") as die_file:
    die_file.write("\n".join(die_uids))
