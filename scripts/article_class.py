import sys

from lxml import etree
import requests
import pandas as pd

class ArticlesProcessing(object):
    """Articles processing class."""

    def __init__(self, csv_file_path):
        self.csv_file = csv_file_path

    def get_article(self, article_url):
        # Example PMC article ID
        pmcid = article_url.split('/')[-2]  

        # Fetch full-text XML (NXML format, structured and machine-readable)
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        params = {
            "db": "pmc",
            "id": pmcid,
            "rettype": "full",
            "retmode": "xml"
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.text, article_url
        else:
            print("Error:", response.status_code)

    def load_and_process_csv(self):
        """Load CSV and process each article."""
        df = pd.read_csv(self.csv_file)
        for url in df['Link']:
            print("Process article: ", url)
            article_text, article_url = self.get_article(url)
            self.parse_xml_article(article_text, article_url)

    def parse_section(self, sec, depth=0):
        """Recursively parse <sec> sections from the body"""
        section_text = """"""
        title = " ".join(sec.xpath("./title//text()")).strip()
        paragraphs = [" ".join(p.xpath(".//text()")).strip() for p in sec.xpath("./p")]

        if title:
            section_text += f"## {title}\n"
        for para in paragraphs:
            if para:
                section_text += f"{para}\n"

        # Recurse into subsections
        for child_sec in sec.xpath("./sec"):
            section_text += "#"+ self.parse_section(child_sec, depth + 1)
        return section_text

    def parse_xml_article(self, article_xml, url):
        """Parse XML article and convert to markdown-like text."""
        # Load XML
        tree = etree.fromstring(article_xml.encode("utf-8"))
        text = """"""
        # Start from <body>
        ns = {}
        article_title = tree.xpath("//title-group/article-title//text()", namespaces=ns)
        text += f"# {' '.join(article_title).strip()} ({url})\n"
        abstract_texts = tree.xpath("//abstract//p//text()", namespaces=ns)
        abstract = " ".join(abstract_texts).strip()
        text += f"## Abstract\n{abstract}\n"
        body = tree.xpath("//body")[0]
        for sec in body.xpath("./sec"):
            text += self.parse_section(sec)
        formatted_name =f"articles/{url.split('articles')[-1].strip("/")}" + ".md"
        with open(formatted_name, "w", encoding="UTF-8") as f:
            f.write(text)

if __name__ == "__main__":
    processor = ArticlesProcessing(sys.argv[1])
    processor.load_and_process_csv()
