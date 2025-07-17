"""Permalink generation utilities for basic-memory."""

import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Union

def generate_permalink(file_path: Union[Path, str, Any]) -> str:
    """
    Generate a permalink from a file path.

    Returns:
        Normalized permalink that matches validation rules. Converts spaces and underscores
        to hyphens for consistency. Preserves non-ASCII characters like Chinese.

    Examples:
        >>> generate_permalink("docs/My Feature.md")
        'docs/my-feature'
        >>> generate_permalink("specs/API_v2.md")
        'specs/api-v2'
        >>> generate_permalink("design/unified_model_refactor.md")
        'design/unified-model-refactor'
        >>> generate_permalink("中文/测试文档.md")
        '中文/测试文档'
    """
    # Convert Path to string if needed
    path_str = str(file_path)

    # Remove extension
    base = os.path.splitext(path_str)[0]

    # Create a transliteration mapping for specific characters
    transliteration_map = {
        "ø": "o",  # Handle Søren -> soren
        "å": "a",  # Handle Kierkegård -> kierkegard
        "ü": "u",  # Handle Müller -> muller
        "é": "e",  # Handle Café -> cafe
        "è": "e",  # Handle Mère -> mere
        "ê": "e",  # Handle Fête -> fete
        "à": "a",  # Handle À la mode -> a la mode
        "ç": "c",  # Handle Façade -> facade
        "ñ": "n",  # Handle Niño -> nino
        "ö": "o",  # Handle Björk -> bjork
        "ä": "a",  # Handle Häagen -> haagen
        # Add more mappings as needed
    }

    # Process character by character, transliterating Latin characters with diacritics
    result = ""
    for char in base:
        # Direct mapping for known characters
        if char.lower() in transliteration_map:
            result += transliteration_map[char.lower()]
        # General case using Unicode normalization
        else:
            # Normalize the character (NFD splits accented characters into base + diacritic)
            normalized = unicodedata.normalize('NFD', char)
            # Keep only the base character, discarding diacritics
            base_char = ''.join(c for c in normalized if not unicodedata.combining(c))
            result += base_char

    # Convert to lowercase and replace spaces/underscores with hyphens
    clean_text = (
        result.lower()
        .replace(" ", "-")
        .replace("_", "-")
    )

    # Remove any remaining non-word characters except slashes and hyphens
    clean_text = re.sub(r"[^\w\-/]", "", clean_text)

    # Replace multiple hyphens with a single one
    clean_text = re.sub(r"-+", "-", clean_text)

    # Clean each path segment
    segments = clean_text.split("/")
    clean_segments = [s.strip("-") for s in segments]

    return "/".join(clean_segments)
