import subprocess
import os
import tempfile
import hashlib
import logging
import functools
import boto3
  
logger = logging.getLogger('polly')

SAY_CACHE = os.path.expanduser('~/.cache/say/')
TTS_DIR = '/tmp'

def create_say(player):
  return functools.partial(say, player)

def say(player, words, voice="Matthew"):
  """Say the given words with TTS.
  Args:
    player: To play the text-to-speech audio.
    words: string to say aloud.
    lang: language for the text-to-speech engine.
  """

  if not os.path.exists(SAY_CACHE):
    os.makedirs(SAY_CACHE)

  digest = hashlib.md5()
  digest.update((words+voice).encode('utf-8'))
  tts_ogg = SAY_CACHE + digest.hexdigest() + '.ogg'

  if not os.path.exists(tts_ogg):
    client = boto3.client('polly')
    
    logger.info("Caching: " + tts_ogg)
    resp = client.synthesize_speech(Text=words, OutputFormat="ogg_vorbis", VoiceId=voice)
    file = open(tts_ogg, 'wb')
    file.write(resp.get('AudioStream').read())
    file.close()

  logger.info("Play from cache: " + tts_ogg)
  player.play_ogg(tts_ogg)

if __name__ == '__main__':
  import aiy.audio
  player = aiy.audio.get_player()
  say(None, "My name is butler jenkins")


  
  
  