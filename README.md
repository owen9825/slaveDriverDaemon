slaveDriverDaemon
=================

Allocates chores reasonably fairly and sends emails. I recommend forking this project (and issuing pull requests!) if you have housemates. Get Windows task scheduler / cron to run the script eg weekly.

The fairness comes from allocating each chore randomly (and independently), with the randomness coming from a public source, so that the script can't just run repeatedly until desired results are achieved. The randomness therefore comes from scraping the most recent NSW lottery results.

To do:
· Send emails.

The command-line help explains the format of the files for slaves and chores. The concept of a group is that some slaves might be eg upstairs and can therefore only be assigned tasks marked as "upstairs" or "all", otherwise they'll revolt.
