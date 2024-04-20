import logging
import os
import json
import pika
import configparser

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Interpret the error message as JSON
def interpret_json(error_message, queue_name):
    try:
        data = json.loads(error_message)
        data_lower = {key.lower(): value for key, value in data.items()}

        if "exception" in data:
            exception = data["exception"]
            exception_message = exception[:120]
            print("")
            logger.info("Queue: %s", queue_name)
            logger.info("Exception: %s", exception_message)

            # The directory state
            base_dir = os.path.join(os.path.dirname(__file__), "RabbitMQoutput")
            queue_dir = os.path.join(base_dir, queue_name)
            exception_part = "".join(c for c in exception_message[-21:].strip() if c.isalpha())
            exception_dir = os.path.join(queue_dir, exception_part)

            os.makedirs(exception_dir, exist_ok=True)
            logger.info("Exception Directory: %s", exception_dir)
            print("")

        if "message" in data:
            message_part = data["message"]
            data = json.loads(message_part)
            data_lower = {key.lower(): value for key, value in data.items()}
            logger.info("The Message:\n")
            for key, value in data_lower.items():
                logger.info("%s: %s", key, value)
            logger.info("\n" + "-" * 42 + "\n")

            for key in data_lower:
                if key.lower() in data_lower:
                    value = data_lower[key.lower()]

                    if key.lower() == "datecreated":
                        value = value.split(".")[0].replace("T", " ")
                        date_part = value.split(" ")[0]

                        # Save file in the appropriate directory
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

    except json.JSONDecodeError as e:
        logger.error("JSON decoding error: %s", e)
    except Exception as e:
        logger.error("An error occurred: %s", e)

config = configparser.ConfigParser()
config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.ini')
config.read(config_file_path)

rabbitmq_config = config['RabbitMQ']
credentials = pika.PlainCredentials(rabbitmq_config['username'], rabbitmq_config['password'])
parameters = pika.ConnectionParameters(rabbitmq_config['host'], virtual_host=rabbitmq_config['virtual_host'], credentials=credentials)

# ask me anything
def main():
    logger.info("*****                                          *******")
    logger.info("******                                        ********")
    logger.info("*******                                      *********")
    logger.info("*******                                      *********")
    logger.info("******************************************************")
    logger.info("*    ||||    RabbitMQ Processing Program     ====    *")
    logger.info("*           **           or            **            *")
    logger.info("*            ***JSON the white Rabbit***             *")
    logger.info("******************************************************\n")

    while True:
        try:
            queue_input = input("Queues, comma-separated: ")
            queue_names = [queue.strip() for queue in queue_input.split(",")]

            # Function to start listening
            def start_listening():
                for queue_name in queue_names:
                    try:
                        connection = pika.BlockingConnection(parameters)
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
            if queue_input == "exit":
                break
            
        except KeyboardInterrupt:
            logger.info("hasin'forth...")
            continue

if __name__ == "__main__":
    main()
