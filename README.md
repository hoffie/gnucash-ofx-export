gnucash-ofx-export
==================
Gnucash currently does not provide an OFX exporter, but it has
Python bindings to get all the necessary information.

This small script is very minimalistic and is designed for just one
specific use case, but it may serve as a base for more complicated
setups.

Use case
--------
- you do accounting for your expenses
- your roommate does the same
- both of you have expenses which the other one has to pay
- so you will export your expenses from a designated Gnucash account
- and so will your roommate

The script allows for exactly that -- exporting transactions from exactly one account. It has flags to select only the expenses and to reverse the direction of the transaction so that your roommate can just import it using the Gnucash importer.

Usage
-----
See all-in-one.sh for a possible usage scenario.

Environment
-----------
Tested on Ubuntu 13.10 with Gnucash 2.4.13, requires python-gnucash

Quality
-------
It works for me, but consider it more or less to be quick & dirty.
