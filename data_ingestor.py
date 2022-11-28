import json
import yaml
# import re
# re module from python does not support yet negative lookahead, so had to use third party module
import regex as re

# REGEX ADDRESSES
# example italian addresses https://regexr.com/73bbe
# first part is the qualificatore, see http://blog.terminologiaetc.it/2009/02/28/denominazioni-urbanistiche-generiche/#:~:text=Qualificatore%20di%20toponimo%20e%20denominazione,nell%27indirizzo%20corso%20Garibaldi%2023.
# it has a lot of possible values, only a few are used here
# schema example: qualificatore + nome strada + civico + cap + nome città + Provincia
regex_match_addresses = r'(via|viale|piazza|strada)(\s[A-Za-z]+\.?)+\s\d{1,5}[\s,]{1,2}\d{5}\s(\w+\.?\s)+[A-Za-z]{2}'

# REGEX EMAIL
# used https://en.wikipedia.org/wiki/Email_address#Local-part as reference
# local part of an email can container special chars as !#$%&'*+-/=?^_`{|}~ , can not start or end with a point
# domain can have alfanumeric chars, - can be in domain but not at start or end, first level domain can not be all numeric
# https://regexr.com/73adn
regex_match_email = r'([\w\!\#\$\%\&\'\*\+\-\/\=\?\^\_\`\{\|\}\~]+\.)*(\.?[\w\!\#\$\%\&\'\*\+\-\/\=\?\^\_\`\{\|\}\~]+)+@(\w([\w-]+\.))+([\w-]+\.)*([\w-]{1,}\w)'

# REGEEX TELEPHONE NUMBERS
# https://stackoverflow.com/questions/16699007/regular-expression-to-match-standard-10-digit-phone-number
regex_match_telephones = r'(\+\d{1,2}\s)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}'

# REGEEX TOKENS
# v1
# finds only the token
# ?<= is a negative lookahead, returns the content placed after the group where the lookahead is
# looks for a declaration of a variable that has token, key or password in the variable name.
# regex_match_tokens = r'(?<=(["\']?[\w-]*(key|password|pwd|secret|token)[\w-]*["\']?\s*[=:]))["\']?.*'
# v2
# extracts also the variable name
# https://regexr.com/7381d
regex_match_tokens = r'(["\']?[\w-]*(key|password|pwd|secret|token)[\w-]*["\']?\s*[=:]).*'

# REGEX URL
# https://regexr.com/73b66
regex_match_url = r'[A-Za-z]+:\/\/((\w[\w-]*\.)*\w+|([0-2]?\d{1,2}\.){3}[0-2]?\d{1,2})(:[0-6]?\d{1,4})?(\/[\w\?\&\=\%\.\£\$]+)*'

class Data:
    addresses = []
    emails = []
    telephones = []
    tokens = []
    urls = []

    collect = {
        "addresses" : False,
        "emails" : False,
        "telephones" : False,
        "tokens" : False,
        "urls" : False
    }

    collection = { }

    def __init__ (self, collect_addresses = False, collect_emails = False, collect_telephones = False, collect_tokens = False, collect_urls = False ):
        self.collect["addresses"] = collect_addresses
        self.collect["emails"] = collect_emails
        self.collect["telephones"] = collect_telephones
        self.collect["tokens"] = collect_tokens
        self.collect["urls"] = collect_urls

        if self.collect["addresses"]: self.collection["addresses"] = self.addresses
        if self.collect["emails"]: self.collection["emails"] = self.emails
        if self.collect["telephones"]: self.collection["telephones"] = self.telephones
        if self.collect["tokens"]: self.collection["tokens"] = self.tokens
        if self.collect["urls"]: self.collection["urls"] = self.urls

    def ingest(self, text):

        if self.collect["addresses"]:

            self.addresses += [ item.group() for item in re.finditer( regex_match_addresses, text) if isinstance(item.group(), str) ]
        
        if self.collect["emails"]:

            self.emails += [ item.group() for item in re.finditer( regex_match_email, text) if isinstance(item.group(), str) ]

        if self.collect["telephones"]:

            self.telephones += [ item.group() for item in re.finditer( regex_match_telephones, text) if isinstance(item.group(), str) ]

        if self.collect["tokens"]:

            self.tokens += [ item.group() for item in re.finditer( regex_match_tokens, text) if isinstance(item.group(), str) ]

        if self.collect["urls"]:

            self.urls += [ item.group() for item in re.finditer( regex_match_url, text) if isinstance(item.group(), str) ]


    def export_as_JSON(self):
        return json.dumps(self.collection, indent=4 )

    def export_as_YAML(self):
        return yaml.dump(self.collection)

    def __str__(self):
        return json.dumps(self.collection)