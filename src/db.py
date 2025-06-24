import os
import re
import json
import logging
from typing import List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from fuzzywuzzy import process, fuzz
import config

logger = logging.getLogger(__name__)

@dataclass
class Card:
    name: str
    attribute: str
    level: str
    card_type: str
    atk: str
    defense: str
    description: str
    rarity: str

    def to_html(self, query: str = None) -> str:
        name = self.name
        attribute = self.attribute
        level = self.level
        card_type = self.card_type
        atk = self.atk
        defense = self.defense
        description = self.description
        rarity = self.rarity
        
        if query:
            highlight_terms = self._extract_highlight_terms(query)
            name = self._highlight_text(name, highlight_terms)
            attribute = self._highlight_text(attribute, highlight_terms)
            level = self._highlight_text(level, highlight_terms)
            card_type = self._highlight_text(card_type, highlight_terms)
            atk = self._highlight_text(atk, highlight_terms)
            defense = self._highlight_text(defense, highlight_terms)
            description = self._highlight_text(description, highlight_terms)
            rarity = self._highlight_text(rarity, highlight_terms)

        return f"""
        <div style="border: 2px solid #d4af37; border-radius: 10px; padding: 15px; margin: 10px 0; background: linear-gradient(135deg, #f5f5dc, #fffacd);">
            <h2 style="color: #8b4513; margin: 0 0 10px 0; border-bottom: 2px solid #d4af37; padding-bottom: 5px;">
                {name} <span style="font-size: 14px; color: #666;">({rarity})</span>
            </h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0;">
                <div><strong>Attribute:</strong> {attribute}</div>
                <div><strong>Level/Rank:</strong> {level}</div>
                <div><strong>Type:</strong> {card_type}</div>
                <div><strong>ATK/DEF:</strong> {atk}/{defense}</div>
            </div>
            <div style="margin-top: 15px;">
                <strong>Description:</strong>
                <p style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 5px; margin: 5px 0; line-height: 1.4;">
                    {description}
                </p>
            </div>
        </div>
        """
    
    def _extract_highlight_terms(self, query: str) -> Set[str]:
        terms = set()
        words = re.findall(r'\b\w+\b', query.lower())
        
        for word in words:
            if len(word) >= 2:
                terms.add(word)
        
        return terms
    
    def _highlight_text(self, text: str, terms: Set[str]) -> str:
        if not terms or not text:
            return text
            
        highlighted_text = text
        
        for term in terms:
            # Use word boundaries to match whole words and partial matches
            pattern = re.compile(f'({re.escape(term)})', re.IGNORECASE)
            highlighted_text = pattern.sub(
                r'<mark style="background-color: #ffff00; padding: 1px 3px; border-radius: 3px; font-weight: bold;">\1</mark>',
                highlighted_text
            )
        
        return highlighted_text

class CardDatabase:
    def __init__(self):
        self.cards: List[Card] = []
        self.search_corpus = {}
        self.cache_file = config.CACHE_FILE

    def add_card(self, card: Card):
        self.cards.append(card)
        searchable_text = f"{card.name} {card.description} {card.card_type} {card.attribute}"
        if card.atk:
            searchable_text += f"ATK: {card.atk}"
        if card.defense:
            searchable_text += f"DEF: {card.defense}"
        self.search_corpus[searchable_text] = card

    def find_best_match(self, query: str) -> Optional[Tuple[Card, int, str]]:
        if not self.cards:
            return None
        
        choices = list(self.search_corpus.keys())
        best_match = process.extractOne(query, choices, scorer=fuzz.token_set_ratio)
        
        if best_match and best_match[1] >= config.FUZZY_SCORE_CUTOFF_SINGLE:
            matched_string, similarity_score = best_match
            matched_card = self.search_corpus[matched_string]
            return matched_card, similarity_score, query
            
        return None

    def find_multiple_matches(self, query: str) -> List[Tuple[Card, int, str]]:
        if not self.cards:
            return []
        
        required_keywords = []
        clean_query = query

        found_hash_matches = re.findall(r'#([^#]+)#', query, re.IGNORECASE)
        for match in found_hash_matches:
            required_keywords.append(match.strip().lower())
            clean_query = clean_query.replace(f"#{match}#", "", 1).strip() # Use count=1 to replace only first occurrence
        
        logger.info(required_keywords)

        clean_query = re.sub(r'\s+', ' ', clean_query).strip()
        
        choices = list(self.search_corpus.keys())
        matches = process.extract(clean_query, choices, limit=config.MULTI_SEARCH_LIMIT, scorer=fuzz.token_set_ratio)
        
        filtered_results = []
        for matched_string, similarity_score in matches:
            if similarity_score >= config.FUZZY_SCORE_CUTOFF_MULTI:
                matched_card = self.search_corpus[matched_string]
                
                card_text_for_check = f"{matched_card.name} {matched_card.description} {matched_card.card_type} {matched_card.attribute}".lower()

                if matched_card.atk:
                    card_text_for_check += f"ATK: {matched_card.atk}"
                if matched_card.defense:
                    card_text_for_check += f"DEF: {matched_card.defense}"
                
                all_required_found = True
                if len(required_keywords) > 0:
                    for req_kw in required_keywords:
                        if req_kw not in card_text_for_check:
                            all_required_found = False
                            break
                
                if all_required_found:
                    filtered_results.append((matched_card, similarity_score, query))

        return filtered_results

    def save_cache(self):
        try:
            cache_data = [asdict(card) for card in self.cards]
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Saved {len(self.cards)} cards to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def load_cache(self) -> bool:
        try:
            if not os.path.exists(self.cache_file):
                return False
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            for card_data in cache_data:
                card = Card(**card_data)
                self.add_card(card)
            
            logger.info(f"Loaded {len(self.cards)} cards from cache")
            return True
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return False