# IRIV IO Controller with MQTT GPIO Control #

This CircuitPython code enables IRIV IO Controller to control its digital output (D0-D3) via MQTT. It establishes a robust Ethernet connection using DHCP and then connects to an MQTT broker, allowing for remote command and control of IRIV IO Controller digital outputs. 

🌟 Features
- Ethernet Connectivity: Initializes the WIZnet W5500 Ethernet module for reliable network access, obtaining an IP address via DHCP.
- HTTP GET Test: Includes a basic HTTP GET request to http://wifitest.adafruit.com/testwifi/index.html to verify successful network connectivity at startup.
- GPIO Control: Configures specified digital output pins (DO0-DO3) as outputs, ready for controlling external components.

MQTT Communication:
- Connects to a user-defined MQTT broker using the adafruit_minimqtt library.
- Subscribes to the pico/gpio_control/# topic to receive commands for controlling individual GPIOs.
- Parses incoming MQTT messages in the format GPIOX,STATE (e.g., "GPIO12,ON" or "GPIO13,OFF") to set the state of the corresponding GPIO pin.
- Publishes the current state of the controlled GPIO pins back to a state topic (e.g., pico/gpio_state/GPIOX) after a command is processed, providing feedback.
- Robustness: Incorporates comprehensive error handling for both network and MQTT connection issues, featuring automatic reconnection attempts to maintain continuous operation.

🛠️ Setup
Prerequisites

Hardware:
- IRIV IO Controller

Software:
- CircuitPython firmware loaded on your IRIV IO Controller.
- CircuitPython Libraries (available from the CircuitPython Bundle):
  - adafruit_connection_manager
  - adafruit_requests
  - adafruit_wiznet5k
  - adafruit_minimqtt

Configuration
Open code.py and modify the MQTT broker details section with your specific information:

### --- MQTT Broker Setup details--- ###

```
MQTT_BROKER = "your_mqtt_broker_ip_or_hostname"  # Replace with your MQTT broker IP or hostname
MQTT_PORT = 1883                               # Default MQTT port
# For MQTT over SSL (if your broker supports it, typically port 8883)
# MQTT_PORT = 8883
MQTT_USERNAME = 'your_mqtt_username'           # Your MQTT broker username (leave empty if none)
MQTT_PASSWORD = 'your_mqtt_password'           # Your MQTT broker password (leave empty if none)
```

🚀 Usage
1. Upload the Code: Save the modified code.py to your Pico W's CIRCUITPY drive.
2. Monitor Output: Open a serial console (e.g., using minicom, PuTTY, or the Thonny IDE's serial monitor) to see the network initialization and MQTT connection status.

Control GPIOs via MQTT:
1. Connect to your MQTT broker using an MQTT client (e.g., mqtt-explorer, Mosquitto client, or a custom application).
2. To turn a GPIO pin ON, publish a message to the topic pico/gpio_control/GPIOX with the payload "ON".
    
    Example: Topic: pico/gpio_control/GPIO12, Payload: ON

3. To turn a GPIO pin OFF, publish a message to the topic pico/gpio_control/GPIOX with the payload "OFF".
    
    Example: Topic: pico/gpio_control/GPIO12, Payload: OFF

The on_message function expects the message payload to be in the format GPIOX,STATE. For example, a single message like "GPIO12,ON" to the pico/gpio_control base topic. However, the subscription pico/gpio_control/# allows for more specific topics like pico/gpio_control/GPIO12. The current parsing expects the full GPIOX,STATE in the message content. If you are publishing to specific sub-topics, you might adjust the on_message logic. The current setup implies the payload contains the GPIOX,STATE string.

Example MQTT Publication (using a client like mqtt-explorer):

| Topic | Payload | Description |
| --- | --- | --- |
| `pico/gpio_control` | `GPIO12,ON` | Turns GPIO12 on |
| `pico/gpio_control` | `GPIO12,OFF` | Turns GPIO12 off |
| `pico/gpio_control` | `GPIO13,ON` | Turns GPIO13 on |


State Feedback:
The Pico W will publish the updated state of a GPIO pin to pico/gpio_state/GPIOX (e.g., pico/gpio_state/GPIO12) with a payload of "ON" or "OFF" after a command is processed. You can subscribe to these topics to monitor the current state of your pins.
