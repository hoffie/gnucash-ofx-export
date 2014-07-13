from uuid import UUID
from gnucash import Session
from .common import CHARSET

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


