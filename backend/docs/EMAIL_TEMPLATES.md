# Email Template Customization Guide

This guide explains how to customize email templates for the Chess Tutor safety monitoring system.

## Overview

The application uses **Jinja2** templates to generate email content. Templates are separated from code, making it easy to customize the look and feel of emails without modifying Python code.

## Template Location

All email templates are located in:
```
backend/templates/email/
```

## Available Templates

### 1. Weekly/Daily Report Templates

**Files:**
- `weekly_report.html` - HTML version of weekly/daily reports
- `weekly_report.txt` - Plain text version of weekly/daily reports

**Used for:**
- Automated weekly reports
- Automated daily reports
- Manual report generation

### 2. Safety Alert Templates

**Files:**
- `safety_alert.html` - HTML version of critical safety alerts
- `safety_alert.txt` - Plain text version of critical safety alerts

**Used for:**
- Immediate crisis/abuse notifications
- High-severity safety alerts

## Template Structure

### Weekly Report Template Variables

The following variables are available in `weekly_report.html` and `weekly_report.txt`:

#### User & Period Info
```jinja2
{{ user_name }}              # Child's name
{{ period }}                 # "Weekly" or "Daily"
{{ start_date }}             # Formatted start date
{{ end_date }}               # Formatted end date
```

#### Status Info
```jinja2
{{ status_color }}           # Hex color code (#16a34a, #d97706, #ea580c, #dc2626)
{{ status_text }}            # "All Clear", "Minor Concerns", "Review Recommended", "Attention Required"
{{ status_icon }}            # Emoji icon (✅, ⚠️, 🚨)
```

#### Safety Data
```jinja2
{{ total_flags }}            # Total number of safety flags
{{ by_severity }}            # Dict: {'critical': 0, 'high': 2, 'medium': 1, 'low': 0}
{{ by_type }}                # Dict: {'crisis': 1, 'profanity': 2, ...}
{{ critical_and_high_flags }}# List of flag objects with severity critical/high
{{ has_critical }}           # Boolean
{{ has_high }}               # Boolean
```

#### Activity Data
```jinja2
{{ total_conversations }}    # Total conversation count
{{ total_messages }}         # Total message count
{{ total_duration_minutes }} # Total time in minutes
{{ active_days }}            # Number of active days
{{ avg_messages_per_session }}# Average messages per conversation
{{ primary_mood }}           # Most common mood detected
{{ topics }}                 # List of topics discussed
```

#### Conversation Summaries
```jinja2
{{ summaries }}              # List of conversation summary objects
```

Each summary object contains:
```jinja2
{{ summary.conversation_id }}
{{ summary.start_time }}
{{ summary.summary }}        # Text summary
{{ summary.mood }}
{{ summary.topics }}         # List
{{ summary.message_count }}
```

#### Preferences
```jinja2
{{ include_snippets }}       # Boolean - whether to show content snippets
```

#### Styling
```jinja2
{{ severity_colors }}        # Dict of hex colors for each severity level
```

### Safety Alert Template Variables

Available in `safety_alert.html` and `safety_alert.txt`:

```jinja2
{{ alert_icon }}             # Emoji (🚨, ⚠️)
{{ alert_title }}            # "URGENT: Suicide-Related Content Detected"
{{ child_name }}             # Child's name
{{ timestamp }}              # Formatted timestamp
{{ severity }}               # "critical", "high", etc.
{{ severity_color }}         # Hex color code
{{ message }}                # Main alert message
{{ action_message }}         # Recommended action text
{{ content_snippet }}        # Optional content snippet
{{ resources }}              # List of crisis resources
```

## Customizing Templates

### Changing Colors

**In HTML templates**, modify the color values:

```html
<!-- Change header gradient -->
<div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);">

<!-- Change status colors -->
{% if safety['has_critical'] %}
    {% set status_color = '#dc2626' %}  <!-- Red -->
{% endif %}
```

**Color scheme:**
- Blue: `#3b82f6` (primary)
- Red: `#dc2626` (critical)
- Orange: `#ea580c` (high)
- Amber: `#d97706` (medium)
- Yellow: `#ca8a04` (low)
- Green: `#16a34a` (success)

### Changing Layout

**Modify the grid layout:**

```html
<!-- Current: 2 columns -->
<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">

<!-- Change to 4 columns -->
<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">
```

### Adding Custom Sections

**Add a new section to the report:**

```html
<!-- After existing sections -->
<h2 style="color: #111827; margin-top: 40px;">Custom Section</h2>
<div style="padding: 20px; background-color: #f9fafb;">
    <p>Your custom content here</p>
    <p>Access template variables: {{ user_name }}</p>
</div>
```

### Conditional Content

**Show/hide content based on conditions:**

```jinja2
{% if total_flags > 5 %}
<div class="warning">
    <p>High activity detected this week!</p>
</div>
{% endif %}

{% if primary_mood == 'happy' %}
<p>😊 {{ user_name }} had a positive week!</p>
{% endif %}
```

### Loops and Iteration

**Iterate over topics:**

```jinja2
{% for topic in topics %}
<span style="background: #e0e7ff; padding: 6px 12px; border-radius: 12px;">
    {{ topic }}
</span>
{% endfor %}
```

**Iterate over flags with index:**

```jinja2
{% for flag in critical_and_high_flags %}
<div>
    <strong>Flag {{ loop.index }}:</strong> {{ flag.flag_type }}
</div>
{% endfor %}
```

