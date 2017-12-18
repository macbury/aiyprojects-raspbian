import dialogflow
import logging
import os
import uuid
import google.auth
from google.oauth2 import service_account

logger = logging.getLogger('local_assistant')

class LocalAssistant:
  def __init__(self, credentials_path, project_id, language="en-us"):
    self.language = language
    credentials = service_account.Credentials.from_service_account_file(os.path.expanduser("~/dialogflow.json"))
    credentials = credentials.with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
    self.client = dialogflow.SessionsClient(credentials=credentials)
    self.session = self.client.session_path(project_id, uuid.uuid1())
    logger.info("Initialized!")

  def process(self, text, say,retry_left=3):
    try:
      logger.info("Processing text: " + text)
      if len(text) == 0:
        return False
      text_input = dialogflow.types.TextInput(text=text, language_code=self.language)
      query_input = dialogflow.types.QueryInput(text=text_input)
      response = self.client.detect_intent(session=self.session, query_input=query_input)
      logger.info("Got a action: " + response.query_result.action)
      logger.info("Responding with: " + response.query_result.fulfillment_text)
      if len(response.query_result.fulfillment_text) > 0:
        logger.info("Responding with: " + response.query_result.fulfillment_text)
        say(response.query_result.fulfillment_text)
        return True
      else:
        logger.info("Empty response from HomeAssistant!")
        return False
    except Exception as e:
      if retry_left > 0:
        return self.process(text, say, retry_left-1)
      else:
        logger.error(e)
        say(str(e))
        return False


if __name__ == '__main__':
  def say(text):
    print(text)

  local_assistant = LocalAssistant('~/dialogflow.json', "butlerjenkins-2400c", 'en-us')
  local_assistant.process("Where are everybody", say)
  local_assistant.process("Where are current conditions mr. dont ask questions", say)
  local_assistant.process("Bla bla bla", say)

