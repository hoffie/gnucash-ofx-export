#!/bin/bash
GNUCASH_FILE=/path/to/your/data.gnucash
GNUCASH_ACCOUNT=Verrechnungskonto:Mitbewohner
OUTPUT=/tmp/export.ofx # use a temp file on multi-user systems!
FLAGS="-r -p" # reverse and positive-only

MAILTO=roommate@example.org
MAILTO_SUBJECT="Gnucash $(date)"

source $0.conf 2>/dev/null

python export.py "$GNUCASH_FILE" "$GNUCASH_ACCOUNT" $FLAGS -o "$OUTPUT" && \
thunderbird -compose "to='$MAILTO',subject='$MAILTO_SUBJECT',attachment=file://$OUTPUT"
