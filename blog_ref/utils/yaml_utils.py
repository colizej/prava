"""
YAML Utilities for Piece de Theatre
====================================

Shared utilities for YAML parsing and text processing across the project.

This module provides consistent YAML parsing and text cleaning for:
- blog.models (Article)
- library.models (ClassicPlay)
- profiles.models (Profile, Play)
- scripts/pdf/generate_edition.py
- scripts/maintenance/*

Functions:
- clean_yaml_text(): Remove hard line breaks from YAML multiline strings
- parse_yaml_frontmatter(): Extract YAML frontmatter from markdown
- normalize_yaml_keys(): Convert dashed keys to underscores (meta-title → meta_title)
- extract_seo_fields(): Extract and clean SEO fields from YAML data

Created: 19 February 2026
Purpose: DRY principle - single source of truth for YAML processing
"""

import re
import yaml


def clean_yaml_text(text):
    """
    Remove hard line breaks from YAML multiline strings.

    YAML preserves line breaks from multiline strings (| or >),
    but for display we want them removed within paragraphs.

    Rules:
    - Replace single newlines with spaces (within paragraphs)
    - Preserve double newlines (paragraph breaks)
    - Strip leading/trailing whitespace
    - Clean up multiple consecutive spaces

    Args:
        text: Text to clean (str, or any other type)

    Returns:
        str: Cleaned text with normalized whitespace
        any: Original value if not a string

    Examples:
        >>> clean_yaml_text("Line 1\\nLine 2\\n\\nParagraph 2")
        "Line 1 Line 2\\n\\nParagraph 2"

        >>> clean_yaml_text("Multiple    spaces")
        "Multiple spaces"

        >>> clean_yaml_text(123)  # Non-string passthrough
        123

    Use Cases:
    - Cleaning YAML descriptions with hard line breaks
    - Normalizing meta descriptions for SEO
    - Processing multi-line synopses from YAML files
    """
    if not isinstance(text, str):
        return text

    # Replace multiple newlines with placeholder to preserve paragraph breaks
    text = re.sub(r'\n\n+', '|||PARAGRAPH_BREAK|||', text)
    # Replace single newlines with spaces (join lines within paragraph)
    text = re.sub(r'\n', ' ', text)
    # Restore paragraph breaks
    text = text.replace('|||PARAGRAPH_BREAK|||', '\n\n')
    # Clean up multiple consecutive spaces
    text = re.sub(r' +', ' ', text)
    # Strip leading/trailing whitespace
    return text.strip()


def parse_yaml_frontmatter(content):
    """
    Parse YAML frontmatter from markdown content.

    Extracts YAML metadata block from markdown files following the format:
    ---
    key: value
    ---
    # Markdown content

    Args:
        content (str): Markdown content with YAML frontmatter

    Returns:
        tuple: (yaml_data dict, markdown_text str)
            - yaml_data: Parsed YAML as dictionary (empty dict if no YAML)
            - markdown_text: Markdown content without YAML block

    Raises:
        ValueError: If YAML frontmatter format is invalid
        ValueError: If YAML parsing fails (syntax error)

    Examples:
        >>> content = "---\\ntitle: Test\\nmeta-title: SEO Title\\n---\\n# Content"
        >>> data, text = parse_yaml_frontmatter(content)
        >>> data['title']
        'Test'
        >>> text
        '# Content'

        >>> content = "No YAML here\\n# Just markdown"
        >>> data, text = parse_yaml_frontmatter(content)
        ValueError: Content must start with YAML frontmatter (---)

    Use Cases:
    - Loading article metadata from markdown files
    - Syncing play data from Library_text/*.md files
    - Processing blog posts with SEO metadata
    """
    if not content:
        raise ValueError("Content is empty")

    if not content.startswith('---'):
        raise ValueError("Content must start with YAML frontmatter (---)")

    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError("Invalid YAML frontmatter format (missing closing ---)")

    yaml_content = parts[1]
    markdown_text = parts[2].strip()

    try:
        data = yaml.safe_load(yaml_content)
        # Handle empty YAML block
        if data is None:
            data = {}
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parsing error: {e}")

    return data, markdown_text


