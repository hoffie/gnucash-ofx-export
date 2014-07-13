from datetime import datetime
from hashlib import sha1
from xml.sax.saxutils import escape as xml_escape
from .common import CHARSET

def xml_template(template, data):
    """
    return template % data but with proper escaping
    """
    escaped_data = {}
    for key, value in data.items():
        escaped_data[key] = xml_escape(value)
    return template % escaped_data

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


