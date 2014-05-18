# -*- coding: utf-8 -*-

import sys
import codecs
import pandas
import csv
from fuzzywuzzy import process
import argparse

def allocateChores(history, unfairRatio, slaves):
    pass;
    # try to balance the variety of tasks between weeks
    # try to balance the distribution of tasks this week and overall
    # to do: handle some kind of start date so that there isn't a bias for overloading new slaves

def sendChores(chores, master):
    pass;

""" Get slaves from a csv file """
def gatherSlaves(csvFilename):
    try:
        rawFile = codecs.open(csvFilename, encoding='utf-8', mode='r');
    except IOError:
        print("Failed to open {0}".format(csvFilename));
        return None
    else:
        hasHeaders = csv.Sniffer().has_header(rawFile.readline());
        assert(hasHeaders == True);
        rawFile.seek(0);
        df = pandas.read_csv(rawFile);
        rawFile.close();
        headers = df.columns;
        assert(headers is not None and len(headers) >= 3);

        nameCol, nameScore = process.extractOne("Name", headers);
        assert(nameScore >= 70); # assert that there's a column for the slaves' names
        nameCol = headers.index(nameCol);
        emailCol, emailScore = process.extractOne("Email", headers);
        assert(emailScore >= 70); # assert that slaves have email addresses
        emailCol = headers.index(emailCol);
        groupCol, groupScore = process.extractOne("Group", headers);
        groupCol = headers.index(groupCol);
        if(groupScore < 70):
            # no groups
            print("Out of design scope");
            return None;
        else:
            slaves = {}; # assert that slaves have unique email addresses
            for row in df:
                assert(row[emailCol] not in slaves);
                slaves[row[emailCol]] = {'name':row[nameCol], 'group':row[groupCol]};
            return slaves;

""" Get the master from a JSON file """
def gatherMaster(masterFilename):
    pass;

""" Read a log file (CSV format) that records the labours of the slaves """
def readHistory(historyFile):
    try:
        rawFile = codecs.open(csvFilename, encoding='utf-8', mode='r');
    except IOError:
        print("Failed to open {0}".format(csvFilename));
        return None; # no history
    
        # this program writes history, so we can assume history is consistent
        # with how we would want it written
        # date, email, group, task
        # doing tasks for one group doesn't curry favour with other groups
        df = pandas.read_csv(rawFile);
        rawFile.close();
        headers = df.columns;
        assert(headers is not None and len(headers) >= 4);

        dateCol, dateScore = process.extractOne("Date",headers);
        assert(dateScore >= 75); # dates are not actually needed in current design anyway
        emailCol, emailScore = process.extractOne("Email",headers);
        assert(emailScore >= 70);
        groupCol, groupScore = process.extractOne("Group", headers);
        assert(groupScore >= 70);
        choreCol, choreScore = process.extractOne("Chore", headers);


""" Connect to Google and pull all contacts from a group """
def pullSlaves(master, groupName):
    print("To do");

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="I shall allocate tasks to slaves "\
        " reasonably fairly.");
    parser.add_argument("--past", help="CSV file that records the history "\
        "of allocation.", type=str);
    parser.add_argument("--slaves", help="CSV file that records names, groups and email addresses"\
        " of the slaves.", type=str);
    parser.add_argument("--master", help="JSON file with settings for the master. This is used as "\
        "the sender's email address etc.", type=str);
    parser.add_argument("--unfair", help="Max ratio of one person's work to average",
        type=float, default=3, required=False);

    args = parser.parse_args();
    history = readHistory(args.past);
    slaves = gatherSlaves(args.slaves);
    chores = allocateChores(history, args.unfair, slaves);
    master = gatherMaster(args.master);
    sendChores(chores, master);