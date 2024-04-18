import os
import json
import pika
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Interpret the error message as JSON
def interpret_json(error_message, queue_name):
    try:
        data = json.loads(error_message)
        data_lower = {key.lower(): value for key, value in data.items()}

        exception_message = ""
        exception_part = ""

        if "exception" in data:
            exception = data["exception"]
            exception_message = exception[:210]
            print("")
            logger.info("Queue: %s", queue_name)
            logger.info("Exception: %s", exception_message)

            # The directory state
            base_dir = os.path.join(os.path.dirname(__file__), "RabbitMQTESToutput")
            queue_dir = os.path.join(base_dir, queue_name)
            exception_part = "".join(c for c in exception_message[-21:].strip() if c.isalpha())
            exception_dir = os.path.join(queue_dir, exception_part)

            os.makedirs(exception_dir, exist_ok=True)
            logger.info("Exception Directory: %s", exception_dir)
            print("")
            
        if "message" in data:
            message_part = data["message"]
            message_data = json.loads(message_part)

            for key, value in message_data.items():
                if isinstance(value, dict):
                    for k, v in value.items():
                        logger.info("%s: %s", k, v)
                else:
                    logger.info("%s: %s", key, value)
            logger.info("-" * 42)

            # Saving data to file
            if exception_part:
                if not os.path.exists(exception_dir):
                    os.makedirs(exception_dir)

                file_name = f"data_{exception_part}.json"
                file_path = os.path.join(exception_dir, file_name)
                with open(file_path, "a") as file:
                    json.dump(message_data, file, indent=4)
                    logger.info("Data written to file: %s", file_path)

    except json.JSONDecodeError as e:
        logger.error("JSON decoding error: %s", e)
    except Exception as e:
        logger.error("An error occurred: %s", e)

# Main loop
while True:
    try:
        queue_input = input("Queues, comma-separated: ")

        queue_names = [queue.strip() for queue in queue_input.split(",")]

        # Function to start listening
        def start_listening():
            for queue_name in queue_names:
                try:
                    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
                    channel = connection.channel()

                    try:
                        channel.queue_declare(queue=queue_name, durable=True)
                    except pika.exceptions.ChannelClosedByBroker:
                        logger.warning("Channel closed by broker. Reopening and retrying...")
                        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
                        channel = connection.channel()
                        channel.queue_declare(queue=queue_name, durable=True)

                    def callback(ch, method, properties, body):
                        interpret_json(body.decode(), method.routing_key)

                    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)

                    channel.start_consuming()

                except pika.exceptions.AMQPConnectionError:
                    logger.error("Failed to establish connection to RabbitMQ. Retrying...")

        start_listening()

    except KeyboardInterrupt:
        logger.info("Keep chasin' ...")
        continue
