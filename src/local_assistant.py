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

  def process(self, text, say):
    logger.info("Processing text")
    text_input = dialogflow.types.TextInput(text=text, language_code=self.language)
    query_input = dialogflow.types.QueryInput(text=text_input)
    response = self.client.detect_intent(session=self.session, query_input=query_input)
    logger.info("Got a action: " + response.query_result.action)
    logger.info("Responding with: " + response.query_result.fulfillment_text)
    say(response.query_result.fulfillment_text)
    return True


if __name__ == '__main__':
  def say(text):
    print(text)

  local_assistant = LocalAssistant('~/dialogflow.json', "just-sunrise-677", 'en-us')
  local_assistant.process("Where are everybody", say)
  local_assistant.process("Where are current conditions mr. dont ask questions", say)
  local_assistant.process("Bla bla bla", say)

