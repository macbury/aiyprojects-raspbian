from rpi_rf import RFDevice
from threading import Lock
import json
import logging
import aiy.voicehat
import time

logger = logging.getLogger('rf')

RF_STATES = dict()

PULSE_LENGTH = [321, 308]

class RFController:
  def __init__(self, config):
    self.rfdevice = RFDevice(config['gpio'])
    self.rfdevice.enable_tx()
    self.config = config
    self.state_topic = config['state_topic']
    self.command_topic = config['command_topic']
    self.protocol = config['protocol']
    self.states = {}
    self.dirty = []
    self.client = None
    self.lock = Lock()

  def setup(self, client):
    self.client = client
    logger.info("Subscribing to topic: {}".format(self.command_topic))
    self.client.subscribe(self.command_topic)

  def pop(self):
    with self.lock:
      if len(self.dirty) > 0:
        logger.info("Elements on queue: {}".format(len(self.dirty)))
        return self.dirty.pop(0)
      else:
        return None

  def size(self):
    with self.lock:
      return len(self.dirty)

  def update(self, led):
    while self.size() > 0:
      led.set_state(aiy.voicehat.LED.ON)
      code = self.pop()

      logger.info("Update!")
      self.broadcast(code)
      led.set_state(aiy.voicehat.LED.BEACON_DARK)

  def send_state(self, new_states):
    states = json.dumps(new_states)
    logger.info("Sending states {}".format(self.states))
    self.client.publish(topic=self.state_topic, payload=states, retain=True, qos=1)

  def broadcast(self, code):
    logger.info("Broadcasting all states!")
    for x in range(0,2):
      for pulse_length in PULSE_LENGTH:
        logger.info("RFDevice code={} protocol={} pulse_length={}".format(code, self.protocol, pulse_length))
        self.rfdevice.tx_code(code, self.protocol, pulse_length)
        time.sleep(0.1)

  def handle_message(self, msg):
    logger.info("Got message")
    logger.info(msg.payload)
    if msg.topic == self.command_topic:
      message = json.loads(msg.payload.decode('utf-8'))
      with self.lock:
        self.states[str(message['name'])] = int(message['code'])
        self.dirty.append(int(message['code']))
    self.send_state(self.states)
    