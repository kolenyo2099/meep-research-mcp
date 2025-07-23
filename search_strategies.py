"""
Simple Research Query Translator
Converts natural language research requests into precise Google search operators.
Designed for MCP integration with focus on user-controlled source restrictions.
"""

from typing import Dict, List, Any, Optional, Tuple
import re
from dataclasses import dataclass

@dataclass
class SearchQuery:
    """Simple container for a search query and its purpose"""
    query: str
    purpose: str
    operator_breakdown: Dict[str, str]

class QueryTranslator:
    """
    Simple translator that converts natural language research requests 
    into precise Google search operators with user-specified restrictions.
    """
    
    def __init__(self):
        # Core Google operators
        self.operators = {
            'exact_phrase': lambda text: f'"{text}"',
            'site_restrict': lambda domain: f'site:{domain}',
            'exclude_site': lambda domain: f'-site:{domain}',
            'filetype': lambda ext: f'filetype:{ext}',
            'intitle': lambda text: f'intitle:"{text}"',
            'inurl': lambda text: f'inurl:{text}',
            'intext': lambda text: f'intext:"{text}"',
            'proximity': lambda term1, term2, distance: f'"{term1}" AROUND({distance}) "{term2}"',
            'date_after': lambda date: f'after:{date}',
            'date_before': lambda date: f'before:{date}',
            'exclude_term': lambda term: f'-{term}',
            'wildcard': lambda phrase: f'"{phrase}"',  # phrase should contain *
            'or_operator': lambda terms: f'({" OR ".join(terms)})',
            'and_operator': lambda terms: f'{" ".join(terms)}'
        }
        
        # Common patterns in research requests
        self.patterns = {
            'proximity_request': re.compile(r'(.*?)\s+(mentioned|described|discussed|appear)\s+(close|together|near)\s+(.*?)'),
            'site_restriction': re.compile(r'(on|in|from)\s+([\w\.-]+\.\w+)'),
            'content_location': re.compile(r'in\s+(title|url|text|paragraphs?)'),
            'exclusion_request': re.compile(r'(but not|exclude|without|except)\s+(.*?)'),
            'time_restriction': re.compile(r'(after|since|before|until)\s+(\d{4}(?:/\d{1,2}(?:/\d{1,2})?)?)')
        }

    def translate_request(self, request: str, source_restrictions: Optional[str] = None) -> SearchQuery:
        """
        Main method: translate natural language request into Google search operators.
        
        Args:
            request: Natural language research question
            source_restrictions: User-specified search operators to constrain sources
        
        Returns:
            SearchQuery object with the translated query and breakdown
        """
        # Clean and prepare the request
        request = request.strip()
        
        # Extract key components
        entities = self._extract_entities(request)
        relationships = self._detect_relationships(request)
        restrictions = self._parse_restrictions(request)
        content_focus = self._detect_content_focus(request)
        
        # Build the search query
        query_parts = []
        operator_breakdown = {}
        
        # Handle entity relationships (proximity, exact phrases, etc.)
        if relationships['proximity'] and len(entities) >= 2:
            proximity_part = self._build_proximity_query(entities, relationships['proximity'])
            query_parts.append(proximity_part)
            operator_breakdown['proximity'] = proximity_part
        elif entities:
            # Use exact phrases for entities
            exact_phrases = [self.operators['exact_phrase'](entity) for entity in entities]
            query_parts.extend(exact_phrases)
            operator_breakdown['entities'] = exact_phrases
        
        # Apply content location restrictions
        if content_focus:
            content_operator = self._apply_content_focus(content_focus, query_parts[0] if query_parts else request)
            query_parts = [content_operator]
            operator_breakdown['content_focus'] = content_operator
        
        # Apply user-specified source restrictions first (highest priority)
        if source_restrictions:
            query_parts.append(source_restrictions)
            operator_breakdown['user_restrictions'] = source_restrictions
        
        # Apply parsed restrictions from the request
        if restrictions['site']:
            site_op = self.operators['site_restrict'](restrictions['site'])
            query_parts.append(site_op)
            operator_breakdown['site_restriction'] = site_op
        
        if restrictions['exclude_sites']:
            exclude_ops = [self.operators['exclude_site'](site) for site in restrictions['exclude_sites']]
            query_parts.extend(exclude_ops)
            operator_breakdown['exclude_sites'] = exclude_ops
        
        if restrictions['filetype']:
            filetype_op = self.operators['filetype'](restrictions['filetype'])
            query_parts.append(filetype_op)
            operator_breakdown['filetype'] = filetype_op
        
        if restrictions['date_after']:
            date_op = self.operators['date_after'](restrictions['date_after'])
            query_parts.append(date_op)
            operator_breakdown['date_restriction'] = date_op
        
        if restrictions['exclude_terms']:
            exclude_ops = [self.operators['exclude_term'](term) for term in restrictions['exclude_terms']]
            query_parts.extend(exclude_ops)
            operator_breakdown['exclude_terms'] = exclude_ops
        
        # Combine all parts
        final_query = ' '.join(query_parts)
        
        return SearchQuery(
            query=final_query,
            purpose=self._generate_purpose(request),
            operator_breakdown=operator_breakdown
        )

    def _extract_entities(self, request: str) -> List[str]:
        """Extract named entities (people, places, organizations) from request."""
        entities = []
        
        # Extract quoted terms
        quoted = re.findall(r'"([^"]*)"', request)
        entities.extend(quoted)
        
        # Extract capitalized terms (potential proper nouns)
        # But be smart about it - don't capture sentence starters
        words = request.split()
        for i, word in enumerate(words):
            if word[0].isupper() and i > 0:  # Not sentence starter
                # Look for multi-word proper nouns
                entity_parts = [word]
                j = i + 1
                while j < len(words) and words[j][0].isupper():
                    entity_parts.append(words[j])
                    j += 1
                
                if len(entity_parts) > 0:
                    entities.append(' '.join(entity_parts))
        
        # Remove duplicates and clean
        entities = list(set(entities))
        entities = [e for e in entities if len(e.strip()) > 1]
        
        return entities

    def _detect_relationships(self, request: str) -> Dict[str, Any]:
        """Detect relationships between entities (proximity, co-occurrence, etc.)."""
        relationships = {
            'proximity': None,
            'co_occurrence': False,
            'sequence': False
        }
        
        # Check for proximity indicators
        proximity_indicators = ['close', 'together', 'near', 'mentioned together', 'same paragraph', 'same sentence']
        for indicator in proximity_indicators:
            if indicator in request.lower():
                relationships['proximity'] = 3  # Default proximity
                break
        
        # Look for specific distance indicators
        distance_match = re.search(r'within (\d+) words?', request.lower())
        if distance_match:
            relationships['proximity'] = int(distance_match.group(1))
        
        return relationships

    def _parse_restrictions(self, request: str) -> Dict[str, Any]:
        """Parse various restrictions from the request."""
        restrictions = {
            'site': None,
            'exclude_sites': [],
            'filetype': None,
            'date_after': None,
            'date_before': None,
            'exclude_terms': []
        }
        
        # Site restrictions
        site_match = self.patterns['site_restriction'].search(request)
        if site_match:
            restrictions['site'] = site_match.group(2)
        
        # File type restrictions
        if 'pdf' in request.lower():
            restrictions['filetype'] = 'pdf'
        elif 'document' in request.lower():
            restrictions['filetype'] = 'doc'
        elif 'spreadsheet' in request.lower():
            restrictions['filetype'] = 'xls'
        
        # Time restrictions
        time_match = self.patterns['time_restriction'].search(request)
        if time_match:
            direction, date = time_match.groups()
            if direction.lower() in ['after', 'since']:
                restrictions['date_after'] = date
            else:
                restrictions['date_before'] = date
        
        # Exclusion terms
        exclude_match = self.patterns['exclusion_request'].search(request)
        if exclude_match:
            exclude_text = exclude_match.group(2)
            # Simple split on common separators
            exclude_terms = re.split(r'[,\s]+', exclude_text.strip())
            restrictions['exclude_terms'] = [term for term in exclude_terms if term]
        
        return restrictions

    def _detect_content_focus(self, request: str) -> Optional[str]:
        """Detect if user wants to focus on specific content areas."""
        content_match = self.patterns['content_location'].search(request.lower())
        if content_match:
            location = content_match.group(1)
            if location in ['title']:
                return 'intitle'
            elif location in ['url']:
                return 'inurl'
            elif location in ['text', 'paragraph', 'paragraphs']:
                return 'intext'
        
        return None

    def _apply_content_focus(self, focus_type: str, base_query: str) -> str:
        """Apply content focus operators."""
        if focus_type == 'intitle':
            return self.operators['intitle'](base_query.replace('"', ''))
        elif focus_type == 'inurl':
            return self.operators['inurl'](base_query.replace('"', ''))
        elif focus_type == 'intext':
            return self.operators['intext'](base_query.replace('"', ''))
        
        return base_query

    def _build_proximity_query(self, entities: List[str], distance: int) -> str:
        """Build proximity query for multiple entities."""
        if len(entities) < 2:
            return ' '.join([self.operators['exact_phrase'](e) for e in entities])
        
        # For multiple entities, chain them with AROUND operators
        if len(entities) == 2:
            return self.operators['proximity'](entities[0], entities[1], distance)
        
        # For more than 2 entities, build a chain
        query_parts = []
        for i in range(len(entities) - 1):
            proximity_part = self.operators['proximity'](entities[i], entities[i + 1], distance)
            query_parts.append(proximity_part)
        
        return ' '.join(query_parts)

    def _generate_purpose(self, request: str) -> str:
        """Generate a clear purpose statement for the search."""
        return f"Research query: {request[:100]}{'...' if len(request) > 100 else ''}"

    def create_multiple_variations(self, request: str, source_restrictions: Optional[str] = None) -> List[SearchQuery]:
        """
        Create multiple search variations for comprehensive research.
        This is MCP-friendly as it returns multiple independent queries.
        """
        base_query = self.translate_request(request, source_restrictions)
        variations = [base_query]
        
        # Create variations with different operator combinations
        entities = self._extract_entities(request)
        
        if len(entities) >= 2:
            # Variation 1: Exact phrase combination
            combined_phrase = ' '.join(entities)
            exact_query = SearchQuery(
                query=f'"{combined_phrase}" {source_restrictions or ""}',
                purpose=f"Exact phrase search: {combined_phrase}",
                operator_breakdown={'exact_phrase': f'"{combined_phrase}"'}
            )
            variations.append(exact_query)
            
            # Variation 2: OR combination
            or_terms = [f'"{entity}"' for entity in entities]
            or_query = SearchQuery(
                query=f'({" OR ".join(or_terms)}) {source_restrictions or ""}',
                purpose=f"Any of these entities: {', '.join(entities)}",
                operator_breakdown={'or_terms': or_terms}
            )
            variations.append(or_query)
        
        return variations

