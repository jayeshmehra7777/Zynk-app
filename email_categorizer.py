#!/usr/bin/env python3
"""
Enhanced Email Categorization and Summarization System
This system categorizes emails by type and topic, then generates summaries for newsletters/blogs.
"""

import re
import os
import json
import base64
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import defaultdict

import nltk
import pandas as pd
from textblob import TextBlob
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

from gmail_reader import GmailReader

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class EmailCategorizer:
    def __init__(self):
        self.gmail = GmailReader()
        
        # Predefined categories and keywords
        self.categories = {
            'technology': [
                'ai', 'artificial intelligence', 'machine learning', 'tech', 'software', 
                'programming', 'coding', 'developer', 'startup', 'innovation', 'digital',
                'blockchain', 'cryptocurrency', 'cloud', 'cybersecurity', 'data science'
            ],
            'finance': [
                'finance', 'money', 'investment', 'trading', 'stock', 'market', 'economy',
                'banking', 'cryptocurrency', 'bitcoin', 'portfolio', 'wealth', 'financial'
            ],
            'investing': [
                'investing', 'investment', 'portfolio', 'stocks', 'bonds', 'etf', 'mutual fund',
                'dividend', 'returns', 'asset', 'equity', 'venture capital', 'ipo'
            ],
            'geopolitics': [
                'politics', 'government', 'election', 'policy', 'international', 'global',
                'war', 'conflict', 'diplomacy', 'trade war', 'sanctions', 'geopolitical'
            ],
            'business': [
                'business', 'company', 'corporate', 'enterprise', 'management', 'strategy',
                'leadership', 'entrepreneurship', 'revenue', 'profit', 'growth'
            ],
            'health': [
                'health', 'medical', 'wellness', 'fitness', 'nutrition', 'healthcare',
                'medicine', 'disease', 'treatment', 'therapy', 'mental health'
            ],
            'education': [
                'education', 'learning', 'course', 'university', 'school', 'training',
                'skill', 'knowledge', 'academic', 'research', 'study'
            ]
        }
        
        # Newsletter/blog indicators
        self.newsletter_indicators = [
            'newsletter', 'digest', 'weekly', 'daily', 'update', 'bulletin',
            'unsubscribe', 'medium.com', 'substack', 'blog', 'article'
        ]
        
    def authenticate(self):
        """Authenticate with Gmail API"""
        self.gmail.authenticate()
    
    def categorize_email_type(self, email_data: Dict) -> str:
        """Categorize email into main types: articles, jobs, notifications, promotions, personal"""
        subject = email_data['subject'].lower()
        sender = email_data['sender'].lower()
        body = email_data['body'].lower()
        text_to_check = f"{subject} {sender} {body}"
        
        # Job alerts and career-related emails
        job_indicators = [
            'job alert', 'job opportunity', 'career', 'hiring', 'position available',
            'linkedin job', 'indeed', 'glassdoor', 'naukri', 'monster.com',
            'recruitment', 'vacancy', 'apply now', 'job match'
        ]
        
        for indicator in job_indicators:
            if indicator in text_to_check:
                return 'jobs'
        
        # Promotional emails and marketing
        promo_indicators = [
            'sale', 'discount', 'offer', 'deal', 'coupon', 'promo', 'limited time',
            'buy now', 'shop now', 'free shipping', 'save money', 'special offer'
        ]
        
        for indicator in promo_indicators:
            if indicator in text_to_check:
                return 'promotions'
        
        # System notifications and alerts
        notification_indicators = [
            'notification', 'alert', 'reminder', 'security', 'password',
            'account', 'verification', 'confirm', 'activate', 'update required'
        ]
        
        for indicator in notification_indicators:
            if indicator in text_to_check:
                return 'notifications'
        
        # Articles, blogs, and newsletters (content-focused)
        article_indicators = [
            'newsletter', 'digest', 'weekly', 'daily update', 'blog',
            'article', 'read more', 'latest news', 'insights', 'analysis',
            'medium.com', 'substack', 'the-ken.com', 'economic times',
            'techcrunch', 'hacker news', 'ycombinator'
        ]
        
        article_domains = [
            'medium.com', 'substack.com', 'the-ken.com', 'techcrunch.com',
            'hbr.org', 'mit.edu', 'stanford.edu', 'newsletter', 'digest'
        ]
        
        # Check for article indicators
        for indicator in article_indicators:
            if indicator in text_to_check:
                return 'articles'
        
        # Check sender domains for articles
        for domain in article_domains:
            if domain in sender:
                return 'articles'
        
        # Default to personal for everything else
        return 'personal'
    
    def is_newsletter_or_blog(self, email_data: Dict) -> bool:
        """Determine if an email is a newsletter or blog post (for backward compatibility)"""
        return self.categorize_email_type(email_data) == 'articles'
    
    def extract_clean_text(self, html_content: str) -> str:
        """Extract clean text from HTML content"""
        if not html_content:
            return ""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception:
            return html_content
    
    def categorize_by_topic(self, text: str) -> str:
        """Categorize email by topic based on keywords"""
        text_lower = text.lower()
        scores = {}
        
        for category, keywords in self.categories.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'general'
    
    def generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """Generate extractive summary of the text"""
        if not text or len(text.strip()) < 100:
            return text[:200] + "..." if len(text) > 200 else text
        
        try:
            # Clean text
            clean_text = self.extract_clean_text(text)
            if len(clean_text) < 100:
                return clean_text
            
            # Split into sentences
            blob = TextBlob(clean_text)
            sentences = [str(sentence) for sentence in blob.sentences]
            
            if len(sentences) <= max_sentences:
                return ' '.join(sentences)
            
            # Use TF-IDF to find most important sentences
            vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
            
            try:
                tfidf_matrix = vectorizer.fit_transform(sentences)
                sentence_scores = tfidf_matrix.sum(axis=1).A1
                
                # Get top sentences
                top_indices = sentence_scores.argsort()[-max_sentences:][::-1]
                top_indices.sort()  # Maintain original order
                
                summary_sentences = [sentences[i] for i in top_indices]
                return ' '.join(summary_sentences)
            
            except Exception:
                # Fallback: return first few sentences
                return ' '.join(sentences[:max_sentences])
        
        except Exception:
            # Final fallback
            return text[:300] + "..." if len(text) > 300 else text
    
    def extract_article_info(self, email_data: Dict) -> Dict:
        """Extract article information from newsletter/blog email"""
        full_text = f"{email_data['subject']} {email_data['body']}"
        clean_text = self.extract_clean_text(full_text)
        
        return {
            'id': email_data['id'],
            'title': email_data['subject'],
            'sender': email_data['sender'],
            'date': email_data['date'],
            'category': self.categorize_by_topic(clean_text),
            'summary': self.generate_summary(clean_text),
            'full_content': clean_text,
            'snippet': email_data['snippet'],
            'thread_id': email_data['thread_id']
        }
    
    def process_emails(self, query: str = '', max_results: int = 50) -> Dict:
        """Process emails and categorize them into sections"""
        print(f"🔍 Fetching emails with query: '{query}'")
        
        # Get messages from Gmail
        messages = self.gmail.get_messages(query=query, max_results=max_results)
        
        if not messages:
            return {
                'sections': {
                    'articles': [],
                    'jobs': [],
                    'promotions': [],
                    'notifications': [],
                    'personal': []
                },
                'article_categories': {},
                'stats': {}
            }
        
        print(f"📧 Processing {len(messages)} emails...")
        
        # Initialize sections
        sections = {
            'articles': [],
            'jobs': [],
            'promotions': [],
            'notifications': [],
            'personal': []
        }
        
        article_categories = defaultdict(list)
        
        for i, message in enumerate(messages):
            print(f"Processing email {i+1}/{len(messages)}")
            
            # Get detailed message information
            email_data = self.gmail.get_message_details(message['id'])
            if not email_data:
                continue
            
            # Categorize email type
            email_type = self.categorize_email_type(email_data)
            
            if email_type == 'articles':
                # For articles, extract full article info with topic categorization
                article_info = self.extract_article_info(email_data)
                sections['articles'].append(article_info)
                article_categories[article_info['category']].append(article_info)
            else:
                # For other types, create simplified info
                email_info = {
                    'id': email_data['id'],
                    'title': email_data['subject'],
                    'sender': email_data['sender'],
                    'date': email_data['date'],
                    'snippet': email_data['snippet'],
                    'thread_id': email_data['thread_id'],
                    'type': email_type
                }
                sections[email_type].append(email_info)
        
        # Calculate stats
        total_by_section = {section: len(emails) for section, emails in sections.items()}
        
        print(f"✅ Processed emails by section:")
        for section, count in total_by_section.items():
            if count > 0:
                print(f"   {section.title()}: {count} emails")
        
        return {
            'sections': sections,
            'article_categories': dict(article_categories),
            'stats': {
                'total_emails': len(messages),
                'by_section': total_by_section,
                'article_categories_found': list(article_categories.keys())
            }
        }
    
    def save_processed_data(self, data: Dict, filename: str = 'processed_emails.json'):
        """Save processed email data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"💾 Saved processed data to {filename}")
        except Exception as e:
            print(f"❌ Error saving data: {e}")
    
    def load_processed_data(self, filename: str = 'processed_emails.json') -> Dict:
        """Load processed email data from JSON file"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ Error loading data: {e}")
        return {'newsletters': [], 'regular_emails': [], 'categories': {}}

