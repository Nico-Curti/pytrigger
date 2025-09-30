#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import requests
import platform
import threading

__author__  = ['Nico Curti']
__email__ = ['nico.curti2@unibo.it']

__all__ = [
  'buffered_request',

  'RESET_COLOR_CODE',
  'GREEN_COLOR_CODE',
  'ORANGE_COLOR_CODE',
  'VIOLET_COLOR_CODE',
  'RED_COLOR_CODE',
  'CRLF',
]

# code colors
RESET_COLOR_CODE  = '\033[0m'
GREEN_COLOR_CODE  = '\033[38;5;40m'
ORANGE_COLOR_CODE = '\033[38;5;208m'
VIOLET_COLOR_CODE = '\033[38;5;141m'
RED_COLOR_CODE    = '\033[38;5;196m'
VIOLET_COLOR_CODE = '\033[38;5;141m'
CRLF              = '\r\x1B[K' if platform.system() != 'Windows' else '\r\x1b[2K'

def _spinner (msg: str, stop_event: threading.Event):
  '''
  Disply a rotating spinner

  Parameters
  ----------
  msg: str
    Initial message to display before the spinner

  stop_event: threading.Event
    Stop criteria of the infinite loop
  '''
  symbols = '|/-\\'
  idx = 0
  while not stop_event.is_set():
    sys.stdout.write(f'\r{msg} {symbols[idx % len(symbols)]}')
    sys.stdout.flush()
    idx += 1
    time.sleep(0.1)
  sys.stdout.write('\r' + ' ' * (len(msg) + 2) + '\r') # clean the line

def buffered_request (url: str, **kwargs):
  '''
  Pretty layout for a GET request

  Parameters
  ----------
  url: str
    Url for the request

  kwargs: dict
    Parameters to pass to the request

  Returns
  -------
  res: requests
    Response of the requests
  '''
  stop_event = threading.Event()
  t = threading.Thread(target=_spinner, args=('Analyzing...', stop_event))
  t.start()

  try:
    resp = requests.get(url, **kwargs) # send the request
  finally:
    stop_event.set()
    t.join()

  return resp
