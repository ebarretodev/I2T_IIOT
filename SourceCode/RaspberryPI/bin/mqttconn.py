import paho.mqtt.client as mqtt

class MQTT_IOTA_STREAMS():
    def __init__(self, name, IP_address, Port=1883):
        self.client = mqtt.Client(name)
        self.IP_address = IP_address
        self.Port = Port


    def PublishMessage(self, topic, payload):
        self.client.connect(self.IP_address, self.Port)
        self.client.publish(topic, payload)
        self.client.disconnect()

if __name__ == '__main__':
    ConTest = MQTT_IOTA_STREAMS('RaspberryS4B', 'localhost')
    ConTest.PublishMessage('teste', 'hello1')
