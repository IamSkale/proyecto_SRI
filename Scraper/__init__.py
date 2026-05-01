"""
Módulo de Scraping para Sistema de Búsqueda Musical
"""

from .scraper import (
    MusicScraper,
    GeniusScraper,
    AZLyricsScraper,
    MusixmatchScraper,
    LastFMScraper,
    MusicBrainzScraper,
    AllMusicScraper,
    ScrapeadorGeneral,
    FactoryScraper,
    extraer_datos
)

__all__ = [
    'MusicScraper',
    'GeniusScraper',
    'AZLyricsScraper',
    'MusixmatchScraper',
    'LastFMScraper',
    'MusicBrainzScraper',
    'AllMusicScraper',
    'ScrapeadorGeneral',
    'FactoryScraper',
    'extraer_datos'
]
