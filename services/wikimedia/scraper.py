import wikipedia
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class WikipediaScraper:
    """
    Uses the wikipedia library to fetch a page and extract its 'See also' section.
    """
    def fetch_page(self, title: str):
        """
        Retrieve a wikipedia page object for a given title.

        Args:
            title (str): The article title.

        Returns:
            wikipedia.WikipediaPage: The page object.
        """
        try:
            page = wikipedia.page(title)
            logger.info("Fetched page for '%s'.", title)
            return page
        except Exception as e:
            logger.error("Error fetching page for '%s': %s", title, e)
            raise

    def extract_see_also(self, page) -> list:
        """
        Extract the 'See also' section from the page's content.

        Args:
            page (wikipedia.WikipediaPage): The page object.

        Returns:
            list: A list of article titles found in the 'See also' section.
        """
        content = page.content
        # Look for a section starting with "== See also =="
        match = re.search(r'==\s*See also\s*==(.*?)(==|$)', content, re.DOTALL | re.IGNORECASE)
        if not match:
            logger.info("No 'See also' section found for '%s'.", page.title)
            return []
        see_also_section = match.group(1).strip()
        # Split the section into lines and clean each line.
        lines = see_also_section.split('\n')
        links = []
        for line in lines:
            # Remove bullet markers and extra whitespace.
            line = line.strip().lstrip("*-").strip()
            if line:
                # In many pages the section is a simple list of article titles.
                links.append(line)
        logger.info("Extracted %d 'See also' links from '%s'.", len(links), page.title)
        return links
    
    def extract_content_chunks(self, page) -> List[Dict[str, Any]]:
        """
        Extract meaningful content chunks from the page's content.

        Args:
            page (wikipedia.WikipediaPage): The page object.

        Returns:
            List[Dict[str, Any]]: A list of content chunks with their types and content.
        """
        content = page.content
        chunks = []
        
        # Split content into sections
        sections = re.split(r'(?m)^==\s*', content)
        
        for section in sections:
            if not section.strip():
                continue
                
            # Extract section title and content
            title_match = re.match(r'^(.*?)\s*==\n(.*)', section, re.DOTALL)
            if not title_match:
                continue
                
            section_title = title_match.group(1).strip()
            section_content = title_match.group(2).strip()
            
            # Skip certain sections
            if section_title.lower() in ['references', 'external links', 'see also', 'notes']:
                continue
                
            # Split section content into paragraphs
            paragraphs = [p.strip() for p in section_content.split('\n\n') if p.strip()]
            
            for paragraph in paragraphs:
                # Skip empty paragraphs
                if not paragraph:
                    continue
                
                # Try to extract a title from the paragraph
                chunk_title = None
                # Look for a title in the first line if it's short
                first_line = paragraph.split('\n')[0]
                if len(first_line) < 100 and not first_line.startswith(('*', '-', '|')):
                    chunk_title = first_line
                    paragraph = '\n'.join(paragraph.split('\n')[1:])
                
                # Determine chunk type
                chunk_type = "TEXT"
                if paragraph.startswith('*') or paragraph.startswith('-'):
                    chunk_type = "LIST"
                elif '|' in paragraph:
                    chunk_type = "TABLE"
                
                # If no title was found, use a default based on type and section
                if not chunk_title:
                    chunk_title = f"{section_title} - {chunk_type}"
                
                chunks.append({
                    'content': paragraph,
                    'type': chunk_type,
                    'section': section_title,
                    'title': chunk_title
                })
        
        logger.info("Extracted %d content chunks from '%s'", len(chunks), page.title)
        return chunks

    def extract_linked_pages(self, page) -> list:
        """
        Extract all linked pages from the page's content.
        """
        content = page.content
        # Look for all links in the content.
        links = re.findall(r'\[(.*?)\]', content)
        return links

