
def handle_markdown_error(error, section_name):
    """Handle errors when accessing markdown reference files."""
    fallback_sections = [
        "Brand Voice", 
        "Style Guide", 
        "Content Structure", 
        "Terminology Preferences",
        "Company Background",
        "Product Information",
        "Competitor Analysis"
    ]
    
    # Remove the section that failed
    if section_name in fallback_sections:
        fallback_sections.remove(section_name)
    
    # Return structured response with fallback guidance
    return {
        "status": "error",
        "message": f"Error accessing '{section_name}' section: {str(error)}",
        "fallback_options": fallback_sections,
        "recommendation": "Try accessing one of the fallback sections, or proceed using professional standards if all sections are inaccessible."
    }

import os
import re
from datetime import datetime

def sanitize_filename(filename):
    """Sanitizes a string to be used as a filename."""
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", filename)
    # Replace multiple spaces with a single underscore
    sanitized = re.sub(r'\s+', "_", sanitized)
    return sanitized.lower()

def generate_output_filename(topic, output_dir):
    """Generates a filename for the output content."""
    date_str = datetime.now().strftime("%Y%m%d")
    sanitized_topic = sanitize_filename(topic)
    return os.path.join(output_dir, f"{date_str}_{sanitized_topic}.md")

def ensure_directory_exists(directory):
    """Ensures that the specified directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
    return directory 