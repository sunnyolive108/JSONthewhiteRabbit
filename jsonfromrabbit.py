import os
import json
import pika

def interpret_json(error_message, queue_name):
    # read line as JSON and give me data
    try:
        data = json.loads(error_message)
        if "exception" in data:
            exception = data["exception"]
            exception_message = exception[:120]
            # print exception part
            print("Queue:", queue_name)  # Display queue name
            print("Exception:", exception_message)

            # one directory for every exception
            exception_part = exception_message[-5:]
            exception_dir = os.path.join("JSONoutput", exception_part)
            print("Exception Directory:", exception_dir)  # Debug print
            print()
            if not os.path.exists(exception_dir):
                os.makedirs(exception_dir)
            
        if "message" in data:
            message_part = data["message"]
            # load message part into a dictionary
            data = json.loads(message_part)
            # all keys in lowercase
            data_lower = {key.lower(): value for key, value in data.items()}

            # extract desired keys
            desired_keys = ["OrderProcessPositionId", "IdOrderWmsHead", "SourceHandlingUnit", "StoragePlace", "Guid", "DateCreated"]
            for key in desired_keys:
                if key.lower() in data_lower:
                    value = data_lower[key.lower()]

                    # Sonderfall für "DateCreated"
                    if key.lower() == "datecreated":
                        value = value.split(".")[0].replace("T", " ")
                        date_part = value.split(" ")[0]

                        # write a file 
                        file_name = f"{date_part}_{exception_part}.json"
                        # check if the file exists
                        file_path = os.path.join(exception_dir, file_name)
                        if os.path.exists(file_path):
                            # if file exists, load existing data
                            with open(file_path, "r") as file:
                                existing_data = json.load(file)
                            # append new data
                            existing_data.append(data)
                            # write the updated data back to file
                            with open(file_path, "w") as file:
                                json.dump(existing_data, file, indent=4)
                        else:
                            # if file does't exist, create a new file
                            with open(file_path, "w") as file:
                                json.dump([data], file, indent=4)

                    # print key: value pairs to screen
                    print(f"{key}: {value}")

        print("\n", end="")  # just a line of space 
        print("-" * 50)
        print("\n", end="")

    except json.JSONDecodeError:
        print("The Matrix has you...")

def callback(ch, method, properties, body):
    # call the interpret_json function with the message received from RabbitMQ
    interpret_json(body.decode(), method.routing_key)  # Pass the queue name as parameter

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare the queue
# Declare the queue with durability first
queue_name = 'THENAMEOFFTHEQUEUE'
try:
    channel.queue_declare(queue=queue_name, durable=True)
except pika.exceptions.ChannelClosedByBroker:
    # If the durable declaration fails, try declaring the queue as non-durable
    channel.queue_declare(queue=queue_name, durable=False)

# Set up a consumer to consume messages from the queue
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

# Start consuming messages
channel.start_consuming()
