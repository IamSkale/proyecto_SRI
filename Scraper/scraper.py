import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

class MusicScraper:
    def __init__(self):
        self.logger = logging.getLogger('MusicScraper')
        self.valid_domains = []

    def scrape(self, html, url):
        raise NotImplementedError


class GeniusScraper(MusicScraper):
    def __init__(self):
        super().__init__()
        self.valid_domains = ['genius.com']

    def scrape(self, html, url):
        soup = BeautifulSoup(html, 'lxml')
        datos = {
            'titulo': '',
            'artista': '',
            'letra': '',
            'generos': [],
            'tags': [],
            'url': url
        }

        try:
            # Extraer título - Intentar varios métodos
            titulo_elem = soup.find('h1')
            if titulo_elem:
                datos['titulo'] = titulo_elem.get_text(strip=True)
            
            if not datos['titulo']:
                # Intentar meta tag de og:title
                meta_title = soup.find('meta', property='og:title')
                if meta_title:
                    datos['titulo'] = meta_title.get('content', '').split(' – ')[-1].strip()

            # Extraer artista(s)
            artista_elem = soup.find('a', {'class': re.compile('.*Artist.*|.*artist.*')})
            if not artista_elem:
                artista_elem = soup.select_one('a[class*="ArtistName"], span[class*="ArtistName"]')
            
            if artista_elem:
                datos['artista'] = artista_elem.get_text(strip=True)
            
            if not datos['artista']:
                # Intentar meta tag de og:title (formato: "Artist – Title")
                meta_title = soup.find('meta', property='og:title')
                if meta_title:
                    content = meta_title.get('content', '')
                    if ' – ' in content:
                        datos['artista'] = content.split(' – ')[0].strip()
                    elif ' - ' in content:
                        datos['artista'] = content.split(' - ')[0].strip()

            # Extraer letra - Usando la lógica de Indexer/searcher.py
            lyrics_nodes = soup.find_all('div', {'data-lyrics-container': 'true'})
            if not lyrics_nodes:
                lyrics_nodes = soup.select('div[class*="Lyrics__Container"]')

            if lyrics_nodes:
                fragments = []
                for node in lyrics_nodes:
                    # Copiamos la lógica de searcher.py para preservar saltos de línea
                    for br in node.find_all('br'):
                        br.replace_with('\n')
                    fragments.append(node.get_text(separator='\n'))
                
                letra = '\n'.join([fragment.strip() for fragment in fragments if fragment.strip()])
                datos['letra'] = letra.strip() if letra.strip() else ""
            else:
                # Fallback de letras clásicas
                letras_fallback = soup.find('div', class_='lyrics')
                if letras_fallback:
                    datos['letra'] = letras_fallback.get_text(strip=True)

            # Extraer géneros
            generos_elems = soup.find_all('a', {'class': re.compile('.*genre.*')})
            datos['generos'] = [g.get_text(strip=True) for g in generos_elems]

            # Extraer tags/descriptores
            tags_elems = soup.find_all('span', {'class': re.compile('.*tag.*')})
            datos['tags'] = [t.get_text(strip=True) for t in tags_elems]

        except Exception as e:
            self.logger.error(f"Error scrapeando Genius: {e}")

        return datos

class FactoryScraper:
    """Factory para obtener el scraper correcto según el dominio."""

    scrapers = {
        'genius.com': GeniusScraper(),
    }

    @staticmethod
    def obtener_scraper(url):
        domain = urlparse(url).netloc.lower()

        # Buscar scraper específico
        for scraper_domain, scraper in FactoryScraper.scrapers.items():
            if scraper_domain in domain:
                return scraper

        # Retornar scraper genérico si no hay específico
        return FactoryScraper.scraper_generico

    @staticmethod
    def scrape(html, url):
        scraper = FactoryScraper.obtener_scraper(url)
        return scraper.scrape(html, url)


# Función de utilidad para usar el factory fácilmente
def extraer_datos(html, url):
    return FactoryScraper.scrape(html, url)
