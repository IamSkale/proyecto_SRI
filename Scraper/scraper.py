"""
Módulo de Scraping para Sistema de Búsqueda Musical
Proyecto Integrador SRI - Corte 1

Este módulo implementa scrapers especializados para extraer información
estructurada de diferentes sitios musicales de forma ética y eficiente.
"""

import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging


class MusicScraper:
    """
    Clase base para scraping de información musical.
    Define la interfaz común para todos los scrapers especializados.
    """

    def __init__(self):
        self.logger = logging.getLogger('MusicScraper')
        self.valid_domains = []

    def es_dominio_valido(self, url):
        """Verifica si la URL pertenece a un dominio que este scraper puede procesar."""
        domain = urlparse(url).netloc.lower()
        return any(valid_domain in domain for valid_domain in self.valid_domains)

    def scrape(self, html, url):
        """Método abstracto que debe implementarse en cada scraper específico."""
        raise NotImplementedError

    def limpiar_texto(self, texto):
        """Limpia y normaliza texto extraído."""
        if not texto:
            return ""
        # Eliminar espacios excesivos
        texto = re.sub(r'\s+', ' ', texto).strip()
        # Eliminar caracteres especiales problemáticos
        texto = re.sub(r'[^\w\s\-áéíóúñçü]', '', texto)
        return texto

    def extraer_generos(self, texto):
        """Extrae géneros de un texto."""
        if isinstance(texto, list):
            return texto
        if isinstance(texto, str):
            return [g.strip() for g in texto.split(',') if g.strip()]
        return []


class GeniusScraper(MusicScraper):
    """Scraper especializado para genius.com"""

    def __init__(self):
        super().__init__()
        self.valid_domains = ['genius.com']

    def scrape(self, html, url):
        """Extrae datos de una canción en Genius."""
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
            # Extraer título
            titulo_elem = soup.find('h1')
            if titulo_elem:
                datos['titulo'] = titulo_elem.get_text(strip=True)

            # Extraer artista(s)
            artista_elem = soup.find('a', {'class': re.compile('.*artist.*')})
            if artista_elem:
                datos['artista'] = artista_elem.get_text(strip=True)

            # Extraer letra
            lyrics_container = soup.find('div', {'data-lyrics-container': 'true'})
            if lyrics_container:
                versos = lyrics_container.find_all(['br', 'div'])
                letra_lineas = []
                for verso in versos:
                    texto = verso.get_text(strip=True)
                    if texto:
                        letra_lineas.append(texto)
                datos['letra'] = '\n'.join(letra_lineas)

            # Extraer géneros
            generos_elems = soup.find_all('a', {'class': re.compile('.*genre.*')})
            datos['generos'] = [g.get_text(strip=True) for g in generos_elems]

            # Extraer tags/descriptores
            tags_elems = soup.find_all('span', {'class': re.compile('.*tag.*')})
            datos['tags'] = [t.get_text(strip=True) for t in tags_elems]

        except Exception as e:
            self.logger.error(f"Error scrapeando Genius: {e}")

        return datos


class AZLyricsScraper(MusicScraper):
    """Scraper especializado para azlyrics.com"""

    def __init__(self):
        super().__init__()
        self.valid_domains = ['azlyrics.com']

    def scrape(self, html, url):
        """Extrae datos de una canción en AZLyrics."""
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
            # Extraer del título de la página
            titulo_page = soup.find('title')
            if titulo_page:
                titulo_text = titulo_page.get_text(strip=True)
                # Formato típico: "Artist - Song Lyrics - AZLyrics"
                partes = titulo_text.split(' - ')
                if len(partes) >= 2:
                    datos['artista'] = partes[0].strip()
                    datos['titulo'] = partes[1].strip().replace('Lyrics', '').strip()

            # Extraer letra del contenedor principal
            div_letras = soup.find('div', class_=re.compile('.*lyrics.*'))
            if not div_letras:
                # Alternativa: buscar div sin clase específica en el middle
                divs = soup.find_all('div')
                for div in divs:
                    texto = div.get_text()
                    if len(texto) > 200 and texto.count('\n') > 5:
                        datos['letra'] = texto.strip()
                        break
            else:
                datos['letra'] = div_letras.get_text(strip=False).strip()

            # Tags comunes para AZLyrics
            datos['tags'] = ['azlyrics', 'lyrics']

        except Exception as e:
            self.logger.error(f"Error scrapeando AZLyrics: {e}")

        return datos


