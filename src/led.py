"""Signal states on a LED and MQTT broker"""

import logging
import os
import time

import aiy.voicehat
import RPi.GPIO as GPIO

import paho.mqtt.client as mqtt
from ruamel.yaml import YAML
from rpi_rf import RFDevice

logger = logging.getLogger('led')

CONFIG_DIR = os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
MQTT_CONFIG_FILE = os.path.join(CONFIG_DIR, 'mqtt.yaml')
CONFIG_FILES = [
  '/etc/status-led.ini',
  os.path.join(CONFIG_DIR, 'status-led.ini')
]

logger.info("Loading config: " + MQTT_CONFIG_FILE)
MQTT_CONFIG = YAML(typ='safe').load(open(MQTT_CONFIG_FILE))
RF_CONFIG = MQTT_CONFIG['rf_switch']

def prepare_client(rfdevice):
  client = mqtt.Client()
  client.enable_logger(logger)
  client.username_pw_set(MQTT_CONFIG['username'], MQTT_CONFIG['password'])
  logger.info("Connecting to: " + MQTT_CONFIG['host'] + " at " + str(MQTT_CONFIG['port']))
  client.connect(MQTT_CONFIG['host'], MQTT_CONFIG['port'], 60)

  def on_connect(client, userdata, flags, rc):
    logger.info("Subscribing to topic: " + RF_CONFIG['topic'])
    client.subscribe(RF_CONFIG['topic'])

  def on_message(client, userdata, msg):
    if msg.topic == RF_CONFIG['topic']:
      rfdevice.tx_code(int(msg.payload), RF_CONFIG['protocol'], RF_CONFIG['pulselength'])
    logger.info("Got message")
    logger.info(msg.payload)

  client.on_connect = on_connect
  client.on_message = on_message

  logger.info("Starting mqtt loop...")
  client.loop_start()
  return client

def main():
  logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
  )

  import configargparse
  parser = configargparse.ArgParser(
    default_config_files=CONFIG_FILES,
    description="Status LED daemon"
  )
  parser.add_argument('-G', '--gpio-pin', default=25, type=int,
            help='GPIO pin for the LED (default: 25)')
  args = parser.parse_args()

  led = None

  state_map = {
    "starting": aiy.voicehat.LED.PULSE_QUICK,
    "ready": aiy.voicehat.LED.BEACON_DARK,
    "listening": aiy.voicehat.LED.ON,
    "thinking": aiy.voicehat.LED.PULSE_QUICK,
    "stopping": aiy.voicehat.LED.PULSE_QUICK,
    "power-off": aiy.voicehat.LED.OFF,
    "error": aiy.voicehat.LED.BLINK_3,
  }
  try:
    GPIO.setmode(GPIO.BCM)
    rfdevice = RFDevice(RF_CONFIG['gpio'])
    rfdevice.enable_tx()

    led = aiy.voicehat.get_led()
    client = prepare_client(rfdevice)
    logger.info("Default state sending: " + MQTT_CONFIG['topic'])
    client.publish(MQTT_CONFIG['topic'], 'ready', 2)

    while True:
      try:
        state = input()
        if not state:
          continue
        if state not in state_map:
          logger.warning("unsupported state: %s, must be one of: %s",
                   state, ",".join(state_map.keys()))
          continue
        logger.info("Pushing: " + state + " to topic " + MQTT_CONFIG['topic'])
        client.publish(MQTT_CONFIG['topic'], str(state), 2)
        logger.info("Pushed: " + state + " to topic " + MQTT_CONFIG['topic'])
        led.set_state(state_map[state])
      except EOFError:
        logger.info("Waiting...")
        time.sleep(1)
  except KeyboardInterrupt:
    pass
  finally:
    led.stop()
    rfdevice.cleanup()
    GPIO.cleanup()


if __name__ == '__main__':
  main()
