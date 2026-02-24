"""
OCR text cleanup utilities for improving RapidOCR output formatting.
"""

import re


def cleanup_ocr_text(raw_text):
    """Clean and format OCR text output."""
    if not raw_text or not raw_text.strip():
        return ""
    
    lines = raw_text.split('\n')
    cleaned_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Remove OCR noise
        if len(line) <= 2 and not line.isalpha():
            i += 1
            continue
        
        # Fix word spacing
        line = fix_word_spacing(line)
        
        # Format headings
        if is_heading(line):
            if cleaned_lines:
                cleaned_lines.append("")
            
            if is_main_heading(line):
                cleaned_lines.append(f"## {line}")
            else:
                cleaned_lines.append(f"### {line}")
            
            cleaned_lines.append("")
            i += 1
            continue
        
        # Format lists
        if is_list_item(line):
            if not line.startswith('-'):
                line = f"- {line.lstrip('•·*→')}"
            cleaned_lines.append(line)
            i += 1
            continue
        
        # Merge broken sentences
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            
            if (not line.endswith(('.', '!', '?', ':', ';')) and next_line and 
                not is_heading(next_line) and not is_list_item(next_line) and len(next_line) > 0):
                
                if line[-1].isalnum() and next_line[0].isalnum():
                    line = f"{line} {next_line}"
                else:
                    line = f"{line}{next_line}"
                i += 2
            else:
                i += 1
        else:
            i += 1
        
        cleaned_lines.append(line)
    
    # Remove duplicates
    deduped_lines = []
    prev_line = None
    for line in cleaned_lines:
        if line != prev_line or line == "":
            deduped_lines.append(line)
        prev_line = line
    
    cleaned_text = '\n'.join(deduped_lines)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    return cleaned_text.strip()


def fix_word_spacing(text):
    """Fix common OCR word spacing issues."""
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    replacements = {
        'andNarratedby': 'and Narrated by',
        'Createdby': 'Created by',
        'fordesigning': 'for designing',
        'yourown': 'your own',
        'quickguidefor': 'quick guide for',
        'designingyourown': 'designing your own',
        'CreatedandNarratedby': 'Created and Narrated by',
        'Graphicsfromcreativecommons': 'Graphics from creative commons',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def is_heading(line):
    """Detect if a line is likely a heading."""
    if len(line) > 100:
        return False
    
    alpha_chars = [c for c in line if c.isalpha()]
    if alpha_chars:
        upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        if upper_ratio > 0.7:
            return True
    
    heading_keywords = ['STEP', 'WHAT', 'HOW', 'WHY', 'BENEFITS', 'EXAMPLE', 'TYPES', 'INFOGRAPHIC']
    if any(keyword in line.upper() for keyword in heading_keywords):
        return True
    
    if line.endswith('?'):
        return True
    
    return False


def is_main_heading(line):
    """Determine if heading is main (##) or sub (###)."""
    return len(line) < 40 or line.isupper()


def is_list_item(line):
    """Detect if a line is a list item."""
    list_indicators = ['-', '•', '·', '*', '→']
    if any(line.startswith(indicator) for indicator in list_indicators):
        return True
    
    if re.match(r'^\d+[\.\)]\s+', line):
        return True
    
    return False
