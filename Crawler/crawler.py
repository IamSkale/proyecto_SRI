"""
Módulo de Crawling y Scraping para Sistema de Búsqueda Musical
Proyecto Integrador SRI - Corte 1

Este módulo implementa un crawler que recopila información musical
de fuentes web confiables, respetando políticas de crawling éticas.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup
import time
import json
import logging
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from Scraper.scraper import FactoryScraper

class MusicCrawler:
    """
    Crawler especializado para recopilar información musical de la web.

    Características:
    - Respeta robots.txt y políticas de crawling
    - Rate limiting para evitar sobrecargar servidores
    - Extracción estructurada de datos musicales
    - Almacenamiento organizado en JSON
    - Filtrado de URLs relevantes para música
    """

    def __init__(self, seed_urls, max_pages=1000, delay=1.0, data_dir="Database/crawled_data",
                 user_agent="MusicResearchCrawler/1.0 (educational project)", max_retries=3):
        """
        Inicializar el crawler.

        Args:
            seed_urls (list): URLs iniciales para comenzar el crawling
            max_pages (int): Límite máximo de páginas a crawlear
            delay (float): Segundos de espera entre requests
            data_dir (str): Directorio para almacenar datos extraídos
            user_agent (str): User-Agent para identificar el crawler
            max_retries (int): Número máximo de reintentos por request
        """
        self.seed_urls = seed_urls
        self.max_pages = max_pages
        self.delay = delay
        self.data_dir = Path(data_dir)
        self.user_agent = user_agent
        self.max_retries = max_retries

        self.visited_urls = set()
        self.song_data = []
        self.queue = []
        self.failed_urls = []

        # Crear directorio si no existe (ANTES de configurar logging)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Configurar logging
        self.setup_logging()

        # Crear sesión HTTP con retry logic
        self.session = self.create_session()

        self.logger.info(f"Crawler inicializado con {len(seed_urls)} URLs semilla")

    def setup_logging(self):
        """Configurar sistema de logging para el crawler."""
        self.logger = logging.getLogger('MusicCrawler')
        self.logger.setLevel(logging.INFO)

        # Crear handler para archivo
        log_file = self.data_dir / 'crawler.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # Crear handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formato de log
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Agregar handlers al logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def create_session(self):
        """Crear sesión HTTP con configuración de retry."""
        session = requests.Session()

        # Configurar retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],  # Cambiado de method_whitelist
            backoff_factor=1
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Headers por defecto
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

        return session

    def check_robots_txt(self, url):
        """
        Verificar si podemos crawlear esta URL según robots.txt.

        Args:
            url (str): URL a verificar

        Returns:
            bool: True si está permitido crawlear
        """
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()

            return rp.can_fetch('*', url)
        except Exception as e:
            print(f"Error verificando robots.txt para {url}: {e}")
            return True  # Si no hay robots.txt, asumir que está permitido

    def extract_song_data(self, soup, url):
        """
        Extraer información de canción de la página HTML.
        Utiliza el FactoryScraper para scraping especializado por dominio.

        Args:
            soup (BeautifulSoup): Objeto BeautifulSoup de la página
            url (str): URL de la página

        Returns:
            dict: Diccionario con información extraída de la canción
        """
        try:
            # Obtener el HTML como string
            html = str(soup)
            
            # Usar el FactoryScraper para extraer datos
            datos_extraidos = FactoryScraper.scrape(html, url)
            
            # Normalizar estructura
            song_info = {
                'url': url,
                'titulo': datos_extraidos.get('titulo', ''),
                'artista': datos_extraidos.get('artista', ''),
                'album': datos_extraidos.get('album', ''),
                'generos': datos_extraidos.get('generos', []),
                'letra': datos_extraidos.get('letra', ''),
                'tags': datos_extraidos.get('tags', []),
                'metadatos': {},
                'fecha_extraccion': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Extraer metadatos adicionales de meta tags
            meta_tags = soup.select('meta[name], meta[property]')
            for meta in meta_tags:
                name = meta.get('name') or meta.get('property')
                content = meta.get('content', '')
                if name and content:
                    song_info['metadatos'][name] = content

        except Exception as e:
            print(f"Error extrayendo datos de {url}: {e}")

        return song_info

    def find_new_urls(self, soup, base_url, max_new_urls=10):
        """
        Encontrar nuevas URLs relevantes para crawlear.

        Args:
            soup (BeautifulSoup): Página parseada
            base_url (str): URL base para resolver enlaces relativos
            max_new_urls (int): Máximo número de nuevas URLs a retornar

        Returns:
            list: Lista de nuevas URLs relevantes
        """
        new_urls = []

        # Buscar enlaces
        links = soup.select('a[href]')

        for link in links:
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)

                # Filtrar URLs relevantes para música
                if (self.is_relevant_url(full_url) and
                    full_url not in self.visited_urls and
                    full_url not in self.queue):

                    # Verificar que sea del mismo dominio o dominios confiables
                    if self.is_trusted_domain(full_url):
                        new_urls.append(full_url)

                        if len(new_urls) >= max_new_urls:
                            break

        return new_urls

    def is_relevant_url(self, url):
        """
        Determinar si una URL es relevante para el dominio musical.

        Args:
            url (str): URL a evaluar

        Returns:
            bool: True si es relevante
        """
        relevant_patterns = [
            '/lyrics/', '/song/', '/artist/', '/album/',
            '/track/', '/music/', '/cancion/', '/letra/',
            '/artists/', '/songs/', '/albums/'
        ]

        url_lower = url.lower()

        # Verificar patrones relevantes
        for pattern in relevant_patterns:
            if pattern in url_lower:
                return True

        return False

    def is_trusted_domain(self, url):
        """
        Verificar si el dominio es confiable para crawling.

        Args:
            url (str): URL a verificar

        Returns:
            bool: True si es un dominio confiable
        """
        trusted_domains = [
            'azlyrics.com'
        ]

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Verificar dominios confiables
            for trusted in trusted_domains:
                if trusted in domain:
                    return True

            return False
        except:
            return False

    def save_data(self, filename=None):
        """
        Guardar datos extraídos en archivo JSON.

        Args:
            filename (str, optional): Nombre del archivo. Si no se especifica,
                                    se genera automáticamente con timestamp.
        """
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"crawled_songs_{timestamp}.json"

        filepath = self.data_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.song_data, f, ensure_ascii=False, indent=2)

            print(f"✅ Datos guardados en {filepath} ({len(self.song_data)} canciones)")

        except Exception as e:
            print(f"❌ Error guardando datos: {e}")

    def get_stats(self):
        """
        Obtener estadísticas del proceso de crawling.

        Returns:
            dict: Estadísticas actuales
        """
        return {
            'paginas_visitadas': len(self.visited_urls),
            'canciones_extraidas': len(self.song_data),
            'urls_en_cola': len(self.queue),
            'urls_fallidas': len(self.failed_urls),
            'tiempo_ejecucion': time.time() - getattr(self, 'start_time', time.time())
        }

    def crawl(self):
        """
        Método principal que ejecuta el proceso de crawling.
        """
        self.logger.info("🚀 Iniciando proceso de crawling musical...")
        self.logger.info(f"📊 Límite de páginas: {self.max_pages}")
        self.logger.info(f"⏱️  Delay entre requests: {self.delay}s")
        self.logger.info(f"📁 Directorio de datos: {self.data_dir}")

        self.start_time = time.time()

        # Inicializar cola con URLs semilla
        self.queue.extend(self.seed_urls)
        self.logger.info(f"📋 Cola inicializada con {len(self.queue)} URLs")

        pages_crawled = 0
        songs_found = 0

        try:
            while self.queue and pages_crawled < self.max_pages:
                current_url = self.queue.pop(0)

                if current_url in self.visited_urls:
                    continue

                self.logger.info(f"🔍 Crawleando: {current_url}")

                # Verificar robots.txt
                if not self.check_robots_txt(current_url):
                    self.logger.warning(f"🚫 Saltando {current_url} (bloqueado por robots.txt)")
                    self.visited_urls.add(current_url)
                    continue

                try:
                    # Delay aleatorio para ser más respetuoso
                    delay = self.delay + random.uniform(0, 1)
                    time.sleep(delay)

                    # Hacer request usando la sesión
                    response = self.session.get(current_url, timeout=15)
                    response.raise_for_status()

                    # Verificar que sea HTML
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/html' not in content_type:
                        self.logger.info(f"⏭️  Saltando {current_url} (no es HTML)")
                        self.visited_urls.add(current_url)
                        continue

                    # Parsear HTML
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Extraer datos de canción
                    song_info = self.extract_song_data(soup, current_url)

                    # Solo guardar si tiene información básica
                    if song_info['titulo'] and song_info['artista']:
                        self.song_data.append(song_info)
                        songs_found += 1
                        self.logger.info(f"✅ Extraída: {song_info['titulo']} - {song_info['artista']}")
                    else:
                        self.logger.debug(f"⚠️  Página sin datos musicales: {current_url}")

                    # Encontrar nuevas URLs
                    new_urls = self.find_new_urls(soup, current_url)
                    self.queue.extend(new_urls)
                    self.logger.debug(f"➕ Agregadas {len(new_urls)} nuevas URLs a la cola")

                    # Marcar como visitada
                    self.visited_urls.add(current_url)
                    pages_crawled += 1

                    # Mostrar progreso cada 25 páginas
                    if pages_crawled % 25 == 0:
                        stats = self.get_stats()
                        self.logger.info(f"📊 Progreso: {pages_crawled} páginas, {songs_found} canciones")
                        self.logger.info(f"⏳ Tiempo: {stats['tiempo_ejecucion']:.1f}s")

                    # Guardar periódicamente cada 100 páginas
                    if pages_crawled % 100 == 0:
                        self.save_data()
                        self.logger.info("💾 Datos guardados periódicamente")

                except requests.exceptions.RequestException as e:
                    self.logger.error(f"❌ Error de red en {current_url}: {e}")
                    self.failed_urls.append(current_url)
                    continue
                except Exception as e:
                    self.logger.error(f"❌ Error procesando {current_url}: {e}")
                    self.failed_urls.append(current_url)
                    continue

        except KeyboardInterrupt:
            self.logger.info("⏹️  Crawling interrumpido por usuario")

        # Guardar datos finales
        self.save_data("crawled_songs_final.json")

        # Mostrar estadísticas finales
        final_stats = self.get_stats()
        self.logger.info("="*50)
        self.logger.info("🏁 CRAWLING COMPLETADO")
        self.logger.info("="*50)
        self.logger.info(f"📄 Páginas visitadas: {final_stats['paginas_visitadas']}")
        self.logger.info(f"🎵 Canciones extraídas: {final_stats['canciones_extraidas']}")
        self.logger.info(f"❌ URLs fallidas: {len(self.failed_urls)}")
        self.logger.info(f"⏱️  Tiempo total: {final_stats['tiempo_ejecucion']:.1f} segundos")
        self.logger.info(f"📁 Datos guardados en: {self.data_dir}")
        self.logger.info("="*50)


# Ejemplo de uso y configuración
if __name__ == "__main__":
    # URLs semilla para diferentes sitios musicales confiables
    seed_urls = [
        "https://www.azlyrics.com/",  # Permite crawling limitado
        # Agregar más URLs después de verificar robots.txt
        # "https://genius.com/",
        # "https://www.lyrics.com/",
    ]

    # Configuración del crawler
    config = {
        'max_pages': 500,  # Límite razonable para evitar sobrecargar
        'delay': 2.0,      # 2 segundos entre requests (respetuoso)
        'data_dir': 'Database/crawled_data',
        'user_agent': 'MusicResearchCrawler/1.0 (educational project)',
        'max_retries': 3
    }

    print("🎵 CRAWLER MUSICAL - PROYECTO SRI")
    print("=" * 50)
    print(f"📊 Configuración:")
    print(f"   URLs semilla: {len(seed_urls)}")
    print(f"   Páginas límite: {config['max_pages']}")
    print(f"   Delay: {config['delay']}s")
    print(f"   User-Agent: {config['user_agent']}")
    print(f"   Directorio: {config['data_dir']}")
    print()

    # Crear e iniciar crawler
    crawler = MusicCrawler(seed_urls, **config)
    crawler.crawl()

    print("\n✅ Crawling completado!")
    print("📁 Revisa los archivos en Database/crawled_data/")
    print("📋 Revisa el log en Database/crawled_data/crawler.log")

    # Opcional: Integrar con el sistema de indexación
    # print("\n🔄 Integrando con sistema de indexación...")
    # from Indexer.indexer import IndexadorTFIDF
    # indexador = IndexadorTFIDF("Database", "Database/lyrics")
    # # Aquí iría el código para integrar los datos crawleados