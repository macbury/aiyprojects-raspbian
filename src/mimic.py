import subprocess
import os
import tempfile
import hashlib
import logging
import functools

logger = logging.getLogger('mimic')

SAY_CACHE = '/tmp/say_cache/'
TTS_DIR = '/tmp'

def create_say(player):
  return functools.partial(say, player)

def say(player, words, lang='en-US', voice='ap'):
  """Say the given words with TTS.
  Args:
    player: To play the text-to-speech audio.
    words: string to say aloud.
    lang: language for the text-to-speech engine.
  """

  if not os.path.exists(SAY_CACHE):
    os.makedirs(SAY_CACHE)

  digest = hashlib.md5()
  digest.update((words+lang+voice).encode('utf-8'))
  tts_wav = SAY_CACHE + digest.hexdigest() + '.wav'

  if not os.path.exists(tts_wav):
    try:
      (fd, tts_text) = tempfile.mkstemp(suffix='.txt', dir=TTS_DIR)
    except IOError:
      logger.exception('Using fallback directory for TTS output')
      (fd, tts_text) = tempfile.mkstemp(suffix='.txt')
    os.close(fd)

    file = open(tts_text, 'w')
    file.write(words)
    file.close()
    
    try:
      logger.info("Caching response to: " + tts_wav)
      subprocess.call(['mimic', '-voice', voice, '-f', tts_text, '-o', tts_wav])
    finally:
      os.unlink(tts_text)
  
  logger.info("Play from cache: " + tts_wav)
  player.play_wav(tts_wav)

if __name__ == '__main__':
  import aiy.audio
  player = aiy.audio.get_player()
  say(None, "My name is butler jenkins")