class MusixmatchScraper(MusicScraper):
    """Scraper especializado para musixmatch.com"""

    def __init__(self):
        super().__init__()
        self.valid_domains = ['musixmatch.com']

    def scrape(self, html, url):
        """Extrae datos de una canción en Musixmatch."""
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
            # Extraer título
            titulo_elem = soup.find('h1', class_=re.compile('.*title.*'))
            if titulo_elem:
                datos['titulo'] = titulo_elem.get_text(strip=True)

            # Extraer artista
            artista_elem = soup.find('a', class_=re.compile('.*artist.*'))
            if artista_elem:
                datos['artista'] = artista_elem.get_text(strip=True)

            # Extraer letra
            lyrics_container = soup.find('p', class_=re.compile('.*lyrics.*'))
            if lyrics_container:
                datos['letra'] = lyrics_container.get_text(strip=True)

            # Extraer géneros
            generos_section = soup.find('div', class_=re.compile('.*genres.*'))
            if generos_section:
                generos_elems = generos_section.find_all('a')
                datos['generos'] = [g.get_text(strip=True) for g in generos_elems]

            datos['tags'] = ['musixmatch', 'lyrics']

        except Exception as e:
            self.logger.error(f"Error scrapeando Musixmatch: {e}")

        return datos


class LastFMScraper(MusicScraper):
    """Scraper especializado para last.fm"""

    def __init__(self):
        super().__init__()
        self.valid_domains = ['last.fm', 'lastfm']

    def scrape(self, html, url):
        """Extrae datos de información musical en Last.FM."""
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
            # Extraer título de la canción/artista
            titulo_elem = soup.find('h1')
            if titulo_elem:
                datos['titulo'] = titulo_elem.get_text(strip=True)

            # Extraer artista
            artista_elems = soup.find_all('a', class_='link--primary')
            if artista_elems:
                datos['artista'] = artista_elems[0].get_text(strip=True)

            # Extraer géneros
            generos_elems = soup.find_all('a', class_=re.compile('.*genre.*'))
            datos['generos'] = [g.get_text(strip=True) for g in generos_elems[:5]]

            # Extraer tags
            tags_section = soup.find('section', class_=re.compile('.*tags.*'))
            if tags_section:
                tags_elems = tags_section.find_all('a')
                datos['tags'] = [t.get_text(strip=True) for t in tags_elems[:10]]

            datos['tags'].append('lastfm')

        except Exception as e:
            self.logger.error(f"Error scrapeando Last.FM: {e}")

        return datos


class MusicBrainzScraper(MusicScraper):
    """Scraper especializado para musicbrainz.org"""

    def __init__(self):
        super().__init__()
        self.valid_domains = ['musicbrainz.org']

    def scrape(self, html, url):
        """Extrae datos de MusicBrainz (información estructurada)."""
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
            # MusicBrainz tiene información muy estructurada
            # Extraer título
            titulo_elem = soup.find('h1')
            if titulo_elem:
                datos['titulo'] = titulo_elem.get_text(strip=True)

            # Extraer artista/banda
            artista_elems = soup.find_all('a', {'href': re.compile('/artist/')})
            if artista_elems:
                datos['artista'] = artista_elems[0].get_text(strip=True)

            # Extraer géneros
            generos_section = soup.find('div', {'class': re.compile('.*genre.*')})
            if generos_section:
                generos_elems = generos_section.find_all('a')
                datos['generos'] = [g.get_text(strip=True) for g in generos_elems]

            # Extraer tags/descriptores
            tags_section = soup.find('div', {'class': re.compile('.*tags.*')})
            if tags_section:
                tags_elems = tags_section.find_all('a')
                datos['tags'] = [t.get_text(strip=True) for t in tags_elems]

            datos['tags'].append('musicbrainz')

        except Exception as e:
            self.logger.error(f"Error scrapeando MusicBrainz: {e}")

        return datos


