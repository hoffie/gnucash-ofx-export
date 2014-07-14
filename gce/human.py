from datetime import datetime
from .common import CHARSET

class HumanReadableExporter(object):
    def __init__(self):
        self.transactions = []

    def add_transaction(self, guid, unixtime, memo, value):
        self.transactions.append((guid, unixtime, memo, value))

    def set_account(self, name):
        pass

    def generate(self, reverse=False):
        result = ""
        for guid, unixtime, memo, amount in self.transactions:
            date = datetime.fromtimestamp(unixtime)
            if reverse:
                if amount[0] == '-':
                    amount = amount[1:]
                else:
                    amount = '-' + amount
            result += "%s %s %s %s\n" % (guid, date, amount, memo)
        return result.encode(CHARSET)
