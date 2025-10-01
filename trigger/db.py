#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import requests
from typing import List
from typing import Dict
from typing import Union
from typing import Optional

from .utils import RESET_COLOR_CODE
from .utils import ORANGE_COLOR_CODE
from .utils import GREEN_COLOR_CODE
from .utils import RED_COLOR_CODE
from .utils import buffered_request

from ._credentials import ensure_credentials_on_first_use

__author__  = ['Nico Curti']
__email__ = ['nico.curti2@unibo.it']

__all__ = [
  'TriggerDB',
]

# main parameter of the server
SERVER_PORT=8083
SERVER_HOST='https://trigger-io.difa.unibo.it/api'

class TriggerDB (object):
  '''
  Interface for Trigger Server APIs

  Examples
  --------    
  Example of standard mode connection and query::

    from trigger import TriggerDB

    with TriggerDB() as db:
      res = db.select(
        table='myair',
        columns=['year', 'month'],
        where={
          'year': '=2025', 
          'month': '=9', 
          'day': '=10', 
          'hour': '>=0', 
          'email': '=DE000086'
        },
        order_by='month',
        order='ASC'
      )

  Example of chaining mode connection and query::

    from trigger import TriggerDB

    with TriggerDB() as db:
      res = (
        db.from_('myair')
          .select('year', 'month')
          .where(year='=2025', month='=9', day='=10', hour='>=0', email='=DE000086')
          .order_by('month')
          .asc()
          .fetch()
      )
  '''

  _available_tables = {
    'myair': ['email', 'userId', 'year','month','day','hour','minute','second','pm1','pm25','pm10','pc03','pc05','pc1','pc25','pc5','pc10','temperature','humidity','pressure','sound','uvb','light'],
    'ecg': ['email', 'userId', 'year','month','day','hour','minute','second','microsecond','ecg'],
    'ppg': ['email', 'userId', 'year','month','day','hour','minute','second','microsecond','ppg'],
    'gsp': ['email', 'userId', 'year', 'month', 'day', 'hour', 'minute', 'second', 'longitude', 'latitude', 'accuracy'],
    'sleep': ['email', 'userId', 'year', 'month', 'day', 'hour', 'minute', 'second', 'sleepduration', 'awake', 'insomnia', 'remsleep', 'lightsleep', 'deepsleep', 'sleepquality'],
    'smartwatchlow': ['email', 'userId', 'year', 'month', 'day', 'hour', 'minute', 'second', 'step', 'cal', 'bphigh', 'bplow', 'bodytemp'],
    'smartwatchhigh': ['email', 'userId', 'year', 'month', 'day', 'hour', 'minute', 'second', 'heartrate', 'sleeprate', 'oxygens'],
    'accounts': ['id', 'email', 'created_at', 'last_login'],
  }

  _valid_functions = {'AVG', 'SUM', 'COUNT', 'MIN', 'MAX'}

  def __init__ (self):

    # Running these lines at the import the script will
    # load or ask the credentials for the account
    try:
      credentials = ensure_credentials_on_first_use()
    except Exception as e:
      print(f'{RED_COLOR_CODE}[ERROR]{RESET_COLOR_CODE} Invalid credentials found')
      print(e)
      raise ValueError('Missing credential infos')

    # set the url of the API
    api_url = f'{SERVER_HOST}/auth'
    # set the user information for the login
    data = {
      'email' : credentials['email'],
      'password' : credentials['password'],
    }

    # send the login request
    res = requests.post(api_url, data=data)

    # check the status of the response
    if res.status_code != 200:
      print(f'{RED_COLOR_CODE}[ERROR]{RESET_COLOR_CODE} Invalid credentials found')
      raise ValueError('Authentication failed')

    # store the token
    self._token = res.text
    self._logged_out = False

  def _logout (self):
    '''
    Perform the safety logout when the object is destructed
    '''
    if self._logged_out:
      return  # already done

    api_url = f'{SERVER_HOST}/logout'
    res = requests.post(
      api_url,
      data={"token": self._token}
    )

    if res.status_code != 200:
      print(f'{ORANGE_COLOR_CODE}[WARN]{RESET_COLOR_CODE} Logout failed: {res.status_code} {res.text}')
    else:
      print(f'{GREEN_COLOR_CODE}[INFO]{RESET_COLOR_CODE} Logout success')

    self._logged_out = True

  def __del__ (self):
    '''
    Object destructor leads to logout of the account
    '''
    try:
      self._logout()
    except Exception as e:
      print(f'{ORANGE_COLOR_CODE}[WARN]{RESET_COLOR_CODE} Exception in database deletion: {e}')

  def __enter__ (self):
    return self

  def __exit__ (self, exc_type, exc_value, traceback):
    self._logout()
    return False  # suppress exception failed

  def _check_table (self, table: str) -> bool:
    '''
    Check the validity of the required table

    Parameters
    ----------
    table: str
      Name of the table to check

    Returns
    -------
    check: bool
      True if the table is valid
      An exception is raised if something is incorrect
    '''
    if table not in self._available_tables:
      raise ValueError((
        f"Table '{table}' not found in the database. "
        f'Available tables are: {list(self._available_tables.keys())}'
      ))
    return True

  def _is_valid_column_or_agg (self, table: str, column: str) -> bool:
    '''
    Check if the given column is available in the given
    table in the normal or aggregated form.

    Parameters
    ----------
    table: str
      Name of the table to use

    column: str
      Name of the column to check

    Returns
    -------
    check: bool
      True if the column is valid
    '''
    col = column.strip()

    # COUNT(*)
    if col.upper() == 'COUNT(*)':
      return True

    # Match like FUNC(column)
    match = re.match(r"^([A-Z]+)\((\w+)\)$", col, re.IGNORECASE)

    if match:
      func, inner_col = match.group(1).upper(), match.group(2)
      return func in self._valid_functions and inner_col in self._available_tables[table]

    # Normal column
    return col in self._available_tables[table]

  def _check_column (self, table: str, column: str) -> bool:
    '''
    Check the validity of the column/function for the given table

    Parameters
    ----------
    table: str
      Name of the table to use

    column: str
      Name of the column to check

    Returns
    -------
    check: bool
      True if the column is valid
      An exception is raised if something is incorrect
    '''
    if not self._is_valid_column_or_agg(table=table, column=column):
      raise ValueError((
        f"Column '{column}' not found in the table '{table}'. "
        f'Available columns are: {self._available_tables[table]}'
      ))
    return True

  def tables (self) -> list:
    '''
    Get the list of available tables

    Returns
    -------
      tables: list
        List of table names in the database
    '''
    return list(self._available_tables.keys())

  def columns (self, table: str) -> list:
    '''
    Get the list of available columns in the current table

    Parameters
    ----------
    table: str
      Table name to evaluate

    Returns
    -------
      columns: list
        Available column names in the desired table
    '''
    self._check_table(table)
    return self._available_tables[table]

  def accounts (self) -> list:
    '''
    Get the list of available accounts

    Returns
    -------
    accounts: list
      List of account names registered
    '''
    return self.select(
      table='accounts',
      columns=['email'],
      where=None,
      order_by=None,
      order='ASC',
      limit=100000,
    )
  
  def num_elements (self, table: str) -> int:
    '''
    Get the number of elements in the given
    table

    Parameters
    ----------
    table: str
      Table name to evaluate

    Returns
    -------
    num: int
      Number of elements in the table
    '''
    return int(self.select(
      table=table,
      columns=['COUNT(email)'],
    )[0]['COUNT(email)'])

  def select (
    self,
    table: str,
    columns: Union[List[str], str] = '*',
    where: Dict[str, Union[str, int, float]] = None,
    order_by: str = None,
    order: str = 'ASC',
    limit: int = 100,
  ) -> dict:
    '''
    Select interface for the GET query of the available tables

    Parameters
    ----------
    table: str
      Name of the table on which extract the data

    columns: str
      Name of columns to select from the table

    where: dict
      Condition to apply on the columns

    order_by: str
      Ordering column name

    order: str
      Ascending or descending order

    limit: int
      Maximum number of records to retrieve

    Returns
    -------
    res: dict
      Resulting filtered dataset
    '''
    # check the table
    self._check_table(table)

    # check select columns
    selected = []
    if columns == '*':
      selected = self._available_tables[table]
    elif isinstance(columns, list):
      for col in columns:
        if not self._is_valid_column_or_agg(table=table, column=col):
          raise ValueError(f"Invalid column or aggregated function: '{col}' in table '{table}'")
        selected.append(col)
    else:
      raise ValueError('Columns parameter must be a string or a list of strings')

    # check order_by column
    if order_by:
      for col in order_by.split(','):
        self._check_column(table=table, column=col)

    # SELECT
    params = {
      'select': ','.join(selected)
    }

    # WHERE
    if where:
      conds = []
      for col, expr in where.items():
        self._check_column(table=table, column=col)
        conds.append(f'{col}{expr}')
      params['where'] = ','.join(conds)

    # ORDER
    if order_by:
      params['orderBy'] = order_by
      params['order'] = order.upper()

    # LIMIT
    params['limit'] = limit

    url = f'{SERVER_HOST}/{table}/'
    # send the buffered request
    resp = buffered_request(
      url=url,
      params=params,
      headers={'token': self._token}
    )

    if resp.status_code != 200:
      print(f'{RED_COLOR_CODE}[ERROR]{RESET_COLOR_CODE} Query error')
      raise Exception(f'Query Error: {resp.status_code} {resp.text}')

    return resp.json()
  
  def from_(self, table: str):
    '''
    Chaining interface for the query management

    Parameters
    ----------
    table: str
      Table name to use in the query

    Returns
    -------
    builder: QueryBuilder
      Builder of the query for the chaining interface
    '''
    return QueryBuilder(self, table)

