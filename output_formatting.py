#!/usr/bin/env python3

import json
import pprint
import csv
from collections import OrderedDict


class OutputColumn:
    def __init__(self, header, width, display=True, before_width="", after_width="s"):
        self.header = header
        self.display = display
        self.bw = before_width
        self.aw = after_width

        if isinstance(width, str):
            self.width = len(width)
        elif isinstance(width, (list, dict)):
            self.width = max(len(str(i)) for i in width)
        elif isinstance(width, tuple):
            if isinstance(width[0], dict):
                self.width = max(len(str(val[width[1]])) for _, val in width[0].items())
            else:
                self.width = max(len(str(val[width[1]])) for val in width[0])
        else:
            self.width = width


class OutputTable:
    def __init__(self, columns, csv_path=None):
        self.columns = OrderedDict(columns)
        if csv_path is not None:
            headers = [oc.header for oc in self.columns.values() if oc.display]
            self.csv_file = open(csv_path, "w", newline="")
            self.csv_writer = csv.DictWriter(self.csv_file, headers)
            self.csv_writer.writeheader()
        else:
            self.csv_file = None
            self.csv_writer = None

    def close(self):
        if self.csv_file is not None:
            self.csv_file.close()

    def get_header_format(self):
        return "  ".join("{{{}:{}}}".format(k, oc.width) for k, oc in self.columns.items() if oc.display)

    def get_row_format(self):
        return "  ".join("{{{}:{}{}{}}}".format(k, oc.bw, oc.width, oc.aw) for k, oc in self.columns.items() if oc.display)

    def get_width(self):
        return (2 * (len(self.columns) - 1)) + sum(oc.width for oc in self.columns.values())

    def print_line(self):
        print("-" * self.get_width())

    def print_header_row(self, print_line):
        print(self.get_header_format().format(**{k: oc.header for k, oc in self.columns.items() if oc.display}))
        if print_line:
            self.print_line()

    def print_row(self, row):
        print(self.get_row_format().format(**row))
        if self.csv_writer is not None:
            self.csv_writer.writerow({oc.header: row[k] for k, oc in self.columns.items() if oc.display})

    def print_rows(self, rows):
        for row in rows:
            self.print_row(row)


class Printer:
    formats = ["json", "json-pretty", "pprint"]

    def __init__(self, format):
        if format not in self.formats:
            raise InputValidationException("Invalid format: {}".format(format))
        self.format = format

    def pprint(self, content):
        if self.format == "json":
            print(json.dumps(content))
        elif self.format == "json-pretty":
            print(json.dumps(content, sort_keys=True, indent=4))
        elif self.format == "pprint":
            pprint.pprint(content)


class InputValidationException(Exception):
    pass
