# scraper.py

import requests
import json
import logging
from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PyQt5.QtCore import QThread, pyqtSignal
import re

# Import our own modules
from db import Card, CardDatabase
import config

logger = logging.getLogger(__name__)

def scrape_pack_urls(base_url: str, output_filename: str):
    pack_urls = []
    try:
        headers = {'User-Agent': config.USER_AGENT}
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for pack_div in soup.select('div.pack.pack_en'):
            pack_name_tag = pack_div.find('strong')
            hidden_input = pack_div.find('input', class_='link_value')
            if pack_name_tag and hidden_input:
                full_url = urljoin(base_url, hidden_input.get('value'))
                pack_urls.append({"name": pack_name_tag.text.strip(), "url": full_url})
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(pack_urls, f, indent=4)
            
        logger.info(f"Scraped {len(pack_urls)} pack URLs")
        
    except Exception as e:
        logger.error(f"Failed to scrape pack URLs: {e}")
        raise

class ScraperThread(QThread):
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str)
    finished = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.db = CardDatabase()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': config.USER_AGENT})

    def run(self):
        try:
            if self.db.load_cache():
                self.status_update.emit("Loaded cards from cache!")
                self.progress.emit(100)
                self.finished.emit(self.db)
                return

            self.status_update.emit("Loading pack URLs...")
            with open(config.PACK_URLS_FILE, 'r', encoding='utf-8') as f:
                packs_to_scrape = json.load(f)
            
            if config.MAX_PACKS_TO_SCRAPE:
                packs_to_scrape = packs_to_scrape[:config.MAX_PACKS_TO_SCRAPE]
            
            total_packs = len(packs_to_scrape)
            cards_scraped = 0
            
            for i, pack in enumerate(packs_to_scrape):
                self.status_update.emit(f"Scraping pack: {pack['name']}")
                pack_cards = self.scrape_cards_from_url(pack['url'])
                cards_scraped += pack_cards
                
                progress = int(((i + 1) / total_packs) * 100)
                self.progress.emit(progress)
                self.msleep(100)
            
            self.db.save_cache()
            self.status_update.emit(f"Scraping complete! Found {cards_scraped} cards from {total_packs} packs.")
            self.finished.emit(self.db)
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            self.error_occurred.emit(str(e))
            self.finished.emit(None)
            
    def scrape_cards_from_url(self, url: str) -> int:
        cards_found = 0
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try different possible container IDs/classes
            card_list = (soup.find('div', id='card_list') or 
                        soup.find('div', class_='t_body') or
                        soup.find('div', class_='card_list'))
            
            if not card_list:
                logger.warning(f"No card list found for URL: {url}")
                return cards_found

            # Look for card rows with multiple possible selectors
            card_rows = (card_list.select('.t_row') or 
                        card_list.select('.c_simple') or
                        card_list.select('[class*="row"]'))

            for card_div in card_rows:
                try:
                    card = self.extract_card_info(card_div)
                    if card:
                        self.db.add_card(card)
                        cards_found += 1
                except Exception as e:
                    logger.warning(f"Failed to extract card info: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to scrape URL {url}: {e}")
        return cards_found

    def extract_card_info(self, card_div) -> Optional[Card]:
        # Extract card name with multiple fallback selectors
        name = self.extract_card_name(card_div)
        if not name:
            return None
            
        # Extract attribute with icon detection
        attribute = self.extract_attribute(card_div)
        
        # Extract level/rank with better parsing
        level = self.extract_level_rank(card_div)
        
        # Extract card type/species with better parsing
        card_type = self.extract_card_type(card_div)
        
        # Extract ATK/DEF with better number parsing
        atk, defense = self.extract_atk_def(card_div)
        
        # Extract description with HTML cleaning
        description = self.extract_description(card_div)
        
        # Extract rarity with multiple selectors
        rarity = self.extract_rarity(card_div)
        
        return Card(name, attribute, level, card_type, atk, defense, description, rarity)

    def extract_card_name(self, card_div):
        """Extract card name with multiple selectors"""
        selectors = [
            'span.card_name',
            '.card_name_flex_1',
            '.card_name',
            'a[title]',
            '.t_title a'
        ]
        
        for selector in selectors:
            element = card_div.select_one(selector)
            if element:
                name = element.get('title') or element.text.strip()
                if name:
                    return name
        return None

    def extract_attribute(self, card_div):
        """Extract attribute with icon detection"""
        # Check for attribute icons first
        attribute_icon = card_div.select_one('img[src*="attribute"], .icon_img')
        if attribute_icon:
            src = attribute_icon.get('src', '')
            alt = attribute_icon.get('alt', '').lower()
            title = attribute_icon.get('title', '').lower()
            
            # Check src, alt, and title for attribute info
            for attr_text in [src.lower(), alt, title]:
                if 'light' in attr_text:
                    return 'LIGHT'
                elif 'dark' in attr_text:
                    return 'DARK'
                elif 'fire' in attr_text:
                    return 'FIRE'
                elif 'water' in attr_text:
                    return 'WATER'
                elif 'earth' in attr_text:
                    return 'EARTH'
                elif 'wind' in attr_text:
                    return 'WIND'
                elif 'divine' in attr_text:
                    return 'DIVINE'
                elif 'spell' in attr_text:
                    return 'SPELL'
                elif 'trap' in attr_text:
                    return 'TRAP'
        
        # Check for spell/trap indicators in the card structure
        if card_div.select_one('.icon_img[title*="Spell"], .icon_img[alt*="Spell"]'):
            return 'SPELL'
        if card_div.select_one('.icon_img[title*="Trap"], .icon_img[alt*="Trap"]'):
            return 'TRAP'
        
        # Fallback to text extraction
        return self.safe_extract_text(card_div, 'div', 'box_card_attribute', "N/A")

    def extract_level_rank(self, card_div):
        """Extract level/rank with better parsing"""
        level_element = card_div.select_one('.box_card_level_rank span, .item_box_value')
        if level_element:
            level_text = level_element.text.strip()
            # Extract numeric value
            level_match = re.search(r'(\d+)', level_text)
            if level_match:
                return level_match.group(1)
        return "N/A"

    def extract_card_type(self, card_div):
        """Extract card type with better parsing for spell/trap subtypes"""
        type_selectors = [
            '.card_info_species_and_other_item span',
            '.species',
            '.card_type', 
            'div.item_box_title + .item_box_value',
            '.item_box_value',
            'span[title*="Spell"]',
            'span[title*="Trap"]',
            '.box_card_species span',
            '.card_info span'
        ]
        
        # First, try to find the card type from various selectors
        for selector in type_selectors:
            element = card_div.select_one(selector)
            if element:
                card_type = element.text.strip()
                if card_type and card_type != "N/A":
                    # Clean up the card type text
                    card_type = ' '.join(card_type.split())
                    
                    # If it's a spell or trap, check for subtypes
                    if 'spell' in card_type.lower() or 'trap' in card_type.lower():
                        return card_type
                    
                    # For monster cards, return as is
                    if card_type not in ["", "N/A", "-"]:
                        return card_type
        
        # Special handling for spell/trap cards - look in the card structure
        # Check if this is a spell card by looking for spell indicators
        spell_indicators = card_div.select('.icon_img[title*="Spell"], .icon_img[alt*="Spell"], img[src*="spell"]')
        if spell_indicators:
            # Look for spell subtype in nearby text
            for element in card_div.select('*'):
                text = element.get_text(strip=True).lower()
                if 'continuous' in text and 'spell' in text:
                    return "Continuous Spell"
                elif 'quick-play' in text and 'spell' in text:
                    return "Quick-Play Spell"
                elif 'field' in text and 'spell' in text:
                    return "Field Spell"
                elif 'equip' in text and 'spell' in text:
                    return "Equip Spell"
                elif 'ritual' in text and 'spell' in text:
                    return "Ritual Spell"
            
            return "Normal Spell"
        
        trap_indicators = card_div.select('.icon_img[title*="Trap"], .icon_img[alt*="Trap"], img[src*="trap"]')
        if trap_indicators:
            for element in card_div.select('*'):
                text = element.get_text(strip=True).lower()
                if 'continuous' in text and 'trap' in text:
                    return "Continuous Trap"
                elif 'counter' in text and 'trap' in text:
                    return "Counter Trap"
            
            return "Normal Trap"
        
        # Look more broadly in the card div for type information
        all_text = card_div.get_text(strip=True).lower()
        
        # Check for specific spell types in the full text
        if 'continuous spell' in all_text:
            return "Continuous Spell"
        elif 'quick-play spell' in all_text:
            return "Quick-Play Spell"
        elif 'field spell' in all_text:
            return "Field Spell"
        elif 'equip spell' in all_text:
            return "Equip Spell"
        elif 'ritual spell' in all_text:
            return "Ritual Spell"
        elif 'normal spell' in all_text:
            return "Normal Spell"
        
        # Check for specific trap types
        elif 'continuous trap' in all_text:
            return "Continuous Trap"
        elif 'counter trap' in all_text:
            return "Counter Trap"
        elif 'normal trap' in all_text:
            return "Normal Trap"
        
        return "N/A"

    def extract_atk_def(self, card_div):
        """Extract ATK/DEF with better number parsing"""
        atk, defense = "N/A", "N/A"
        
        # Look for ATK/DEF container
        atkdef_container = card_div.select_one('.atkdef, .item_box')
        if atkdef_container:
            # Extract ATK
            atk_element = atkdef_container.select_one('.atk_power span, .item_box_value')
            if atk_element:
                atk_text = atk_element.text.strip()
                # Clean up the text and extract numbers
                atk_match = re.search(r'(\d+|[?])', atk_text)
                if atk_match:
                    atk = atk_match.group(1)
            
            # Extract DEF
            def_element = atkdef_container.select_one('.def_power span, .item_box_value')
            if def_element:
                def_text = def_element.text.strip()
                def_match = re.search(r'(\d+|[?])', def_text)
                if def_match:
                    defense = def_match.group(1)
        
        return atk, defense

    def extract_description(self, card_div):
        """Extract card description with HTML cleaning"""
        desc_selectors = [
            'dd.box_card_text',
            '.card_text',
            '.text_title'
        ]
        
        for selector in desc_selectors:
            element = card_div.select_one(selector)
            if element:
                # Clean HTML and normalize whitespace
                desc_text = element.get_text(separator=' ', strip=True)
                if desc_text and desc_text != "No Description":
                    return desc_text
        
        return "No Description"

    def extract_rarity(self, card_div):
        """Extract rarity with multiple selectors"""
        rarity_selectors = [
            '.rarity span',
            '.rarity',
            '.star_shining',
            '.star_gold',
            '.star_silver',
            '.icon_rarity'
        ]
        
        # Check for rarity text in various elements
        for element in card_div.select('*'):
            text = element.get_text(strip=True)
            if text in ['Ultra Rare', 'Super Rare', 'Secret Rare', 'Common', 'Rare', 
                       'Ghost Rare', 'Ultimate Rare', 'Parallel Rare', 'Gold Rare']:
                return text
        
        for selector in rarity_selectors:
            element = card_div.select_one(selector)
            if element:
                rarity = element.text.strip()
                if rarity:
                    return rarity
        
        return "N/A"

    def extract_card_number(self, card_div):
        """Extract card number/ID"""
        number_element = card_div.select_one('.card_number, .number, [class*="number"]')
        if number_element:
            return number_element.text.strip()
        return "N/A"

    def extract_pack_info(self, card_div):
        """Extract pack information"""
        pack_element = card_div.select_one('.pack_info, .set_info, [class*="pack"]')
        if pack_element:
            return pack_element.text.strip()
        return "N/A"

    def safe_extract_text(self, parent, tag, class_name, default, nested_span=False):
        """Safe text extraction with error handling"""
        try:
            element = parent.find(tag, class_=class_name)
            if element:
                if nested_span and element.find('span'):
                    text = element.find('span').text
                else:
                    text = element.text
                return ' '.join(text.split()) if text else default
        except Exception as e:
            logger.debug(f"Error extracting text: {e}")
        return default