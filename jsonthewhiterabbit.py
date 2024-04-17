import os
import json
import pika
import logging
from PyQt5.QtWidgets import QMainWindow, QLineEdit, QPushButton, QTextEdit, QApplication, QLabel
from PyQt5.QtGui import QPixmap

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
            logger.info("Queue: %s", queue_name)
            logger.info("Exception: %s", exception_message)

            # The directory state
            base_dir = os.path.join(os.path.dirname(__file__), "RabbitMQTESToutput")
            queue_dir = os.path.join(base_dir, queue_name)
            exception_part = "".join(c for c in exception_message[-21:].strip() if c.isalpha())
            exception_dir = os.path.join(queue_dir, exception_part)

            os.makedirs(exception_dir, exist_ok=True)
            logger.info("Exception Directory: %s", exception_dir)

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

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("JSON the White Rabbit")
        self.setGeometry(90, 95, 500, 400)

        # Get the path to the "img" directory
        script_dir = os.path.dirname(__file__)
        img_dir = os.path.join(script_dir, "img")

        # Load the image
        pixmap = QPixmap(os.path.join(img_dir, "rabbitmq.png"))

        # Create a label for the image
        self.image_label = QLabel(self)
        self.image_label.setPixmap(pixmap)
        self.image_label.setGeometry(370, 10, 120, 160)

        # Labels for input fields
        self.username_label = QLabel("Username:", self)
        self.username_label.setGeometry(40, 40, 80, 30)

        self.password_label = QLabel("Password:", self)
        self.password_label.setGeometry(40, 80, 80, 30)

        self.hostname_label = QLabel("Hostname:", self)
        self.hostname_label.setGeometry(100, 120, 80, 30)

        self.virtual_host_label = QLabel("Virtual Host:", self)
        self.virtual_host_label.setGeometry(90, 160, 80, 30)

        self.queue_names_label = QLabel("Queue Names (comma-s):", self)
        self.queue_names_label.setGeometry(30, 200, 250, 30)

        # Input fields for credentials and parameters
        self.username_field = QLineEdit(self)
        self.username_field.setGeometry(120, 40, 200, 30)

        self.password_field = QLineEdit(self)
        self.password_field.setGeometry(120, 80, 200, 30)
        self.password_field.setEchoMode(QLineEdit.Password)

        self.hostname_field = QLineEdit(self)
        self.hostname_field.setGeometry(180, 120, 138, 30)

        self.virtual_host_field = QLineEdit(self)
        self.virtual_host_field.setGeometry(180, 160, 138, 30)

        self.queue_names_field = QTextEdit(self)
        self.queue_names_field.setGeometry(30, 230, 420, 100)

        # Create button to start listening
        self.listen_button = QPushButton("Start Listening", self)
        self.listen_button.setGeometry(180, 340, 150, 30)
        self.listen_button.clicked.connect(self.start_listening)

    # Function to start listening
    def start_listening(self):
        try:
            credentials = pika.PlainCredentials(self.username_field.text(), self.password_field.text())
            parameters = pika.ConnectionParameters(host=self.hostname_field.text(),
                                                    virtual_host=self.virtual_host_field.text(),
                                                    credentials=credentials)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            queue_names = self.queue_names_field.toPlainText().split(',')

            for queue_name in queue_names:
                try:
                    channel.queue_declare(queue=queue_name.strip(), durable=True)
                except pika.exceptions.ChannelClosedByBroker:
                    logger.warning("Channel closed by broker. Reopening and retrying...")
                    connection = pika.BlockingConnection(parameters)
                    channel = connection.channel()
                    channel.queue_declare(queue=queue_name.strip(), durable=True)

            def callback(ch, method, properties, body):
                interpret_json(body.decode(), method.routing_key)

            for queue_name in queue_names:
                channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)

            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            logger.error("AMQP connection error: %s", e)
        except Exception as e:
            logger.error("An unexpected error occurred: %s", e)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
