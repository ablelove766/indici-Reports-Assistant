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

            // Check authentication status after initialization
            setTimeout(() => {
                this.checkAuthenticationStatus();
            }, 2000);

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

            console.log('🔄 [TeamsAuth] Sending token verification request to /auth/verify');

            // Verify Teams token with backend and store in session
            const response = await fetch('/auth/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Teams-Token': teamsToken,
                    'Authorization': `Bearer ${teamsToken}`
                },
                credentials: 'include',
                body: JSON.stringify({
                    token: teamsToken
                })
            });

            console.log('🔍 [TeamsAuth] Token verification response status:', response.status);
            console.log('🔍 [TeamsAuth] Token verification response headers:', Object.fromEntries(response.headers.entries()));

            if (response.ok) {
                const data = await response.json();
                console.log('✅ [TeamsAuth] Token verification successful');
                console.log('🔍 [TeamsAuth] Response data:', data);

                this.currentUser = data.user;
                this.accessToken = teamsToken; // Store Teams token

                // Process AD data if available
                if (data.ad_data) {
                    console.log('✅ [TeamsAuth] AD data received:', data.ad_data);
                    this.currentUser.ad_data = data.ad_data;
                    
                    // Update UI with AD user information
                    this.updateUIWithADData(data.ad_data);
                } else {
                    console.log('⚠️ [TeamsAuth] No AD data received - user may not be registered in indici');
                    // Show error message for unregistered user
                    this.showADLoginError();
                }

                // Notify authentication success
                this.notifyAuthSuccess(data.user);

                return true;
            } else {
                const errorData = await response.json().catch(() => ({ error: 'Failed to parse error response' }));
                console.error('❌ [TeamsAuth] Token verification failed with status:', response.status);
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
        console.warn('🔐 Authentication failed:', error);

        // Check if we're in Teams mode and should redirect to auth error page
        if (document.body.classList.contains('teams-mode')) {
            console.log('🔐 Teams mode detected, checking if redirect is needed...');

            // Check if this is a critical authentication failure
            const criticalErrors = [
                'ConsentRequired',
                'UiRequired',
                'InteractionRequired',
                'TokenExpired',
                'InvalidGrant'
            ];

            const errorCode = error?.errorCode || error?.code || '';
            const isCriticalError = criticalErrors.some(code =>
                errorCode.includes(code) || (error?.message && error.message.includes(code))
            );

            if (isCriticalError) {
                console.warn('🔐 Critical authentication error detected, redirecting to auth error page');
                this.redirectToAuthError();
                return;
            }
        }

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
     * Redirect to authentication error page
     */
    redirectToAuthError() {
        console.log('🔐 Redirecting to authentication error page...');
        window.location.href = '/auth/error';
    }

    /**
     * Check authentication status and redirect if needed
     */
    async checkAuthenticationStatus() {
        try {
            // Make a request to check authentication status
            const response = await fetch('/teams?auth_check=true', {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'X-Teams-Token': this.currentToken || '',
                    'Authorization': this.currentToken ? `Bearer ${this.currentToken}` : ''
                }
            });

            if (response.status === 401 || response.redirected) {
                console.warn('🔐 Authentication check failed, redirecting to auth error page');
                this.redirectToAuthError();
                return false;
            }

            return true;
        } catch (error) {
            console.error('🔐 Error checking authentication status:', error);
            return false;
        }
    }
    
    /**
     * Notify authentication success
     */
    notifyAuthSuccess(user) {
        console.log('🎉 Authentication successful for user:', user.displayName || user.name || user.email);

        // Update UI to show authenticated state
        this.updateUIForAuthenticatedUser(user);

        // Update user info display in header (if function exists)
        if (typeof updateUserInfoDisplay === 'function') {
            updateUserInfoDisplay(user);
        }

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
                // Remove any existing user info to prevent duplicates
                const existingUserInfo = sidebarFooter.querySelector('.user-info');
                if (existingUserInfo) {
                    existingUserInfo.remove();
                    console.log('🧹 Removed existing user info from sidebar');
                }

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

                console.log('✅ Added user info to sidebar:', user.displayName || 'User');
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
     * Update UI with AD user information
     */
    updateUIWithADData(adData) {
        try {
            console.log('🔄 [TeamsAuth] Updating UI with AD data:', adData);
            
            // Update sidebar with enhanced user info
            const sidebarFooter = document.querySelector('.sidebar-footer');
            if (sidebarFooter) {
                // Remove any existing user info to prevent duplicates
                const existingUserInfo = sidebarFooter.querySelector('.user-info');
                if (existingUserInfo) {
                    existingUserInfo.remove();
                    console.log('🧹 Removed existing user info from sidebar');
                }

                const userInfo = document.createElement('div');
                userInfo.className = 'user-info';
                
                // Use AD full name if available, otherwise fall back to display name
                const fullName = adData.fullName || this.currentUser.displayName || 'User';
                const email = adData.email || this.currentUser.email || this.currentUser.userPrincipalName || '';
                const practiceCount = adData.practiceCount || 0;
                
                userInfo.innerHTML = `
                    <div class="user-avatar">
                        <i class="fas fa-user-circle"></i>
                    </div>
                    <div class="user-details">
                        <div class="user-name">${fullName}</div>
                        <div class="user-email">${email}</div>
                        <div class="user-practices">${practiceCount} practice(s) available</div>
                    </div>
                `;

                // Insert before version info
                const versionElement = sidebarFooter.querySelector('.version');
                if (versionElement) {
                    sidebarFooter.insertBefore(userInfo, versionElement);
                } else {
                    sidebarFooter.appendChild(userInfo);
                }

                console.log('✅ Added enhanced user info to sidebar:', fullName);
            }
            
            // Update header to show authenticated state with AD info
            const headerInfo = document.querySelector('.header-info p');
            if (headerInfo) {
                const fullName = adData.fullName || this.currentUser.displayName || 'User';
                headerInfo.textContent = `Welcome, ${fullName}! Your intelligent assistant for indici Reports`;
            }
            
            // Show practice name and email in top right corner
            this.showUserInfoInTopRight(adData);
            
            // Display practice information if available
            if (adData.practices && adData.practices.length > 0) {
                this.displayPracticeInfo(adData.practices);
            }
            
        } catch (error) {
            console.error('Error updating UI with AD data:', error);
        }
    }
    
    /**
     * Show user info (practice name + email) in top right corner
     */
    showUserInfoInTopRight(adData) {
        try {
            // Remove any existing top right user info
            const existingTopRight = document.querySelector('.top-right-user-info');
            if (existingTopRight) {
                existingTopRight.remove();
            }
            
            const email = adData.email || this.currentUser.email || this.currentUser.userPrincipalName || '';
            const practices = adData.practices || [];
            
            // Get primary practice name or first practice name
            let practiceName = 'No Practice';
            if (practices.length > 0) {
                const primaryPractice = practices.find(p => p.isPrimary) || practices[0];
                practiceName = primaryPractice.practiceName || 'Unknown Practice';
            }
            
            const topRightInfo = document.createElement('div');
            topRightInfo.className = 'top-right-user-info';
            topRightInfo.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 12px 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 1000;
                font-size: 14px;
                max-width: 300px;
                text-align: right;
            `;
            
            topRightInfo.innerHTML = `
                <div style="font-weight: bold; color: #333; margin-bottom: 4px;">🏥 ${practiceName}</div>
                <div style="color: #666; font-size: 12px;">${email}</div>
            `;
            
            document.body.appendChild(topRightInfo);
            console.log('✅ Added user info to top right corner:', practiceName, email);
            
        } catch (error) {
            console.error('Error showing user info in top right:', error);
        }
    }
    
    /**
     * Show error when AD login fails (user not registered in indici)
     */
    showADLoginError() {
        try {
            // Remove any existing error
            const existingError = document.querySelector('.ad-login-error');
            if (existingError) {
                existingError.remove();
            }
            
            const errorContainer = document.createElement('div');
            errorContainer.className = 'ad-login-error';
            errorContainer.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                z-index: 1001;
                max-width: 400px;
                text-align: center;
            `;
            
            errorContainer.innerHTML = `
                <div style="color: #856404; font-size: 18px; margin-bottom: 10px;">
                    ⚠️ User Not Registered
                </div>
                <div style="color: #856404; font-size: 14px; margin-bottom: 15px;">
                    You are authenticated with Azure AD but not registered in indici system.
                </div>
                <div style="color: #856404; font-size: 12px; margin-bottom: 15px;">
                    Please contact your indici administrator to register your account.
                </div>
                <button onclick="this.parentElement.remove()" style="
                    background: #856404;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                ">Close</button>
            `;
            
            document.body.appendChild(errorContainer);
            console.log('⚠️ AD login error displayed');
            
        } catch (error) {
            console.error('Error showing AD login error:', error);
        }
    }
    
    /**
     * Display practice information in the UI
     */
    displayPracticeInfo(practices) {
        try {
            console.log('🔄 [TeamsAuth] Displaying practice info:', practices);
            
            // Create practice info container
            const practiceContainer = document.createElement('div');
            practiceContainer.className = 'practice-info-container';
            practiceContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 1000;
                max-width: 300px;
                font-size: 14px;
            `;
            
            let practiceHtml = '<h4 style="margin: 0 0 10px 0; color: #333;">🏥 Available Practices</h4>';
            
            practices.forEach((practice, index) => {
                const isPrimary = practice.isPrimary ? ' (Primary)' : '';
                practiceHtml += `
                    <div style="margin-bottom: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
                        <strong>${practice.practiceName}${isPrimary}</strong><br>
                        <small style="color: #666;">ID: ${practice.practiceID}</small>
                    </div>
                `;
            });
            
            practiceContainer.innerHTML = practiceHtml;
            
            // Add close button
            const closeButton = document.createElement('button');
            closeButton.innerHTML = '×';
            closeButton.style.cssText = `
                position: absolute;
                top: 5px;
                right: 10px;
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                color: #666;
            `;
            closeButton.onclick = () => practiceContainer.remove();
            practiceContainer.appendChild(closeButton);
            
            // Add to page
            document.body.appendChild(practiceContainer);
            
            // Auto-remove after 10 seconds
            setTimeout(() => {
                if (practiceContainer.parentNode) {
                    practiceContainer.remove();
                }
            }, 10000);
            
            console.log('✅ Practice info displayed');
            
        } catch (error) {
            console.error('Error displaying practice info:', error);
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
