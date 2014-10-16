#!/usr/bin/env python3

""" BibTeX Normalization Tool

    An example of a normalized entry:
    @article{greenwade93,
        author     = {George D. Greenwade},
        title      = {The {C}omprehensive {T}ex {A}rchive {N}etwork ({CTAN})},
        year       = {1993},
        journal    = {TUGBoat},
        volume     = {14},
        number     = {3},
        pages      = {342--351},
    }

    To do:
        1) DBLP sync
        2) automatically add location for conference papers
        http://dblp.uni-trier.de/rec/bibtex/conf/sp/1996
"""

__author__ = "Xiaokui Shu"
__copyright__ = "Copyright 2014, Xiaokui Shu"
__license__ = "Apache"
__version__ = "1.0.0"
__maintainer__ = "Xiaokui Shu"
__email__ = "subx@cs.vt.edu"
__status__ = "Testing"

import sys
import os
import argparse
import time
import datetime
import logging
import string
import re

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

CATEGORIES = ("article", "book", "booklet", "inbook", "incollection",
"inproceedings", "manual", "mastersthesis", "phdthesis", "misc", "techreport",
"unpublished")

# attributes in order
ATTRIBUTES = ("author", "title", "journal", "booktitle", "institution",
"school", "key", "year", "month", "series", "volume", "number", "pages",
"publisher", "edition", "note", "howpublished", "url")

ATTR_ONLY_IN = {"url":("note"), "publisher": ("book", "inbook", "incollection")}

ATTRIBUTES_DROP = ("location", "address", "organization", "ee",
"doi", "crossref", "bibsource", "isbn", "issn", "acmid", "numpages",
"issue_date", "keywords")

SYNTAX_CORRECTION_MONTH = {"Jnu": "Jun"}

re_pages = re.compile("(\d+)\s*-+\s*(\d+)")

def process_entry(oneline_entry, if_shorten_entry):
    """
    process each entry in a line

    @param oneline_entry: the entry in one line string
    """

    def check_int_attr(attr_name):
        """
        check integer type attribute

        @param attr_name: atribute name in string
        """
        if attr_name in final_entries:
            try:
                int(final_entries[attr_name])
            except:
                logger.warn('format error in "{0}" for entry {1}'.format(
                    attr_name, anchor_word))

    # Step 0: init
    final_entries = {}
    final_entry_lines = []
    oneline_entry = oneline_entry.strip()

    # Stpe 1: check entry
    if oneline_entry[0] != "@" or \
            oneline_entry.find("{") < 0 or \
            oneline_entry[-1] != "}" or \
            oneline_entry.count("{") != oneline_entry.count("}"):
                raise ErrorParsedEntry()

    # Step 2: extract category
    cap_left_bracket_index = oneline_entry.find("{")

    category = oneline_entry[1:cap_left_bracket_index].lower().strip()

    if category not in CATEGORIES:
        logger.info("drop comment:\n"
                + "    {0}".format(oneline_entry))
        return

    # Step 3: find content and extract anchor word
    content = oneline_entry[cap_left_bracket_index+1: -1]
    attrs_raw = content.split(",")
    attrs = []
    attr_merged_seg = ""

    for item in attrs_raw:
        if not attr_merged_seg:
            attr_merged_seg = item
        else:
            attr_merged_seg = attr_merged_seg + ", " + item

        if attr_merged_seg.count("{") == attr_merged_seg.count("}") and \
                attr_merged_seg.count('"') % 2 == 0:
                    attrs.append(attr_merged_seg)
                    attr_merged_seg = ""

    if attr_merged_seg:
        logger.warning("unmatched bracket, potential program logic error")

    anchor_word = attrs[0].strip()
    attrs = attrs[1:]

    # Step 4: extract attributes in content
    for attrline in attrs:
        attrline = attrline.strip()
        if attrline == "":
            continue

        eq_index = attrline.find("=")
        attribute = attrline[:eq_index].strip().lower()

        if attribute in ATTRIBUTES_DROP:
            continue

        if attribute not in ATTRIBUTES:
            logger.info("drop unknown attribute:\n"
                    + "    {0}".format(attrline))
            continue

        # drop attribute if not required
        if attribute in ATTR_ONLY_IN:
            if category not in ATTR_ONLY_IN[attribute]:
                continue

        # get rid of double quotations or brackets
        value = attrline[eq_index+1:].strip()
        
        # sometimes year is not surrounded by quatation or bracket
        if value[0] == '"' or value[0] == "{":
            value = value[1:-1].strip()

        # merge multiple spaces into one
        value = " ".join(value.split())

        if value == "":
            continue

        if value.isupper() and len(value.split()) > 2:
            value = string.capwords(value)
            logger.warn("ALL UPPER LETTER VALUE, Turned To Capwords:\n"
                    + "    {0}".format(value))

        final_entries[attribute] = value

    # Step 5: correct attributes
    if "title" not in final_entries:
        if category == "misc" and "note" in final_entries:
            final_entries["title"] = final_entries.pop("note")
        else:
            logger.warning("entry has no title:\n"
                    + "    {0}".format(oneline_entry))

    if "url" in final_entries or "howpublished" in final_entries:
        if "note" in final_entries:
            logger.warning('entry has "note", replace it with url')
        try:
            value_to_move = final_entries.pop("url")
        except:
            value_to_move = final_entries.pop("howpublished")
        finally:
            final_entries["note"] = "\\url{{{0}}}, accessed {1}".format(
                    value_to_move, time.strftime("%B %Y"))

    if "pages" in final_entries:
        pages_value = final_entries["pages"]
        re_match = re_pages.match(pages_value)
        if re_match:
            final_entries["pages"] = "--".join(re_match.groups())
        else:
            logger.warn('format error in "pages" ' + \
                    "for entry {0}".format(anchor_word))

    if "month" in final_entries:
        month_value = final_entries["month"][:3]
        if month_value in SYNTAX_CORRECTION_MONTH:
            month_value = SYNTAX_CORRECTION_MONTH[month_value]
        mon = datetime.datetime.strptime(month_value, "%b")
        if if_shorten_entry:
            final_entries["month"] = mon.strftime("%b")
        else:
            final_entries["month"] = mon.strftime("%B")

    for attr_name in ("number", "volume", "edition"):
        check_int_attr(attr_name)

    # Step 6: write entry into the new format
    final_entry_lines.append("@{0}{{{1},".format(category, anchor_word))
    for attribute in ATTRIBUTES:
        if attribute in final_entries:
            final_entry_lines.append("    {0:10} = {{{1}}},".format(
                attribute, final_entries[attribute]))
    final_entry_lines.append("}")

    # Step 7: return normalized entry in a line and the title
    return "\n".join(final_entry_lines), final_entries["title"]

