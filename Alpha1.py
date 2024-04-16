import os
import json 
import pika

def interpret_json(error_message, queue_name): 
    try:
        data = json.loads(error_message)
        data = {key.lower(): value for key, value in data.items()}

        if "exception" in data:
            exception = data["exception"]
            exception_message = exception[:120]
            print("Queue: ", queue_name)
            print("Exception: ", exception_message)

            # the directory state
            base_dir = os.path.join(os.getcwd(), "RabbitMQoutput")
            queue_dir = os.path.join(base_dir, queue_name)
            exception_part = "".join(c for c in exception_message[-21:].strip() if c.isalpha())
            exception_dir = os.path.join(queue_dir, exception_part)
          
            os.makedirs(exception_dir, exist_ok=True)
            print("Exception Directory: ", exception_dir)
            print()

        if "message" in data:
            message_part = data["message"]
            data = json.loads(message_part)
            data_lower = {key.lower(): value for key, value in data.items()}
            print("The Message: \n")
            for key, value in data_lower.items():
                print(f"{key}: {value}")
            print("\n")
            print("-" * 51)
            print("\n")

            for key in data_lower:
                if key.lower() in data_lower:
                    value = data_lower[key.lower()]

                    if key.lower() == "datecreated":
                        value = value.split(".")[0].replace("T", " ")
                        date_part = value.split(" ")[0]

                        # save file in the appropriate directory
                        file_name = f"{date_part}_{exception_part}.json"
                        file_path = os.path.join(exception_dir, file_name)
                        if os.path.exists(file_path):
                            with open(file_path, "r") as file:
                                existing_data = json.load(file)
                            existing_data.append(data)
                            with open(file_path, "w") as file:
                                json.dump(existing_data, file, indent=4)
                        else:
                            with open(file_path, "w") as file:
                                json.dump([data], file, indent=4)

    except json.JSONDecodeError:
        print("The Matrix has you...")

# establish a connection to a RabbitMQ server
credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('localhost', credentials=credentials) # 'your_host', virtual_host='XYZ', 
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

queue_names = ['yourchoice', 'whateveryouwantittobe']

for queue_name in queue_names:
  try:   
    channel.queue_declare(queue=queue_name, durable=True)
  except pika.exceptions.ChannelClosedByBroker:
    channel.queue_declare(queue=queue_name, durable=False)

def callback(ch, method, properties, body):
  interpret_json(body.decode(), method.routing_key)

for queue_name in queue_names:
  channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)

channel.start_consuming()