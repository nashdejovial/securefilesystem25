"""
Custom Jinja2 filters for template formatting.
"""

from datetime import datetime

def format_datetime(value, format='%B %d, %Y %I:%M %p'):
    """Format a datetime object to a string."""
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return value
    return value.strftime(format)

def format_filesize(bytes, binary=True):
    """Format file size in bytes to human readable format."""
    if binary:
        units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
        k = 1024
    else:
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        k = 1000

    if bytes == 0:
        return '0 B'

    i = 0
    while bytes >= k and i < len(units) - 1:
        bytes /= k
        i += 1

    return f'{bytes:.1f} {units[i]}'

def register_filters(app):
    """Register custom filters with the Flask app."""
    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.filters['filesize'] = format_filesize 