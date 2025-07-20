// Zynk Email Intelligence Dashboard JavaScript

class EmailDashboard {
    constructor() {
        this.apiBase = 'http://localhost:5002/api';
        this.currentSection = 'articles';
        this.currentCategory = 'all';
        this.currentView = 'grid';
        this.emailsData = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadEmails();
    }
    
    bindEvents() {
        // Section tabs
        document.querySelectorAll('.section-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const section = e.currentTarget.dataset.section;
                this.switchSection(section);
            });
        });
        
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshEmails();
        });
        
        // Process emails button
        document.getElementById('processEmailsBtn').addEventListener('click', () => {
            this.processEmails();
        });
        
        // Process first time button
        document.getElementById('processFirstTime').addEventListener('click', () => {
            this.processEmails();
        });
        
        // View toggle buttons - use event delegation
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('view-btn') || e.target.closest('.view-btn')) {
                const btn = e.target.classList.contains('view-btn') ? e.target : e.target.closest('.view-btn');
                const view = btn.dataset.view;
                if (view) {
                    this.toggleView(view);
                }
            }
        });
        
        // Category buttons - use event delegation to handle dynamically created buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('category-btn') || e.target.closest('.category-btn')) {
                const btn = e.target.classList.contains('category-btn') ? e.target : e.target.closest('.category-btn');
                const category = btn.dataset.category;
                if (category) {
                    this.filterByCategory(category);
                }
            }
        });
        
        // Modal close
        document.getElementById('modalClose').addEventListener('click', () => {
            this.closeModal();
        });
        
        // Close modal on backdrop click
        document.getElementById('articleModal').addEventListener('click', (e) => {
            if (e.target.id === 'articleModal') {
                this.closeModal();
            }
        });
        
        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }
    
    async loadEmails() {
        try {
            this.showLoading();
            
            const response = await fetch(`${this.apiBase}/emails`);
            const result = await response.json();
            
            if (result.success) {
                this.emailsData = result.data;
                this.updateUI();
                this.showEmails();
            } else {
                this.showEmpty();
            }
        } catch (error) {
            console.error('Error loading emails:', error);
            this.showToast('Failed to load emails', 'error');
            this.showEmpty();
        }
    }
    
    async refreshEmails() {
        try {
            this.showToast('Refreshing emails...', 'info');
            
            const response = await fetch(`${this.apiBase}/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: 'newer_than:7d',
                    max_results: 50
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.emailsData = result.data;
                this.updateUI();
                this.showEmails();
                this.showToast('Emails refreshed successfully!', 'success');
            } else {
                this.showToast(result.error || 'Failed to refresh emails', 'error');
            }
        } catch (error) {
            console.error('Error refreshing emails:', error);
            this.showToast('Failed to refresh emails', 'error');
        }
    }
    
    async processEmails() {
        try {
            this.showLoading();
            this.showToast('Processing emails... This may take a few minutes', 'info');
            
            const response = await fetch(`${this.apiBase}/process-emails`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: 'newer_than:7d',
                    max_results: 50
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.emailsData = result.data;
                this.updateUI();
                this.showEmails();
                this.showToast('Emails processed successfully!', 'success');
            } else {
                this.showToast(result.error || 'Failed to process emails', 'error');
                this.showEmpty();
            }
        } catch (error) {
            console.error('Error processing emails:', error);
            this.showToast('Failed to process emails', 'error');
            this.showEmpty();
        }
    }
    
    updateUI() {
        if (!this.emailsData) return;
        
        // Update section tab counts
        this.updateSectionCounts();
        
        // Update category filters (only for articles section)
        if (this.currentSection === 'articles') {
            this.updateCategoryFilters();
        }
        
        // Update total count in header
        const stats = this.emailsData.stats || {};
        const totalEmails = stats.total_emails || 0;
        document.getElementById('totalCount').textContent = totalEmails;
    }
    
    updateSectionCounts() {
        if (!this.emailsData || !this.emailsData.sections) return;
        
        const sections = this.emailsData.sections;
        
        // Update each section tab count
        Object.keys(sections).forEach(section => {
            const countElement = document.getElementById(`count-${section}`);
            if (countElement) {
                countElement.textContent = sections[section].length;
            }
        });
    }
    
    switchSection(section) {
        this.currentSection = section;
        
        // Update active tab
        document.querySelectorAll('.section-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`).classList.add('active');
        
        // Show/hide sidebar based on section
        const sidebar = document.getElementById('articlesSidebar');
        const contentLayout = document.getElementById('contentLayout');
        
        if (section === 'articles') {
            sidebar.style.display = 'block';
            contentLayout.classList.remove('no-sidebar');
            // Reset to 'all' category when switching to articles
            this.currentCategory = 'all';
            this.updateCategoryFilters();
        } else {
            sidebar.style.display = 'none';
            contentLayout.classList.add('no-sidebar');
        }
        
        // Update content area
        this.displayCurrentSection();
    }
    
    updateCategoryFilters() {
        const filtersContainer = document.getElementById('categoryFilters');
        const categories = this.emailsData.article_categories || {};
        
        // Clear existing filters except "All"
        const allButton = filtersContainer.querySelector('[data-category="all"]');
        filtersContainer.innerHTML = '';
        filtersContainer.appendChild(allButton);
        
        // Update "All" count
        const totalCount = this.emailsData.sections && this.emailsData.sections.articles ? this.emailsData.sections.articles.length : 0;
        allButton.querySelector('.count').textContent = totalCount;
        
        // Add category filters
        Object.entries(categories).forEach(([category, emails]) => {
            const button = document.createElement('button');
            button.className = 'category-btn';
            button.dataset.category = category;
            
            button.innerHTML = `
                <span>
                    <i class="fas fa-tag"></i>
                    ${this.formatCategoryName(category)}
                </span>
                <span class="count">${emails.length}</span>
            `;
            
            button.addEventListener('click', () => {
                this.filterByCategory(category);
            });
            
            filtersContainer.appendChild(button);
        });
    }
    
    displayCurrentSection() {
        if (!this.emailsData) return;
        
        if (this.currentSection === 'articles') {
            this.displayArticles();
        } else {
            this.displaySectionEmails();
        }
    }
    
    displayEmails() {
        // Generic method to display emails based on current section
        this.displayCurrentSection();
    }
    
    displaySectionEmails() {
        if (!this.emailsData || !this.emailsData.sections) return;
        
        const emails = this.emailsData.sections[this.currentSection] || [];
        const articlesContainer = document.getElementById('articlesList');
        
        // Update header
        document.getElementById('currentCategory').textContent = this.formatSectionName(this.currentSection);
        
        articlesContainer.innerHTML = '';
        
        if (emails.length === 0) {
            articlesContainer.innerHTML = `
                <div class="empty-category">
                    <p>No ${this.currentSection} found.</p>
                </div>
            `;
            return;
        }
        
        emails.forEach(email => {
            const emailCard = this.createSectionEmailCard(email);
            articlesContainer.appendChild(emailCard);
        });
    }
    
    createSectionEmailCard(email) {
        const card = document.createElement('div');
        card.className = 'article-card';
        card.addEventListener('click', () => this.openSectionEmail(email));
        
        const date = new Date(email.date).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        
        card.innerHTML = `
            <div class="article-header">
                <h3 class="article-title">${this.escapeHtml(email.title)}</h3>
                <div class="article-meta">
                    <span class="article-sender">${this.escapeHtml(email.sender)}</span>
                    <span class="article-date">${date}</span>
                </div>
                <span class="article-category ${email.type}">${this.formatSectionName(email.type)}</span>
            </div>
            <div class="article-summary">
                ${this.escapeHtml(email.snippet)}
            </div>
        `;
        
        return card;
    }
    
    openSectionEmail(email) {
        document.getElementById('modalTitle').textContent = email.title;
        document.getElementById('modalSender').textContent = `From: ${email.sender}`;
        document.getElementById('modalDate').textContent = new Date(email.date).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        document.getElementById('modalCategory').textContent = this.formatSectionName(email.type);
        document.getElementById('modalCategory').className = `article-category ${email.type}`;
        
        document.getElementById('modalContent').innerHTML = `<p>${this.escapeHtml(email.snippet)}</p>`;
        
        document.getElementById('articleModal').classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    formatSectionName(section) {
        const sectionNames = {
            'articles': 'Articles & Blogs',
            'jobs': 'Job Alerts',
            'promotions': 'Promotions',
            'notifications': 'Notifications',
            'personal': 'Personal'
        };
        return sectionNames[section] || section.charAt(0).toUpperCase() + section.slice(1);
    }
    
    formatCategoryName(category) {
        return category.charAt(0).toUpperCase() + category.slice(1);
    }
    
    filterByCategory(category) {
        this.currentCategory = category;
        
        // Update active button
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-category="${category}"]`).classList.add('active');
        
        // Update header
        document.getElementById('currentCategory').textContent = 
            category === 'all' ? 'All Articles' : this.formatCategoryName(category);
        
        // Filter and display articles
        this.displayArticles();
    }
    
    displayArticles() {
        if (!this.emailsData) return;
        
        let articles;
        if (this.currentCategory === 'all') {
            articles = this.emailsData.sections && this.emailsData.sections.articles ? this.emailsData.sections.articles : [];
        } else {
            articles = this.emailsData.article_categories && this.emailsData.article_categories[this.currentCategory] ? this.emailsData.article_categories[this.currentCategory] : [];
        }
        
        const articlesContainer = document.getElementById('articlesList');
        articlesContainer.innerHTML = '';
        
        if (articles.length === 0) {
            articlesContainer.innerHTML = `
                <div class="empty-category">
                    <p>No articles found in this category.</p>
                </div>
            `;
            return;
        }
        
        articles.forEach(article => {
            const articleCard = this.createArticleCard(article);
            articlesContainer.appendChild(articleCard);
        });
    }
    
    createArticleCard(article) {
        const card = document.createElement('div');
        card.className = 'article-card';
        card.addEventListener('click', () => this.openArticle(article));
        
        const date = new Date(article.date).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        
        card.innerHTML = `
            <div class="article-header">
                <h3 class="article-title">${this.escapeHtml(article.title)}</h3>
                <div class="article-meta">
                    <span class="article-sender">${this.escapeHtml(article.sender)}</span>
                    <span class="article-date">${date}</span>
                </div>
                <span class="article-category ${article.category}">${this.formatCategoryName(article.category)}</span>
            </div>
            <div class="article-summary">
                ${this.escapeHtml(article.summary)}
            </div>
        `;
        
        return card;
    }
    
    openArticle(article) {
        document.getElementById('modalTitle').textContent = article.title;
        document.getElementById('modalSender').textContent = `From: ${article.sender}`;
        document.getElementById('modalDate').textContent = new Date(article.date).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        document.getElementById('modalCategory').textContent = this.formatCategoryName(article.category);
        document.getElementById('modalCategory').className = `article-category ${article.category}`;
        
        // Format content with paragraphs
        const content = article.full_content || article.summary;
        const formattedContent = content.split('\n').map(paragraph => 
            paragraph.trim() ? `<p>${this.escapeHtml(paragraph.trim())}</p>` : ''
        ).join('');
        
        document.getElementById('modalContent').innerHTML = formattedContent || '<p>No content available.</p>';
        
        document.getElementById('articleModal').classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    closeModal() {
        document.getElementById('articleModal').classList.remove('active');
        document.body.style.overflow = '';
    }
    
    toggleView(view) {
        console.log('Toggling view to:', view);
        this.currentView = view;
        
        // Update button states - ensure all view buttons are updated
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.view === view) {
                btn.classList.add('active');
            }
        });
        
        // Update grid/list view
        const emailsGrid = document.getElementById('emailsGrid');
        if (emailsGrid) {
            emailsGrid.className = `emails-${view}`;
        }
        
        // Re-display emails with new view
        this.displayEmails();
        
        // Show success message
        this.showToast(`Switched to ${view} view`, 'success');
    }
    
    showLoading() {
        document.getElementById('loadingState').style.display = 'flex';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('emailsGrid').style.display = 'none';
    }
    
    showEmpty() {
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('emptyState').style.display = 'flex';
        document.getElementById('emailsGrid').style.display = 'none';
    }
    
    showEmails() {
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('emailsGrid').style.display = 'block';
        
        this.displayEmails();
    }
    
    filterByCategory(category) {
        console.log('Filtering by category:', category);
        this.currentCategory = category;
        
        // Update category button states
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.category === category) {
                btn.classList.add('active');
            }
        });
        
        // Re-display emails with new filter
        this.displayEmails();
        
        // Show success message
        const categoryName = category === 'all' ? 'All Articles' : this.formatCategoryName(category);
        this.showToast(`Showing ${categoryName}`, 'success');
    }
    
    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        const icon = toast.querySelector('.toast-icon');
        const messageEl = toast.querySelector('.toast-message');
        
        // Set icon based on type
        if (type === 'success') {
            icon.className = 'toast-icon fas fa-check-circle';
            toast.className = 'toast';
        } else if (type === 'error') {
            icon.className = 'toast-icon fas fa-exclamation-circle';
            toast.className = 'toast error';
        } else if (type === 'info') {
            icon.className = 'toast-icon fas fa-info-circle';
            toast.className = 'toast';
        }
        
        messageEl.textContent = message;
        toast.classList.add('show');
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            toast.classList.remove('show');
        }, 5000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new EmailDashboard();
});

// Service worker for offline functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
