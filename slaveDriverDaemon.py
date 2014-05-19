# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import codecs
import pandas
import csv
from fuzzywuzzy import process
import argparse
import randomapi # prove that the master didn't bias the choices.
import json
import numpy as np
import math

def allocateChores(history, chores, slaves):
    pass;
    # try to balance the variety of tasks between weeks, then also handle some kind of start date so that there isn't a bias for overloading new slaves
    # try to balance the distribution of tasks this week and overall
        
    # the Group column of chores can be All
    assert(u"U" not in slaves.columns); # to do: accomodate bias from previous weeks so eg slaves will floor() instead of ceil()
    # U as in potential energy
    slaves[u"U"] = 1;
    castes = slaves[u"Group"].unique();
    castePotentials = {}; # potential energy remaining in each caste
    everyoneChores = float(np.sum(chores[u"Group"] == u"All"));
    assert(u"Group" in chores.columns);
    assert(u"Chore" in chores.columns);
    assert(u"Chores" not in slaves); # to do: handle situation where some tasks have been pre-allocated
    slaves[u"Chores"] = "; "; # make it easy to strip later

    randomBlock = np.random.random_sample(size=len(chores));
    b = 0; # place in block

    slaves.set_index(u"Email", inplace=True); # allow this to be used as a key

    for caste in castes:
        assert(caste != u"All"); # reserved word
        castePopulation = float(np.sum(slaves[u"Group"] == caste));
        casteChores = float(len(chores.loc[chores[u"Group"] == caste]));
        casteEffort = int(math.ceil(casteChores / castePopulation + everyoneChores / float(len(slaves))));
        slaves.loc[slaves[u"Group"] == caste, u"U"] = casteEffort;
        print("Members of {0} caste shall exert average of {1} tasks: ({2}/{3}) + ({4}/{5})".format(
            caste, casteEffort, casteChores, castePopulation, everyoneChores, float(len(slaves))));

        castePotentials[caste] = castePopulation * casteEffort;
        # now assign chores for that caste. These slaves will still be eligible for everyoneChores later
        casteKeys = slaves.index[slaves[u"Group"] == caste]; # used for access
        for c in chores.index[chores[u"Group"] == caste]:
            straw = randomBlock[b] * castePotentials[caste];
            # iterate over caste members until the straw position
            cumulation = 0; # Python doesn't allow "Σ = 0;"
            for slaveKey in casteKeys:
                cumulation += slaves.ix[slaveKey, u"U"];
                if cumulation >= straw:
                    slaves.ix[slaveKey, u"U"] -= 1;
                    slaves.ix[slaveKey, u"Chores"] += chores.ix[c,u"Chore"] + "; ";
                    break;
            b += 1; # position in random block
            castePotentials[caste] -= 1;
    # now assign everyone tasks
    allPotential = np.sum(castePotentials.values());
    slaveKeys = slaves.index;
    for c in chores.index[chores[u"Group"] == u"All"]:
        straw = randomBlock[b] * allPotential;
        # iterate over caste members until the straw position
        cumulation = 0;
        for slaveKey in slaveKeys:
            cumulation += slaves.ix[slaveKey, u"U"];
            if cumulation >= straw:
                slaves.ix[slaveKey, u"U"] -= 1;
                slaves.ix[slaveKey, u"Chores"] += chores.ix[c,u"Chore"] + "; ";
                break;
        b += 1;
        allPotential -= 1;

    print("Slaves could've been pushed for another {0} tasks.".format(allPotential));

    # return to state
    slaves.reset_index(inplace=True);
    slaves.drop(u"U", inplace=True, axis=1);
    return slaves, randomBlock;

def sendChores(chores, master, randomBlock):
    # save to log file for this version of the program
    try:
        outFile = codecs.open("newChores.txt", encoding='utf-8', mode='w');
    except IOError:
        print("Failed to open {0} for writing".format("newChores.txt"));
    else:
        for c in chores.index:
            ownershipName = chores.ix[c,u"Name"];
            if(ownershipName[-1] == u"s"):
                ownershapName += "'";
            else:
                ownershipName += "'s";
            slaveChores = chores.ix[c,u"Chores"];
            slaveChores = slaveChores[2:-2]; # leading and trailing ;
            print("{0} chores for the week: {1}".format(ownershipName, slaveChores), file=outFile);
        print("The random values used were:", file=outFile);
        print(list(randomBlock), file=outFile);
        #outFile.write(";".join(list(randomBlock)));
        #outFile.write("\n");
        outFile.close();
    # to do: send the email


