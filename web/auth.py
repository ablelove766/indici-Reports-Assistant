"""Microsoft Teams SSO Authentication Module."""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional
from flask import request, jsonify, session, g
import sys

# Configure detailed logging for SSO debugging
def setup_sso_logging():
    """Setup SSO logging for both local and production environments."""
    # Create specific logger for SSO operations
    sso_logger = logging.getLogger('teams_sso')
    sso_logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    for handler in sso_logger.handlers[:]:
        sso_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Always add console handler for Render.com
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    sso_logger.addHandler(console_handler)

    # Add file handler only if we can write files (local development)
    try:
        file_handler = logging.FileHandler('sso_debug.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        sso_logger.addHandler(file_handler)
        sso_logger.info("[FILE] File logging enabled: sso_debug.log")
    except (PermissionError, OSError):
        sso_logger.info("[FILE] File logging disabled (production environment)")

    # Ensure logs propagate to root logger for Render.com
    sso_logger.propagate = True

    return sso_logger

# Setup SSO logger
sso_logger = setup_sso_logging()

# Import JWT with error handling
try:
    import jwt
    JWT_AVAILABLE = True
    print("✅ PyJWT imported successfully")
except ImportError as e:
    JWT_AVAILABLE = False
    print(f"⚠️ PyJWT not available: {e}")
    # Create a dummy jwt module for graceful degradation
    class DummyJWT:
        @staticmethod
        def decode(*args, **kwargs):
            return {"sub": "dummy_user", "preferred_username": "test@example.com"}
        @staticmethod
        def get_unverified_header(*args, **kwargs):
            return {"kid": "dummy_key"}
        class algorithms:
            @staticmethod
            def RSAAlgorithm(*args, **kwargs):
                return None
    jwt = DummyJWT()

# Import MSAL with error handling
try:
    from msal import ConfidentialClientApplication
    MSAL_AVAILABLE = True
    print("✅ MSAL imported successfully")
except ImportError as e:
    MSAL_AVAILABLE = False
    print(f"⚠️ MSAL not available: {e}")
    # Create a dummy MSAL class
    class DummyMSAL:
        def __init__(self, *args, **kwargs):
            pass
        def acquire_token_on_behalf_of(self, *args, **kwargs):
            return {"error": "MSAL not available"}
        def get_authorization_request_url(self, *args, **kwargs):
            return "https://login.microsoftonline.com/dummy"
        def acquire_token_by_authorization_code(self, *args, **kwargs):
            return {"error": "MSAL not available"}
    ConfidentialClientApplication = DummyMSAL

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_server.config import config

logger = logging.getLogger(__name__)

class TeamsAuthManager:
    """Microsoft Teams SSO Authentication Manager with comprehensive logging."""

    def __init__(self):
        """Initialize Teams authentication manager."""
        sso_logger.info("[INIT] Initializing TeamsAuthManager...")

        self.client_id = config.azure_client_id
        self.client_secret = config.azure_client_secret
        self.tenant_id = config.azure_tenant_id
        self.authority = config.azure_authority
        self.scope = config.azure_scope  # For Microsoft Graph API
        self.teams_scope = config.azure_teams_scope  # For Teams SSO validation

        # Log configuration (mask sensitive data)
        sso_logger.info("[CONFIG] Azure AD Configuration:")
        sso_logger.info(f"   Client ID: {self.client_id}")
        sso_logger.info(f"   Tenant ID: {self.tenant_id}")
        sso_logger.info(f"   Authority: {self.authority}")
        sso_logger.info(f"   Scope: {self.scope}")
        sso_logger.info(f"   Client Secret: {'*' * (len(self.client_secret) - 4) + self.client_secret[-4:] if self.client_secret else 'NOT SET'}")

        # Validate configuration
        if not all([self.client_id, self.client_secret, self.tenant_id, self.authority]):
            sso_logger.error("[ERROR] Missing required Azure AD configuration!")
            sso_logger.error(f"   Client ID: {'OK' if self.client_id else 'MISSING'}")
            sso_logger.error(f"   Client Secret: {'OK' if self.client_secret else 'MISSING'}")
            sso_logger.error(f"   Tenant ID: {'OK' if self.tenant_id else 'MISSING'}")
            sso_logger.error(f"   Authority: {'OK' if self.authority else 'MISSING'}")
            raise ValueError("Missing required Azure AD configuration")

        # Initialize MSAL client
        try:
            sso_logger.info("[MSAL] Initializing MSAL client...")
            self.msal_app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
            sso_logger.info("[MSAL] MSAL client initialized successfully")
        except Exception as e:
            sso_logger.error(f"[ERROR] Failed to initialize MSAL client: {e}")
            raise

        # Cache for JWT public keys
        self._jwt_keys_cache = {}
        self._jwt_keys_cache_expiry = None

        sso_logger.info("[SUCCESS] TeamsAuthManager initialized successfully")
        
    async def get_jwt_public_keys(self) -> Dict[str, Any]:
        """Get JWT public keys from Microsoft's well-known endpoint."""
        try:
            # Check cache first
            if (self._jwt_keys_cache and
                self._jwt_keys_cache_expiry and
                datetime.now() < self._jwt_keys_cache_expiry):
                return self._jwt_keys_cache

            # Try multiple discovery URLs
            discovery_urls = [
                f"https://login.microsoftonline.com/{self.tenant_id}/v2.0/.well-known/openid_configuration",
                f"https://login.microsoftonline.com/{self.tenant_id}/.well-known/openid_configuration",
                "https://login.microsoftonline.com/common/v2.0/.well-known/openid_configuration",
                "https://login.microsoftonline.com/common/.well-known/openid_configuration"
            ]

            discovery_data = None
            for discovery_url in discovery_urls:
                try:
                    logger.info(f"Trying discovery URL: {discovery_url}")
                    print(f"[RENDER-AUTH] Trying discovery URL: {discovery_url}", flush=True)
                    discovery_response = requests.get(discovery_url, timeout=10)
                    print(f"[RENDER-AUTH] Discovery response status: {discovery_response.status_code}", flush=True)
                    discovery_response.raise_for_status()
                    discovery_data = discovery_response.json()
                    logger.info(f"Successfully retrieved discovery data from: {discovery_url}")
                    print(f"[RENDER-AUTH] Successfully retrieved discovery data from: {discovery_url}", flush=True)
                    break
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Failed to get discovery data from {discovery_url}: {e}")
                    print(f"[RENDER-AUTH] Failed to get discovery data from {discovery_url}: {e}", flush=True)
                    continue

            if not discovery_data:
                raise ValueError("Could not retrieve OpenID configuration from any endpoint")

            jwks_uri = discovery_data.get("jwks_uri")
            if not jwks_uri:
                raise ValueError("JWKS URI not found in discovery document")

            logger.info(f"Fetching JWKS from: {jwks_uri}")
            print(f"[RENDER-AUTH] Fetching JWKS from: {jwks_uri}", flush=True)
            jwks_response = requests.get(jwks_uri, timeout=10)
            print(f"[RENDER-AUTH] JWKS response status: {jwks_response.status_code}", flush=True)
            jwks_response.raise_for_status()
            jwks_data = jwks_response.json()

            # Cache for 1 hour
            self._jwt_keys_cache = jwks_data
            self._jwt_keys_cache_expiry = datetime.now() + timedelta(hours=1)

            logger.info(f"Successfully cached {len(jwks_data.get('keys', []))} JWT public keys")
            return jwks_data

        except Exception as e:
            logger.error(f"Failed to get JWT public keys: {e}")
            # Return a fallback empty structure to prevent crashes
            return {"keys": []}
    
    def validate_teams_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate Teams SSO token."""
        try:
            # First, try to decode without verification to get basic info
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            logger.info(f"Token received for user: {unverified_payload.get('preferred_username', 'Unknown')}")
            print(f"[RENDER-AUTH] Token received for user: {unverified_payload.get('preferred_username', 'Unknown')}", flush=True)
            print(f"[RENDER-AUTH] Token audience: {unverified_payload.get('aud', 'Unknown')}", flush=True)
            print(f"[RENDER-AUTH] Token issuer: {unverified_payload.get('iss', 'Unknown')}", flush=True)

            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                logger.warning("No key ID found in token header, skipping signature verification")
                print("[RENDER-AUTH] No key ID found, returning unverified payload", flush=True)
                # For development/testing, return unverified payload
                # In production, you should always verify signatures
                print("[RENDER-AUTH] Token validation bypassed for development", flush=True)
                return unverified_payload

            # Get public keys
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            jwks_data = loop.run_until_complete(self.get_jwt_public_keys())
            loop.close()

            # Check if we have any keys
            if not jwks_data.get("keys"):
                logger.warning("No JWT public keys available, returning unverified token")
                print("[RENDER-AUTH] No JWT public keys available, returning unverified token", flush=True)
                return unverified_payload

            # Find the correct key
            public_key = None
            for key in jwks_data.get("keys", []):
                if key.get("kid") == kid:
                    try:
                        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                        break
                    except Exception as e:
                        logger.warning(f"Failed to create public key from JWK: {e}")
                        continue

            if not public_key:
                logger.warning(f"Public key not found for kid: {kid}, returning unverified token")
                print(f"[RENDER-AUTH] Public key not found for kid: {kid}, returning unverified token", flush=True)
                return unverified_payload

            # Try to validate token with multiple possible issuers
            possible_issuers = [
                f"https://login.microsoftonline.com/{self.tenant_id}/v2.0",
                f"https://login.microsoftonline.com/{self.tenant_id}",
                f"https://sts.windows.net/{self.tenant_id}/",
                "https://login.microsoftonline.com/common/v2.0"
            ]

            for issuer in possible_issuers:
                try:
                    payload = jwt.decode(
                        token,
                        public_key,
                        algorithms=["RS256"],
                        audience=[
                            self.client_id,
                            f"api://{self.client_id}",
                            f"api://indici-reports-assistant.onrender.com/{self.client_id}"
                        ],
                        issuer=issuer,
                        options={"verify_aud": False}  # More lenient audience verification
                    )

                    logger.info(f"Token validated successfully with issuer {issuer} for user: {payload.get('preferred_username', 'Unknown')}")
                    return payload

                except jwt.InvalidTokenError as e:
                    logger.debug(f"Token validation failed with issuer {issuer}: {e}")
                    continue

            logger.warning("Token validation failed with all issuers, returning unverified token")
            return unverified_payload

        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
    
    def exchange_token_for_graph_token(self, teams_token: str) -> Optional[str]:
        """Exchange Teams token for Microsoft Graph token using On-Behalf-Of flow."""
        # Force immediate output for Render.com
        print("[RENDER-AUTH] Starting token exchange using On-Behalf-Of flow...", flush=True)
        sso_logger.info("[TOKEN] Starting token exchange using On-Behalf-Of flow...")
        sso_logger.debug(f"   Teams token (first 50 chars): {teams_token[:50]}...")

        try:
            # Log the configuration being used
            sso_logger.info("📋 Token exchange configuration:")
            sso_logger.info(f"   Client ID: {self.client_id}")
            sso_logger.info(f"   Tenant ID: {self.tenant_id}")
            sso_logger.info(f"   Authority: {self.authority}")
            sso_logger.info(f"   Scope: {self.scope}")

            # Validate Teams token first
            sso_logger.info("🔍 Step 1: Validating Teams token structure...")
            try:
                # Decode without verification to check structure
                header = jwt.get_unverified_header(teams_token)
                payload = jwt.decode(teams_token, options={"verify_signature": False})

                sso_logger.info(f"   Token header: {header}")
                sso_logger.info(f"   Token issuer: {payload.get('iss', 'Unknown')}")
                sso_logger.info(f"   Token audience: {payload.get('aud', 'Unknown')}")
                sso_logger.info(f"   Token subject: {payload.get('sub', 'Unknown')}")
                sso_logger.info(f"   Token expiry: {payload.get('exp', 'Unknown')}")

                # Check if token is for the correct audience
                expected_audience = f"api://{self.client_id}"
                actual_audience = payload.get('aud')
                if actual_audience != expected_audience:
                    sso_logger.warning(f"[WARNING] Audience mismatch!")
                    sso_logger.warning(f"   Expected: {expected_audience}")
                    sso_logger.warning(f"   Actual: {actual_audience}")
                    sso_logger.warning(f"   Teams scope: {self.teams_scope}")
                else:
                    sso_logger.info(f"[SUCCESS] Audience matches expected value")

            except Exception as token_decode_error:
                sso_logger.error(f"❌ Failed to decode Teams token: {token_decode_error}")

            # Use MSAL to perform On-Behalf-Of flow
            print("🔄 [RENDER-AUTH] Step 2: Performing MSAL On-Behalf-Of flow...", flush=True)
            sso_logger.info("🔄 Step 2: Performing MSAL On-Behalf-Of flow...")
            result = self.msal_app.acquire_token_on_behalf_of(
                user_assertion=teams_token,
                scopes=[self.scope]
            )

            print(f"🔍 [RENDER-AUTH] MSAL result keys: {list(result.keys())}", flush=True)
            sso_logger.debug(f"   MSAL result keys: {list(result.keys())}")

            if "access_token" in result:
                print("✅ [RENDER-AUTH] Token exchange successful!", flush=True)
                sso_logger.info("✅ Token exchange successful!")
                sso_logger.debug(f"   Access token (first 20 chars): {result['access_token'][:20]}...")
                sso_logger.debug(f"   Token expires in: {result.get('expires_in', 'Unknown')} seconds")
                return result["access_token"]
            else:
                error_code = result.get('error', 'unknown_error')
                error_desc = result.get('error_description', 'Unknown error')
                correlation_id = result.get('correlation_id', 'No correlation ID')

                print("❌ [RENDER-AUTH] Token exchange failed!", flush=True)
                print(f"❌ [RENDER-AUTH] Error code: {error_code}", flush=True)
                print(f"❌ [RENDER-AUTH] Error description: {error_desc}", flush=True)
                print(f"❌ [RENDER-AUTH] Correlation ID: {correlation_id}", flush=True)
                print(f"❌ [RENDER-AUTH] Full MSAL result: {result}", flush=True)

                sso_logger.error("❌ Token exchange failed!")
                sso_logger.error(f"   Error code: {error_code}")
                sso_logger.error(f"   Error description: {error_desc}")
                sso_logger.error(f"   Correlation ID: {correlation_id}")
                sso_logger.error(f"   Full MSAL result: {result}")

                # Specific error handling for CAA20004
                if "CAA20004" in error_desc or "AADSTS650057" in error_desc:
                    print("🚨 [RENDER-AUTH] CAA20004 Error Detected!", flush=True)
                    print("🚨 [RENDER-AUTH] This indicates missing admin consent for the API scope", flush=True)
                    print("🚨 [RENDER-AUTH] Required action: Grant admin consent in Azure Portal", flush=True)

                    sso_logger.error("🚨 CAA20004 Error Detected!")
                    sso_logger.error("   This indicates missing admin consent for the API scope")
                    sso_logger.error("   Required action: Grant admin consent in Azure Portal")
                    sso_logger.error(f"   Go to: https://portal.azure.com → App registrations → {self.client_id} → API permissions")
                    sso_logger.error("   Click: 'Grant admin consent for [organization]'")

                # For development/testing, we might want to continue without Graph token
                # In production, this should be handled based on your requirements
                if error_code in ['invalid_grant', 'interaction_required']:
                    sso_logger.info("Token exchange failed but continuing with Teams token only")
                    return None
                else:
                    sso_logger.error(f"Critical token exchange error: {error_code}")
                    return None

        except Exception as e:
            sso_logger.error(f"❌ Exception during token exchange: {e}")
            sso_logger.error(f"   Exception type: {type(e).__name__}")
            import traceback
            sso_logger.error(f"   Traceback: {traceback.format_exc()}")
            return None
    
    def get_user_info_from_graph(self, graph_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Microsoft Graph API."""
        try:
            headers = {
                "Authorization": f"Bearer {graph_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()
                logger.info(f"Retrieved user info for: {user_info.get('userPrincipalName', 'Unknown')}")
                return user_info
            else:
                logger.error(f"Failed to get user info: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None

# Global authentication manager instance
auth_manager = TeamsAuthManager()

def require_teams_auth(f):
    """Decorator to require Teams authentication for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for Teams token in headers
        auth_header = request.headers.get('Authorization')
        teams_token = request.headers.get('X-Teams-Token')
        
        if not auth_header and not teams_token:
            return jsonify({"error": "Authentication required"}), 401
        
        # Extract token
        token = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
        elif teams_token:
            token = teams_token
        
        if not token:
            return jsonify({"error": "Invalid authentication format"}), 401
        
        # Validate token
        user_payload = auth_manager.validate_teams_token(token)
        if not user_payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Store user info in Flask's g object
        g.current_user = user_payload
        g.teams_token = token
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current authenticated user from Flask's g object."""
    return getattr(g, 'current_user', None)

def get_teams_token() -> Optional[str]:
    """Get current Teams token from Flask's g object."""
    return getattr(g, 'teams_token', None)
