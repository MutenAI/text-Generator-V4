"""Quality checking module for content generation system."""

import logging
import re

logger = logging.getLogger(__name__)

class ContentQualityChecker:
    """Handles content quality validation and improvement suggestions."""
    
    def __init__(self):
        self.min_section_length = 200  # Minimum characters per section
        self.max_section_length = 5000  # Maximum characters per section
        
    def check_content_quality(self, content):
        """Performs comprehensive quality checks on the content.
        
        Args:
            content (str): The markdown content to check
            
        Returns:
            dict: Quality check results and suggestions
        """
        results = {
            'overall_quality': 'good',
            'issues': [],
            'suggestions': []
        }
        
        # Check content structure
        structure_issues = self._check_structure(content)
        if structure_issues:
            results['issues'].extend(structure_issues)
            results['overall_quality'] = 'needs_improvement'
        
        # Check section lengths
        length_issues = self._check_section_lengths(content)
        if length_issues:
            results['issues'].extend(length_issues)
            results['overall_quality'] = 'needs_improvement'
        
        # Generate improvement suggestions
        if results['issues']:
            results['suggestions'] = self._generate_suggestions(results['issues'])
        
        return results
    
    def _check_structure(self, content):
        """Checks markdown structure for proper headings and formatting."""
        issues = []
        
        # Check for main heading
        if not re.search(r'^#\s+.+', content, re.MULTILINE):
            issues.append('Missing main heading (H1)')
        
        # Check for subheadings
        if not re.search(r'^##\s+.+', content, re.MULTILINE):
            issues.append('Missing subheadings (H2)')
        
        # Check for balanced heading structure
        headings = re.findall(r'^(#+)\s+.+', content, re.MULTILINE)
        if headings:
            levels = [len(h) for h in headings]
            if max(levels) - min(levels) > 1:
                issues.append('Inconsistent heading hierarchy')
        
        return issues
    
    def _check_section_lengths(self, content):
        """Validates the length of each content section."""
        issues = []
        
        # Split content into sections
        sections = re.split(r'^##\s+.+$', content, flags=re.MULTILINE)[1:]
        
        for i, section in enumerate(sections, 1):
            length = len(section.strip())
            if length < self.min_section_length:
                issues.append(f'Section {i} is too short ({length} chars)')
            elif length > self.max_section_length:
                issues.append(f'Section {i} is too long ({length} chars)')
        
        return issues
    
    def _generate_suggestions(self, issues):
        """Generates improvement suggestions based on identified issues."""
        suggestions = []
        
        for issue in issues:
            if 'too short' in issue:
                suggestions.append('Expand section with more details or examples')
            elif 'too long' in issue:
                suggestions.append('Consider breaking down into smaller subsections')
            elif 'heading' in issue.lower():
                suggestions.append('Review and restructure content hierarchy')
        
        return list(set(suggestions))  # Remove duplicates