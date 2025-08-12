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
        
        // Initialize message input state
        this.initializeMessageInputState();
    }
    
    /**
     * Initialize message input state
     */
    initializeMessageInputState() {
        try {
            // Initially disable message input until user is authenticated
            this.disableMessageInput();
            console.log('✅ [TeamsAuth] Message input state initialized - disabled until authentication');
            
            // Set up periodic checks to ensure chat state is correct
            setInterval(() => {
                this.ensureCorrectChatState();
            }, 5000); // Check every 5 seconds
            
        } catch (error) {
            console.error('Error initializing message input state:', error);
        }
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

                // If this is an AD login failure, show the specific error and disable chat
                if (response.status === 401 || response.status === 403 || 
                    (errorData.error && (errorData.error.includes('AD') || errorData.error.includes('indici')))) {
                    console.log('🚨 [TeamsAuth] AD login failure detected - disabling chat and showing error');
                    this.showADLoginError();
                } else {
                    this.handleAuthFailure(errorData);
                }
                
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

        // Disable message input on authentication failure
        this.disableMessageInput();

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
            // Enable message input since user is authenticated
            this.enableMessageInput();
            
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
                
                // Prioritize Azure AD email from Teams authentication
                const azureADEmail = user.userPrincipalName || user.email || user.preferred_username || user.mail || '';
                
                userInfo.innerHTML = `
                    <div class="user-avatar">
                        <i class="fas fa-user-circle"></i>
                    </div>
                    <div class="user-details">
                        <div class="user-name">${user.displayName || 'User'}</div>
                        <div class="user-email">${azureADEmail}</div>
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
            
            // Enable message input since user is now authenticated
            this.enableMessageInput();
            
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
                
                // Prioritize Azure AD email from currentUser (Teams authentication)
                const azureADEmail = this.currentUser?.userPrincipalName || this.currentUser?.email || this.currentUser?.preferred_username || '';
                const adEmail = adData.email || '';
                const email = azureADEmail || adEmail || '';
                
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
                
                console.log('🔍 [TeamsAuth] Sidebar email sources - Azure AD:', azureADEmail, 'AD:', adEmail, 'Final:', email);

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
            
            // Update header user info display with AD login format
            this.updateHeaderUserInfo(adData);
            
        } catch (error) {
            console.error('Error updating UI with AD data:', error);
        }
    }
    
    /**
     * Update header user info display with AD login format
     */
    updateHeaderUserInfo(adData) {
        try {
            console.log('🔄 [TeamsAuth] Updating header user info with AD data:', adData);
            
            // Find the user info display in the header
            const userInfoDisplay = document.querySelector('.user-info-display');
            if (!userInfoDisplay) {
                console.log('⚠️ [TeamsAuth] Header user info display not found');
                return;
            }
            
            // Get user details from AD data - prioritize Azure AD email
            const fullName = adData.fullName || this.currentUser.displayName || 'User';
            const profileType = adData.profileType || 'User';
            
            // Prioritize Azure AD email from currentUser (Teams authentication)
            const azureADEmail = this.currentUser?.userPrincipalName || this.currentUser?.email || this.currentUser?.preferred_username || '';
            const adEmail = adData.email || '';
            const email = azureADEmail || adEmail || '';
            
            const practices = adData.practices || [];
            
            // Get practice name - prioritize primary practice
            let practiceName = 'No Practice';
            if (practices && practices.length > 0) {
                const primaryPractice = practices.find(p => p.isPrimary) || practices[0];
                practiceName = primaryPractice.practiceName || 'Unknown Practice';
            }
            
            // Update the user name display with AD format: FullName (ProfileType) - PracticeName
            const userNameElement = userInfoDisplay.querySelector('.user-name');
            if (userNameElement) {
                userNameElement.textContent = `${fullName} (${profileType}) - ${practiceName}`;
                console.log('✅ Updated header user name:', userNameElement.textContent);
            }
            
            // Update the user email display
            const userEmailElement = userInfoDisplay.querySelector('.user-email');
            if (userEmailElement) {
                userEmailElement.textContent = email;
                console.log('✅ Updated header user email:', email);
                console.log('🔍 [TeamsAuth] Email sources - Azure AD:', azureADEmail, 'AD:', adEmail, 'Final:', email);
            }
            
            // Update auth status indicator to show success
            const authStatusIndicator = userInfoDisplay.querySelector('.auth-status-indicator');
            if (authStatusIndicator) {
                authStatusIndicator.innerHTML = '<i class="fas fa-check-circle" title="AD Authenticated"></i>';
                console.log('✅ Updated auth status indicator');
            }
            
        } catch (error) {
            console.error('Error updating header user info:', error);
        }
    }
    

    
    /**
     * Show error when AD login fails (user not registered in indici)
     */
    showADLoginError() {
        try {
            console.log('🚨 [TeamsAuth] showADLoginError called - starting to disable chat...');
            
            // Remove any existing error
            const existingError = document.querySelector('.ad-login-error');
            if (existingError) {
                existingError.remove();
            }
            
            // Completely disable message input and add visual overlay
            console.log('🔒 [TeamsAuth] Calling forceDisableMessageInput...');
            this.forceDisableMessageInput();
            
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
                <button id="ad-login-close-btn" style="
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
            
            // Add event listener to the close button
            const closeButton = document.getElementById('ad-login-close-btn');
            if (closeButton) {
                closeButton.addEventListener('click', () => {
                    this.handleADLoginErrorClose();
                });
            }
            
            console.log('⚠️ AD login error displayed - message input disabled');
            
            // Verify that elements are actually disabled
            setTimeout(() => {
                this.verifyChatDisabled();
            }, 100);
            
        } catch (error) {
            console.error('Error showing AD login error:', error);
        }
    }
    
    /**
     * Verify that chat is properly disabled
     */
    verifyChatDisabled() {
        try {
            console.log('🔍 [TeamsAuth] Verifying chat disabled state...');
            
            const messageInput = document.getElementById('message-input');
            const sendButton = document.getElementById('send-button');
            
            if (messageInput) {
                console.log('📝 Message input state:', {
                    disabled: messageInput.disabled,
                    readonly: messageInput.hasAttribute('readonly'),
                    opacity: messageInput.style.opacity,
                    cursor: messageInput.style.cursor,
                    backgroundColor: messageInput.style.backgroundColor,
                    placeholder: messageInput.placeholder
                });
            } else {
                console.log('❌ Message input element not found!');
            }
            
            if (sendButton) {
                console.log('📤 Send button state:', {
                    disabled: sendButton.disabled,
                    opacity: sendButton.style.opacity,
                    cursor: sendButton.style.cursor,
                    backgroundColor: sendButton.style.backgroundColor
                });
            } else {
                console.log('❌ Send button element not found!');
            }
            
            // Check if overlay is present
            const overlay = document.querySelector('.chat-disabled-overlay');
            if (overlay) {
                console.log('✅ Chat disabled overlay is present');
            } else {
                console.log('❌ Chat disabled overlay not found');
            }
            
        } catch (error) {
            console.error('Error verifying chat disabled state:', error);
        }
    }
    
    /**
     * Handle closing of AD login error modal
     */
    handleADLoginErrorClose() {
        try {
            // Remove the error modal
            const existingError = document.querySelector('.ad-login-error');
            if (existingError) {
                existingError.remove();
            }
            
            // Re-enable message input
            this.enableMessageInput();
            
            console.log('✅ AD login error closed - message input re-enabled');
            
        } catch (error) {
            console.error('Error handling AD login error close:', error);
        }
    }
    
    /**
     * Disable message input and send button
     */
    disableMessageInput() {
        try {
            console.log('🔒 [TeamsAuth] Attempting to disable message input...');
            
            const messageInput = document.getElementById('message-input');
            const sendButton = document.getElementById('send-button');
            
            if (messageInput) {
                messageInput.disabled = true;
                messageInput.placeholder = 'User not registered - contact administrator';
                messageInput.style.opacity = '0.6';
                messageInput.style.cursor = 'not-allowed';
                messageInput.style.backgroundColor = '#f8f9fa';
                messageInput.style.borderColor = '#dee2e6';
                messageInput.style.color = '#6c757d';
                messageInput.setAttribute('readonly', 'readonly');
                console.log('✅ Message input disabled');
            } else {
                console.log('❌ Message input element not found - will retry in 1 second');
                // Retry after a short delay in case DOM is not ready
                setTimeout(() => this.disableMessageInput(), 1000);
                return;
            }
            
            if (sendButton) {
                sendButton.disabled = true;
                sendButton.style.opacity = '0.6';
                sendButton.style.cursor = 'not-allowed';
                sendButton.style.backgroundColor = '#6c757d';
                sendButton.title = 'Chat disabled - user not registered';
                console.log('✅ Send button disabled');
            } else {
                console.log('❌ Send button element not found - will retry in 1 second');
                // Retry after a short delay in case DOM is not ready
                setTimeout(() => this.disableMessageInput(), 1000);
                return;
            }
            
            // Also disable any Enter key functionality
            if (messageInput) {
                messageInput.removeEventListener('keypress', this.handleEnterKey);
                messageInput.addEventListener('keypress', this.handleEnterKeyDisabled);
            }
            
            console.log('🔒 Chat functionality completely disabled - user not registered');
            
        } catch (error) {
            console.error('Error disabling message input:', error);
        }
    }
    
    /**
     * Handle Enter key when input is disabled
     */
    handleEnterKeyDisabled(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            event.stopPropagation();
            console.log('⚠️ Enter key blocked - chat is disabled');
            return false;
        }
    }
    
    /**
     * Check if message input is currently disabled
     */
    isMessageInputDisabled() {
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        
        return messageInput?.disabled === true || sendButton?.disabled === true;
    }
    
    /**
     * Check if chat should be disabled based on authentication state
     */
    shouldChatBeDisabled() {
        // Chat should be disabled if:
        // 1. User is not authenticated, OR
        // 2. User is authenticated but not registered in indici system
        return !this.currentUser || !this.currentUser.ad_data;
    }
    
    /**
     * Ensure chat is in correct state based on authentication
     */
    ensureCorrectChatState() {
        try {
            if (this.shouldChatBeDisabled()) {
                console.log('🔒 [TeamsAuth] Chat should be disabled - ensuring disabled state');
                if (!this.isMessageInputDisabled()) {
                    this.disableMessageInput();
                }
            } else {
                console.log('🔓 [TeamsAuth] Chat should be enabled - ensuring enabled state');
                if (this.isMessageInputDisabled()) {
                    this.enableMessageInput();
                }
            }
        } catch (error) {
            console.error('Error ensuring correct chat state:', error);
        }
    }
    
    /**
     * Force disable message input (for emergency cases)
     */
    forceDisableMessageInput() {
        try {
            console.log('🚨 Force disabling message input...');
            this.disableMessageInput();
            
            // Add a visual indicator that chat is completely disabled
            const chatContainer = document.querySelector('.chat-container');
            if (chatContainer) {
                const disabledOverlay = document.createElement('div');
                disabledOverlay.className = 'chat-disabled-overlay';
                disabledOverlay.style.cssText = `
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(108, 117, 125, 0.1);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 100;
                    pointer-events: none;
                `;
                disabledOverlay.innerHTML = `
                    <div style="
                        background: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 8px;
                        padding: 15px;
                        text-align: center;
                        color: #856404;
                        font-size: 14px;
                        pointer-events: auto;
                    ">
                        <i class="fas fa-ban" style="font-size: 18px; margin-bottom: 8px; display: block;"></i>
                        Chat is disabled - User not registered
                    </div>
                `;
                chatContainer.style.position = 'relative';
                chatContainer.appendChild(disabledOverlay);
                console.log('✅ Chat disabled overlay added');
            }
            
        } catch (error) {
            console.error('Error force disabling message input:', error);
        }
    }
    
    /**
     * Enable message input and send button
     */
    enableMessageInput() {
        try {
            const messageInput = document.getElementById('message-input');
            const sendButton = document.getElementById('send-button');
            
            if (messageInput) {
                messageInput.disabled = false;
                messageInput.placeholder = 'Ask me about indici Reports...';
                messageInput.style.opacity = '1';
                messageInput.style.cursor = 'text';
                messageInput.style.backgroundColor = '';
                messageInput.style.borderColor = '';
                messageInput.style.color = '';
                messageInput.removeAttribute('readonly');
                console.log('✅ Message input re-enabled');
            }
            
            if (sendButton) {
                sendButton.disabled = false;
                sendButton.style.opacity = '1';
                sendButton.style.cursor = 'pointer';
                sendButton.style.backgroundColor = '';
                sendButton.title = '';
                console.log('✅ Send button re-enabled');
            }
            
            // Restore Enter key functionality
            if (messageInput) {
                messageInput.removeEventListener('keypress', this.handleEnterKeyDisabled);
                // Note: The original Enter key handler should be restored by the main app
            }
            
            // Remove any disabled overlay
            this.removeChatDisabledOverlay();
            
            console.log('🔓 Chat functionality re-enabled');
            
        } catch (error) {
            console.error('Error enabling message input:', error);
        }
    }
    
    /**
     * Remove chat disabled overlay
     */
    removeChatDisabledOverlay() {
        try {
            // Remove all chat disabled overlays (both initial and regular)
            const disabledOverlays = document.querySelectorAll('.chat-disabled-overlay');
            disabledOverlays.forEach(overlay => {
                overlay.remove();
                console.log('✅ Chat disabled overlay removed:', overlay.className);
            });
        } catch (error) {
            console.error('Error removing chat disabled overlay:', error);
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
