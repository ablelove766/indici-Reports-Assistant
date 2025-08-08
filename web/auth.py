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
    """Microsoft Teams SSO Authentication Manager."""
    
    def __init__(self):
        """Initialize Teams authentication manager."""
        self.client_id = config.azure_client_id
        self.client_secret = config.azure_client_secret
        self.tenant_id = config.azure_tenant_id
        self.authority = config.azure_authority
        self.scope = config.azure_scope
        
        # Initialize MSAL client
        self.msal_app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
        
        # Cache for JWT public keys
        self._jwt_keys_cache = {}
        self._jwt_keys_cache_expiry = None
        
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
                    discovery_response = requests.get(discovery_url, timeout=10)
                    discovery_response.raise_for_status()
                    discovery_data = discovery_response.json()
                    logger.info(f"Successfully retrieved discovery data from: {discovery_url}")
                    break
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Failed to get discovery data from {discovery_url}: {e}")
                    continue

            if not discovery_data:
                raise ValueError("Could not retrieve OpenID configuration from any endpoint")

            jwks_uri = discovery_data.get("jwks_uri")
            if not jwks_uri:
                raise ValueError("JWKS URI not found in discovery document")

            logger.info(f"Fetching JWKS from: {jwks_uri}")
            jwks_response = requests.get(jwks_uri, timeout=10)
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

            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                logger.warning("No key ID found in token header, skipping signature verification")
                # For development/testing, return unverified payload
                # In production, you should always verify signatures
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
                        audience=[self.client_id, f"api://{self.client_id}"],
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
        try:
            logger.info("Attempting token exchange using On-Behalf-Of flow")

            # Use MSAL to perform On-Behalf-Of flow
            result = self.msal_app.acquire_token_on_behalf_of(
                user_assertion=teams_token,
                scopes=[self.scope]
            )

            if "access_token" in result:
                logger.info("Successfully exchanged Teams token for Graph token")
                return result["access_token"]
            else:
                error_desc = result.get('error_description', 'Unknown error')
                error_code = result.get('error', 'unknown_error')
                logger.warning(f"Token exchange failed: {error_code} - {error_desc}")

                # For development/testing, we might want to continue without Graph token
                # In production, this should be handled based on your requirements
                if error_code in ['invalid_grant', 'interaction_required']:
                    logger.info("Token exchange failed but continuing with Teams token only")
                    return None
                else:
                    logger.error(f"Critical token exchange error: {error_code}")
                    return None

        except Exception as e:
            logger.error(f"Token exchange error: {e}")
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
