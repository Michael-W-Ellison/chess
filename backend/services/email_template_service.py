"""
Email Template Service
Handles rendering of email templates using Jinja2
"""

import logging
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

logger = logging.getLogger("chatbot.email_template")


class EmailTemplateService:
    """
    Email Template Service

    Features:
    - Loads and renders Jinja2 email templates
    - Supports both HTML and plain text templates
    - Template caching for performance
    - Custom filters for formatting
    - Centralized template management

    Usage:
        template_service.render('weekly_report.html', context_data)
    """

    def __init__(self, templates_dir: str = None):
        """
        Initialize EmailTemplateService

        Args:
            templates_dir: Path to templates directory (defaults to backend/templates/email)
        """
        if templates_dir is None:
            # Default to backend/templates/email
            backend_dir = Path(__file__).parent.parent
            templates_dir = backend_dir / "templates" / "email"

        self.templates_dir = Path(templates_dir)

        # Ensure templates directory exists
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory does not exist: {self.templates_dir}")
            self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,  # Auto-escape for HTML safety
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self._register_filters()

        logger.info(f"EmailTemplateService initialized with templates from: {self.templates_dir}")

    def _register_filters(self):
        """Register custom Jinja2 filters"""

        # Date formatting filter
        def format_date(value, format_str='%B %d, %Y'):
            """Format ISO date string"""
            if not value:
                return 'Unknown'
            try:
                from datetime import datetime
                if isinstance(value, str):
                    # Parse ISO format
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    dt = value
                return dt.strftime(format_str)
            except Exception as e:
                logger.debug(f"Error formatting date {value}: {e}")
                return str(value)[:10]  # Return first 10 chars as fallback

        # Time formatting filter
        def format_time(value, format_str='%I:%M %p'):
            """Format ISO datetime string to time"""
            if not value:
                return 'Unknown'
            try:
                from datetime import datetime
                if isinstance(value, str):
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    dt = value
                return dt.strftime(format_str)
            except Exception as e:
                logger.debug(f"Error formatting time {value}: {e}")
                return str(value)

        # Register filters
        self.env.filters['format_date'] = format_date
        self.env.filters['format_time'] = format_time

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context

        Args:
            template_name: Name of the template file (e.g., 'weekly_report.html')
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template as string

        Raises:
            TemplateNotFound: If template file doesn't exist
        """
        try:
            template = self.env.get_template(template_name)
            rendered = template.render(**context)

            logger.debug(f"Rendered template: {template_name}")
            return rendered

        except TemplateNotFound:
            logger.error(f"Template not found: {template_name} in {self.templates_dir}")
            raise

        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}", exc_info=True)
            raise

    def render_report(
        self,
        report_data: Dict[str, Any],
        prefs: Any,
        format_type: str = 'html'
    ) -> str:
        """
        Render a weekly/daily report template

        This is a convenience method that prepares the context and renders
        the appropriate template (HTML or plain text).

        Args:
            report_data: Report data dictionary from weekly_report_service
            prefs: Parent notification preferences object
            format_type: 'html' or 'text'

        Returns:
            Rendered report as string
        """
        # Determine status color and text based on safety flags
        safety = report_data['safety']
        if safety['has_critical']:
            status_color = '#dc2626'  # Red
            status_text = 'Attention Required'
            status_icon = '🚨'
        elif safety['has_high']:
            status_color = '#ea580c'  # Orange
            status_text = 'Review Recommended'
            status_icon = '⚠️'
        elif safety['total_flags'] > 0:
            status_color = '#d97706'  # Amber
            status_text = 'Minor Concerns'
            status_icon = '⚠️'
        else:
            status_color = '#16a34a'  # Green
            status_text = 'All Clear'
            status_icon = '✅'

        # Severity colors for badges
        severity_colors = {
            'critical': '#dc2626',
            'high': '#ea580c',
            'medium': '#d97706',
            'low': '#ca8a04'
        }

        # Format dates for display
        from datetime import datetime
        try:
            start_dt = datetime.fromisoformat(report_data['start_date'])
            end_dt = datetime.fromisoformat(report_data['end_date'])
            start_date = start_dt.strftime('%B %d, %Y')
            end_date = end_dt.strftime('%B %d, %Y')
        except:
            start_date = report_data['start_date'][:10]
            end_date = report_data['end_date'][:10]

        # Build template context
        context = {
            # User and period info
            'user_name': report_data['user_name'],
            'period': report_data['period'],
            'start_date': start_date,
            'end_date': end_date,

            # Status
            'status_color': status_color,
            'status_text': status_text,
            'status_icon': status_icon,

            # Safety data
            'total_flags': safety['total_flags'],
            'by_severity': safety['by_severity'],
            'by_type': safety['by_type'],
            'critical_and_high_flags': safety['critical_and_high_flags'],
            'has_critical': safety['has_critical'],
            'has_high': safety['has_high'],

            # Conversation data
            'total_conversations': report_data['conversations']['total_conversations'],
            'total_messages': report_data['conversations']['total_messages'],
            'total_duration_minutes': report_data['conversations']['total_duration_minutes'],
            'primary_mood': report_data['conversations']['primary_mood'],
            'topics': report_data['conversations']['topics'],
            'summaries': report_data['conversations']['summaries'],

            # Engagement data
            'active_days': report_data['engagement']['active_days'],
            'avg_messages_per_session': report_data['engagement']['avg_messages_per_session'],

            # Preferences
            'include_snippets': prefs.include_content_snippets,

            # Styling
            'severity_colors': severity_colors,
        }

        # Select template based on format
        if format_type == 'html':
            template_name = 'weekly_report.html'
        elif format_type == 'text':
            template_name = 'weekly_report.txt'
        else:
            raise ValueError(f"Invalid format_type: {format_type}. Must be 'html' or 'text'")

        return self.render(template_name, context)

    def list_templates(self) -> list:
        """
        List all available templates

        Returns:
            List of template filenames
        """
        if not self.templates_dir.exists():
            return []

        templates = []
        for file_path in self.templates_dir.iterdir():
            if file_path.is_file() and file_path.suffix in ['.html', '.txt', '.jinja2']:
                templates.append(file_path.name)

        return sorted(templates)

    def template_exists(self, template_name: str) -> bool:
        """
        Check if a template exists

        Args:
            template_name: Name of the template file

        Returns:
            True if template exists
        """
        template_path = self.templates_dir / template_name
        return template_path.exists()


# Global service instance
email_template_service = EmailTemplateService()


# Convenience functions
def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """Render a template with the given context"""
    return email_template_service.render(template_name, context)


def render_report(report_data: Dict[str, Any], prefs: Any, format_type: str = 'html') -> str:
    """Render a weekly/daily report template"""
    return email_template_service.render_report(report_data, prefs, format_type)


def list_templates() -> list:
    """List all available templates"""
    return email_template_service.list_templates()
