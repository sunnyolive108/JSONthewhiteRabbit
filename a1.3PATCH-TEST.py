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

      exception_part = "".join(c for c in exception_message[-15:].strip() if c.isalnum())
      exception_dir = os.path.join("JSONoutput", exception_part)
      print("Exception Directory: ", exception_dir)
      print()
      if not os.path.exists(exception_dir):
        os.makedirs(exception_dir)

    if "message" in data:
      message_part = data["message"]
      data = json.loads(message_part)
      data_lower = {key.lower(): value for key, value in data.items()}
      desired_keys = ["OrderProcessPositionId", "IdOrderWmsHead", "SourceHandlingUnit", "HandlingUnitId",
                      "StorePlace", "PicklistId", "Guid", "DateCreated"]

    for key in desired_keys:
        if key.lower() in data_lower:
            value = data_lower[key.lower()]

            if key.lower() == "datecreated":
                value = value.split(".")[0].replace("T", " ")
                date_part = value.split(" ")[0]

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

            print(f"{key}: {value}")

    print("\n", end="")
    print("-" * 50)
    print("\n", end="")

  except json.JSONDecodeError:
    print("The Matrix has you...")

# establish a connection to a RabbitMQ server
credentials = pika.PlainCredentials('Lx1Admin', 'fFIGSCMVdyc5SyhYO2Mr')
parameters = pika.ConnectionParameters('svrzaapp015.ads.loxxess.de', virtual_host='BorC3', credentials=credentials) # virtual_host='XYZ', 
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

queue_names = ['loxxess.lx1.c3.los.orderstarts.errors']

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
