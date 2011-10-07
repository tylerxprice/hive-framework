import os
os.environ["DJANGO_SETTINGS_MODULE"] = "hive.website.settings"

import argparse
import logging
import sys
from website.tournaments.models import *

logging.basicConfig(level=logging.DEBUG)


class Scheduler(object):
  def __init__(self, args):
    self.args = self.parse_args(args) 

  def parse_args(self, args):
    parser = argparse.ArgumentParser(prog='scheduler', argument_default='')
    parser.add_argument(args[0], default='') 
    args = parser.parse_args(args)
    args = vars(args)
    return args

  def run(self):
    logging.debug(Tournament.objects.all())

if __name__ == "__main__": 
  Scheduler(sys.argv).run()