# Example usage functions
def demonstrate_translation():
    """Demonstrate the translation capabilities."""
    translator = QueryTranslator()
    
    # Example requests
    examples = [
        {
            "request": "how are General Smith and General Jones described when mentioned close together on army.mil",
            "restrictions": "site:army.mil"
        },
        {
            "request": "find documents about climate change in NASA reports but exclude press releases",
            "restrictions": "site:nasa.gov filetype:pdf"
        },
        {
            "request": "research about Facebook scams targeting Netherlands users",
            "restrictions": None
        }
    ]
    
    for example in examples:
        print(f"REQUEST: {example['request']}")
        print(f"USER RESTRICTIONS: {example['restrictions']}")
        
        query = translator.translate_request(example['request'], example['restrictions'])
        
        print(f"TRANSLATED QUERY: {query.query}")
        print(f"PURPOSE: {query.purpose}")
        print("OPERATOR BREAKDOWN:")
        for op_type, op_value in query.operator_breakdown.items():
            print(f"  {op_type}: {op_value}")
        print("-" * 50)

# MCP-compatible functions
def translate_research_query(request: str, source_restrictions: str = None) -> Dict[str, Any]:
    """
    MCP-compatible function to translate a research request.
    
    Args:
        request: Natural language research question
        source_restrictions: Optional Google search operators to restrict sources
    
    Returns:
        Dictionary with translated query and metadata
    """
    translator = QueryTranslator()
    result = translator.translate_request(request, source_restrictions)
    
    return {
        "query": result.query,
        "purpose": result.purpose,
        "operator_breakdown": result.operator_breakdown,
        "original_request": request,
        "restrictions_applied": source_restrictions
    }

def create_research_variations(request: str, source_restrictions: str = None) -> List[Dict[str, Any]]:
    """
    MCP-compatible function to create multiple search variations.
    
    Args:
        request: Natural language research question  
        source_restrictions: Optional Google search operators to restrict sources
    
    Returns:
        List of search query variations
    """
    translator = QueryTranslator()
    variations = translator.create_multiple_variations(request, source_restrictions)
    
    return [
        {
            "query": var.query,
            "purpose": var.purpose,
            "operator_breakdown": var.operator_breakdown
        }
        for var in variations
    ]

if __name__ == "__main__":
    demonstrate_translation() 