def main():
    """Main function to demonstrate email categorization"""
    print("🚀 Email Categorization and Summarization System")
    print("=" * 60)
    
    categorizer = EmailCategorizer()
    
    try:
        # Authenticate
        categorizer.authenticate()
        
        # Process recent emails
        print("\n📥 Processing recent emails...")
        processed_data = categorizer.process_emails(query='newer_than:7d', max_results=30)
        
        # Save processed data
        categorizer.save_processed_data(processed_data)
        
        # Display results
        stats = processed_data['stats']
        print(f"\n📊 Processing Results:")
        print(f"Total emails processed: {stats['total_emails']}")
        print(f"Newsletters/blogs found: {stats['newsletters_count']}")
        print(f"Regular emails: {stats['regular_emails_count']}")
        print(f"Categories identified: {', '.join(stats['categories_found'])}")
        
        # Show newsletter summaries by category
        print(f"\n📰 Newsletter Summaries by Category:")
        print("=" * 60)
        
        for category, articles in processed_data['categories'].items():
            print(f"\n🏷️  {category.upper()} ({len(articles)} articles)")
            print("-" * 40)
            
            for article in articles[:3]:  # Show top 3 per category
                print(f"📄 {article['title']}")
                print(f"From: {article['sender']}")
                print(f"Summary: {article['summary'][:150]}...")
                print(f"Date: {article['date']}")
                print()
        
        print(f"\n✅ Email categorization complete!")
        print(f"💡 Next: Run the web interface to view articles as playcards")
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
