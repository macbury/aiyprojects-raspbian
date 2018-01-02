import telepot
import logging
from telepot.loop import MessageLoop

logger = logging.getLogger('telegram_bot')

class TelegramBot:
  def __init__(self, local_assistant, token, usernames):
    self.local_assistant = local_assistant
    self.usernames = usernames
    self.bot = telepot.Bot(token)
    MessageLoop(self.bot, self.handle).run_as_thread()

  def handle(self, msg):
    username = msg['from']['username']
    chat_id = msg['chat']['id']
    command = msg['text']

    if username not in self.usernames:
      logger.error("Ignoring {} from {}".format(command, username))
      return

    logger.info('Got command {} from {}'.format(command, username))

    def respond(msg):
      self.bot.sendMessage(chat_id, msg)

    if not self.local_assistant.process(command, respond):
      self.bot.sendMessage(chat_id, "I dont understand this...")
  

if __name__ == '__main__':
  while 1:
    time.sleep(10)

