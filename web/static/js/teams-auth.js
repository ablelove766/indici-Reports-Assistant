/**
 * Microsoft Teams SSO Authentication Module
 * Handles silent authentication and token exchange for Teams tabs
 */

class TeamsAuthManager {
    constructor() {
        this.isInitialized = false;
        this.currentUser = null;
        this.accessToken = null;
        this.teamsContext = null;
        this.authCallbacks = [];
        
        // Initialize Teams SDK
        this.initializeTeamsSDK();
    }
    
    /**
     * Initialize Microsoft Teams SDK
     */
    async initializeTeamsSDK() {
        try {
            console.log('🔐 Initializing Teams SDK for SSO...');
            
            // Check if Teams SDK is available
            if (typeof microsoftTeams === 'undefined') {
                console.warn('⚠️ Teams SDK not available, running in standalone mode');
                this.isInitialized = true;
                return;
            }
            
            // Initialize Teams SDK
            await microsoftTeams.app.initialize();
            console.log('✅ Teams SDK initialized successfully');
            
            // Get Teams context
            this.teamsContext = await microsoftTeams.app.getContext();
            console.log('📋 Teams context:', this.teamsContext);
            
            this.isInitialized = true;
            
            // Attempt silent authentication
            await this.performSilentAuth();
            
        } catch (error) {
            console.error('❌ Failed to initialize Teams SDK:', error);
            this.isInitialized = true; // Continue without Teams features
        }
    }
    
    /**
     * Perform silent authentication using Teams SSO
     */
    async performSilentAuth() {
        try {
            console.log('🔐 Attempting silent authentication...');
            
            if (typeof microsoftTeams === 'undefined') {
                console.log('⚠️ Teams SDK not available, skipping silent auth');
                return false;
            }
            
            // Request Teams SSO token
            const authTokenRequest = {
                successCallback: async (token) => {
                    console.log('✅ Teams SSO token received');
                    await this.handleTeamsToken(token);
                },
                failureCallback: (error) => {
                    console.warn('⚠️ Silent auth failed:', error);
                    this.handleAuthFailure(error);
                }
            };
            
            // Use Teams SDK to get SSO token
            microsoftTeams.authentication.getAuthToken(authTokenRequest);
            
        } catch (error) {
            console.error('❌ Silent authentication error:', error);
            this.handleAuthFailure(error);
            return false;
        }
    }
    
    /**
     * Handle Teams SSO token and exchange for Graph token
     */
    async handleTeamsToken(teamsToken) {
        try {
            console.log('🔄 Exchanging Teams token for Graph token...');
            
            // Exchange Teams token for Graph token via backend
            const response = await fetch('/auth/token-exchange', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Teams-Token': teamsToken
                },
                body: JSON.stringify({
                    token: teamsToken
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('✅ Token exchange successful');
                
                this.currentUser = data.user;
                this.accessToken = teamsToken; // Store Teams token
                
                // Notify authentication success
                this.notifyAuthSuccess(data.user);
                
                return true;
            } else {
                const errorData = await response.json();
                console.error('❌ Token exchange failed:', errorData);
                this.handleAuthFailure(errorData);
                return false;
            }
            
        } catch (error) {
            console.error('❌ Error handling Teams token:', error);
            this.handleAuthFailure(error);
            return false;
        }
    }
    
    /**
     * Handle authentication failure
     */
    handleAuthFailure(error) {
        console.warn('🔐 Authentication failed, continuing without auth:', error);
        
        // Notify callbacks about auth failure
        this.authCallbacks.forEach(callback => {
            try {
                callback(null, error);
            } catch (e) {
                console.error('Error in auth callback:', e);
            }
        });
    }
    
    /**
     * Notify authentication success
     */
    notifyAuthSuccess(user) {
        console.log('🎉 Authentication successful for user:', user.displayName);
        
        // Update UI to show authenticated state
        this.updateUIForAuthenticatedUser(user);
        
        // Notify callbacks about auth success
        this.authCallbacks.forEach(callback => {
            try {
                callback(user, null);
            } catch (e) {
                console.error('Error in auth callback:', e);
            }
        });
    }
    
    /**
     * Update UI for authenticated user
     */
    updateUIForAuthenticatedUser(user) {
        try {
            // Update sidebar with user info
            const sidebarFooter = document.querySelector('.sidebar-footer');
            if (sidebarFooter) {
                const userInfo = document.createElement('div');
                userInfo.className = 'user-info';
                userInfo.innerHTML = `
                    <div class="user-avatar">
                        <i class="fas fa-user-circle"></i>
                    </div>
                    <div class="user-details">
                        <div class="user-name">${user.displayName || 'User'}</div>
                        <div class="user-email">${user.mail || user.userPrincipalName || ''}</div>
                    </div>
                `;
                
                // Insert before version info
                const versionElement = sidebarFooter.querySelector('.version');
                if (versionElement) {
                    sidebarFooter.insertBefore(userInfo, versionElement);
                } else {
                    sidebarFooter.appendChild(userInfo);
                }
            }
            
            // Update header to show authenticated state
            const headerInfo = document.querySelector('.header-info p');
            if (headerInfo) {
                headerInfo.textContent = `Welcome, ${user.displayName || 'User'}! Your intelligent assistant for indici Reports`;
            }
            
        } catch (error) {
            console.error('Error updating UI for authenticated user:', error);
        }
    }
    
    /**
     * Register callback for authentication events
     */
    onAuthStateChange(callback) {
        this.authCallbacks.push(callback);
        
        // If already authenticated, call immediately
        if (this.currentUser) {
            callback(this.currentUser, null);
        }
    }
    
    /**
     * Get current user
     */
    getCurrentUser() {
        return this.currentUser;
    }
    
    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return this.currentUser !== null;
    }
    
    /**
     * Get access token
     */
    getAccessToken() {
        return this.accessToken;
    }
    
    /**
     * Logout user
     */
    async logout() {
        try {
            // Call backend logout
            await fetch('/auth/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            // Clear local state
            this.currentUser = null;
            this.accessToken = null;
            
            // Notify callbacks
            this.authCallbacks.forEach(callback => {
                try {
                    callback(null, null);
                } catch (e) {
                    console.error('Error in auth callback:', e);
                }
            });
            
            console.log('✅ Logout successful');
            
        } catch (error) {
            console.error('❌ Logout error:', error);
        }
    }
}

// Global Teams authentication manager
window.teamsAuth = new TeamsAuthManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TeamsAuthManager;
}
