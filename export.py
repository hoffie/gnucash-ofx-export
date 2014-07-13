import argparse
from datetime import datetime
from uuid import UUID
from hashlib import sha1
from xml.sax.saxutils import escape as xml_escape
from gnucash import Session

CHARSET = 'utf-8'

def numeric_to_doublestr(numeric, delimiter="."):
    """precision-safe conversion of 214/100 to 2,14"""
    if numeric.denom() != 100:
        raise NotImplementedError("Unsupported GNCNumeric %r" % numeric.denom)
    ret = list(str(numeric.num()))
    # ensure that we have A.BC, so we need at least 3 parts; missing
    # digits are filled up with 0 from the left
    if len(ret) < 3:
        num_fill_digits = 3 - len(ret)
        ret = ['0'] * num_fill_digits + ret
    ret.insert(-2, delimiter)
    return ''.join(ret)

def xml_template(template, data):
    """
    return template % data but with proper escaping
    """
    escaped_data = {}
    for key, value in data.items():
        escaped_data[key] = xml_escape(value)
    return template % escaped_data

class TransactionListing(object):
    """
    Extracts all transactions from a specific account in a GnuCash file
    and returns them as a list"""

    def load(self, filename):
        """
        Load a GnuCash file, e.g. xml:///tmp/test.gnucash
        """
        self.session = Session(filename, is_new=False, ignore_lock=True)
        self.book = self.session.get_book()

    def format_guid(self, gnc_guid):
        as_string = gnc_guid.to_string()
        uuid = UUID(as_string)
        return str(uuid)

    def get_all_transactions(self, account, positive_only=False):
        """
        Yields a list of all transactions as a tuple.

        @param str account
        @return tuple(unix time stamp, memo, value as string)
        """
        account = self.get_account(account)
        transactions = []
        split_list = account.GetSplitList()

        def get_transaction_str_amount(transaction):
            return numeric_to_doublestr(
                    transaction.GetAccountAmount(account))

        # this temporary list is used so that duplicate transactions
        # can be detected (these appear when multiple splits of the
        # same transaction belong to the current account)
        gnc_transactions = []
        for split in split_list:
            transaction = split.GetParent()
            amount = get_transaction_str_amount(transaction)
            if positive_only and amount[0] == '-':
                continue
            if transaction not in gnc_transactions:
                gnc_transactions.append(transaction)

        for transaction in gnc_transactions:
            guid = self.format_guid(transaction.GetGUID())
            date = transaction.GetDate()
            desc = transaction.GetDescription().decode(CHARSET)
            amount = get_transaction_str_amount(transaction)
            if not desc.strip() and not float(amount):
                continue
            yield (
                guid,
                date,
                desc,
                amount)

    def get_account(self, account):
        """
        Looks up an account object by a given navigation string
        (e.g. Aktiva:Foo:Bar)

        @param str account
        @param GnuCash.Account account
        """
        account_path = account.split(':')
        search = self.book.get_root_account()
        found = True
        while found and account_path:
            account_name = account_path.pop(0).lower()
            found = False
            for account in search.get_children():
                if account.name.lower() == account_name:
                    search = account
                    found = True
                    break
        if not found:
            raise RuntimeError("Account not found")
        return account

class OFXExporter(object):
    HEADER = """ENCODING:UTF-8
OFXHEADER:100
DATA:OFXSGML
VERSION:211
SECURITY:NONE
CHARSET:UTF-8
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <TRNUID>0</TRNUID>
      <STMTRS>
        <CURDEF>EUR</CURDEF>
        <BANKACCTFROM>
          <BANKID>info.hoffmann-christian.gnucash-export</BANKID>
          <ACCTID>%(acctid)s</ACCTID>
          <ACCTTYPE>CHECKING</ACCTTYPE>
        </BANKACCTFROM>
        <BANKTRANLIST>
          <DTSTART>%(dtstart)s</DTSTART>
          <DTEND>%(dtend)s</DTEND>"""

    TRANSACTION = """
          <STMTTRN>
            <TRNTYPE>%(trntype)s</TRNTYPE>
            <DTPOSTED>%(dtposted)s</DTPOSTED>
            <DTUSER>%(dtuser)s</DTUSER>
            <TRNAMT>%(trnamt)s</TRNAMT>
            <FITID>%(fitid)s</FITID>
            <NAME>%(name)s</NAME>
            <MEMO>%(name)s</MEMO>
          </STMTTRN>"""

    FOOTER = """
        </BANKTRANLIST>
     </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>
"""
    def __init__(self):
        self.transactions = []

    def set_account(self, name):
        self.account_name = name
        self.account_id = sha1(name).hexdigest()

    def add_transaction(self, guid, unixtime, memo, value):
        self.transactions.append((guid, unixtime, memo, value))

    def unixtime2ofx(self, unixtime):
        dt = datetime.fromtimestamp(unixtime)
        return dt.strftime("%Y%m%d%H%M%S")

    def generate_ofx(self, reverse=False):
        earliest_tx = None
        latest_tx = None
        transactions = ""
        for guid, unixtime, memo, amount in self.transactions:
            if reverse:
                if amount[0] == '-':
                    amount = amount[1:]
                else:
                    amount = '-' + amount
            ofxdate = self.unixtime2ofx(unixtime)
            transaction_type = "CREDIT"
            if amount[0] == '-':
                transaction_type = "DEBIT"
            transactions += xml_template(self.TRANSACTION, {
                'trntype': transaction_type,
                'fitid': guid,
                'dtposted': ofxdate,
                'dtuser': ofxdate,
                'trnamt': amount,
                'name': memo
            })
            if not earliest_tx or earliest_tx > unixtime:
                earliest_tx = unixtime
            if not latest_tx or latest_tx < unixtime:
                latest_tx = unixtime

        header = xml_template(self.HEADER, {
            'acctid': self.account_id,
            'dtstart': self.unixtime2ofx(earliest_tx),
            'dtend': self.unixtime2ofx(latest_tx)
        })

        footer = self.FOOTER % {
        }

        return (header + transactions + footer).encode(CHARSET)

def main():
    parser = argparse.ArgumentParser(description="Export GnuCash transactions to QIF")
    parser.add_argument("inputfile")
    parser.add_argument("account")
    parser.add_argument("--output", "-o")
    parser.add_argument("--reverse", "-r", action="store_true",
        default=False)
    parser.add_argument("--positive-only", "-p", action="store_true",
        default=False)
    args = parser.parse_args()
    exporter = OFXExporter()
    exporter.set_account(args.account)
    tl = TransactionListing()
    tl.load(args.inputfile)
    for transaction in tl.get_all_transactions(args.account,
            positive_only=args.positive_only):
        exporter.add_transaction(*transaction)
    ofx = exporter.generate_ofx(reverse=args.reverse)
    if args.output:
        output_fh = open(args.output, 'wb')
        output_fh.write(ofx)
        output_fh.close()
    else:
        print ofx


if __name__ == '__main__':
    main()
