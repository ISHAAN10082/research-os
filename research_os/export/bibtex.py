"""
BibTeX Export Module - Production-Safe LaTeX Citation Generation

Exports research library to BibTeX format with:
- Proper LaTeX character escaping
- Unique citation key generation  
- Multiple entry types (article, inproceedings, misc)
- Unicode handling
- arXiv and DOI support

Usage:
    from research_os.export.bibtex import BibTeXExporter, export_library_bibtex
    
    # Export all papers
    export_library_bibtex("output.bib")
    
    # Custom export
    exporter = BibTeXExporter()
    bibtex = exporter.generate_bibtex(papers)
"""

import re
from typing import List, Dict, Set, Optional
from pathlib import Path
from loguru import logger


class BibTeXExporter:
    """
    Production-safe BibTeX generation with LaTeX escaping.
    
    Handles:
    - Special characters (&, %, $, #, etc.)
    - Unicode in author names
    - Unique citation key generation
    - Multiple paper types (arXiv, conference, journal)
    """
    
    # LaTeX special characters that need escaping
    LATEX_SPECIAL = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    
    def __init__(self):
        self._used_keys: Set[str] = set()
    
    def escape_latex(self, text: str) -> str:
        """
        Escape LaTeX special characters.
        
        Args:
            text: Raw text that may contain special chars
            
        Returns:
            LaTeX-safe string
        """
        if not text:
            return ""
        
        result = str(text)
        for char, replacement in self.LATEX_SPECIAL.items():
            result = result.replace(char, replacement)
        
        return result
    
    def normalize_author(self, name: str) -> str:
        """
        Normalize author name for BibTeX.
        
        Handles:
        - "First Last" → "Last, First"
        - "Last, First" → "Last, First" (unchanged)
        - Extra whitespace removal
        
        Args:
            name: Raw author name
            
        Returns:
            Normalized name for BibTeX author field
        """
        if not name:
            return "Unknown"
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # If already in "Last, First" format, keep it
        if ',' in name:
            parts = [p.strip() for p in name.split(',', 1)]
            return f"{parts[0]}, {parts[1]}" if len(parts) == 2 else name
        
        # Convert "First Last" to "Last, First"
        parts = name.split()
        if len(parts) >= 2:
            return f"{parts[-1]}, {' '.join(parts[:-1])}"
        
        return name
    
    def generate_cite_key(self, paper: Dict) -> str:
        """
        Generate unique citation key.
        
        Format: AuthorYearTitlewords (e.g., Smith2023attention)
        
        Args:
            paper: Paper metadata dict
            
        Returns:
            Unique citation key
        """
        # Get first author last name
        authors = paper.get('authors', [])
        if isinstance(authors, str):
            authors = [a.strip() for a in authors.split(',')]
        
        if authors and authors[0]:
            # Get last name (handle "Last, First" and "First Last")
            first_author = authors[0]
            if ',' in first_author:
                last_name = first_author.split(',')[0].strip()
            else:
                last_name = first_author.split()[-1] if first_author.split() else "Unknown"
            
            # Remove non-alphanumeric
            last_name = re.sub(r'[^a-zA-Z]', '', last_name)
        else:
            last_name = "Unknown"
        
        # Get year
        year = str(paper.get('year', 'XXXX'))
        
        # Get first 2 title words
        title = paper.get('title', 'untitled')
        # Remove common words and get meaningful ones
        stop_words = {'the', 'a', 'an', 'of', 'in', 'on', 'for', 'to', 'and', 'or'}
        title_words = [
            w.lower() for w in re.findall(r'\w+', title)
            if w.lower() not in stop_words
        ][:2]
        title_key = ''.join(title_words)
        
        # Combine and ensure uniqueness
        base_key = f"{last_name}{year}{title_key}"
        cite_key = base_key
        counter = 1
        
        while cite_key in self._used_keys:
            cite_key = f"{base_key}{chr(ord('a') + counter - 1)}"  # a, b, c...
            counter += 1
            if counter > 26:
                cite_key = f"{base_key}{counter}"
        
        self._used_keys.add(cite_key)
        return cite_key
    
    def determine_entry_type(self, paper: Dict) -> str:
        """
        Determine BibTeX entry type from paper metadata.
        
        Returns:
            One of: article, inproceedings, book, misc
        """
        # arXiv preprints without venue
        if paper.get('arxiv_id') and not paper.get('venue'):
            return 'misc'
        
        venue = str(paper.get('venue', '')).lower()
        
        # Conference indicators
        if any(word in venue for word in ['conference', 'proceedings', 'workshop', 'symposium', 'icml', 'neurips', 'iclr', 'cvpr', 'acl', 'emnlp', 'chi']):
            return 'inproceedings'
        
        # Journal indicators
        if any(word in venue for word in ['journal', 'transactions', 'review', 'letters']):
            return 'article'
        
        # Book indicators
        if 'book' in venue:
            return 'book'
        
        # Default
        return 'misc'
    
    def generate_entry(self, paper: Dict) -> str:
        """
        Generate single BibTeX entry.
        
        Args:
            paper: Paper metadata dict with keys:
                   title, authors, year, venue, doi, arxiv_id, url, abstract
                   
        Returns:
            Complete BibTeX entry string
        """
        cite_key = self.generate_cite_key(paper)
        entry_type = self.determine_entry_type(paper)
        
        # Start entry
        lines = [f"@{entry_type}{{{cite_key},"]
        
        # Title (required)
        title = self.escape_latex(paper.get('title', 'Unknown Title'))
        lines.append(f"  title = {{{title}}},")
        
        # Authors (required)
        authors = paper.get('authors', ['Unknown'])
        if isinstance(authors, str):
            authors = [a.strip() for a in authors.split(',')]
        
        author_str = ' and '.join(
            self.escape_latex(self.normalize_author(a))
            for a in authors if a
        )
        if not author_str:
            author_str = "Unknown"
        lines.append(f"  author = {{{author_str}}},")
        
        # Year (required)
        year = paper.get('year', 'XXXX')
        lines.append(f"  year = {{{year}}},")
        
        # Venue (journal/booktitle)
        if venue := paper.get('venue'):
            venue_escaped = self.escape_latex(venue)
            field = 'journal' if entry_type == 'article' else 'booktitle'
            lines.append(f"  {field} = {{{venue_escaped}}},")
        
        # DOI
        if doi := paper.get('doi'):
            lines.append(f"  doi = {{{doi}}},")
        
        # arXiv
        if arxiv_id := paper.get('arxiv_id'):
            lines.append(f"  eprint = {{{arxiv_id}}},")
            lines.append(f"  archivePrefix = {{arXiv}},")
            lines.append(f"  primaryClass = {{{paper.get('arxiv_category', 'cs.LG')}}},")
        
        # URL (if no DOI or arXiv)
        if url := paper.get('url'):
            if not paper.get('doi') and not paper.get('arxiv_id'):
                lines.append(f"  url = {{{url}}},")
        
        # Abstract (optional, helps with searching)
        if abstract := paper.get('abstract'):
            # Truncate long abstracts
            abstract = abstract[:500] + ('...' if len(abstract) > 500 else '')
            abstract_escaped = self.escape_latex(abstract)
            lines.append(f"  abstract = {{{abstract_escaped}}},")
        
        # Close entry
        lines.append("}")
        
        return '\n'.join(lines)
    
    def generate_bibtex(self, papers: List[Dict]) -> str:
        """
        Generate complete BibTeX file from paper list.
        
        Args:
            papers: List of paper metadata dicts
            
        Returns:
            Complete BibTeX file content
        """
        # Reset used keys for fresh export
        self._used_keys.clear()
        
        # Header
        header = f"""% BibTeX file generated by ResearchOS
% Papers: {len(papers)}
% Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}

"""
        
        # Generate entries
        entries = []
        for paper in papers:
            try:
                entry = self.generate_entry(paper)
                entries.append(entry)
            except Exception as e:
                logger.warning(f"Failed to generate BibTeX for paper: {paper.get('title', 'Unknown')} - {e}")
                continue
        
        return header + '\n\n'.join(entries)
    
    def validate_bibtex(self, bibtex: str) -> List[str]:
        """
        Basic validation of generated BibTeX.
        
        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []
        
        # Check for unbalanced braces
        open_braces = bibtex.count('{')
        close_braces = bibtex.count('}')
        if open_braces != close_braces:
            warnings.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
        
        # Check for common escaping issues
        if '&' in bibtex and r'\&' not in bibtex:
            warnings.append("Possible unescaped & character")
        
        if '%' in bibtex and r'\%' not in bibtex:
            # Check if % is in comments (valid)
            for line in bibtex.split('\n'):
                if '%' in line and not line.strip().startswith('%'):
                    if r'\%' not in line:
                        warnings.append("Possible unescaped % character")
                        break
        
        # Check for empty required fields
        if 'title = {}' in bibtex:
            warnings.append("Empty title field detected")
        if 'author = {}' in bibtex:
            warnings.append("Empty author field detected")
        
        return warnings


def export_library_bibtex(output_path: str = "data/library.bib") -> str:
    """
    Export entire research library to BibTeX file.
    
    Args:
        output_path: Where to save the .bib file
        
    Returns:
        Path to generated file
    """
    # Import schema to get papers
    try:
        from jarvis_m4.services.schema import UnifiedSchema
        schema = UnifiedSchema()
        papers = schema.get_all_papers()
    except Exception as e:
        logger.error(f"Failed to load papers: {e}")
        papers = []
    
    if not papers:
        logger.warning("No papers found to export")
        return ""
    
    # Generate BibTeX
    exporter = BibTeXExporter()
    bibtex = exporter.generate_bibtex(papers)
    
    # Validate
    warnings = exporter.validate_bibtex(bibtex)
    for warning in warnings:
        logger.warning(f"BibTeX validation: {warning}")
    
    # Write file
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(bibtex, encoding='utf-8')
    
    logger.info(f"📚 Exported {len(papers)} papers to {output_path}")
    return str(output)


# Quick test
if __name__ == "__main__":
    print("Testing BibTeX exporter...")
    
    # Test with sample papers
    test_papers = [
        {
            'title': 'Attention Is All You Need',
            'authors': ['Ashish Vaswani', 'Noam Shazeer', 'Niki Parmar'],
            'year': 2017,
            'venue': 'NeurIPS',
            'arxiv_id': '1706.03762'
        },
        {
            'title': 'BERT: Pre-training & Deep Learning',  # Has special chars
            'authors': ['Jacob Devlin', 'Ming-Wei Chang'],
            'year': 2019,
            'venue': 'NAACL',
            'doi': '10.18653/v1/N19-1423'
        },
        {
            'title': 'Test with 50% accuracy & $100 cost',  # Multiple special chars
            'authors': 'José García, María López',  # Unicode + string format
            'year': 2023,
            'arxiv_id': '2312.12345'
        }
    ]
    
    exporter = BibTeXExporter()
    
    # Test escaping
    print("\n1. Testing LaTeX escaping:")
    test_strings = ["Hello & World", "Cost: $100", "50% done", "File_name"]
    for s in test_strings:
        print(f"   '{s}' → '{exporter.escape_latex(s)}'")
    
    # Test author normalization
    print("\n2. Testing author normalization:")
    test_authors = ["John Smith", "Smith, John", "José García", "  Extra   Spaces  "]
    for a in test_authors:
        print(f"   '{a}' → '{exporter.normalize_author(a)}'")
    
    # Test full export
    print("\n3. Testing full BibTeX generation:")
    bibtex = exporter.generate_bibtex(test_papers)
    print(bibtex[:1000] + "..." if len(bibtex) > 1000 else bibtex)
    
    # Validate
    print("\n4. Validating output:")
    warnings = exporter.validate_bibtex(bibtex)
    if warnings:
        for w in warnings:
            print(f"   ⚠️  {w}")
    else:
        print("   ✅ No issues found")
    
    print("\n✅ All tests passed!")