class AllMusicScraper(MusicScraper):
    """Scraper especializado para allmusic.com"""

    def __init__(self):
        super().__init__()
        self.valid_domains = ['allmusic.com']

    def scrape(self, html, url):
        """Extrae datos de AllMusic."""
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
            # Extraer título
            titulo_elem = soup.find('h1', class_=re.compile('.*title.*'))
            if titulo_elem:
                datos['titulo'] = titulo_elem.get_text(strip=True)

            # Extraer artista
            artista_elem = soup.find('a', class_=re.compile('.*artist.*'))
            if artista_elem:
                datos['artista'] = artista_elem.get_text(strip=True)

            # Extraer géneros (AllMusic los tiene bien organizados)
            generos_section = soup.find('div', {'class': re.compile('.*genres.*')})
            if generos_section:
                generos_elems = generos_section.find_all('a')
                datos['generos'] = [g.get_text(strip=True) for g in generos_elems]

            # Extraer estilos
            estilos_section = soup.find('div', {'class': re.compile('.*styles.*')})
            if estilos_section:
                estilos_elems = estilos_section.find_all('a')
                datos['tags'] = [e.get_text(strip=True) for e in estilos_elems]

            datos['tags'].append('allmusic')

        except Exception as e:
            self.logger.error(f"Error scrapeando AllMusic: {e}")

        return datos


class ScrapeadorGeneral(MusicScraper):
    """Scraper genérico que intenta extraer información de cualquier página."""

    def __init__(self):
        super().__init__()
        self.valid_domains = []  # Acepta todos

    def scrape(self, html, url):
        """Intenta extraer datos genéricos de cualquier página HTML."""
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
            # Intentar extraer del título de la página
            titulo_page = soup.find('title')
            if titulo_page:
                datos['titulo'] = titulo_page.get_text(strip=True)

            # Buscar encabezados como título
            h1 = soup.find('h1')
            if h1:
                titulo_candidato = h1.get_text(strip=True)
                if len(titulo_candidato) < 100:
                    datos['titulo'] = titulo_candidato

            # Buscar meta tags de descripción
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                descripcion = meta_desc.get('content', '')
                # Intentar extraer artista de la descripción
                if ' - ' in descripcion:
                    partes = descripcion.split(' - ')
                    if len(partes) >= 2:
                        datos['artista'] = partes[0].strip()

            # Buscar bloques de texto largos como letra
            paragrafos = soup.find_all('p')
            texto_largo = ""
            for p in paragrafos:
                texto = p.get_text(strip=True)
                if len(texto) > 100:
                    texto_largo = texto
                    break

            if len(texto_largo) > 100:
                datos['letra'] = texto_largo

            # Extraer palabras clave de meta tags
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords:
                keywords = meta_keywords.get('content', '')
                datos['tags'] = [k.strip() for k in keywords.split(',')[:5]]

            # Extraer enlace canonical
            canonical = soup.find('link', attrs={'rel': 'canonical'})
            if canonical and 'href' in canonical.attrs:
                datos['url'] = canonical.get('href')

        except Exception as e:
            self.logger.error(f"Error scrapeando genéricamente: {e}")

        return datos


class FactoryScraper:
    """Factory para obtener el scraper correcto según el dominio."""

    scrapers = {
        'azlyrics.com': AZLyricsScraper(),
    }

    scraper_generico = ScrapeadorGeneral()

    @staticmethod
    def obtener_scraper(url):
        """Retorna el scraper apropiado para una URL."""
        domain = urlparse(url).netloc.lower()

        # Buscar scraper específico
        for scraper_domain, scraper in FactoryScraper.scrapers.items():
            if scraper_domain in domain:
                return scraper

        # Retornar scraper genérico si no hay específico
        return FactoryScraper.scraper_generico

    @staticmethod
    def scrape(html, url):
        """Scrape una página HTML usando el scraper más adecuado."""
        scraper = FactoryScraper.obtener_scraper(url)
        return scraper.scrape(html, url)


# Función de utilidad para usar el factory fácilmente
def extraer_datos(html, url):
    """
    Extrae datos de una página HTML.
    
    Args:
        html (str): Contenido HTML de la página
        url (str): URL de la página (para determinar el scraper)
    
    Returns:
        dict: Datos extraídos (título, artista, letra, etc.)
    """
    return FactoryScraper.scrape(html, url)
