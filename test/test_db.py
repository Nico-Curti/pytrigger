#!/usr/bin/python3
# -*- coding: utf-8 -*-

from trigger import TriggerDB

__author__  = ['Nico Curti']
__email__ = ['nico.curti2@unibo.it']

class TestQuery:
  '''
  Test the possible combination of queries and
  expected results
  '''

  def test_accounts (self):
    '''
    Test the validity of the list of accounts
    '''
    with TriggerDB() as db:
      res = db.accounts()

    assert isinstance(res, list)
    