# to do: merge gatherSlaves and getChores into the same function with an input list
# of expected columns and unique columns
""" Get slaves from a csv file, return as df """
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
        headers = list(df.columns);
        assert(headers is not None and len(headers) >= 3);

        nameCol, nameScore = process.extractOne("Name", headers);
        assert(nameScore >= 70); # assert that there's a column for the slaves' names
        nameCol = headers.index(nameCol);
        assert(np.sum(headers == u"Name") <= 1);
        headers[nameCol] = "Name"; # apply our naming for ease of processing later
        emailCol, emailScore = process.extractOne("Email", headers);
        assert(emailScore >= 70); # assert that slaves have email addresses
        assert(np.sum(headers == u"Email") <= 1);
        emailCol = headers.index(emailCol);
        headers[emailCol] = "Email";
        groupCol, groupScore = process.extractOne("Group", headers);
        if(groupScore < 70):
            # no groups
            print("Out of design scope");
            return None;
        else:
            assert(np.sum(headers == u"Group") <= 1);
            groupCol = headers.index(groupCol);
            headers[groupCol] = "Group";
            df.columns = headers;
            assert(len(df[u"Email"].unique()) == len(df)); # assert emails are unique
            # to do: use email & name as combination key
            return df;

""" To do: get chores from eg a to do list on Google Docs """
def getChores(csvFilename):
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
        if headers is None:
            print("Out of design scope for the moment");
            return None;
        headers = list(headers);
        assert(len(headers) >= 2); # item and applicability

        choreCol, choreScore = process.extractOne("Chore", headers);
        assert(choreScore >= 70);
        assert(np.sum(headers == u"Chore") <= 1);
        choreCol = headers.index(choreCol);
        headers[choreCol] = "Chore";

        groupCol, groupScore = process.extractOne("Group", headers);
        if(groupScore < 70):
            # no groups
            print("Out of design scope");
            return None;
        else:
            assert(np.sum(headers == u"Group") <= 1);
            groupCol = headers.index(groupCol);
            headers[groupCol] = "Group";
            df.columns = headers;
            return df; 

""" Get the master from a JSON file """
def gatherMaster(masterFilename):
    try:
        rawFile = codecs.open(masterFilename, encoding='utf-8', mode='r');
    except IOError:
        print("Failed to open {0}".format(masterFilename));
        return None;
    else:
        masterSettings = json.load(rawFile,encoding='utf-8');
        rawFile.close;
        assert(type(masterSettings) == dict);
        assert(u"master password" in masterSettings);
        assert(u"randomApiKey" in masterSettings);
        assert(u"master email" in masterSettings);
        return masterSettings;

""" Read a log file (CSV format) that records the labours of the slaves """
def readHistory(historyFile=None):
    if historyFile is None:
        return None;
    try:
        rawFile = codecs.open(csvFilename, encoding='utf-8', mode='r');
    except IOError:
        print("Failed to open {0}".format(csvFilename));
        return None; # no history
    else:
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
    
    parser.add_argument("-past", help="CSV file that records the history "\
        "of allocation.", default=None, required=False, type=str);
    parser.add_argument("-slaves", help="CSV file that records names, groups and email addresses"\
        " of the slaves.", type=str, required=True);
    parser.add_argument("-master", help="JSON file with settings for the master. This is used as "\
        "the sender's email address etc.", type=str, required=True);
    parser.add_argument("-chores", help="CSV file with list of chores and group "\
        "applicability", type=str, required=True);
    parser.add_argument("-v","--verbose", help="Print more comments", action='store_true',
        required=False);

    args = parser.parse_args();
    history = readHistory(args.past);
    slaves = gatherSlaves(args.slaves);
    if(args.verbose):
        print("slaves",slaves);
    choreList = getChores(args.chores);
    if(args.verbose):
        print("chores",choreList);
    newChores, randomBlock = allocateChores(history, choreList, slaves);
    master = gatherMaster(args.master);
    if(args.verbose):
        print("master settings",master);
    sendChores(newChores, master, randomBlock);