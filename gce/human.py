from datetime import datetime

class HumanReadableExporter(object):
    def __init__(self):
        self.transactions = []

    def add_transaction(self, guid, unixtime, memo, value):
        self.transactions.append((guid, unixtime, memo, value))

    def set_account(self, name):
        pass

    def generate(self, reverse=False):
        for guid, unixtime, memo, value in self.transactions:
            date = datetime.fromtimestamp(unixtime)
            print("%s %s %s %s" % (guid, date, memo, value))
        return ""
