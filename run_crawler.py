"""
Script para ejecutar el Crawler + Scraper fácilmente.
Ejecutar desde el directorio raíz del proyecto.
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from Crawler.crawler import MusicCrawler


def main():
    """Ejecutar el crawler con configuración predefinida."""
    
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

    print("\n" + "="*60)
    print("🎵 CRAWLER MUSICAL + SCRAPER - PROYECTO SRI")
    print("="*60)
    print(f"\n📊 Configuración:")
    print(f"   URLs semilla: {len(seed_urls)}")
    print(f"   Páginas límite: {config['max_pages']}")
    print(f"   Delay: {config['delay']}s")
    print(f"   User-Agent: {config['user_agent']}")
    print(f"   Directorio: {config['data_dir']}")
    print(f"\n🔗 URLs a crawlear:")
    for url in seed_urls:
        print(f"   - {url}")
    print()

    # Crear e iniciar crawler
    crawler = MusicCrawler(seed_urls, **config)
    crawler.crawl()

    print("\n" + "="*60)
    print("✅ CRAWLING COMPLETADO")
    print("="*60)
    print(f"📁 Datos guardados en: Database/crawled_data/")
    print(f"📋 Log en: Database/crawled_data/crawler.log")
    print(f"\n🔄 Próximo paso: python merge_crawler_data.py")
    print()


if __name__ == "__main__":
    main()
