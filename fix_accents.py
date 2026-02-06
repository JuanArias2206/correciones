#!/usr/bin/env python3
import unicodedata
import re

def remove_accents(s):
    """Remove accents from a string"""
    nfd = unicodedata.normalize('NFD', s)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')

# Read patterns.py
with open('/Users/mac/Documents/trabajo/javeriana/sivigila/py_sivigila/correciones/pipeline_bundle/patterns.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix accents in raw strings
lines = content.split('\n')
fixed_lines = []

for line in lines:
    # Handle r'...' patterns
    if "r'" in line:
        # Split by r' to handle multiple occurrences
        parts = line.split("r'")
        new_parts = [parts[0]]
        for part in parts[1:]:
            if "'" in part:
                quote_pos = part.find("'")
                string_part = part[:quote_pos]
                rest = part[quote_pos:]
                clean_string = remove_accents(string_part)
                new_parts.append(f"r'{clean_string}{rest}")
            else:
                new_parts.append(f"r'{part}")
        line = "".join(new_parts)
    fixed_lines.append(line)

# Write back
with open('/Users/mac/Documents/trabajo/javeriana/sivigila/py_sivigila/correciones/pipeline_bundle/patterns.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fixed_lines))

print("✓ Removed accents from raw strings in patterns.py")
