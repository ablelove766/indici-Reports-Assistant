/**
 * Teams SSO Fix - Aggressive SSO initialization and debugging
 */

console.log('[SSO-FIX] Teams SSO Fix script loaded');

// Global variables for debugging
window.ssoDebug = {
    teamsSDKAvailable: false,
    teamsInitialized: false,
    contextReceived: false,
    ssoAttempted: false,
    ssoSuccessful: false,
    errors: []
};

// Force SSO initialization
function forceSSOInitialization() {
    console.log('[SSO-FIX] Force SSO initialization started');
    
    // Check Teams SDK availability
    if (typeof microsoftTeams === 'undefined') {
        console.error('[SSO-FIX] Teams SDK not available');
        window.ssoDebug.errors.push('Teams SDK not available');
        updateSSOStatus('Teams SDK Not Available', 'error');
        return false;
    }
    
    window.ssoDebug.teamsSDKAvailable = true;
    console.log('[SSO-FIX] Teams SDK available');
    
    // Initialize Teams SDK
    microsoftTeams.app.initialize()
        .then(() => {
            console.log('[SSO-FIX] Teams SDK initialized successfully');
            window.ssoDebug.teamsInitialized = true;
            updateSSOStatus('Teams SDK Initialized', 'success');
            
            // Get Teams context
            return microsoftTeams.app.getContext();
        })
        .then((context) => {
            console.log('[SSO-FIX] Teams context received:', context);
            window.ssoDebug.contextReceived = true;
            window.ssoDebug.teamsContext = context;
            updateSSOStatus('Teams Context Received', 'success');
            
            // Check if we're in Teams
            if (context && context.app && context.app.host) {
                console.log('[SSO-FIX] Running in Teams environment');
                
                // Attempt SSO
                attemptSSO();
            } else {
                console.warn('[SSO-FIX] Not running in Teams environment');
                updateSSOStatus('Not in Teams Environment', 'warning');
            }
        })
        .catch((error) => {
            console.error('[SSO-FIX] Teams initialization failed:', error);
            window.ssoDebug.errors.push(`Teams init failed: ${error.message}`);
            updateSSOStatus('Teams Initialization Failed', 'error');
        });
}

// Attempt SSO authentication
function attemptSSO() {
    console.log('[SSO-FIX] Attempting SSO authentication...');
    window.ssoDebug.ssoAttempted = true;
    updateSSOStatus('Requesting SSO Token...', 'info');
    
    microsoftTeams.authentication.getAuthToken({
        successCallback: (token) => {
            console.log('[SSO-FIX] SSO token received successfully');
            console.log('[SSO-FIX] Token length:', token.length);
            console.log('[SSO-FIX] Token preview:', token.substring(0, 50) + '...');
            
            window.ssoDebug.ssoSuccessful = true;
            window.ssoDebug.ssoToken = token;
            updateSSOStatus('SSO Token Received', 'success');
            
            // Exchange token
            exchangeTokenForGraph(token);
        },
        failureCallback: (error) => {
            console.error('[SSO-FIX] SSO token request failed:', error);
            window.ssoDebug.errors.push(`SSO failed: ${error}`);
            updateSSOStatus('SSO Token Failed', 'error');
            
            // Show detailed error
            const userInfoEl = document.getElementById('user-info');
            if (userInfoEl) {
                userInfoEl.textContent = `SSO Error: ${error}`;
                userInfoEl.style.color = 'red';
            }
        }
    });
}

// Exchange token for Graph token
async function exchangeTokenForGraph(ssoToken) {
    console.log('[SSO-FIX] Exchanging SSO token for Graph token...');
    updateSSOStatus('Exchanging Token...', 'info');
    
    try {
        const response = await fetch('/auth/token-exchange', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Teams-Token': ssoToken
            },
            body: JSON.stringify({
                token: ssoToken
            })
        });
        
        console.log('[SSO-FIX] Token exchange response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('[SSO-FIX] Token exchange successful:', data);
            
            window.ssoDebug.exchangeSuccessful = true;
            window.ssoDebug.userData = data.user;
            
            updateSSOStatus('Authentication Complete', 'success');
            
            // Update user info
            const userInfoEl = document.getElementById('user-info');
            if (userInfoEl) {
                userInfoEl.textContent = `Authenticated as: ${data.user?.displayName || data.user?.mail || 'Unknown User'}`;
                userInfoEl.style.color = 'green';
            }
            
            // Update header
            const headerInfo = document.querySelector('.header-info p');
            if (headerInfo) {
                headerInfo.textContent = `Welcome, ${data.user?.displayName || 'User'}! Your intelligent assistant for indici Reports`;
            }
            
        } else {
            const errorData = await response.json().catch(() => ({ error: 'Failed to parse error' }));
            console.error('[SSO-FIX] Token exchange failed:', errorData);
            
            window.ssoDebug.errors.push(`Token exchange failed: ${JSON.stringify(errorData)}`);
            updateSSOStatus('Token Exchange Failed', 'error');
            
            // Show specific error
            const userInfoEl = document.getElementById('user-info');
            if (userInfoEl) {
                userInfoEl.textContent = `Exchange Error: ${errorData.error || 'Unknown error'}`;
                userInfoEl.style.color = 'red';
            }
        }
        
    } catch (error) {
        console.error('[SSO-FIX] Token exchange error:', error);
        window.ssoDebug.errors.push(`Exchange error: ${error.message}`);
        updateSSOStatus('Token Exchange Error', 'error');
    }
}

// Update SSO status display
function updateSSOStatus(message, type = 'info') {
    const statusEl = document.getElementById('sso-status');
    if (statusEl) {
        statusEl.textContent = message;
        
        switch (type) {
            case 'success':
                statusEl.style.color = 'green';
                break;
            case 'error':
                statusEl.style.color = 'red';
                break;
            case 'warning':
                statusEl.style.color = 'orange';
                break;
            default:
                statusEl.style.color = 'blue';
        }
    }
}

// Get debug information
function getSSODebugInfo() {
    return {
        ...window.ssoDebug,
        teamsSDKMethods: typeof microsoftTeams !== 'undefined' ? Object.keys(microsoftTeams) : null,
        authMethods: typeof microsoftTeams !== 'undefined' && microsoftTeams.authentication ? Object.keys(microsoftTeams.authentication) : null,
        currentURL: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString()
    };
}

// Initialize when DOM is ready
function initializeSSO() {
    console.log('[SSO-FIX] Initializing SSO...');
    updateSSOStatus('Initializing...', 'info');
    
    // Wait for Teams SDK to be ready
    let attempts = 0;
    const maxAttempts = 10;
    
    const checkAndInit = () => {
        attempts++;
        console.log(`[SSO-FIX] Initialization attempt ${attempts}/${maxAttempts}`);
        
        if (typeof microsoftTeams !== 'undefined') {
            console.log('[SSO-FIX] Teams SDK ready, starting SSO...');
            forceSSOInitialization();
        } else if (attempts < maxAttempts) {
            console.log('[SSO-FIX] Teams SDK not ready, retrying...');
            setTimeout(checkAndInit, 1000);
        } else {
            console.error('[SSO-FIX] Teams SDK failed to load after maximum attempts');
            updateSSOStatus('Teams SDK Load Failed', 'error');
        }
    };
    
    checkAndInit();
}

// Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSSO);
} else {
    initializeSSO();
}

// Global functions for manual testing
window.forceSSOTest = forceSSOInitialization;
window.getSSODebug = getSSODebugInfo;
window.attemptSSO = attemptSSO;

console.log('[SSO-FIX] Teams SSO Fix script ready');
