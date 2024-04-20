# RabbitMQ Message Processing Program
## or Follow the White Rabbit

This program fetches messages from a RabbitMQ queue and processes them, writing the results into a file.

## Features

- Fetch messages from a RabbitMQ queue
- Process messages using the `interpret_json` function
- Write processed data into a file

## Future Ideas

- Further automate the handling process
- Additional processing of data into another program
- Feed data into a statistics & documentation program
- Create an interface to input host and port information

## Usage

1. Set up a RabbitMQ server
2. Clone the repository:

   ```bash
   git clone https://github.com/sunnyolive108/FollowTheWhiteRabbit.git
3. Install the necessary modules
4. Navigate to the repository on your machine & run the program
   ```bash
   python jsonthewhiterabbit.py

 RabbitMQ Server Installation and Management

## Installation

### Install RabbitMQ Server

```bash
sudo apt-get update
sudo apt-get install rabbitmq-server

## Start RabbitMQ Server
```bash
sudo service rabbitmq-server start

## Enabling Management Plugin (if not enabled by default)
```bash
sudo rabbitmq-plugins enable rabbitmq_management
sudo service rabbitmq-server restart

## Access Information
RabbitMQ management plugin listens on port 15672.
http://localhost:15672

Default credentials for the management interface are
Username: guest
Password: guest
---

## Contribution
   feel free to contribute! Just submit a pull request with your changes.
- Thank you :) Oliver
