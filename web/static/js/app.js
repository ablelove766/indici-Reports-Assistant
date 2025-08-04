// Indici Reports Assistant - Frontend JavaScript

// Global print function for provider capitation reports - Teams compatible
window.openPrintWindow = function(printContent) {
    console.log('Opening print window...');

    // If no content provided, try to get it from the page
    if (!printContent) {
        // Look for print content in the latest chat message
        const chatMessages = document.getElementById('chat-messages');
        const lastMessage = chatMessages.lastElementChild;
        if (lastMessage) {
            const printContentElement = lastMessage.querySelector('#printContent');
            if (printContentElement) {
                printContent = printContentElement.innerHTML;
            } else {
                // Extract table content from the message
                const tables = lastMessage.querySelectorAll('table');
                if (tables.length > 0) {
                    let extractedContent = '<div class="print-container">';
                    extractedContent += '<div class="print-header"><h2>Provider Capitation Report</h2></div>';
                    tables.forEach(table => {
                        extractedContent += table.outerHTML;
                    });
                    extractedContent += '</div>';
                    printContent = extractedContent;
                }
            }
        }
    }

    if (!printContent) {
        alert('No print content found. Please try again.');
        return;
    }

    // Check if we're in Teams environment
    const isTeams = window.location.href.includes('/teams') ||
                   window.navigator.userAgent.includes('Teams') ||
                   window.parent !== window;

    if (isTeams) {
        // Teams-compatible print: Use current window with print styles
        console.log('Teams environment detected, using inline print...');
        createInlinePrintView(printContent);
    } else {
        // Regular browser: Try popup window first, fallback to inline
        console.log('Regular browser, attempting popup window...');
        try {
            const printWindow = window.open('', '_blank', 'width=800,height=600,scrollbars=yes');
            if (printWindow && !printWindow.closed) {
                createPopupPrintWindow(printWindow, printContent);
            } else {
                throw new Error('Popup blocked');
            }
        } catch (error) {
            console.log('Popup blocked, falling back to inline print...');
            createInlinePrintView(printContent);
        }
    }
};

// Teams-compatible inline print function
function createInlinePrintView(printContent) {
    // Create overlay with print content
    const printOverlay = document.createElement('div');
    printOverlay.id = 'print-overlay';
    printOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: white;
        z-index: 10000;
        overflow: auto;
        padding: 20px;
        box-sizing: border-box;
    `;

    printOverlay.innerHTML = `
        <div class="print-container">
            <div class="print-header">
                <h2>Provider Capitation Report</h2>
            </div>
            ${printContent}
            <div class="print-controls" style="text-align: center; margin: 20px 0; padding: 20px; border: 1px solid #ddd; background: #f8f9fa;">
                <button onclick="window.print()" style="margin: 0 10px; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; background-color: #007bff; color: white;">
                    🖨️ Print Report
                </button>
                <button onclick="closePrintOverlay()" style="margin: 0 10px; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; background-color: #6c757d; color: white;">
                    ❌ Close
                </button>
            </div>
        </div>
    `;

    // Add print styles
    const printStyles = document.createElement('style');
    printStyles.innerHTML = `
        @media print {
            body * {
                visibility: hidden;
            }
            #print-overlay, #print-overlay * {
                visibility: visible;
            }
            #print-overlay {
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                padding: 0;
                margin: 0;
            }
            .print-controls {
                display: none !important;
            }
        }
    `;
    document.head.appendChild(printStyles);

    // Add close function to global scope
    window.closePrintOverlay = function() {
        const overlay = document.getElementById('print-overlay');
        if (overlay) {
            overlay.remove();
        }
        // Remove print styles
        if (printStyles.parentNode) {
            printStyles.parentNode.removeChild(printStyles);
        }
        delete window.closePrintOverlay;
    };

    document.body.appendChild(printOverlay);
    console.log('Inline print view created for Teams compatibility');
}

// Regular popup window print function
function createPopupPrintWindow(printWindow, printContent) {
    printWindow.document.write(`
