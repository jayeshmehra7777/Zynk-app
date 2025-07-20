# Gmail API Setup Guide

## Prerequisites

You mentioned you have Gmail API credentials. Follow these steps to set them up:

## Step 1: Place Your Credentials

1. **Rename your credentials file** to `credentials.json`
2. **Place it in this directory**: `/Users/apple/CascadeProjects/Zynk-app/`

The file should look something like this:
```json
{
  "installed": {
    "client_id": "your-client-id.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-client-secret",
    "redirect_uris": ["http://localhost"]
  }
}
```

## Step 2: Run the Script

```bash
cd /Users/apple/CascadeProjects/Zynk-app
python3 gmail_reader.py
```

## Step 3: First-time Authentication

1. The script will open your browser
2. Sign in to your Google account
3. Grant permissions to access Gmail
4. The script will save a `token.json` file for future use

## Features

The script can:

- ✅ **Read recent emails** (default: 5 most recent)
- ✅ **Filter emails** using Gmail search queries
- ✅ **Get unread emails** specifically
- ✅ **Extract email content** (subject, sender, body, date)
- ✅ **Display formatted output**

## Example Usage

### Basic Usage
```python
from gmail_reader import GmailReader

gmail = GmailReader()
gmail.authenticate()

# Get recent messages
messages = gmail.get_messages(max_results=10)
```

### Advanced Queries
```python
# Get unread emails
unread = gmail.get_messages(query='is:unread')

# Get emails from specific sender
from_sender = gmail.get_messages(query='from:example@gmail.com')

# Get emails with specific subject
subject_search = gmail.get_messages(query='subject:important')

# Get emails from last week
recent = gmail.get_messages(query='newer_than:7d')
```

## Security Notes

- ✅ `credentials.json` contains sensitive information
- ✅ `token.json` will be created automatically (also sensitive)
- ✅ Both files are already added to `.gitignore`
- ✅ Never commit these files to version control

## Troubleshooting

### Error: "Credentials file not found"
- Make sure `credentials.json` is in the project directory
- Check the filename is exactly `credentials.json`

### Error: "Access denied"
- Make sure Gmail API is enabled in Google Cloud Console
- Check that your credentials have the right permissions

### Error: "Invalid scope"
- The script uses read-only access by default
- Modify `SCOPES` in the script if you need write access