## Jinja2 Syntax Reference

### Variables
```jinja2
{{ variable }}               # Output a variable
{{ user.name }}             # Access object attribute
{{ dict['key'] }}           # Access dictionary key
```

### Filters
```jinja2
{{ name|title }}            # Title case: "john" → "John"
{{ text|upper }}            # Uppercase: "hello" → "HELLO"
{{ text|lower }}            # Lowercase: "HELLO" → "hello"
{{ items|join(', ') }}      # Join list: ['a', 'b'] → "a, b"
{{ text|replace('_', ' ')}} # Replace: "hello_world" → "hello world"
{{ number|round(2) }}       # Round: 3.14159 → 3.14
```

### Control Structures
```jinja2
{% if condition %}
    content
{% elif other_condition %}
    other content
{% else %}
    default content
{% endif %}

{% for item in items %}
    {{ item }}
{% endfor %}
```

### Custom Filters

The template service provides custom filters:

```jinja2
{{ date_string|format_date('%B %d, %Y') }}    # Format date
{{ datetime_string|format_time('%I:%M %p') }} # Format time
```

## Testing Templates

### Preview Templates Locally

Use Python to test template rendering:

```python
from services.email_template_service import email_template_service

# Test with sample data
context = {
    'user_name': 'Test User',
    'period': 'Weekly',
    'total_flags': 5,
    # ... other variables
}

html = email_template_service.render('weekly_report.html', context)
print(html)
```

### Send Test Email

Use the API to send a test report:

```bash
# Preview report data
GET /api/parent/reports/preview?user_id=1&period=weekly

# Send test report
POST /api/parent/reports/send?user_id=1&period=weekly&force_send=true
```

## Creating New Templates

### 1. Create Template Files

Create both HTML and plain text versions:

```bash
cd backend/templates/email
touch my_custom_template.html
touch my_custom_template.txt
```

### 2. Design the Template

Use existing templates as a starting point:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ heading }}</h1>
    <p>{{ content }}</p>
</body>
</html>
```

### 3. Render the Template

Use the template service in your code:

```python
from services.email_template_service import email_template_service

context = {
    'title': 'My Title',
    'heading': 'Hello World',
    'content': 'This is my custom template'
}

html = email_template_service.render('my_custom_template.html', context)
```

## Best Practices

### 1. Mobile-Friendly Design

- Use inline styles (required for email clients)
- Set max-width: 600px for main container
- Use responsive font sizes (16px minimum for body text)
- Test on mobile devices

### 2. Email Client Compatibility

- Always use inline CSS (no `<style>` blocks)
- Avoid JavaScript (not supported in emails)
- Use tables for complex layouts (better support than CSS Grid/Flexbox)
- Test in multiple email clients (Gmail, Outlook, Apple Mail)

### 3. Accessibility

- Use semantic HTML (`<h1>`, `<h2>`, `<p>`)
- Provide alt text for images
- Ensure sufficient color contrast
- Use descriptive link text

### 4. Performance

- Keep HTML size under 102KB (Gmail clips larger emails)
- Optimize images and use external hosting if needed
- Minimize inline styles where possible

## Troubleshooting

### Template Not Found

**Error:** `TemplateNotFound: weekly_report.html`

**Solution:**
- Check template exists in `backend/templates/email/`
- Verify filename matches exactly (case-sensitive)
- Ensure templates directory is created

### Rendering Errors

**Error:** `UndefinedError: 'variable' is undefined`

**Solution:**
- Ensure all variables are passed in context
- Use default values: `{{ variable|default('N/A') }}`
- Check for typos in variable names

### Styling Issues

**Problem:** Styles not displaying correctly

**Solution:**
- Use inline styles only
- Test in multiple email clients
- Avoid advanced CSS (flexbox, grid, animations)
- Use tables for layout if needed

## Advanced Customization

### Template Inheritance

Create a base template that other templates extend:

**base_email.html:**
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{% block title %}Chess Tutor{% endblock %}</title>
</head>
<body>
    {% block header %}
    <div style="background: #3b82f6; color: white; padding: 20px;">
        <h1>Chess Tutor</h1>
    </div>
    {% endblock %}

    {% block content %}{% endblock %}

    {% block footer %}
    <div style="background: #f3f4f6; padding: 20px; text-align: center;">
        <p>© Chess Tutor Safety Monitoring</p>
    </div>
    {% endblock %}
</body>
</html>
```

**custom_report.html:**
```html
{% extends "base_email.html" %}

{% block title %}Custom Report{% endblock %}

{% block content %}
<div style="padding: 20px;">
    <p>Your custom content here</p>
</div>
{% endblock %}
```

### Macros for Reusable Components

Define reusable components:

```jinja2
{% macro severity_badge(severity) %}
<span style="background: {{ severity_colors[severity] }}; color: white; padding: 4px 8px; border-radius: 4px;">
    {{ severity|upper }}
</span>
{% endmacro %}

<!-- Use the macro -->
{{ severity_badge('critical') }}
{{ severity_badge('high') }}
```

## Support

For issues with templates:

1. Check template syntax with online Jinja2 validators
2. Test rendering with sample data
3. Review logs: `backend/logs/chatbot.log`
4. Check for errors in `email_template_service` logs

## Resources

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Email Design Best Practices](https://www.campaignmonitor.com/dev-resources/guides/coding/)
- [Can I Email](https://www.caniemail.com/) - Check CSS support in email clients
