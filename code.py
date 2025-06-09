import board
import busio
import digitalio
import time
import adafruit_connection_manager # New import!
import adafruit_requests
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K # Using the specific import you provided
import adafruit_minimqtt.adafruit_minimqtt as MQTT

### --- MQTT Setup --- ###
# MQTT Broker details
MQTT_BROKER = "your MQTT broker IP"  # Example public broker, replace with yours
MQTT_PORT = 1883
# For MQTT over SSL (if your broker supports it, typically port 8883)
# MQTT_PORT = 8883
MQTT_USERNAME = 'Your MQTT broker username'  # No username for public broker
MQTT_PASSWORD = 'Your MQTT broker password'  # No password for public broker

### --- Ethernet Setup using adafruit_connection_manager --- ###

# It's good practice to explicitly define the pins if they're not
# always available as `board.W5500_CS`, etc., or if you want to be
# explicit about your wiring.
# However, if your CircuitPython build includes these aliases, they're convenient.

# Assuming the following standard pin connections for W5500 on Pico W:
# SCK  -> board.GP18 (usually board.SCK or board.SPI0_SCK)
# MOSI -> board.GP19 (usually board.MOSI or board.SPI0_MOSI)
# MISO -> board.GP16 (usually board.MISO or board.SPI0_MISO)
# CS   -> board.GP17 (Chip Select for W5500, could be board.W5500_CS if defined)
# RST  -> board.GP20 (Reset pin for W5500, optional but good practice)

# Use board aliases if available, otherwise use explicit GP pins:
# If your board.py defines W5500_CS etc., use them directly.
# Otherwise, uncomment and use the GP pins as wired.
ETHERNET_CS = board.W5500_CS if hasattr(board, 'W5500_CS') else board.GP17
ETHERNET_RST = board.W5500_RST if hasattr(board, 'W5500_RST') else board.GP20 # Check if RST is defined or use your GP pin

# Initialize CS (Chip Select) and RST (Reset) pins
cs = digitalio.DigitalInOut(ETHERNET_CS)
reset = digitalio.DigitalInOut(ETHERNET_RST) if ETHERNET_RST else None

# Initialize SPI bus
# Use board.SPI() if available, otherwise specific SPI0 pins
try:
    spi_bus = board.SPI() # This might map to default SPI for the board
except AttributeError:
    # Fallback to specific pins if board.SPI() is not defined or preferred
    print("board.SPI() not found, using explicit GP pins for SPI.")
    spi_bus = busio.SPI(board.GP18, MOSI=board.GP19, MISO=board.GP16)


# Initialize ethernet interface with DHCP
print("Initializing Ethernet via WIZNET5K...")
eth = WIZNET5K(spi_bus, cs, reset=reset) # Pass the reset pin to WIZNET5K

print("Chip ID:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))
print(f"IP lookup adafruit.com: {eth.pretty_ip(eth.get_host_by_name('adafruit.com'))}")


# Initialize a requests session using adafruit_connection_manager
print("Initializing adafruit_connection_manager for requests and MQTT...")
pool = adafruit_connection_manager.get_radio_socketpool(eth)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(eth)
requests = adafruit_requests.Session(pool, ssl_context)

print("Ethernet setup complete. Trying a simple GET request for testing...")
try:
    print("Fetching text from", "http://wifitest.adafruit.com/testwifi/index.html")
    r = requests.get("http://wifitest.adafruit.com/testwifi/index.html")
    print("-" * 40)
    print(r.text)
    print("-" * 40)
    r.close()
    print("HTTP GET test successful.")
except Exception as e:
    print(f"HTTP GET test failed: {e}")
    # Handle network initialization failure, maybe restart or blink an error LED
    while True:
        time.sleep(5) # Halt if basic network isn't working

### --- GPIO Setup --- ###
# Define the GPIO pins for control
PINS = {
    "GPIO12": digitalio.DigitalInOut(board.GP12),
    "GPIO13": digitalio.DigitalInOut(board.GP13),
    "GPIO14": digitalio.DigitalInOut(board.GP14),
    "GPIO15": digitalio.DigitalInOut(board.GP15),
}

# Set all GPIO pins as outputs and initially turn them off
for pin_name, pin_obj in PINS.items():
    pin_obj.direction = digitalio.Direction.OUTPUT
    pin_obj.value = False  # Start with pins off
    print(f"{pin_name} initialized as OUTPUT and set to LOW.")

# Topics
MQTT_COMMAND_TOPIC_BASE = "pico/gpio_control"
MQTT_STATE_TOPIC_BASE = "pico/gpio_state"

# Callback function for when a new MQTT message is received
def on_message(client, topic, message):
    print(f"Received message on topic '{topic}': '{message}'")

    try:
        if topic.startswith(MQTT_COMMAND_TOPIC_BASE):
            parts = message.split(',')
            if len(parts) == 2:
                gpio_name = parts[0].strip().upper()
                command = parts[1].strip().upper()

                if gpio_name in PINS:
                    pin_obj = PINS[gpio_name]
                    if command == "ON":
                        pin_obj.value = True
                        print(f"Turned {gpio_name} ON")
                        client.publish(f"{MQTT_STATE_TOPIC_BASE}/{gpio_name}", "ON")
                    elif command == "OFF":
                        pin_obj.value = False
                        print(f"Turned {gpio_name} OFF")
                        client.publish(f"{MQTT_STATE_TOPIC_BASE}/{gpio_name}", "OFF")
                    else:
                        print(f"Invalid command for {gpio_name}: {command}. Use 'ON' or 'OFF'.")
                else:
                    print(f"Unknown GPIO name: {gpio_name}")
            else:
                print(f"Invalid message format: {message}. Expected 'GPIOX,STATE'.")
        else:
            print(f"Unhandled topic: {topic}")

    except Exception as e:
        print(f"Error processing MQTT message: {e}")

# Callback function for when the MQTT client connects
def connected(client, userdata, flags, rc):
    print("Connected to MQTT Broker!")
    client.subscribe(MQTT_COMMAND_TOPIC_BASE + "/#") # Subscribe to all sub-topics under control

# Callback function for when the MQTT client disconnects
def disconnected(client, userdata, rc):
    print("Disconnected from MQTT Broker!")

# Create MQTT client using the shared socket pool and SSL context
mqtt_client = MQTT.MQTT(
    broker=MQTT_BROKER,
    port=MQTT_PORT,
    username=MQTT_USERNAME,
    password=MQTT_PASSWORD,
    socket_pool=pool,       # Use the pool from adafruit_connection_manager
    ssl_context=ssl_context,# Use the ssl_context from adafruit_connection_manager (even if not using SSL, it's good practice)
    keep_alive=60
)

# Setup the callback functions
mqtt_client.on_connect = connected
mqtt_client.on_message = on_message
mqtt_client.on_disconnect = disconnected

print(f"Attempting to connect to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}...")
try:
    mqtt_client.connect()
    print("MQTT connection successful.")
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")
    # Handle connection failure, e.g., retry or exit
    while True:
        time.sleep(5) # Keep retrying or stop execution

# Main loop
while True:
    try:
        mqtt_client.loop()
    except (MQTT.MMQTTException, OSError) as e:
        print(f"MQTT connection error: {e}. Reconnecting...")
        try:
            mqtt_client.reconnect()
        except Exception as reconnect_e:
            print(f"Failed to reconnect: {reconnect_e}. Retrying in 5 seconds...")
            time.sleep(5)
    except Exception as e:
        print(f"An unexpected error occurred: {e}. Exiting.")
        break # Exit the loop on unexpected errors

    time.sleep(0.5) # Short delay to avoid busy-waiting
