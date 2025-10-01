#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import sys
import json
import argparse
from time import time as now
from trigger import TriggerDB
from trigger import __version__
from trigger.utils import RESET_COLOR_CODE
from trigger.utils import ORANGE_COLOR_CODE
from trigger.utils import GREEN_COLOR_CODE
from trigger.utils import VIOLET_COLOR_CODE
from trigger.utils import RED_COLOR_CODE

__author__ = ['Nico Curti']
__email__ = ['nico.curti2@unibo.it']

def parse_args():
  '''
  Parse command line arguments for the pyTrigger package.
  This function sets up the argument parser, defines the expected arguments,
  and returns the parsed arguments.

  Returns
  -------
  argparse.Namespace
    The parsed command line arguments as a Namespace object.

  Raises
  -------
  argparse.ArgumentError
    If there is an error in the argument parsing, such as a missing required
    argument or an invalid value.
  '''
  # global sofware information
  parser = argparse.ArgumentParser(
    prog='trigger',
    argument_default=None,
    add_help=True,
    prefix_chars='-',
    allow_abbrev=True,
    exit_on_error=True,
    description='Python package for the TRIGGER EU Project analysis.',
  )

  # trigger --table <name>
  parser.add_argument(
    '--table', '-t',
    dest='table',
    type=str,
    action='store',
    required=True,
    help=(
      'Name of the table to use for the query'
    ),
  )

  # trigger --select <columns>
  parser.add_argument(
    '--select', '-s',
    dest='select',
    type=str,
    nargs='+',
    action='store',
    required=False,
    default='*',
    help=(
      'List of column names to select in the query'
    ),
  )

  # trigger --where <condition>
  parser.add_argument(
    '--where', '-w',
    dest='where',
    type=str,
    nargs='+',
    action='store',
    required=False,
    default=None,
    help=(
      'List of condition to apply in the filtering'
    ),
  )

  # trigger --orderby <name>
  parser.add_argument(
    '--orderby', '-b',
    dest='orderby',
    type=str,
    action='store',
    required=False,
    default=None,
    help=(
      'Name of the column to use for the ordering of the results'
    ),
  )

  # trigger --order <ASC|DESC>
  parser.add_argument(
    '--order', '-o',
    dest='order',
    type=str,
    action='store',
    required=False,
    default='ASC',
    choices=[
      'ASC',
      'DESC',
    ],
    help=(
      'Order of the result'
    )
  )

  # trigger --limit <n>
  parser.add_argument(
    '--limit', '-l',
    dest='limit',
    type=int,
    action='store',
    required=False,
    default=None,
    help=(
      'Maximum number of records to retrieve from the request'
    ),
  )

  # trigger --version
  parser.add_argument(
    '--version', '-v',
    dest='version',
    required=False,
    action='store_true',
    default=False,
    help='Get the current version installed',
  )

  return parser

def main ():
  # extract the arguments of the cmd
  parser = parse_args()
  args = parser.parse_args()

  # source: https://patorjk.com/software/taag
  print(fr'''{VIOLET_COLOR_CODE}
           _______   _
          |__   __| (_)
  _ __  _   _| |_ __ _  __ _  __ _  ___ _ __
 | '_ \| | | | | '__| |/ _` |/ _` |/ _ \ '__|
 | |_) | |_| | | |  | | (_| | (_| |  __/ |
 | .__/ \__, |_|_|  |_|\__, |\__, |\___|_|
 | |     __/ |          __/ | __/ |
 |_|    |___/          |___/ |___/
    {RESET_COLOR_CODE}''',
    file=sys.stdout, flush=True
  )

  # start the timer
  tic = now()

  if args.version:
    print(__version__, file=sys.stdout, flush=True)
    exit(0)

  # math operators for the where condition
  operators = re.compile(r"^([a-zA-Z_]\w*)(.*)$")

  # get the parameters of the desired query
  table = args.table
  select = args.select
  where = {
    match.group(1): match.group(2)
    for cond in args.where
    if (match := operators.match(cond))
  } if args.where else None
  orderby = args.orderby
  order = args.order
  limit = args.limit

  # run the query on the database instance
  with TriggerDB() as db:
    res = (
      db.from_(table)
        .select(*select)
        .where(**where)
        .order_by(orderby)
        .order(order)
        .limit(limit)
        .fetch()
    )
    print(
      json.dumps(
        res, 
        indent=2, 
        sort_keys=True,
      ),
      file=sys.stdout,
      flush=True,
    )
  
  # log the time taken to compute the statistics
  toc = now()
  print(
    f'{GREEN_COLOR_CODE}[INFO]{RESET_COLOR_CODE} Elapsed time: {toc - tic:.2f} sec',
    file=sys.stdout, flush=True
  )


if __name__ == '__main__':
  main()
