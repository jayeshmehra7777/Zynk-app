#!/usr/bin/env python3
"""
Gmail API Email Reader
This script connects to Gmail API and reads emails from your account.
"""

import os
import json
import base64
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scope - modify as needed
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailReader:
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        """
        Initialize Gmail Reader
        
        Args:
            credentials_file (str): Path to your Gmail API credentials JSON file
            token_file (str): Path to store the authentication token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        
        # Check if token file exists
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(f"Credentials file '{self.credentials_file}' not found. "
                                          "Please download it from Google Cloud Console.")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        # Build the Gmail service
        self.service = build('gmail', 'v1', credentials=creds)
        print("✅ Successfully authenticated with Gmail API")
        
    def get_messages(self, query='', max_results=10):
        """
        Get messages from Gmail
        
        Args:
            query (str): Gmail search query (e.g., 'is:unread', 'from:example@gmail.com')
            max_results (int): Maximum number of messages to retrieve
            
        Returns:
            list: List of message IDs
        """
        try:
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])
            return messages
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def get_message_details(self, message_id):
        """
        Get detailed information about a specific message
        
        Args:
            message_id (str): Gmail message ID
            
        Returns:
            dict: Message details
        """
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full').execute()
            return self.parse_message(message)
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
    
    def parse_message(self, message):
        """
        Parse Gmail message and extract relevant information
        
        Args:
            message (dict): Raw Gmail message
            
        Returns:
            dict: Parsed message data
        """
        payload = message['payload']
        headers = payload.get('headers', [])
        
        # Extract headers
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
        
        # Extract body
        body = self.extract_body(payload)
        
        return {
            'id': message['id'],
            'thread_id': message['threadId'],
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body,
            'snippet': message.get('snippet', '')
        }
    
    def extract_body(self, payload):
        """Extract email body from payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(
                            part['body']['data']).decode('utf-8')
                        break
        else:
            if payload['mimeType'] == 'text/plain':
                if 'data' in payload['body']:
                    body = base64.urlsafe_b64decode(
                        payload['body']['data']).decode('utf-8')
        
        return body
    
    def display_messages(self, messages_data):
        """Display messages in a formatted way"""
        if not messages_data:
            print("No messages found.")
            return
        
        print(f"\n📧 Found {len(messages_data)} messages:\n")
        print("=" * 80)
        
        for i, msg in enumerate(messages_data, 1):
            print(f"\n📨 Message {i}:")
            print(f"Subject: {msg['subject']}")
            print(f"From: {msg['sender']}")
            print(f"Date: {msg['date']}")
            print(f"Snippet: {msg['snippet'][:100]}...")
            if msg['body']:
                print(f"Body: {msg['body'][:200]}...")
            print("-" * 80)

def main():
    """Main function to demonstrate Gmail API usage"""
    print("🚀 Gmail API Email Reader")
    print("=" * 40)
    
    # Initialize Gmail Reader
    gmail = GmailReader()
    
    try:
        # Authenticate
        gmail.authenticate()
        
        # Get recent messages
        print("\n📥 Fetching recent emails...")
        messages = gmail.get_messages(query='', max_results=5)
        
        if not messages:
            print("No messages found.")
            return
        
        # Get detailed information for each message
        messages_data = []
        for message in messages:
            msg_details = gmail.get_message_details(message['id'])
            if msg_details:
                messages_data.append(msg_details)
        
        # Display messages
        gmail.display_messages(messages_data)
        
        # Example: Get unread messages
        print("\n\n📬 Fetching unread emails...")
        unread_messages = gmail.get_messages(query='is:unread', max_results=3)
        
        unread_data = []
        for message in unread_messages:
            msg_details = gmail.get_message_details(message['id'])
            if msg_details:
                unread_data.append(msg_details)
        
        if unread_data:
            print(f"\n📬 Found {len(unread_data)} unread messages:")
            gmail.display_messages(unread_data)
        else:
            print("No unread messages found.")
            
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\n📋 To use this script, you need to:")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API")
        print("4. Create credentials (OAuth 2.0 Client ID)")
        print("5. Download the credentials JSON file")
        print("6. Rename it to 'credentials.json' and place it in this directory")
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