class QueryBuilder:
  '''
  Build the query in chaining mode to facilitate
  the readability of the code

  Parameters
  ----------
  db: TriggerDB
    Database instance to use for the request

  table: str
    Table name to use in the query
  '''

  def __init__ (self, db: TriggerDB, table: str):
    # check the table
    db._check_table(table)

    self.db = db
    self.table = table
    self._columns: List[str] = ['*']
    self._where: Dict[str, str] = {}
    self._order_by: Optional[str] = None
    self._order: str = 'ASC'
    self._limit: int = 100

  def select (self, *columns: str):
    '''
    Set the list of columns to use

    Parameters
    ----------
    columns: str
      List of columns as string names
    '''
    if columns:
      for col in columns:
        self.db._check_column(table=self.table, column=col)
      self._columns = list(columns)
    return self

  def where (self, **conditions: str):
    '''
    Set the conditions to apply in the filtering

    Parameters
    ----------
    **conditions: str
      Condition to apply as 'name=val' in the query
    '''
    for col, expr in conditions.items():
      self.db._check_column(table=self.table, column=col)
      self._where[col] = expr
    return self

  def order_by (self, column: str):
    '''
    Set the name of the column to use for the ordering of
    the results

    Parameters
    ----------
    column: str
      Column name to use for the ordering of the results
    '''
    for col in column.split(','):
      self.db._check_column(table=self.table, column=col)
    self._order_by = column
    return self

  def asc (self):
    '''
    Set the ascending ordering of the results
    '''
    self._order = 'ASC'
    return self

  def desc (self):
    '''
    Set the descending ordering of the results
    '''
    self._order = 'DESC'
    return self
  
  def order (self, val: str):
    '''
    Set the ordering of the results
    '''
    if not val in ['ASC', 'DESC']:
      raise ValueError('Invalid ordering')
    self._order = val
    return self
  
  def limit (self, val: int):
    '''
    Set the maximum number of records to retrieve
    '''
    self._limit = val
    return self

  def fetch (self) -> dict:
    '''
    Extract the results calling the request

    Returns
    -------
    res: dict
      Resulting response of the given request
    '''
    return self.db.select(
      table=self.table,
      columns=self._columns,
      where=self._where if self._where else None,
      order_by=self._order_by,
      order=self._order,
      limit=self._limit,
    )