def normalize_yaml_keys(data):
    """
    Convert YAML keys with dashes to underscores.

    Normalizes key names to match Python/Django field naming conventions:
    - meta-title → meta_title
    - og-description → og_description
    - published-at → published_at

    Args:
        data (dict): Dictionary with potentially dashed keys

    Returns:
        dict: Dictionary with underscored keys
        any: Original value if not a dictionary

    Examples:
        >>> normalize_yaml_keys({'meta-title': 'Title', 'author': 'John'})
        {'meta_title': 'Title', 'author': 'John'}

        >>> normalize_yaml_keys("not a dict")
        "not a dict"

        >>> normalize_yaml_keys({'nested': {'sub-key': 'value'}})
        {'nested': {'sub-key': 'value'}}  # Only top-level keys normalized

    Use Cases:
    - Processing YAML from markdown files
    - Mapping YAML fields to Django model fields
    - Ensuring consistent key naming across the app

    Note:
    - Only normalizes top-level keys
    - Nested dictionaries are NOT recursively normalized
    - Values are preserved as-is
    """
    if not isinstance(data, dict):
        return data

    return {k.replace('-', '_'): v for k, v in data.items()}


def extract_seo_fields(yaml_data, clean=True):
    """
    Extract and optionally clean SEO fields from YAML data.

    Supports two YAML structures:

    1. Nested (library style):
       seo:
         meta_title: "Title"
         meta_description: "Description"

    2. Flat (blog style):
       meta-title: "Title"
       meta-description: "Description"

    Args:
        yaml_data (dict): Parsed YAML data
        clean (bool): Apply clean_yaml_text() to values (default: True)

    Returns:
        dict: Extracted SEO fields with normalized keys:
            {
                'meta_title': 'cleaned text',
                'meta_description': 'cleaned text',
                'og_title': 'cleaned text',
                'og_description': 'cleaned text'
            }

    Examples:
        >>> data = {'meta-title': 'Title\\nWith\\nBreaks', 'author': 'John'}
        >>> extract_seo_fields(data)
        {'meta_title': 'Title With Breaks'}

        >>> data = {'seo': {'meta_title': 'Title', 'og_title': 'OG Title'}}
        >>> extract_seo_fields(data)
        {'meta_title': 'Title', 'og_title': 'OG Title'}

        >>> data = {'meta-title': '"Quoted Title"'}
        >>> extract_seo_fields(data)
        {'meta_title': 'Quoted Title'}  # Quotes removed by yaml.safe_load

    Use Cases:
    - Mapping YAML metadata to Article/Play model fields
    - Processing SEO fields from markdown files
    - Ensuring consistent SEO data format

    Note:
    - Tries nested 'seo:' structure first
    - Falls back to flat structure
    - Checks both dashed (meta-title) and underscored (meta_title) keys
    - Converts all values to strings before cleaning
    """
    if not isinstance(yaml_data, dict):
        return {}

    seo = {}
    seo_fields = ['meta_title', 'meta_description', 'og_title', 'og_description']

    # Check for nested structure (library style)
    if 'seo' in yaml_data and isinstance(yaml_data['seo'], dict):
        for field in seo_fields:
            if field in yaml_data['seo']:
                seo[field] = yaml_data['seo'][field]
    else:
        # Flat structure (blog style) - check both dashed and underscored versions
        for field in seo_fields:
            # Try underscored version first
            if field in yaml_data:
                seo[field] = yaml_data[field]
            # Try dashed version
            dashed_field = field.replace('_', '-')
            if dashed_field in yaml_data:
                seo[field] = yaml_data[dashed_field]

    # Clean and convert to strings
    if clean:
        return {k: clean_yaml_text(str(v)) for k, v in seo.items()}
    else:
        return {k: str(v) for k, v in seo.items()}


# Convenience function for common use case
def parse_article_yaml(content_markdown):
    """
    Parse article markdown with YAML frontmatter and extract all metadata.

    Convenience function that combines parsing and SEO extraction.

    Args:
        content_markdown (str): Full markdown content with YAML frontmatter

    Returns:
        tuple: (yaml_data dict, markdown_text str, seo_fields dict)
            - yaml_data: All YAML fields
            - markdown_text: Markdown without YAML block
            - seo_fields: Extracted and cleaned SEO fields

    Raises:
        ValueError: If YAML parsing fails

    Examples:
        >>> content = "---\\nmeta-title: Title\\n---\\n# Content"
        >>> yaml_data, text, seo = parse_article_yaml(content)
        >>> seo['meta_title']
        'Title'

    Use Cases:
    - Quick parsing in Article.save() method
    - One-liner for complete YAML processing
    - Reducing boilerplate in views/admin
    """
    try:
        yaml_data, markdown_text = parse_yaml_frontmatter(content_markdown)
        seo_fields = extract_seo_fields(yaml_data, clean=True)
        return yaml_data, markdown_text, seo_fields
    except ValueError:
        # No YAML or invalid format - return empty structures
        return {}, content_markdown, {}
