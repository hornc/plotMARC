#!/usr/bin/env python3
import argparse
import os
import re
from datetime import datetime
from pymarc import MARCReader
from matplotlib import pyplot as plt
from matplotlib_venn import venn3


ABOUT = """
Script to analyse one or more MARC21 collections
for identifier representation, and dates covered.

By default looks for *.mrc files in the current directory.

"""


BINSIZE = 10
LIMIT = 1000
RE_DATE = re.compile(r'[12][0-9]{3}')
BIN_NORMAL = 1700
BIN_EARLY = 1400  # no date / suspicious date bin


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=ABOUT, allow_abbrev=True)
    parser.add_argument('--debug', '-d', help='turn on debug output', action='store_true')
    parser.add_argument('--quiet', '-q', help='suppress pymarc reader warnings', action='store_true')
    args = parser.parse_args()

    fig, axes = plt.subplots(2, 1)
    # A: ISBN, B: LCCN, C: OCLC
    categories = [0] * 8
    nodate = 0
    dates = {0: 0, BIN_EARLY: 0}
    thisyear = datetime.now().year
    i = 0
    name = os.path.basename(os.getcwd())
    for f in os.listdir():
        if not f.endswith('.mrc'):
            continue
        print(f)
        with open(f, 'rb') as marcdata:
            records = MARCReader(marcdata, to_unicode=True, permissive=True, hide_utf8_warnings=args.quiet)
            for record in records:
                if not record:
                    continue
                isbns = record.get_fields('020')
                lccn = record['010']
                oclc = record.get_fields('035')
                pub = record['260']
                #print(bool(isbns), bool(lccn), bool(oclc))
                cat = bool(isbns) + bool(lccn) * 2 + bool(oclc) * 4
                #print(cat)
                categories[cat] += 1
                year = None
                if pub:
                    date = pub.get_subfields('c')
                    if date:
                        m = RE_DATE.findall(date[0])
                        if m:
                            year = max([0] + [int(v) for v in m if int(v) <= thisyear])
                            if year > BIN_NORMAL:
                                dbin = (year // BINSIZE) * BINSIZE
                                if dates.get(dbin):
                                    dates[dbin] += 1
                                else:
                                    dates[dbin] = 1
                            elif year > BIN_EARLY:
                                dates[BIN_EARLY] += 1
                            else:
                                year = None
                if not year:
                    dates[0] += 1
                    #nodate += 1
                i += 1
                #if i > LIMIT:
                #    break
    print('DATES', sorted(dates), [dates[k] for k in sorted(dates)])
    print('NODATES', dates[0])
    print('NO IDS', categories[0])
    print('ID CATS', categories)
    venn = venn3(subsets=categories[1:], set_labels=('ISBN', 'LCCN', 'OCN'), ax=axes[0], normalize_to=1)
    sdates = sorted(dates)
    bins = [0, BIN_EARLY] + [sdates[2] + BINSIZE * i for i in range((sdates[-1] - sdates[2])//BINSIZE)]
    #bins = len(dates)
    # TODO: follow https://stackoverflow.com/questions/58183804/matplotlib-histogram-with-equal-bars-width for
    # custom bar chart approach

    #hist = plt.hist(sdates, weights=[dates[k] for k in sdates], bins=bins, range=(BIN_EARLY - BINSIZE, thisyear + BINSIZE))
    axes[1].bar(range(len(dates)), [dates[k] for k in sdates], width=1, edgecolor='k')
    axes[1].set_xticks(range(len(dates)))
    axes[1].set_xticklabels(['ND', 'EARLY'] + sdates[2:], rotation=60)
    axes[0].set_title(f'{name} identifiers')
    axes[1].set_title(f'{name} dates')
    plt.savefig(f'{name}.png')

