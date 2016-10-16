#!/usr/bin/env python3

import csv
import argparse
from urllib import request as urllib_request
from urllib import parse as urllib_parse
from urllib import error as urllib_error
from bs4 import BeautifulSoup
from termcolor import colored

from output_formatting import OutputTable, OutputColumn


def main():
    parser = argparse.ArgumentParser("Wiki Crawler")
    parser.add_argument("--debug", "-d", action="store_true", default=False, help="Print debugging information")
    mgroup1 = parser.add_mutually_exclusive_group()
    mgroup1.add_argument("--uri", "-u", help="URI to retrieve")
    mgroup1.add_argument("--list_descriptions", "-ld", action="store_true", default=False, help="List BLU spell descriptions")
    mgroup1.add_argument("--print_csv", "-pc", action="store_true", default=False, help="List BLU spell descriptions from csv")
    args = parser.parse_args()

    bwcs = BGWikiCrawlerSession("https://www.bg-wiki.com", args.debug)

    if args.list_descriptions:
        links = bwcs.get_links("/bg/Blue_Magic")
        tbl = OutputTable([("spell", OutputColumn("Spell", links)), ("desc", OutputColumn("Description", 100))], "blu_spells.csv")
        tbl.print_header_row(True)

        for spell, uri in links.items():
            row = {"spell": spell}
            try:
                row["desc"] = bwcs.get_blu_spell_description(uri)
            except AttributeError:
                row["desc"] = colored("[Error]", "red")
            tbl.print_row(row)
    elif args.uri:
        soup = bwcs.get_soup(args.uri)
        print(soup)
    elif args.print_csv:
        rows = read_csv("blu_spells.csv")
        keys = sorted(list(rows[0].keys()))[::-1]   #Preserves order since each row is a dict
        tbl = OutputTable([(keys[0], OutputColumn(keys[0], (rows, keys[0]))), (keys[1], OutputColumn(keys[1], (rows, keys[1])))])
        tbl.print_header_row(True)
        tbl.print_rows(rows)


class BGWikiCrawlerSession:
    def __init__(self, base_url, debug=False):
        self.base_url = base_url[:-1] if base_url.endswith("/") else base_url
        self.debug = debug
        self.hs = HTTPSession(self.debug)

    def _url(self, uri):
        joiner = "" if uri.startswith("/") else "/"
        return "{}{}{}".format(self.base_url, joiner, uri)

    def get_soup(self, uri):
        content = self.hs.get(self._url(uri)).read()
        return BeautifulSoup(content, "html.parser")

    def get_links(self, uri):
        soup = self.get_soup(uri)
        anchors = soup.find("div", {"id": "mw-pages"}).find_all("a", href=True)
        return {a.string: a["href"] for a in anchors}

    def get_blu_spell_description(self, uri):
        soup = self.get_soup(uri)
        try:
            return soup.find("th", text=" Description\n").find_parent().find("td").get_text().strip()
        except AttributeError as e:
            pass
        return soup.find("b", text="Description:").find_parent().find_parent().find_all("td")[-1].get_text().strip()

    def get_blu_spell_descriptions(self, category_page_uri):
        links = self.get_links(category_page_uri)
        return {spell: self.get_blu_spell_description(link) for spell, link in links.items()}


class HTTPSession:
    headers = {
        "json": {"Accept": "application/json"}
    }

    def __init__(self, debug=False):
        self.opener = urllib_request.build_opener(urllib_request.ProxyHandler({}))
        urllib_request.install_opener(self.opener)
        self.debug = debug

    def _build(self, method, url, headers=None, body=None):
        if method == "GET":
            if body is not None:
                params = urllib_parse.urlencode(body)
                if "?" in url:
                    if not url.endswith("&"):
                        url += "&"
                else:
                    url += "?"
                url += params
                body = None
        if headers is None:
            headers = {}
        return urllib_request.Request(url, body, headers, method=method)

    def _send(self, req):
        try:
            resp = self.opener.open(req)
        except urllib_error.HTTPError as e:
            if self.debug:
                print(e.info().as_string())
            print("{}: {}".format(e, e.url))
        else:
            if self.debug:
                print(resp.info().as_string())
            return resp

    def get(self, url, headers=None, body=None):
        return self._send(self._build("GET", url, headers, body))

    def post(self, url, headers=None, body=None):
        return self._send(self._build("POST", url, headers, body))


def read_csv(csv_path):
    with open(csv_path, "rb") as csv_file:
        reader = csv.DictReader(csv_file)
        return [row for row in reader]


def write_csv(csv_path, content, headers):
    with open(csv_path, "wb") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(content)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
