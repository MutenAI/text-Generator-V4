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

def ensure_directory_exists(directory_path):
    """Assicura che una directory esista, creandola se necessario."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        return True
    return False

def handle_markdown_reference(section_name, fallback_sections=None):
    """
    Handler for markdown reference tool to ensure robust access to brand guidelines.

    Args:
        section_name: Primary section to access
        fallback_sections: List of alternative sections to try if primary fails

    Returns:
        Dictionary with results and any error information
    """
    if fallback_sections is None:
        fallback_sections = ["Brand Voice", "Style Guide", "Content Structure", "Terminology Preferences"]

    # Remove the current section from fallbacks if present
    if section_name in fallback_sections:
        fallback_sections.remove(section_name)

    results = {
        "attempts": [],
        "successful_sections": {},
        "failed_sections": [],
        "fallback_recommendations": fallback_sections
    }

    # Try to access the primary section
    try:
        content = markdown_reference({"section": section_name}) # Assumes markdown_reference function exists elsewhere
        results["attempts"].append({"section": section_name, "status": "success"})
        results["successful_sections"][section_name] = content
    except Exception as e:
        results["attempts"].append({"section": section_name, "status": "failed", "error": str(e)})
        results["failed_sections"].append(section_name)

        # Try fallback sections
        for fallback in fallback_sections:
            try:
                content = markdown_reference({"section": fallback}) # Assumes markdown_reference function exists elsewhere
                results["attempts"].append({"section": fallback, "status": "success"})
                results["successful_sections"][fallback] = content
            except Exception as e:
                results["attempts"].append({"section": fallback, "status": "failed", "error": str(e)})
                results["failed_sections"].append(fallback)

    # If all sections failed, try without section specification
    if not results["successful_sections"] and len(results["failed_sections"]) > 0:
        try:
            content = markdown_reference({}) # Assumes markdown_reference function exists elsewhere
            results["attempts"].append({"section": "ALL", "status": "success"})
            results["successful_sections"]["ALL"] = content
        except Exception as e:
            results["attempts"].append({"section": "ALL", "status": "failed", "error": str(e)})
            results["failed_sections"].append("ALL")

    return results