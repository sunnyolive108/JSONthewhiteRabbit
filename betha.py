import os
import json
import pika
import logging
import configparser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Interpret the error message as JSON
def interpret_json(error_message, queue_name):
    try:
        data = json.loads(error_message)
        data_lower = {key.lower(): value for key, value in data.items()}  # Utilize data_lower

        exception_message = ""
        exception_part = ""

        if "exception" in data_lower: 
            exception = data_lower["exception"]
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
            
        if "message" in data_lower:
            message_part = data_lower["message"] 
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

config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.ini')
config.read(config_file_path)

# Get RabbitMQ configurations
rabbitmq_config = config['RabbitMQ']
credentials = pika.PlainCredentials(rabbitmq_config['username'], rabbitmq_config['password'])
parameters = pika.ConnectionParameters(rabbitmq_config['host'], virtual_host=rabbitmq_config['virtual_host'], credentials=credentials)

# Function to start listening
def start_listening(queue_names):
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        for queue_name in queue_names:
            try:
                channel.queue_declare(queue=queue_name, durable=True)
            except pika.exceptions.ChannelClosedByBroker:
                logger.warning("Channel closed by broker. Reopening and retrying...")
                connection = pika.BlockingConnection(parameters)
                channel = connection.channel()
                channel.queue_declare(queue=queue_name, durable=True)

        def callback(ch, method, properties, body):
            interpret_json(body.decode(), method.routing_key)

        for queue_name in queue_names:
            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)

        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        logger.error("AMQP connection error: %s", e)
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)

while True:
    try:
        queue_input = input("Queues, comma-separated: ")
        queue_names = [queue.strip() for queue in queue_input.split(",")]
        start_listening(queue_names)
    except KeyboardInterrupt:
        logger.info("Keep chasin' ...")
        continue