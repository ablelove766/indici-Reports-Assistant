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
            console.log('🔐 [TeamsAuth] Initializing Teams SDK for SSO...');
            console.log('🔍 [TeamsAuth] Current URL:', window.location.href);
            console.log('🔍 [TeamsAuth] User Agent:', navigator.userAgent);

            // Check if Teams SDK is available
            if (typeof microsoftTeams === 'undefined') {
                console.warn('[TeamsAuth] Teams SDK not available, running in standalone mode');
                this.isInitialized = true;
                return;
            }

            console.log('[TeamsAuth] Teams SDK found, version:', microsoftTeams.version || 'unknown');
            console.log('[TeamsAuth] Teams SDK methods available:', Object.keys(microsoftTeams));

            // Wait a bit to ensure Teams SDK is fully loaded
            await new Promise(resolve => setTimeout(resolve, 2000));

            // Check if already initialized by the main template
            if (window.teamsContext) {
                console.log('✅ [TeamsAuth] Using existing Teams context from main template');
                this.teamsContext = window.teamsContext;
                this.isInitialized = true;

                // Attempt silent authentication
                await this.performSilentAuth();
                return;
            }

            // Initialize Teams SDK if not already done
            console.log('🔄 [TeamsAuth] Initializing Teams SDK...');
            await microsoftTeams.app.initialize();
            console.log('✅ [TeamsAuth] Teams SDK initialized successfully');

            // Get Teams context
            console.log('🔄 [TeamsAuth] Getting Teams context...');
            this.teamsContext = await microsoftTeams.app.getContext();
            console.log('📋 [TeamsAuth] Teams context received:', this.teamsContext);

            this.isInitialized = true;

            // Attempt silent authentication
            await this.performSilentAuth();

        } catch (error) {
            console.error('❌ [TeamsAuth] Failed to initialize Teams SDK:', error);
            console.error('❌ [TeamsAuth] Error details:', error.message, error.stack);
            this.isInitialized = true; // Continue without Teams features
        }
    }
    
    /**
     * Perform silent authentication using Teams SSO
     */
    async performSilentAuth() {
        try {
            console.log('🔐 [TeamsAuth] Attempting silent authentication...');
            console.log('🔍 [TeamsAuth] Teams context available:', !!this.teamsContext);
            console.log('🔍 [TeamsAuth] Teams SDK available:', typeof microsoftTeams !== 'undefined');

            if (typeof microsoftTeams === 'undefined') {
                console.log('⚠️ [TeamsAuth] Teams SDK not available, skipping silent auth');
                return false;
            }

            // Check if we're actually running in Teams
            const isInTeams = this.teamsContext && this.teamsContext.app && this.teamsContext.app.host;
            console.log('🔍 [TeamsAuth] Running in Teams:', isInTeams);
            console.log('🔍 [TeamsAuth] Host info:', this.teamsContext?.app?.host);

            if (!isInTeams) {
                console.log('⚠️ [TeamsAuth] Not running in Teams environment, skipping SSO');
                return false;
            }

            console.log('🔄 [TeamsAuth] Requesting Teams SSO token...');

            // Request Teams SSO token
            const authTokenRequest = {
                successCallback: async (token) => {
                    console.log('✅ [TeamsAuth] Teams SSO token received successfully');
                    console.log('🔍 [TeamsAuth] Token length:', token ? token.length : 0);
                    await this.handleTeamsToken(token);
                },
                failureCallback: (error) => {
                    console.warn('⚠️ [TeamsAuth] Silent auth failed:', error);
                    console.error('❌ [TeamsAuth] Auth failure details:', error);
                    this.handleAuthFailure(error);
                }
            };

            // Use Teams SDK to get SSO token
            console.log('🔄 [TeamsAuth] Calling microsoftTeams.authentication.getAuthToken...');
            microsoftTeams.authentication.getAuthToken(authTokenRequest);

        } catch (error) {
            console.error('❌ [TeamsAuth] Silent authentication error:', error);
            console.error('❌ [TeamsAuth] Error details:', error.message, error.stack);
            this.handleAuthFailure(error);
            return false;
        }
    }
    
    /**
     * Handle Teams SSO token and exchange for Graph token
     */
    async handleTeamsToken(teamsToken) {
        try {
            console.log('🔄 [TeamsAuth] Exchanging Teams token for Graph token...');
            console.log('🔍 [TeamsAuth] Token preview (first 50 chars):', teamsToken ? teamsToken.substring(0, 50) + '...' : 'null');

            if (!teamsToken) {
                console.error('❌ [TeamsAuth] No Teams token provided');
                this.handleAuthFailure('No Teams token provided');
                return false;
            }

            console.log('🔄 [TeamsAuth] Sending token exchange request to /auth/token-exchange');

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

            console.log('🔍 [TeamsAuth] Token exchange response status:', response.status);
            console.log('🔍 [TeamsAuth] Token exchange response headers:', Object.fromEntries(response.headers.entries()));

            if (response.ok) {
                const data = await response.json();
                console.log('✅ [TeamsAuth] Token exchange successful');
                console.log('🔍 [TeamsAuth] Response data:', data);

                this.currentUser = data.user;
                this.accessToken = teamsToken; // Store Teams token

                // Notify authentication success
                this.notifyAuthSuccess(data.user);

                return true;
            } else {
                const errorData = await response.json().catch(() => ({ error: 'Failed to parse error response' }));
                console.error('❌ [TeamsAuth] Token exchange failed with status:', response.status);
                console.error('❌ [TeamsAuth] Error response:', errorData);

                // Show user-friendly error for CAA20004
                if (errorData.error && errorData.error.includes('CAA20004')) {
                    console.error('🚨 [TeamsAuth] CAA20004 Error - Admin consent required!');
                    console.error('🔧 [TeamsAuth] Please grant admin consent in Azure Portal');
                }

                this.handleAuthFailure(errorData);
                return false;
            }

        } catch (error) {
            console.error('❌ [TeamsAuth] Error handling Teams token:', error);
            console.error('❌ [TeamsAuth] Error details:', error.message, error.stack);
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
     * Get authentication status with details
     */
    getAuthStatus() {
        return {
            isAuthenticated: this.isAuthenticated(),
            user: this.currentUser,
            hasToken: !!this.accessToken,
            isInitialized: this.isInitialized,
            teamsContext: this.teamsContext
        };
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

            console.log('✅ [TeamsAuth] Logout successful');

        } catch (error) {
            console.error('❌ [TeamsAuth] Logout error:', error);
        }
    }

    /**
     * Debug function to manually trigger authentication
     */
    async debugAuth() {
        console.log('[TeamsAuth] Manual authentication debug triggered');
        console.log('[TeamsAuth] Current state:');
        console.log('   - Initialized:', this.isInitialized);
        console.log('   - Teams SDK available:', typeof microsoftTeams !== 'undefined');
        console.log('   - Teams context:', this.teamsContext);
        console.log('   - Current user:', this.currentUser);
        console.log('   - Access token:', !!this.accessToken);
        console.log('   - Window location:', window.location.href);
        console.log('   - User agent:', navigator.userAgent);

        // Check Teams SDK methods
        if (typeof microsoftTeams !== 'undefined') {
            console.log('[TeamsAuth] Teams SDK methods:', Object.keys(microsoftTeams));
            if (microsoftTeams.authentication) {
                console.log('[TeamsAuth] Authentication methods:', Object.keys(microsoftTeams.authentication));
            }

            console.log('[TeamsAuth] Attempting manual authentication...');
            await this.performSilentAuth();
        } else {
            console.log('[TeamsAuth] Teams SDK not available for manual auth');

            // Try to load Teams SDK if not available
            console.log('[TeamsAuth] Attempting to load Teams SDK...');
            const script = document.createElement('script');
            script.src = 'https://res.cdn.office.net/teams-js/2.0.0/js/MicrosoftTeams.min.js';
            script.onload = () => {
                console.log('[TeamsAuth] Teams SDK loaded, retrying auth...');
                setTimeout(() => this.initializeTeamsSDK(), 1000);
            };
            script.onerror = () => {
                console.error('[TeamsAuth] Failed to load Teams SDK');
            };
            document.head.appendChild(script);
        }
    }
}

// Initialize Teams authentication manager when DOM is ready
function initializeTeamsAuth() {
    console.log('[TEAMS-INIT] Initializing Teams authentication...');

    // Check if already initialized
    if (window.teamsAuth) {
        console.log('[TEAMS-INIT] Teams auth already initialized');
        return window.teamsAuth;
    }

    try {
        window.teamsAuth = new TeamsAuthManager();
        console.log('[TEAMS-INIT] Teams auth manager created successfully');
        return window.teamsAuth;
    } catch (error) {
        console.error('[TEAMS-INIT] Failed to create Teams auth manager:', error);
        return null;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTeamsAuth);
} else {
    // DOM already loaded
    initializeTeamsAuth();
}

// Also initialize when Teams SDK is ready
if (typeof microsoftTeams !== 'undefined') {
    initializeTeamsAuth();
} else {
    // Wait for Teams SDK to load
    window.addEventListener('load', () => {
        setTimeout(initializeTeamsAuth, 1000);
    });
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TeamsAuthManager;
}
