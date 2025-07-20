#!/usr/bin/env python3
"""
Flask API for Email Categorization System
Serves categorized and summarized emails to the web interface
"""

import json
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from email_categorizer import EmailCategorizer

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the email categorizer
categorizer = EmailCategorizer()

@app.route('/')
def index():
    """Serve the main web interface"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files (CSS, JS, etc.)"""
    return send_from_directory('.', filename)

@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    """Authenticate with Gmail API"""
    try:
        categorizer.authenticate()
        return jsonify({'success': True, 'message': 'Authentication successful'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/process-emails', methods=['POST'])
def process_emails():
    """Process and categorize emails"""
    try:
        data = request.get_json()
        query = data.get('query', 'newer_than:7d')
        max_results = data.get('max_results', 30)
        
        # Process emails
        processed_data = categorizer.process_emails(query=query, max_results=max_results)
        
        # Save processed data
        categorizer.save_processed_data(processed_data)
        
        return jsonify({
            'success': True,
            'data': processed_data
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/emails')
def get_emails():
    """Get processed emails data"""
    try:
        # Load processed data
        processed_data = categorizer.load_processed_data()
        
        if not processed_data or not processed_data.get('sections'):
            return jsonify({
                'success': False,
                'message': 'No processed emails found. Please process emails first.'
            })
        
        return jsonify({
            'success': True,
            'data': processed_data
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/emails/section/<section>')
def get_emails_by_section(section):
    """Get emails filtered by section"""
    try:
        processed_data = categorizer.load_processed_data()
        sections = processed_data.get('sections', {})
        
        if section not in sections:
            return jsonify({'success': False, 'error': 'Invalid section'}), 400
        
        emails = sections.get(section, [])
        
        return jsonify({
            'success': True,
            'section': section,
            'count': len(emails),
            'emails': emails
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/emails/category/<category>')
def get_emails_by_category(category):
    """Get articles filtered by topic category"""
    try:
        processed_data = categorizer.load_processed_data()
        
        if category == 'all':
            articles = processed_data.get('sections', {}).get('articles', [])
        else:
            articles = processed_data.get('article_categories', {}).get(category, [])
        
        return jsonify({
            'success': True,
            'category': category,
            'count': len(articles),
            'emails': articles
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/email/<email_id>')
def get_email_details(email_id):
    """Get full details of a specific email"""
    try:
        processed_data = categorizer.load_processed_data()
        newsletters = processed_data.get('newsletters', [])
        
        # Find the email by ID
        email = next((e for e in newsletters if e['id'] == email_id), None)
        
        if not email:
            return jsonify({'success': False, 'error': 'Email not found'}), 404
        
        return jsonify({
            'success': True,
            'email': email
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get email processing statistics"""
    try:
        processed_data = categorizer.load_processed_data()
        
        if not processed_data:
            return jsonify({
                'success': False,
                'message': 'No data available'
            })
        
        stats = processed_data.get('stats', {})
        categories = processed_data.get('categories', {})
        
        # Calculate category stats
        category_stats = {}
        for category, emails in categories.items():
            category_stats[category] = {
                'count': len(emails),
                'recent_titles': [email['title'] for email in emails[:3]]
            }
        
        return jsonify({
            'success': True,
            'stats': {
                **stats,
                'category_breakdown': category_stats
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/refresh', methods=['POST'])
def refresh_emails():
    """Refresh and reprocess emails"""
    try:
        data = request.get_json() or {}
        query = data.get('query', 'newer_than:7d')
        max_results = data.get('max_results', 30)
        
        # Authenticate if needed
        try:
            categorizer.authenticate()
        except:
            pass  # May already be authenticated
        
        # Process emails
        processed_data = categorizer.process_emails(query=query, max_results=max_results)
        
        # Save processed data
        categorizer.save_processed_data(processed_data)
        
        return jsonify({
            'success': True,
            'message': 'Emails refreshed successfully',
            'data': processed_data
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Email Categorization API Server")
    print("📱 Web interface will be available at: http://localhost:5000")
    print("🔗 API endpoints:")
    print("   GET  /api/emails - Get all processed emails")
    print("   GET  /api/emails/category/<category> - Get emails by category")
    print("   POST /api/process-emails - Process new emails")
    print("   POST /api/refresh - Refresh email data")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5002)
