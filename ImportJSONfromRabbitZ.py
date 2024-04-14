import os
import json
import pika

def interpret_json(error_message, queue_name):
    # here we take in data from JSON
    try:
        data = json.loads(error_message)
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

            desired_keys = ["OrderProcessPositionId", "IdOrderWmsHead", "SourceHandlingUnit", "StoragePlace", "Guid", "DateCreated"]
            for key in desired_keys:
                if key.lower() in data_lower:
                    value = data_lower[key.lower()]

                    # Sonderfall für DATE "DateCreated"
                    if key.lower() == "datecreated":
                        value = value.split(".")[0].replace("T", " ")
                        date_part = value.split(" ")[0]


                    file_name = f"{date_part}_{exception_part}.json"
                    file_path = os.path.join(exception_dir, file_name)
                        # check if the file exists
                    if os.path.exists(file_path):
                        # if file exists, load existing data
                        with open(file_path, "r") as file:
                            existing_data = json.load(file)
                        existing_data.append(data)
                        # write the updated data back to file
                        with open(file_path, "w") as file:
                            json.dump(existing_data, file, indent=4)
                    else:   # or create the file
                        with open(file_path, "w") as file:
                                json.dump([data], file, indent=4)

                    print(f"{key}: {value}")

        print("\n", end="")  # just formatting
        print("-" * 50)
        print("\n", end="")

    except json.JSONDecodeError:
        print("The Matrix has you...")

def callback(ch, method, properties, body): # call the interpret_json function with the message received from RabbitMQ
    interpret_json(body.decode(), method.routing_key) 

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare the queues
# Declare the queues with durability first
queue_name1 = 'oliveranderson'
queue_name2 = 'pblnotificationinteractions'
try:
    channel.queue_declare(queue=queue_name1, durable=True)
    channel.queue_declare(queue=queue_name2, durable=True)
except pika.exceptions.ChannelClosedByBroker:
    # If the durable declaration fails, try declaring the queue as non-durable
    channel.queue_declare(queue=queue_name1, durable=False)
    channel.queue_declare(queue=queue_name2, durable=False)

# Set up a consumer to consume messages from the queue
channel.basic_consume(queue=queue_name1, on_message_callback=callback, auto_ack=True)
channel.basic_consume(queue=queue_name2, on_message_callback=callback, auto_ack=True)

# Start consuming messages
channel.start_consuming()