def process_bib_file(in_descriptor, out_descriptor, \
        if_print_titles, if_shorten_entries):

    oneline_content = "".join(in_descriptor.readlines())

    final_entries = []
    titles = []

    # how many half brackets
    half_bracket = 0
    # record the index of entry start point, where the "@" is
    index_of_entry_start = 0

    index = 0
    for char in oneline_content:

        if char == "@":
            if half_bracket != 0:
                raise ErrorBracketNotMatch()
            else:
                index_of_entry_start = index
        elif char == "{":
            half_bracket += 1
        elif char == "}":
            half_bracket -= 1
            if half_bracket == 0:
                final_entry, title = process_entry(
                        oneline_content[index_of_entry_start: index+1],
                        if_shorten_entries)
                final_entries.append(final_entry)
                titles.append(title)
            
        index += 1

    out_descriptor.write("\n\n".join(final_entries))

    if if_print_titles:
        print("\n#### Print All Titles ####")
        for title in titles:
            print("{0}".format(title))

    print()
    logger.info("{0} entries processed.".format(len(final_entries)))

class ErrorParsedEntry(Exception):
    pass

class ErrorBracketNotMatch(Exception):
    pass

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="BibTeX Normalization Tool")
    parser.add_argument("bibfile", help="bibfile to read", metavar="FILE")
    parser.add_argument("-t", "--titles",
            help="print all titles", action="store_true")
    parser.add_argument("-s", "--short",
            help="print months in three letters", action="store_true")
    parser.add_argument("-i", "--inplace",
            help="edit the bib file in-place", action="store_true")
    parser.add_argument("-o", "--output",
            help="output to file", metavar="NEWFILE")
    args = parser.parse_args()

    if args.inplace:
        old_file_name = args.bibfile + ".bak"
        os.rename(args.bibfile, old_file_name)
        in_file = open(old_file_name, "r")
        out_file = open(args.bibfile, "w")
    else:
        in_file = open(args.bibfile, "r")

        if args.output:
            out_file = open(args.output, "w")
        else:
            out_file = sys.stdout

    process_bib_file(in_file, out_file, args.titles, args.short)

    in_file.close()
    if out_file != sys.stdout:
        out_file.close()
