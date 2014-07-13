import argparse
from gce.ofx import OFXExporter
from gce.transaction import TransactionListing

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
