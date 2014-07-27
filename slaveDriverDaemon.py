# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import codecs
import pandas
import csv
from fuzzywuzzy import process
import argparse
import json
import numpy as np
import math

def allocateChores(history, chores, slaves):      
    # the Group column of chores can be All
    assert(u"U" not in slaves.columns); # to do: accommodate bias from previous weeks
    # U as in potential energy
    slaves[u"U"] = 1;
    castes = slaves[u"Group"].unique();
    castePotentials = {}; # potential energy remaining in each caste
    everyoneChores = float(np.sum(chores[u"Group"] == u"All"));
    assert(u"Group" in chores.columns);
    assert(u"Chore" in chores.columns);
    assert(u"Chores" not in slaves); # to do: handle situation where some tasks have been pre-allocated
    slaves[u"Chores"] = "; "; # make it easy to strip later

    # separate function for getting the random numbers?
    try:
        rawFile = codecs.open("lottery/items.json", encoding='utf-8', mode='r');
    except IOError:
        print("Failed to open {0}".format(masterFilename));
        randomBlock = np.random.random_sample(size=len(chores));
        randomBlock *= 40; # typical maximum lottery number
    else:
        # Lotto results have been scraped to prove that this program wasn't 
        # run repeatedly until a beneficial result was generated (presumably for the master)
        lottoResults = json.load(rawFile,encoding='utf-8');
        randomBlock = [];
        for line in lottoResults:
            randomBlock.append(int(line["winningNum"][0]));
        rawFile.close;
    
    b = 0; # place in block of random numbers
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
        lastChore = 0; # when iterating, start from last pos to reduce bias of slave order
        for c in chores.index[chores[u"Group"] == caste]:
            straw = (randomBlock[b] + lastChore) % castePotentials[caste];
            lastChore = straw; # inadvertently incremented as the slave's potential is reduced
            # iterate over caste members until the straw position
            cumulation = 0; # Python doesn't allow "Σ = 0;"
            for slaveKey in casteKeys:
                cumulation += slaves.ix[slaveKey, u"U"];
                if cumulation >= straw:
                    try:
                        slaves.ix[slaveKey, u"U"] -= 1;
                    except ValueError:
                        print("There was a problem using the key to access user {0}".format(u));
                        return None;
                    slaves.ix[slaveKey, u"Chores"] += chores.ix[c,u"Chore"] + "; ";
                    break;
            b += 1; # position in random block
            assert(len(randomBlock) > b); # sufficient quantity of random numbers
            castePotentials[caste] -= 1;
    # now assign everyone tasks
    allPotential = sum(castePotentials.values());
    slaveKeys = slaves.index;
    lastChore = 0;
    for c in chores.index[chores[u"Group"] == u"All"]:
        straw = (randomBlock[b] + lastChore) % int(allPotential);
        lastChore = straw;
        # iterate over caste members until the straw position
        cumulation = 0;
        for slaveKey in slaveKeys:
            cumulation += slaves.ix[slaveKey, u"U"];
            if cumulation >= straw:
                slaves.ix[slaveKey, u"U"] -= 1;
                slaves.ix[slaveKey, u"Chores"] += chores.ix[c,u"Chore"] + "; ";
                break;
        b += 1;
        assert(len(randomBlock) > b); # sufficient quantity of random numbers
        allPotential -= 1;

    randomBlock = randomBlock[0:b]; # this is to avoid printing unused random numbers
    print("Slaves could've been pushed for another {0} tasks for more fairness.".format(allPotential));

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
                ownershipName += "'";
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

""" Read a csv that's at least similar to expected """
def fuzzyRead(csvFilename, expectedHeaders):
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
        assert(headers is not None and len(headers) >= len(expectedHeaders));

        for eh in expectedHeaders:
            fuzzyH, scoreH = process.extractOne(eh, headers);
            assert(scoreH >= 70);
            assert(np.sum(headers == eh) <= 1); # unique
            hCol = headers.index(fuzzyH);
            headers[hCol] = eh;

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
        "the sender's email address etc.", type=str, required=False);
    parser.add_argument("-chores", help="CSV file with list of chores and group "\
        "applicability", type=str, required=True);
    parser.add_argument("-v","--verbose", help="Print more comments", action='store_true',
        required=False);

    args = parser.parse_args();
    if(args.past is not None):
        history = fuzzyRead(args.past, [u"Date", u"Email", u"Chore", u"Group"]);
    else:
        history = None;
    slaves = fuzzyRead(args.slaves, [u"Name", u"Email", u"Group"]);
    if(args.verbose):
        print("slaves",slaves);
    choreList = fuzzyRead(args.chores, [u"Chore", u"Group"]); # to do: get chores from eg a to-do list on Google Docs
    if(args.verbose):
        print("chores",choreList);
    newChores, randomBlock = allocateChores(history, choreList, slaves);
    if(args.master is not None):
        master = gatherMaster(args.master);
        if(args.verbose):
            print("master settings",master);
    else:
        master = None;
    sendChores(newChores, master, randomBlock);