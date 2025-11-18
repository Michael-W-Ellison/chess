# Automated Email Reports Setup Guide

This guide explains how to set up and use the automated email reporting system for weekly and daily safety reports.

## Overview

The Chess Tutor application includes an automated scheduler that sends weekly or daily safety and activity reports to parents via email based on their preferences.

## Features

- **Automated Scheduling**: Reports are sent automatically at configured times
- **Flexible Frequency**: Support for daily or weekly reports
- **Customizable Timing**: Parents can choose which day of the week and hour to receive reports
- **Preference-Based**: Respects all parent notification preferences
- **Comprehensive Content**: Includes safety flags, conversation summaries, and engagement metrics

## Setup Instructions

### 1. Install Dependencies

First, install the required dependencies:

```bash
cd backend
pip install -r requirements.txt
```

This will install APScheduler and other necessary packages.

### 2. Configure Email Settings

Set up your SMTP email configuration in the `.env` file:

```bash
# Enable parent notifications and weekly reports
ENABLE_PARENT_NOTIFICATIONS=True
ENABLE_WEEKLY_REPORTS=True

# SMTP Configuration (example using Gmail)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_USE_TLS=True
```

#### Gmail Setup

If using Gmail, you'll need to:

1. Enable 2-factor authentication on your Google account
2. Generate an **App Password** (not your regular password)
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the generated 16-character password
3. Use this app password as `SMTP_PASSWORD`

#### Other Email Providers

For other email providers, use their SMTP settings:

