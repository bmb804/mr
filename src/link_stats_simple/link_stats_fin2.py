from mrjob.job import MRJob
from mrjob.step import MRStep
from mrjob.protocol import JSONValueProtocol
import mwparserfromhell as mwp
from mwparserfromhell.string_mixin import StringMixIn
import re
import heapq
import math
import random
import lxml.etree as ET
from bs4 import BeautifulSoup

def stats(iterable):
    """Compute some statistics over a numeric iterable."""
    sum_links = 0.0
    sum_articles = 0.0
    sum_sq_links = 0.0
 
    for item in iterable:
        sum_links += item
        sum_articles += 1
        sum_sq_links += item**2
        
    mean = sum_links / sum_articles
    var = sum_sq_links / sum_articles - mean**2
 
    return sum_articles, sum_links, sum_sq_links, mean, math.sqrt(var)

class MRMostUsedWords(MRJob):
    
    OUTPUT_PROTOCOL=JSONValueProtocol
    
    def mapper_join_init(self):
        self.inText = False
        self.begin = False
        self.p = True
        self.count = 0
        self.reservoir = [0] * 100
        self.full = ''
        
    def mapper_join(self, _, line):
        
        line = line.strip()
        if line.find( "<page>" ) != -1:
            self.inText = True
            self.begin = True
        if line.find( "</page>" ) != -1 and self.begin:
            self.inText = False
            self.page = (self.full + " </page> ").strip()
            self.full = ''
            soup = BeautifulSoup(self.page, "lxml")
            texts = soup.findAll("text")
            #tree = ET.fromstring(self.page)
            #texts = tree.findall('.//text')
            for t in texts:
                if t.text:
                    wikicode = mwp.parse(t.text)
                    links = wikicode.filter_wikilinks()
                    links = [l.lower() for l in links]
                    ulinks = list(set(links))
                    yield None, len(ulinks)
        if self.inText:
            self.full = self.full + ' ' + line

    def reducer_join(self, _, nlinks):
        N, total, total_sq, mean, std = stats(nlinks)
        yield None, (N, total, total_sq, mean, std)

    def steps(self):
        return [
            MRStep(mapper_init=self.mapper_join_init,
                   mapper=self.mapper_join)
        ]


if __name__ == '__main__':
    MRMostUsedWords.run()
