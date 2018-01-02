"""Signal states on a LED and MQTT broker"""

import logging
import os
import time
import json
import aiy.voicehat
import RPi.GPIO as GPIO

from rf_manager import RFController
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

rf_controller = RFController(MQTT_CONFIG['rf_switch'])

def prepare_client():
  client = mqtt.Client()
  
  client.enable_logger(logger)
  client.username_pw_set(MQTT_CONFIG['username'], MQTT_CONFIG['password'])

  def on_connect(client, userdata, flags, rc):
    rf_controller.setup(client)

  def on_message(client, userdata, msg):
    rf_controller.handle_message(msg)

  client.on_connect = on_connect
  client.on_message = on_message

  logger.info("Connecting to: " + MQTT_CONFIG['host'] + " at " + str(MQTT_CONFIG['port']))
  client.connect(MQTT_CONFIG['host'], MQTT_CONFIG['port'], 60)
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

    led = aiy.voicehat.get_led()
    client = prepare_client()
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
        rf_controller.update(led)
        time.sleep(0.1)
  except KeyboardInterrupt:
    pass
  finally:
    led.stop()
    rfdevice.cleanup()
    GPIO.cleanup()


if __name__ == '__main__':
  main()
