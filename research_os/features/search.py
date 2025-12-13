import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import os
import ssl
from pathlib import Path
from loguru import logger

class SearchService:
    def __init__(self, download_dir: str = "papers_library"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        # Fix for some macs certificate issues
        self.ssl_ctx = ssl.create_default_context()
        self.ssl_ctx.check_hostname = False
        self.ssl_ctx.verify_mode = ssl.CERT_NONE

    def search_arxiv(self, query: str, max_results: int = 10):
        """
        Search arXiv API for papers.
        Returns list of {title, authors, abstract, pdf_url, published}
        """
        try:
            base_url = 'http://export.arxiv.org/api/query?'
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            url = base_url + urllib.parse.urlencode(params)
            
            with urllib.request.urlopen(url, context=self.ssl_ctx) as response:
                data = response.read()
                
            root = ET.fromstring(data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            papers = []
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
                published = entry.find('atom:published', ns).text[:10]
                
                # Get PDF link
                pdf_url = ""
                for link in entry.findall('atom:link', ns):
                    if link.attrib.get('title') == 'pdf':
                        pdf_url = link.attrib.get('href')
                        
                # Fallback if no explicit pdf link title
                if not pdf_url:
                     for link in entry.findall('atom:link', ns):
                        href = link.attrib.get('href')
                        if 'pdf' in href:
                            pdf_url = href

                authors = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]
                
                papers.append({
                    "title": title,
                    "abstract": summary,
                    "pdf_url": pdf_url,
                    "authors": authors,
                    "published": published,
                    "source": "arxiv"
                })
                
            return papers
        except Exception as e:
            logger.error(f"ArXiv Search Error: {e}")
            return []

    def download_paper(self, pdf_url: str, title: str) -> str:
        """
        Download PDF to local library.
        Returns absolute path.
        """
        try:
            # Sanitize filename
            filename = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            filename = filename.replace(' ', '_')[:100] + ".pdf"
            path = self.download_dir / filename
            
            if path.exists():
                logger.info(f"Paper already exists: {path}")
                return str(path.absolute())
            
            logger.info(f"Downloading {pdf_url} to {path}...")
            # Arxiv usually redirects to a slightly different URL for PDF
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            headers = {'User-Agent': user_agent}
            
            req = urllib.request.Request(pdf_url, headers=headers)
            with urllib.request.urlopen(req, context=self.ssl_ctx) as response, open(path, 'wb') as out_file:
                out_file.write(response.read())
                
            return str(path.absolute())
        except Exception as e:
            logger.error(f"Download Error: {e}")
            return None

search_service = SearchService(download_dir=os.path.expanduser("~/Desktop/Jrvis/papers_library"))
