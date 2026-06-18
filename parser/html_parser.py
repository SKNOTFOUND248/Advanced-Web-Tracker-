from bs4 import BeautifulSoup
import re
from utils.logger import logger

class HTMLParser:
    \"\"\"
    Parses HTML content to extract visible text and normalize it for comparison.
    \"\"\"
    
    @staticmethod
    def extract_text(html_content: str, css_selector: str = None) -> str:
        \"\"\"
        Cleans HTML and extracts visible text.
        Optionally restricts extraction to a specific CSS selector.
        \"\"\"
        if not html_content:
            return ""

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # If a specific selector is provided, try to find it first
            if css_selector:
                selected_elements = soup.select(css_selector)
                if selected_elements:
                    # Create a new soup with just the selected elements
                    soup = BeautifulSoup("".join(str(el) for el in selected_elements), 'html.parser')
                else:
                    logger.warning(f"CSS selector '{css_selector}' not found. Falling back to full page.")

            # Remove unwanted tags
            for element in soup(["script", "style", "noscript", "meta", "link", "header", "footer", "nav"]):
                element.extract()

            # Extract text
            text = soup.get_text(separator=' ')

            # Normalize whitespace: replace multiple spaces/newlines with a single space, strip edges
            # Also collapse spaces before newlines if we were keeping them, but here we just collapse everything to spaces/newlines
            text = re.sub(r'\\s+', ' ', text).strip()

            return text
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return ""
