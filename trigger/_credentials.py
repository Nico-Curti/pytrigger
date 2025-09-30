#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import getpass
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

from .utils import RESET_COLOR_CODE
from .utils import ORANGE_COLOR_CODE
from .utils import GREEN_COLOR_CODE
from .utils import RED_COLOR_CODE

__author__  = ['Nico Curti']
__email__ = ['nico.curti2@unibo.it']

__all__ = [
  'ensure_credentials_on_first_use',
]

# Configuration of directories
APP_NAME = 'pytrigger'
CONFIG_DIR = Path.home() / '.config' / APP_NAME
CONFIG_FILE = CONFIG_DIR / 'credentials.json'
KEY_FILE = CONFIG_DIR / 'secret.key'

# internal cache to avoid re-readings
_credentials_cache = None

def _ensure_config_dir ():
  '''
  Ensure the existance of configuration directories
  '''
  if not CONFIG_DIR.exists():
    CONFIG_DIR.mkdir(
      parents=True,
      exist_ok=True
    )
    # set the privileges
    try:
      CONFIG_DIR.chmod(0o700)
    except Exception:
      pass

def _generate_key () -> bytes:
  '''
  Create or read the encription keys

  Returns
  -------
    key: bytes
      Private key for the encryption
  '''
  # create the directories
  _ensure_config_dir()
  # if there are no files
  if not KEY_FILE.exists():
    # create the private key
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    # set the privileges
    try:
      KEY_FILE.chmod(0o600)
    except Exception:
      pass
    return key
  # get the key as bytes
  return KEY_FILE.read_bytes()

def _store_credentials (email: str, password: str):
  '''
  Save credentials in configuration file

  Parameters
  ----------
    email: str
      Username of the account as email address

    password: str
      Password of the account
  '''
  # (eventually) generate the key
  key = _generate_key()
  # encripter
  f = Fernet(key)
  token = f.encrypt(password.encode('utf-8'))
  # encript the password
  data = {
    'email': email,
    'password_token': token.decode('utf-8')
  }
  # dump the encripted credentials
  with open(CONFIG_FILE, 'w', encoding='utf-8') as fjson:
    json.dump(
      data,
      fjson,
      indent=2
    )
  print(f'{GREEN_COLOR_CODE}[INFO]{RESET_COLOR_CODE} Credentials stored successfully')
  # set the privileges
  try:
    CONFIG_FILE.chmod(0o600)
  except Exception:
    pass

def _load_credentials () -> dict:
  '''
  Load the credentials from file if exists

  Returns
  -------
    credentials: dict
      Dictionary of email and password of the account
      If something goes wrong, the resulting dict is
      set to None
  '''
  # try to load the file
  if not CONFIG_FILE.exists() or not KEY_FILE.exists():
    return None
  try:
    # read the file content
    data = json.loads(
      CONFIG_FILE.read_text(
        encoding='utf-8'
      )
    )
    # generate the key
    key = _generate_key()
    # decrypter
    f = Fernet(key)
    password = f.decrypt(
      data['password_token'].encode('utf-8')
    ).decode('utf-8')
    # log the status
    print(f'{GREEN_COLOR_CODE}[INFO]{RESET_COLOR_CODE} Credentials loaded successfully')
    # get it back
    return {
      'email': data['email'],
      'password': password
    }
  # if something goes wrong...
  except (InvalidToken, Exception):
    print(f'{RED_COLOR_CODE}[ERROR]{RESET_COLOR_CODE} Failed to load credentials')
    return None

def _prompt_and_store () -> dict:
  '''
  Ask the credentials and save them in a secure file

  Returns
  -------
    credentials: dict
      Dictionary of email and password of the account
  '''
  print(f'{ORANGE_COLOR_CODE}[WARN]{RESET_COLOR_CODE} Credentials not found')
  email = input('Email: ').strip()
  password = getpass.getpass('Password: ')
  # store the credentials
  _store_credentials(email, password)
  # return them
  return {
    'email': email,
    'password': password
  }

def ensure_credentials_on_first_use () -> dict:
  '''
  Load the credentials if already stored OR
  ask them to store for future uses

  Returns
  -------
    credentials: dict
      Dictionary of email and password of the account
  '''
  creds = _load_credentials()
  # if it is different from None
  if creds:
    return creds
  # otherwise ask to the user and store them
  # for the future
  return _prompt_and_store()

def get_db_credentials () -> dict:
  '''
  Get the database credentials (stored or asked)

  Returns
  -------
    credentials: dict
      Dictionary of email and password of the account
  '''
  global _credentials_cache
  if _credentials_cache is None:
    _credentials_cache = ensure_credentials_on_first_use()
  return dict(_credentials_cache)

def reset_credentials ():
  '''
  Delete the configuration file with the credentials
  to allow a complete reset of the account.
  '''
  global _credentials_cache
  _credentials_cache = None
  if CONFIG_FILE.exists():
    CONFIG_FILE.unlink()
  if KEY_FILE.exists():
    KEY_FILE.unlink()
  print(f'{ORANGE_COLOR_CODE}[INFO]{RESET_COLOR_CODE} Credentials deleted successfully')
