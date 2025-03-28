import queue
import threading
import time

# Create a thread-safe queue for messages
message_queue = queue.Queue()

# Flag to indicate if the worker is actively processing
is_processing = False

# Lock to protect the is_processing flag
processing_lock = threading.Lock()


def filter_messages(messages):
    """
    Dummy filter function that processes a list of messages and returns filtered messages.
    Replace this logic with your actual filtering logic.
    """
    # Example: filter out any empty messages:
    return [msg for msg in messages if msg.strip()]


def analyze(filtered_messages):
    """
    Dummy analyze function that processes filtered messages.
    Replace this logic with your actual analysis code.
    """
    print("Analyzing:", filtered_messages)
    time.sleep(1)  # Simulate processing time
    print("Finished analysis for:", filtered_messages)


def process_queue():
    """
    Worker function that continuously processes all messages in the queue as batches.
    """
    global is_processing
    while True:
        try:
            # Wait for at least one message (blocking)
            first_message = message_queue.get(
                timeout=0
            )  # adjust timeout as needed
        except queue.Empty:
            # If timeout and no messages, end processing
            with processing_lock:
                is_processing = False
            print("No new messages. Worker is stopping.")
            break

        # Gather the first message
        batch = [first_message]

        # Now extract any additional messages that are already in the queue
        while True:
            try:
                msg = message_queue.get_nowait()
                batch.append(msg)
            except queue.Empty:
                break

        print("Processing batch of messages:", batch)
        filtered = filter_messages(batch)
        analyze(filtered)

        # Mark all items in this batch as processed
        for _ in batch:
            message_queue.task_done()


def add_messages(new_message):
    """
    Adds a new message to the queue and triggers the worker if it's not already running.

    Parameters:
        new_message (str): A new message to be processed.
    """
    global is_processing
    message_queue.put(new_message)
    print("New message added to queue:", new_message)

    # If no worker is running, start a new one
    with processing_lock:
        if not is_processing:
            is_processing = True
            print("Starting new worker thread for queue processing.")
            worker = threading.Thread(target=process_queue)
            worker.daemon = (
                True  # optional: ensures thread exits when main program does
            )
            worker.start()


# Example usage:
if __name__ == "__main__":
    # Simulate incoming messages one by one
    add_messages("Message 1")
    time.sleep(0.3)
    add_messages("Message 2")
    time.sleep(0.3)
    add_messages("Message 3")
    time.sleep(2)  # Wait to allow batch processing to finish
    add_messages("Message 4")
    time.sleep(0.1)
    add_messages("Message 5")

    # Wait for the queue to finish processing before exiting
    message_queue.join()
    print("All messages have been processed.")
