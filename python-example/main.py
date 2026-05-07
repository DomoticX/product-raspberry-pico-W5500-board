from umqtt.simple import MQTTClient
from usocket import socket
import socket
from machine import Pin, SPI
import network
import time

# MQTT config
mqtt_server = '192.168.2.41'
client_id = 'wiz'
topic_pub = b'hello'
topic_msg = b'Hello Pico!'

# Pins voor W5500
rst = Pin(20, Pin.OUT)

# W5500 reset
print("Reset W5500...")
rst.value(0)
time.sleep(0.1)
rst.value(1)
time.sleep(4)
print("OK!")

# W5x00 init
def w5x00_init():
    spi = SPI(0, 5_000_000, mosi=Pin(19), miso=Pin(16), sck=Pin(18))
    nic = network.WIZNET5K(spi, Pin(17), Pin(20))  # SPI, CS, RESET pin
    nic.active(True)
    time.sleep(2)

    # DHCP
    nic.ifconfig('dhcp')
    print('IP address:', nic.ifconfig())
    print(socket.getaddrinfo(mqtt_server, 1883))

    while not nic.isconnected():
        time.sleep(1)
        print('Waiting for Ethernet...')

    return nic

# MQTT connect functie
def mqtt_connect():
    client = MQTTClient(client_id, mqtt_server, keepalive=60)
    client.connect()
    print('Connected to MQTT Broker:', mqtt_server)
    return client

# Main loop
def main():
    counter = 0
    nic = w5x00_init()
    client = None

    while True:
        try:
            if client is None:
                client = mqtt_connect()

            payload = topic_msg + b": " + str(counter).encode()
            client.publish(topic_pub, payload)
            print("Published:", payload)

            counter += 1
            time.sleep(1)

        except OSError as e:
            print('MQTT Error:', e)

            try:
                if client is not None:
                    client.disconnect()
            except:
                pass

            client = None  # Forceer herverbinden
            print('Reconnecting MQTT in 5 seconds...')
            time.sleep(5)

        # Check Ethernet status
        if not nic.isconnected():
            print('Ethernet disconnected! Reconnecting Ethernet...')
            try:
                nic.active(False)
                time.sleep(2)
                nic.active(True)
                time.sleep(2)
                nic.ifconfig('dhcp')
                print('Ethernet reconnected:', nic.ifconfig())
            except OSError as e:
                print('Ethernet reconnect failed:', e)
                time.sleep(5)

if __name__ == "__main__":
    main()


