"""
Utility functions to prevent emojis in generated files.
"""
import re

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "]+",
    flags=re.UNICODE
)

def remove_emojis(text):
    """Remove emojis from text."""
    if not isinstance(text, str):
        return text
    return EMOJI_PATTERN.sub('', text)

def sanitize_text_for_output(text):
    """Sanitize text to remove emojis before writing to files."""
    return remove_emojis(text)
