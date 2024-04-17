dependencies:
# pip install pyqt5
# pip install pika

Du brauchst deine Credentials, 
den hostnamen (-> Aktuelle Installationen) 
sowie den korrekten Virtual Host ('BorC3')

oder hoste deinen eigenen RabbitMQ server
unter 'guest', 'guest', 'localhost'

Dependencies:

To run this application, you'll need the following dependencies:

PyQt5: This is a Python binding for the Qt toolkit. It provides a set of Python modules that allow you to use Qt classes and functions. You can install it using pip:

Copy code
pip install PyQt5
pika: This is a RabbitMQ client library for Python. It enables Python applications to communicate with RabbitMQ message brokers. You can install it using pip:

Copy code
pip install pika
Usage:

Before running the application, make sure you have the following information ready:

Credentials: You'll need the username and password for your RabbitMQ server.
Hostname: Specify the hostname or IP address of the RabbitMQ server. If you're using a local installation, you can use "localhost".
Virtual Host: If required, specify the virtual host for your RabbitMQ server. For this application, the virtual host should be set to "BorC3".
Alternatively, you can host your own RabbitMQ server using the default credentials "guest" and "guest" on "localhost".

Running the Application:

Once you have installed the dependencies and gathered the necessary information, you can run the application by executing the Python script. Make sure to provide the required credentials, hostname, and virtual host when prompted.

Copy code
python your_script_name.py
Replace "your_script_name.py" with the name of your Python script containing the application code.

Note:

Ensure that RabbitMQ server is running and accessible before running the application. If you encounter any issues, refer to the troubleshooting section in the README or consult the official documentation of PyQt5 and pika.