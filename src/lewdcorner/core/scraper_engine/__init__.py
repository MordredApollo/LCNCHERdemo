"""Scraper engine for extracting game data"""

from lewdcorner.core.scraper_engine.game_scraper import GameScraper
from lewdcorner.core.scraper_engine.forum_parser import ForumParser
from lewdcorner.core.scraper_engine.metadata_extractor import MetadataExtractor
from lewdcorner.core.scraper_engine.breadcrumb_parser import BreadcrumbParser

__all__ = ["GameScraper", "ForumParser", "MetadataExtractor", "BreadcrumbParser"]
