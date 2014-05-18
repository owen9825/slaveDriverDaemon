# -*- coding: utf-8 -*-

import sys
import codecs
import pandas
import csv

def allocateChores(history, slaves):
    pass;

def sendChores(chores, master):
    pass;

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="I shall allocate tasks to slaves "\
        " reasonably fairly.");
    parser.addArgument("--past", help="CSV file that records the history "\
        "of allocation.", type=str);
    parser.addArgument("--slaves", help="CSV file that records names, groups and email addresses"\
        " of the slaves.", type=str);
    parser.addArgument("--master", help="JSON file with settings for the master. This is used as "\
        "the sender's email address etc.", type=str);