<!DOCTYPE html>
<html>
<head>
    <title>Provider Capitation Report - Print</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: white;
        }
        .print-container {
            max-width: 100%;
            margin: 0 auto;
        }
        .print-header {
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }
        .print-header h2 {
            margin: 0;
            font-size: 24px;
            color: #333;
        }
        .provider-section {
            margin-bottom: 30px;
            page-break-inside: avoid;
            padding-bottom: 15px;
        }
        .provider-header {
            text-align: center;
            margin-bottom: 15px;
            border-bottom: 1px solid #000;
            padding-bottom: 5px;
        }
        .provider-header h3 {
            margin: 0;
            font-size: 14px;
            font-weight: bold;
            color: #000;
        }
        .provider-data {
            width: 100%;
        }
        .data-row {
            display: flex;
            width: 100%;
            border-bottom: 1px solid #000;
            min-height: 25px;
            align-items: center;
        }
        .data-row.header-row {
            background-color: #f0f0f0;
            font-weight: bold;
            border-bottom: 2px solid #000;
        }
        .data-row.total-row {
            background-color: #f8f8f8;
            border-top: 2px solid #000;
            border-bottom: none;
            font-weight: bold;
        }
        .age-range {
            flex: 2;
            padding: 5px 8px;
            border-right: 1px solid #000;
        }
        .capitation-amount {
            flex: 1.5;
            padding: 5px 8px;
            text-align: right;
            border-right: 1px solid #000;
        }
        .quantity {
            flex: 1;
            padding: 5px 8px;
            text-align: right;
            border-right: 1px solid #000;
        }
        .total-amount {
            flex: 1.5;
            padding: 5px 8px;
            text-align: right;
        }
        .print-controls {
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            border: 1px solid #ddd;
            background: #f8f9fa;
        }
        .print-controls button {
            margin: 0 10px;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-primary {
            background-color: #007bff;
            color: white;
        }
        .btn-secondary {
            background-color: #6c757d;
            color: white;
        }
        @media print {
            .print-controls {
                display: none !important;
            }
            body {
                margin: 0;
                padding: 0;
            }
            .print-container {
                margin: 0;
                padding: 0;
            }
            /* Hide pagination controls in print */
            .pagination,
            .page-navigation,
            .print-pagination,
            [class*="pagination"],
            [class*="page-nav"] {
                display: none !important;
            }
            /* Remove extra spacing after provider sections */
            .provider-section {
                margin-bottom: 15px;
                padding-bottom: 5px;
            }
            /* Ensure total row has proper line positioning */
            .data-row.total-row {
                border-top: 2px solid #000;
                border-bottom: none;
                margin-top: 2px;
            }
        }
    </style>
</head>
<body>
    ${printContent}

    <div class="print-controls">
        <button onclick="window.print()" class="btn-primary">
            🖨️ Print Report
        </button>
        <button onclick="window.close()" class="btn-secondary">
            ❌ Close Window
        </button>
    </div>

    <script>
        // Auto-trigger print dialog after window loads
        window.onload = function() {
            setTimeout(() => {
                window.print();
                console.log('Print dialog triggered automatically');
            }, 1000);
        };
    </script>
</body>
</html>
        `);

    printWindow.document.close();
    printWindow.focus();
    console.log('Popup print window opened successfully');
}

// Global function for sending messages from buttons
window.sendMessage = function(message) {
    const app = window.chatApp;
    if (app && app.messageInput) {
        app.messageInput.value = message;
        app.sendMessage();
    }
};

class IndiciChatApp {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.messageInput = null;
        this.sendButton = null;
        this.chatMessages = null;
        this.typingIndicator = null;
        this.statusDot = null;
        this.statusText = null;
        this.charCount = null;
        
        this.init();
    }
    
    init() {
        // Initialize DOM elements
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.chatMessages = document.getElementById('chat-messages');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.statusDot = document.getElementById('status-dot');
        this.statusText = document.getElementById('status-text');
        this.charCount = document.querySelector('.char-count');
        
        // Initialize Socket.IO
        this.initSocket();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load sample queries
        this.loadSampleQueries();

        // Load sidebar configuration
        this.loadSidebarConfiguration();

        // Load system status
        this.loadSystemStatus();

        // Initialize UI
        this.updateCharCount();
    }
    
    initSocket() {
        console.log('Initializing socket connection...');
        this.socket = io();

        // Connection events
        this.socket.on('connect', () => {
            console.log('✅ Connected to server successfully');
            this.isConnected = true;
            this.updateConnectionStatus('connected', 'Connected');
        });

        this.socket.on('disconnect', () => {
            console.log('❌ Disconnected from server');
            this.isConnected = false;
            this.updateConnectionStatus('error', 'Disconnected');
        });

        this.socket.on('connect_error', (error) => {
            console.error('❌ Connection error:', error);
            this.updateConnectionStatus('error', 'Connection Error');
        });
        
        // Message events
        this.socket.on('bot_message', (data) => {
            this.addMessage(data.message, 'bot', data.type || 'chat', data.timestamp);
        });
        
        this.socket.on('user_message_echo', (data) => {
            this.addMessage(data.message, 'user', 'chat', data.timestamp);
        });
        
        this.socket.on('bot_typing', (data) => {
            if (data.typing) {
                this.showTypingIndicator();
            } else {
                this.hideTypingIndicator();
            }
        });
        
        this.socket.on('chat_cleared', () => {
            this.clearChatMessages();
        });
    }
    
    setupEventListeners() {
        // Send message on Enter key
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Send button click
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Character count update
        this.messageInput.addEventListener('input', () => {
            this.updateCharCount();
        });
        
        // Auto-resize input
        this.messageInput.addEventListener('input', () => {
            this.autoResizeInput();
        });
    }
    
    updateConnectionStatus(status, text) {
        this.statusDot.className = `status-dot ${status}`;
        this.statusText.textContent = text;
    }
    
    sendMessage() {
        console.log('🟢 ChatApp.sendMessage() called');

        if (!this.messageInput) {
            console.error('❌ Message input not found');
            return;
        }

        const message = this.messageInput.value.trim();

        console.log('📝 SendMessage details:', {
            message: message,
            messageLength: message.length,
            isConnected: this.isConnected,
            socket: !!this.socket,
            inputElement: !!this.messageInput
        });

        if (!message) {
            console.log('⚠️ No message to send');
            return;
        }

        if (!this.socket) {
            console.error('❌ Socket not initialized');
            return;
        }

        if (!this.isConnected) {
            console.error('❌ Not connected to server');
            this.addMessage('❌ Connection error. Please refresh the page.', 'assistant', 'error');
            return;
        }

        console.log('✅ All checks passed, sending message...');

        // Add user message to chat
        console.log('📤 Adding user message to chat');
        this.addMessage(message, 'user', 'chat');

        // Send to server
        console.log('🚀 Sending message to server:', message);
        try {
            this.socket.emit('user_message', { message: message });
            console.log('✅ Message emitted successfully');
        } catch (error) {
            console.error('❌ Error emitting message:', error);
            this.addMessage('❌ Error sending message. Please try again.', 'assistant', 'error');
            return;
        }

        // Clear input
        console.log('🧹 Clearing input and updating UI');
        this.messageInput.value = '';
        this.updateCharCount();
        this.autoResizeInput();

        // Disable send button temporarily
        if (this.sendButton) {
            this.sendButton.disabled = true;
            setTimeout(() => {
                if (this.sendButton) {
                    this.sendButton.disabled = false;
                }
            }, 1000);
        }

        console.log('🎉 SendMessage completed successfully');
    }
    
    addMessage(text, sender, type = 'chat', timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender} ${type}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        // Check if the text contains HTML (starts with <div or <table)
        if (text.trim().startsWith('<div') || text.trim().startsWith('<table')) {
            // For HTML content (reports), render directly without message-text wrapper
            const reportContainer = document.createElement('div');
            reportContainer.className = 'report-container';
            reportContainer.innerHTML = text;
            content.appendChild(reportContainer);

            // Check if this is a print request and auto-trigger print
            if (text.includes('openPrintWindow') || text.includes('Print window will open')) {
                console.log('Print request detected, auto-triggering print window...');
                setTimeout(() => {
                    window.openPrintWindow();
                }, 2000);
            }
        } else {
            // For regular text messages, use message-text wrapper
            const messageText = document.createElement('div');
            messageText.className = 'message-text';
            messageText.innerHTML = text; // Changed to innerHTML to support HTML in text messages
            content.appendChild(messageText);

            // Check if this is a print request in text format
            if (text.includes('openPrintWindow') || text.includes('Print window will open')) {
                console.log('Print request detected in text, auto-triggering print window...');
                setTimeout(() => {
                    window.openPrintWindow();
                }, 2000);
            }
        }
        
        const messageTimestamp = document.createElement('div');
        messageTimestamp.className = 'message-timestamp';
        messageTimestamp.textContent = timestamp ? 
            new Date(timestamp).toLocaleTimeString() : 
            new Date().toLocaleTimeString();
        
        content.appendChild(messageTimestamp);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }
    
    updateCharCount() {
        const length = this.messageInput.value.length;
        this.charCount.textContent = `${length}/500`;
        
        if (length > 450) {
            this.charCount.style.color = 'var(--error-color)';
        } else if (length > 400) {
            this.charCount.style.color = 'var(--warning-color)';
        } else {
            this.charCount.style.color = 'var(--text-muted)';
        }
    }
    
    autoResizeInput() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }
    
    clearChatMessages() {
        this.chatMessages.innerHTML = '';
    }
    
    async loadSampleQueries() {
        try {
            const response = await fetch('/api/samples');
            const data = await response.json();
            
            if (data.success && data.samples) {
                this.displaySampleQueries(data.samples);
            } else {
                this.displaySampleQueriesError();
            }
        } catch (error) {
            console.error('Error loading sample queries:', error);
            this.displaySampleQueriesError();
        }
    }
    
    displaySampleQueries(samplesText) {
        const container = document.getElementById('sample-queries');

        // Parse the samples text to extract individual queries
        const lines = samplesText.split('\n');
        const queries = [];
        let currentQuery = null;

        for (const line of lines) {
            if (line.match(/^\*\*\d+\./)) {
                if (currentQuery) {
                    queries.push(currentQuery);
                }
                currentQuery = {
                    title: line.replace(/^\*\*\d+\.\s*/, '').replace(/\*\*$/, ''),
                    description: '',
                    query: ''
                };
            } else if (line.trim().startsWith('*') && currentQuery) {
                currentQuery.description = line.replace(/^\s*\*/, '').trim();
            } else if (line.trim().startsWith('"') && currentQuery) {
                currentQuery.query = line.trim().replace(/^"/, '').replace(/"$/, '');
            }
        }

        if (currentQuery) {
            queries.push(currentQuery);
        }

        // Group queries by category
        const categories = this.categorizeQueries(queries);

        // Create HTML for categorized queries
        container.innerHTML = '';

        Object.keys(categories).forEach(categoryName => {
            const categoryQueries = categories[categoryName];
            const categoryId = categoryName.toLowerCase().replace(/\s+/g, '-');

            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'query-category';

            categoryDiv.innerHTML = `
                <div class="category-header" onclick="toggleCategory('${categoryId}')">
                    <div class="category-title">
                        <i class="fas fa-chevron-right category-icon" id="icon-${categoryId}"></i>
                        ${categoryName}
                    </div>
                    <div class="category-count">${categoryQueries.length}</div>
                </div>
                <div class="category-content" id="content-${categoryId}">
                    ${categoryQueries.map(query => `
                        <div class="sample-query" onclick="sendSampleQuery('${query.query.replace(/'/g, "\\'")}')">
                            <div class="sample-query-title">${query.title}</div>
                            <div class="sample-query-desc">${query.description}</div>
                            <div class="sample-query-text">"${query.query}"</div>
                        </div>
                    `).join('')}
                </div>
            `;

            container.appendChild(categoryDiv);
        });
    }

    categorizeQueries(queries) {
        const categories = {
            'Provider Capitation Queries': [],
            'Health Check Queries': [],
            'Other Queries': []
        };

        queries.forEach(query => {
            const title = query.title.toLowerCase();
            const description = query.description.toLowerCase();
            const queryText = query.query.toLowerCase();

            if (title.includes('capitation') || title.includes('provider') || title.includes('report') ||
                description.includes('capitation') || queryText.includes('capitation')) {
                categories['Provider Capitation Queries'].push(query);
            } else if (title.includes('health') || title.includes('check') || title.includes('status') ||
                       description.includes('health') || queryText.includes('health')) {
                categories['Health Check Queries'].push(query);
            } else {
                categories['Other Queries'].push(query);
            }
        });

        // Remove empty categories
        Object.keys(categories).forEach(key => {
            if (categories[key].length === 0) {
                delete categories[key];
            }
        });

        return categories;
    }
    
    displaySampleQueriesError() {
        const container = document.getElementById('sample-queries');
        container.innerHTML = '<div class="loading">Failed to load samples</div>';
    }
    
    sendSampleQuery(query) {
        if (!this.isConnected) {
            return;
        }

        this.messageInput.value = query;
        this.updateCharCount();
        this.sendMessage();
    }

    async loadSidebarConfiguration() {
        try {
            const response = await fetch('/api/sidebar-config');
            const data = await response.json();

            if (data.sections) {
                this.displaySidebarItems(data);
            } else {
                this.displaySidebarError();
            }
        } catch (error) {
            console.error('Error loading sidebar config:', error);
            this.displaySidebarError();
        }
    }

    displaySidebarItems(data) {
        const container = document.getElementById('sidebar-sections');

        if (container && data.sections) {
            container.innerHTML = data.sections.map(section => {
                // Determine toggle icon based on style
                let toggleIcon = '';
                if (section.collapsible) {
                    if (section.toggle_style === 'checkmark') {
                        toggleIcon = section.expanded ? '✓' : '✓';
                    } else {
                        toggleIcon = section.expanded ? '▼' : '▶';
                    }
                }

                return `
                    <div class="collapsible-section ${section.toggle_style === 'checkmark' ? 'checkmark-style' : ''}">
                        <div class="section-header ${section.collapsible ? 'clickable' : ''}"
                             ${section.collapsible ? `onclick="toggleSection('${section.id}')"` : ''}>
                            <div class="header-left">
                                <span class="section-icon">${section.icon}</span>
                                <span class="section-title">${section.title}</span>
                            </div>
                            ${section.collapsible ? `<span class="toggle-icon ${section.toggle_style === 'checkmark' ? 'checkmark' : 'arrow'}">${toggleIcon}</span>` : ''}
                        </div>
                        <div class="section-content ${section.expanded ? 'expanded' : 'collapsed'}"
                             id="section-${section.id}">
                            ${section.items.map(item => `
                                <button class="action-btn" onclick="sendSampleQuery('${item.query.replace(/'/g, "\\'")}')">
                                    <span class="icon">${item.icon}</span>
                                    ${item.label}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                `;
            }).join('');
        }
    }

    displaySidebarError() {
        const container = document.getElementById('sidebar-sections');
        if (container) {
            container.innerHTML = '<div class="loading">Failed to load menu</div>';
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/system-status');
            const data = await response.json();

            if (data.configuration) {
                this.updateSystemInfo(data);
            }
        } catch (error) {
            console.error('Error loading system status:', error);
        }
    }

    updateSystemInfo(status) {
        const container = document.getElementById('system-info');

        if (container && status.configuration) {
            const config = status.configuration;
            const approach = config.current_approach;

            let approachText = '';
            if (approach === 'intent_only') {
                approachText = '🎯 Intent Classification Only';
            } else if (approach === 'groq_only') {
                approachText = '🤖 Groq LLM Only';
            } else if (approach === 'qwen_only') {
                approachText = '🧠 QWEN LLM Only';
            } else if (approach === 'multiple_enabled') {
                approachText = '🔄 Multiple Approaches Enabled';
            } else if (approach === 'llm_only') {
                approachText = '🤖 LLM Processing Only';
            } else if (approach === 'both_enabled') {
                approachText = '🔄 Both Approaches Enabled';
            } else {
                approachText = '❌ No Approach Enabled';
            }

            container.innerHTML = `
                <div class="info-item">
                    <strong>Current Approach:</strong><br>
                    ${approachText}
                </div>
                <div class="info-item">
                    <strong>Menu Items:</strong> ${config.sidebar_items_count}
                </div>
                <div class="info-note">
                    Configure in chatbot_config.json
                </div>
            `;
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        // Add to page
        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
}

// Global functions for HTML onclick handlers
function sendSampleQuery(query) {
    if (window.chatApp) {
        window.chatApp.sendSampleQuery(query);
    }
}

function clearChat() {
    if (window.chatApp && window.chatApp.isConnected) {
        window.chatApp.socket.emit('clear_chat');
    }
}

function toggleSection(sectionId) {
    const content = document.getElementById(`section-${sectionId}`);
    const header = content.previousElementSibling;
    const toggleIcon = header.querySelector('.toggle-icon');
    const isCheckmarkStyle = toggleIcon.classList.contains('checkmark');

    if (content.classList.contains('expanded')) {
        content.classList.remove('expanded');
        content.classList.add('collapsed');

        if (isCheckmarkStyle) {
            toggleIcon.textContent = '✓';
            toggleIcon.style.transform = 'rotate(0deg)';
        } else {
            toggleIcon.textContent = '▶';
        }
    } else {
        content.classList.remove('collapsed');
        content.classList.add('expanded');

        if (isCheckmarkStyle) {
            toggleIcon.textContent = '✓';
            toggleIcon.style.transform = 'rotate(90deg)';
        } else {
            toggleIcon.textContent = '▼';
        }
    }
}



function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.header-btn[onclick="toggleSidebar()"] i');
    const appContainer = document.querySelector('.app-container');
    const mainContent = document.querySelector('.main-content');
    const chatContainer = document.querySelector('.chat-container');

    sidebar.classList.toggle('hidden');

    // Update toggle button icon and expand chat area
    if (sidebar.classList.contains('hidden')) {
        toggleBtn.className = 'fas fa-chevron-right';
        toggleBtn.parentElement.title = 'Show Sidebar';

        // Fallback for browsers without :has() support
        appContainer.classList.add('sidebar-hidden');
        if (mainContent) mainContent.style.width = '100vw';
        if (chatContainer) chatContainer.style.maxWidth = '100%';
    } else {
        toggleBtn.className = 'fas fa-bars';
        toggleBtn.parentElement.title = 'Hide Sidebar';

        // Fallback for browsers without :has() support
        appContainer.classList.remove('sidebar-hidden');
        if (mainContent) mainContent.style.width = '';
        if (chatContainer) chatContainer.style.maxWidth = '';
    }
}

function sendMessage() {
    console.log('🔵 Global sendMessage called');
    console.log('🔍 ChatApp exists:', !!window.chatApp);
    console.log('🔍 ChatApp connected:', window.chatApp?.isConnected);
    console.log('🔍 Socket exists:', !!window.chatApp?.socket);

    if (!window.chatApp) {
        console.error('❌ ChatApp not initialized');
        return;
    }

    if (!window.chatApp.isConnected) {
        console.error('❌ Not connected to server');
        return;
    }

    console.log('✅ Calling chatApp.sendMessage()');
    window.chatApp.sendMessage();
}

function toggleCategory(categoryId) {
    const content = document.getElementById(`content-${categoryId}`);
    const icon = document.getElementById(`icon-${categoryId}`);

    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-down category-icon';
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-right category-icon';
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new IndiciChatApp();

    // Add some welcome styling
    setTimeout(() => {
        if (window.chatApp.isConnected) {
            console.log('Indici Reports Assistant ready!');
        }
    }, 1000);
});
