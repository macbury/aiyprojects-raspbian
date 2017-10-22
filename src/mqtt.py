"""Push led status to mqtt topic"""

import logging
import os
import time
import paho.mqtt.client as mqtt
from ruamel.yaml import YAML

logger = logging.getLogger('led-mqtt')

CONFIG_DIR = os.getenv('XDG_CONFIG_HOME') or os.path.expanduser('~/.config')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'mqtt.yaml')

def main():
  logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
  )

  logger.info("Loading config: " + CONFIG_FILE)
  config = YAML(typ='safe').load(open(CONFIG_FILE))
  client = mqtt.Client()
  client.enable_logger(logger)
  client.username_pw_set(config['username'], config['password'])
  logger.info("Connecting to: " + config['host'] + " at " + str(config['port']))
  client.connect(config['host'], config['port'], 60)
  client.loop_start()
  logger.info("Starting loop...")

  client.publish(config['topic'], 'ready')
  
  try:
    while True:
      try:
        state = input()
        logger.info("Pusing: " + state + " to topic " + config['topic'])
        client.publish(config['topic'], str(state))
      except EOFError:
        time.sleep(0.1)
  except KeyboardInterrupt:
    pass
  finally:
    logger.info("Ending this now")


if __name__ == '__main__':
  main()

