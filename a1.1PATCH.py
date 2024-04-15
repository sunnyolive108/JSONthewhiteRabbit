import os
import json
import pika

def interpret_json(error_message, queue_name):
    # read line as JSON and give me the data
    try:
        data = json.loads(error_message)
        data = {key.lower(): value for key, value in data.items()}

        if "exception" in data:
            exception = data["exception"]
            exception_message = exception[:120]
            print("Queue:", queue_name)  
            print("Exception:", exception_message)

            # one directory for every exception
            exception_part = exception_message[-5:]
            exception_dir = os.path.join("JSONoutput", exception_part)
            print("Exception Directory:", exception_dir)
            print()
            if not os.path.exists(exception_dir):
                os.makedirs(exception_dir)

        if "message" in data:
            message_part = data["message"]
            data = json.loads(message_part)
            data_lower = {key.lower(): value for key, value in data.items()}
            desired_keys = ["OrderProcessPositionId", "IdOrderWmsHead", "SourceHandlingUnit", "StoragePlace",
                            "Guid", "DateCreated"]
                            
            for key in desired_keys:
                if key.lower() in data_lower:
                    value = data_lower[key.lower()]

                    # Sonderfall für "DateCreated"
                    if key.lower() == "datecreated":
                        value = value.split(".")[0].replace("T", " ")
                        date_part = value.split(" ")[0]

                        # write a file
                        file_name = f"{date_part}_{exception_part}.json"
                        file_path = os.path.join(exception_dir, file_name)
                        if os.path.exists(file_path):
                            # if file exists, load existing data
                            with open(file_path, "r") as file:
                                existing_data = json.load(file)
                            existing_data.append(data)
                            with open(file_path, "w") as file:
                                json.dump(existing_data, file, indent=4)
                        else:
                            # if file not exists, create new file
                            with open(file_path, "w") as file:
                                json.dump([data], file, indent=4)

                    # print key-value pairs to screen
                    print(f"{key}: {value}")

        print("\n", end="")  
        print("-" * 50) # just some formatting
        print("\n", end="")

    except json.JSONDecodeError:
        print("The Matrix has you...")

# Function to establish connection with retry logic
def establish_connection_with_retry(parameters, virtual_host):
    try:
        connection = pika.BlockingConnection(parameters)
        return connection
    except pika.exceptions.ProbableAccessDeniedError:
        print(f"Virtual host '{virtual_host}' not found. Retrying with default virtual host.")
        parameters.virtual_host = '/'
        return pika.BlockingConnection(parameters)

# Connect to RabbitMQ 
credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('localhost', virtual_host='BorC3', credentials=credentials)
connection = establish_connection_with_retry(parameters, 'BorC3')
channel = connection.channel()

# Declare the queues
queue_names = ['oliver', 'saymon']
for queue_name in queue_names:
    try:
        channel.queue_declare(queue=queue_name, durable=True)
    except pika.exceptions.ChannelClosedByBroker:
        # If the durable declaration fails, try declaring the queue as non-durable
        channel.queue_declare(queue=queue_name, durable=False)

# Define the callback function to handle incoming messages
def callback(ch, method, properties, body):
    interpret_json(body.decode(), method.routing_key)  # Pass the queue name as parameter

# Set up a consumer for each queue
for queue_name in queue_names:
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)

# Start consuming messages
channel.start_consuming()