**Outlook/Office 365:**
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
```

**Yahoo:**
```bash
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
```

### 3. Configure Parent Preferences

Parents can configure their report preferences through the parent dashboard UI or API:

**Via API:**
```bash
PUT /api/parent/preferences?user_id=1
{
  "email": "parent@example.com",
  "email_notifications_enabled": true,
  "summary_frequency": "weekly",
  "summary_day_of_week": 0,  // 0=Monday, 1=Tuesday, ..., 6=Sunday
  "summary_hour": 9,          // 9 = 9:00 AM (24-hour format)
  "include_content_snippets": true
}
```

**Report Frequency Options:**
- `"daily"` - Send report every day at the configured hour
- `"weekly"` - Send report once per week on the configured day and hour
- `"none"` - Disable automated reports (can still send manually)

### 4. Start the Backend

Start the FastAPI backend server:

```bash
cd backend
python main.py
```

You should see log messages indicating the scheduler has started:

```
Starting automated report scheduler...
✓ Report scheduler started - will check for due reports every hour
```

## How It Works

### Scheduler Behavior

1. **Hourly Checks**: The scheduler runs every hour at minute :00
2. **User Scanning**: Each hour, it scans all users with email reports enabled
3. **Time Matching**: For each user, it checks if the current day/hour matches their preferences
4. **Report Generation**: If a match is found, it generates and sends the report
5. **Logging**: All actions are logged for monitoring and debugging

### Report Content

Weekly/daily reports include:

**Safety Summary:**
- Total safety flags
- Breakdown by severity (critical, high, medium, low)
- Breakdown by type (crisis, abuse, bullying, profanity, inappropriate)
- Details of critical and high-severity flags

**Activity Summary:**
- Total conversations
- Total messages
- Active days
- Average messages per session
- Primary mood detected
- Topics discussed

**Recent Conversations:**
- Summaries of up to 5 recent conversations
- Topics and moods for each conversation

## API Endpoints

### Preview Report (No Email)

```bash
GET /api/parent/reports/preview?user_id=1&period=weekly
```

Returns report data without sending an email.

### Send Report Manually

```bash
POST /api/parent/reports/send?user_id=1&period=weekly&force_send=true
```

Manually trigger a report. Use `force_send=true` to bypass preference checks.

### Trigger Scheduled Check

```bash
POST /api/parent/reports/trigger-scheduled-check
```

Manually trigger the automated scheduler check (useful for testing).

### Update Preferences

```bash
PUT /api/parent/preferences?user_id=1
{
  "summary_frequency": "daily",
  "summary_hour": 18
}
```

## Testing the Setup

### 1. Test Email Configuration

Send a test notification to verify SMTP settings:

```bash
POST /api/parent/test-notification?user_id=1
```

### 2. Preview a Report

Generate a report preview to see what will be sent:

```bash
GET /api/parent/reports/preview?user_id=1&period=weekly
```

### 3. Send a Test Report

Manually send a report to test the full flow:

```bash
POST /api/parent/reports/send?user_id=1&period=weekly&force_send=true
```

### 4. Test Scheduler

Trigger an immediate scheduler check:

```bash
POST /api/parent/reports/trigger-scheduled-check
```

Check the backend logs to see if reports were sent.

## Troubleshooting

### Reports Not Sending

**Check Email Configuration:**
- Verify SMTP settings in `.env` are correct
- Confirm `ENABLE_PARENT_NOTIFICATIONS=True`
- Confirm `ENABLE_WEEKLY_REPORTS=True`

**Check Parent Preferences:**
- Verify email address is configured
- Verify `email_notifications_enabled=true`
- Verify `summary_frequency` is "daily" or "weekly" (not "none")
- Check the configured day and hour match current time

**Check Logs:**
```bash
tail -f logs/chatbot.log
```

Look for messages from `chatbot.report_scheduler` and `chatbot.weekly_report`.

### SMTP Authentication Errors

**Gmail:**
- Make sure 2FA is enabled
- Use an App Password, not your regular password
- Allow less secure apps if needed (not recommended)

**Office 365:**
- Modern authentication may require OAuth (consider using a service account)

### Scheduler Not Running

Check that the backend started successfully:
```bash
grep "Report scheduler started" logs/chatbot.log
```

If not found, check that both feature flags are enabled in `.env`.

## Monitoring

### Log Locations

All logs are written to:
```
backend/logs/chatbot.log
```

### Important Log Messages

**Scheduler started:**
```
✓ Report scheduler started - will check for due reports every hour
```

**Hourly check:**
```
Starting scheduled report check
Found N users with reports enabled
```

**Report sent:**
```
Successfully sent weekly report to parent@example.com for user 1
```

**Report skipped:**
```
Report not sent for user 1: Email notifications disabled
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` file with credentials
2. **App Passwords**: Use app-specific passwords, not main account passwords
3. **Email Encryption**: Always use TLS (`SMTP_USE_TLS=True`)
4. **Access Control**: Protect the `/api/parent/` endpoints with authentication in production
5. **Content Snippets**: Be mindful of including content snippets in emails

## Advanced Configuration

### Custom Schedule Interval

To change the scheduler check interval, edit `backend/services/report_scheduler.py`:

```python
# Change from hourly to every 30 minutes
self.scheduler.add_job(
    self.check_and_send_reports,
    trigger=CronTrigger(minute='*/30'),  # Every 30 minutes
    ...
)
```

### Timezone Handling

The scheduler uses the server's local timezone. To use a specific timezone:

```python
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

scheduler = BackgroundScheduler(timezone=pytz.timezone('America/New_York'))
```

## Example Workflows

### Parent Wants Weekly Reports on Monday at 9 AM

```bash
PUT /api/parent/preferences?user_id=1
{
  "email": "parent@example.com",
  "email_notifications_enabled": true,
  "summary_frequency": "weekly",
  "summary_day_of_week": 0,  // Monday
  "summary_hour": 9
}
```

The system will automatically send a report every Monday at 9:00 AM.

### Parent Wants Daily Reports at 6 PM

```bash
PUT /api/parent/preferences?user_id=1
{
  "email": "parent@example.com",
  "email_notifications_enabled": true,
  "summary_frequency": "daily",
  "summary_hour": 18  // 6 PM
}
```

The system will automatically send a report every day at 6:00 PM.

### Parent Wants to Disable Automated Reports

```bash
PUT /api/parent/preferences?user_id=1
{
  "summary_frequency": "none"
}
```

Automated reports will stop, but reports can still be sent manually via the API.

## Support

For issues or questions:
- Check the logs: `backend/logs/chatbot.log`
- Review preferences: `GET /api/parent/preferences?user_id=1`
- Test email config: `POST /api/parent/test-notification?user_id=1`
