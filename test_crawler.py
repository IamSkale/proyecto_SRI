#!/usr/bin/env python3
"""
Script de prueba para el Crawler Musical
Ejecuta una prueba limitada del crawler para verificar funcionamiento
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from Crawler.crawler import MusicCrawler

def test_crawler():
    """Función de prueba del crawler con configuración limitada"""

    print("🧪 PRUEBA DEL CRAWLER MUSICAL")
    print("=" * 40)

    # URLs de prueba (sitios que permiten crawling limitado)
    test_urls = [
        "https://www.azlyrics.com/",  # Sitio de letras que permite crawling
    ]

    # Configuración de prueba limitada
    config = {
        'max_pages': 5,     # Solo 5 páginas para prueba
        'delay': 3.0,       # Delay más largo para ser respetuoso
        'data_dir': 'Database/test_data'
    }

    print(f"📊 Configuración de prueba:")
    print(f"   URLs semilla: {len(test_urls)}")
    print(f"   Páginas límite: {config['max_pages']}")
    print(f"   Delay: {config['delay']}s")
    print(f"   Directorio: {config['data_dir']}")
    print()

    # Crear crawler
    crawler = MusicCrawler(test_urls, **config)

    # Ejecutar crawling de prueba
    try:
        crawler.crawl()
        print("\n✅ Prueba completada exitosamente!")

    except KeyboardInterrupt:
        print("\n⏹️  Prueba interrumpida por usuario")
    except Exception as e:
        print(f"\n❌ Error en la prueba: {e}")
        return False

    return True

if __name__ == "__main__":
    success = test_crawler()
    if success:
        print("\n🎉 El crawler está listo para usar en producción!")
        print("💡 Para crawling completo, aumenta max_pages y agrega más URLs semilla")
    else:
        print("\n⚠️  Revisa la configuración y dependencias antes de usar")