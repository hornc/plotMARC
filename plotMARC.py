#!/usr/bin/env python3
import argparse
import csv
import numpy as np
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
DATE_LABELS = ('<1400', '<1700')
I_LABEL = 'Bibliographic Identifiers'
D_LABEL = 'Publication Dates'
ID_CATS = ['Other / No IDs', 'ISBN only', 'LCCN only', 'ISBN & LCCN', 'OCN only', 'ISBN & OCN', 'LCCN & OCN', 'All 3 IDs']
ID_CATS_ABBR = ['No_IDs', 'ISBN', 'LCCN', 'IS+LC', 'OCN', 'IS+OC', 'LC+OC', 'All_3_IDs']
RE_OCLC = re.compile(r'.*(\(OCoLC|OCoOC|ocm|ocn)')


def output_tsv(name, venn, dates):
    print(name.title())
    print(I_LABEL)
    print('\t'.join(ID_CATS_ABBR))
    print('\t'.join([str(v) for v in venn]))
    print(D_LABEL)
    date_output(dates)


def date_output(dates):
    print("Date\tCount")
    for i, d in enumerate(sorted(dates)):
        label = DATE_LABELS[i] if i < 2 else d
        print(f'{label}\t{dates[d]}')
    return dates


def marc_extract():
    """
    Extract identifier categories and year of publication histogram data
    from local MARC records.
    """
    # A: ISBN, B: LCCN, C: OCLC
    categories = [0] * 8
    dates = {0: 0, BIN_EARLY: 0}
    thisyear = datetime.now().year
    i = 0

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
                oclc = [v for v in oclc if RE_OCLC.match(v.value())]
                pub = record['260']
                cat = bool(isbns) + bool(lccn) * 2 + bool(oclc) * 4
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
                i += 1
                if args.debug and i > LIMIT:
                    break
    return categories, dates


def tsv_import(filename):
    """
    Import category data from a TSV file for plotting.
    """
    with open(filename) as tsv:
        read_tsv = csv.reader(tsv, delimiter='\t')
        name = next(read_tsv)[0]
        id_title, i_labels = next(read_tsv), next(read_tsv)
        categories = [int(v) for v in next(read_tsv)]
        date_title, d_labels = next(read_tsv), next(read_tsv)
        dates = {}
        for i, row in enumerate(read_tsv):
            if not row:
                continue
            if i < 2:
                k = (0, BIN_EARLY)[i]
            else:
                k = int(row[0])
            dates[k] = int(row[1])
    return name, categories, dates


def value_formatter(v):
    """
    ``subset_label_formatter`` function to be passed to venn3() to format the value
    labels that describe the size of each subset.
    """
    return format(v, ',')


def plot(name, categories, dates, values=True, noids=True):
    """
    Output plot to <name>.png
    """
    fig, axes = plt.subplots(2, 1)
    formatter = value_formatter if values else lambda v: ''

    # Draw a No ID circle, if there are any
    if noids and categories[0] > 0:
        noid = categories[0] / sum(categories[1:])
        r = np.sqrt(noid / np.pi)
        x, y = (0.8 + r, -0.2)
        axes[0].annotate(formatter(categories[0]), xy=(min(2, x), max(-0.5, y)))
        axes[0].annotate(ID_CATS[0], xy=(min(2, x), max(-0.5, y - r)), fontsize=12, ha='center', va='top')
        circle = plt.Circle((x, y), r, color='silver')
        axes[0].add_patch(circle)

    venn = venn3(
            subsets=categories[1:],
            set_labels=('ISBN', 'LCCN', 'OCN'),
            ax=axes[0],
            normalize_to=1,
            subset_label_formatter=formatter)

    sdates = sorted(dates)
    bins = []
    if len(sdates) > 2:
        bins = [0, BIN_EARLY] + [sdates[2] + BINSIZE * i for i in range((sdates[-1] - sdates[2]) // BINSIZE)]

    #bins = len(dates)
    # TODO: follow https://stackoverflow.com/questions/58183804/matplotlib-histogram-with-equal-bars-width for
    # custom bar chart approach

    #hist = plt.hist(sdates, weights=[dates[k] for k in sdates], bins=bins, range=(BIN_EARLY - BINSIZE, thisyear + BINSIZE))
    plt.suptitle(name, fontsize=16, fontweight='bold')
    axes[1].bar(range(len(dates)), [dates[k] for k in sdates], width=1, edgecolor='k')
    axes[1].set_xticks(range(len(dates)))
    axes[1].set_xticklabels(['<1400', '<1700'] + sdates[2:], rotation=60)
    axes[0].set_title(I_LABEL, fontsize=14)
    axes[1].set_title(D_LABEL, fontsize=14, loc='left')
    axes[1].set_ylabel('records', fontstyle='italic')
    axes[0].set_xlim(-1, 2)
    plt.savefig(f'{name}.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=ABOUT, allow_abbrev=True)
    parser.add_argument('--debug', '-d', help='Turn on debug output', action='store_true')
    parser.add_argument('--quiet', '-q', help='Suppress pymarc reader warnings', action='store_true')
    parser.add_argument('--title', '-t', help='Title')
    parser.add_argument('--import', '-i', help='Import high-level data from tsv', dest='import_')
    parser.add_argument('--values', '-v', help='Suppress values on Venn diagram', action='store_true')
    parser.add_argument('--noids', '-n', help='Suppress No-ids circle on Venn diagram', action='store_true')
    args = parser.parse_args()

    # Default name
    name = os.path.basename(os.getcwd()).title()

    if args.import_:
        print(f"Import data from {args.import_}...")
        name, categories, dates = tsv_import(args.import_)
    else:
        print("Extract data from MARC records...")
        categories, dates = marc_extract()

    if args.title:
        name = args.title

    # Output tsv data to STDOUT:
    output_tsv(name, categories, dates)

    # Output plot to <name>.png
    plot(name, categories, dates, values=not args.values, noids=not args.noids)

