"""Tools for interacting with the indici Reports API."""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
from .config import config

logger = logging.getLogger(__name__)

def validate_dates(date_from: Optional[str], date_to: Optional[str]) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    Validate date parameters according to business rules.

    Args:
        date_from: Start date string (optional)
        date_to: End date string (optional)

    Returns:
        Tuple of (is_valid, error_message, validated_date_from, validated_date_to)
    """
    # If no dates provided, return nulls
    if not date_from and not date_to:
        return True, "", None, None

    # If date_to provided but date_from is not, show error
    if date_to and not date_from:
        return False, "Date from is empty, please add date from", None, None

    # Parse and validate date_from if provided
    validated_date_from = None
    if date_from:
        try:
            # Try to parse the date (assuming ISO format or common formats)
            if 'T' in date_from:
                datetime.fromisoformat(date_from.replace('Z', '+00:00')).date()
            else:
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
                    try:
                        datetime.strptime(date_from, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    return False, f"Invalid date format for date from: {date_from}", None, None

            # Allow future dates - business requirement: Allow querying future dates for planning purposes
            validated_date_from = date_from
        except Exception as e:
            return False, f"Invalid date from: {str(e)}", None, None

    # Parse and validate date_to if provided
    validated_date_to = None
    if date_to:
        try:
            # Try to parse the date
            if 'T' in date_to:
                parsed_date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00')).date()
            else:
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
                    try:
                        parsed_date_to = datetime.strptime(date_to, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    return False, f"Invalid date format for date to: {date_to}", None, None

            # If both dates provided, check that date_to > date_from
            if validated_date_from:
                if 'T' in validated_date_from:
                    parsed_validated_from = datetime.fromisoformat(validated_date_from.replace('Z', '+00:00')).date()
                else:
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
                        try:
                            parsed_validated_from = datetime.strptime(validated_date_from, fmt).date()
                            break
                        except ValueError:
                            continue

                if parsed_date_to <= parsed_validated_from:
                    return False, f"Date to ({date_to}) should be greater than date from ({validated_date_from})", None, None

            validated_date_to = date_to
        except Exception as e:
            return False, f"Invalid date to: {str(e)}", None, None

    return True, "", validated_date_from, validated_date_to

class indiciAPITools:
    """Tools for interacting with the indici Reports API."""
    
    def __init__(self):
        """Initialize the API tools."""
        self.base_url = config.indici_api_base_url
        self.endpoints = config.indici_api_endpoints
        self.timeout = config.indici_api_timeout
        
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the indici API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        try:
                            return await response.json()
                        except json.JSONDecodeError:
                            return {"success": True, "data": response_text}
                    else:
                        logger.error(f"API request failed: {response.status} - {response_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {response_text}",
                            "status_code": response.status
                        }
                        
        except asyncio.TimeoutError:
            logger.error(f"Request timeout for {url}")
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_provider_capitation_report(
        self,
        practice_id: int = 1,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        provider_name: Optional[str] = None,
        location_id: Optional[str] = None,
        practice_location_id: Optional[int] = None,
        sort_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get Provider Capitation Report using query parameters.

        Args:
            practice_id: Practice ID (defaults to 0)
            date_from: Start date (optional, will be null if not provided)
            date_to: End date (optional, will be null if not provided)
            provider_name: Provider Name(s) - comma separated (optional)
            location_id: Location ID(s) - comma separated (optional)
            practice_location_id: Practice Location ID (optional)
            sort_by: Sort by field (optional)

        Returns:
            Dict containing the API response
        """
        # Validate dates first
        is_valid, error_message, validated_date_from, validated_date_to = validate_dates(date_from, date_to)

        if not is_valid:
            return {
                "success": False,
                "error": error_message,
                "data": None
            }

        params = {"practiceId": practice_id}

        # Only add dates to params if they are provided and valid
        if validated_date_from:
            params["dateFrom"] = validated_date_from
        if validated_date_to:
            params["dateTo"] = validated_date_to
        if provider_name:
            params["providerName"] = provider_name
        if location_id:
            params["locationId"] = location_id
        if practice_location_id is not None:
            params["practiceLocationId"] = practice_location_id
        if sort_by:
            params["sortBy"] = sort_by
            
        logger.info(f"Getting Provider Capitation Report with params: {params}")
        
        return await self._make_request(
            method="GET",
            endpoint=self.endpoints["provider_capitation_report"],
            params=params
        )

    async def get_all_income_providers(
        self,
        practice_id: int = 1,
        practice_location_id: int = 1
    ) -> Dict[str, Any]:
        """
        Get all income providers for Provider Capitation Report.

        Args:
            practice_id: Practice ID (defaults to 0)
            practice_location_id: Practice Location ID (defaults to 0)

        Returns:
            Dict containing the API response with income providers list
        """
        params = {
            "practiceId": practice_id,
            "practiceLocationId": practice_location_id
        }

        logger.info(f"Getting Income Providers with params: {params}")

        return await self._make_request(
            method="GET",
            endpoint=self.endpoints["income_providers_report"],
            params=params
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Provider Capitation Report service by calling the main endpoint.

        Returns:
            Dict containing the health check response
        """
        logger.info("Performing health check by testing main endpoint")

        # Test the main endpoint with minimal parameters to check if service is running
        try:
            result = await self.get_provider_capitation_report()
            if result.get("success", True):
                return {
                    "success": True,
                    "message": "Provider Capitation Report service is healthy",
                    "data": "Service responded successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Provider Capitation Report service health check failed",
                    "error": result.get("error", "Unknown error")
                }
        except Exception as e:
            return {
                "success": False,
                "message": "Provider Capitation Report service health check failed",
                "error": str(e)
            }
    
    def format_report_summary(self, report_data: Dict[str, Any]) -> str:
        """
        Format report data into responsive HTML tables with Bootstrap styling.

        Args:
            report_data: The report response data

        Returns:
            HTML formatted table string grouped by provider
        """
        if not report_data.get("success", True):
            return f'<div class="alert alert-danger">❌ Report generation failed: {report_data.get("error", "Unknown error")}</div>'

        data = report_data.get("data", {})
        if not data:
            return '<div class="alert alert-warning">❌ No report data received</div>'

        # Extract key information
        total_records = data.get("totalRecords", 0)
        results = data.get("results", [])
        provider_name_filter = data.get("providerName", "")

        # Debug logging
        logger.info(f"Results count: {len(results)}")
        logger.info(f"Total records: {total_records}")
        logger.info(f"Provider name filter: {provider_name_filter}")

        # Handle zero records case - show simple "No record found" message
        if not results or total_records == 0:
            return self._format_no_records_table(provider_name_filter)

        # Group results by provider
        providers = {}
        for result in results:
            provider_name = result.get("providerName", "Unknown")
            if provider_name not in providers:
                providers[provider_name] = []
            providers[provider_name].append(result)



        # Build the HTML output with full-width styling
        html_output = f"""
<div class="w-100" style="width: 100% !important; max-width: 100% !important;">
    <div class="card border-0 w-100">
        <div class="card-header bg-primary text-white">
            <h4 class="mb-0">📊 Provider Capitation Report</h4>
        </div>
        <div class="card-body p-2 w-100">
            <div class="mb-2">
                <strong>Total Records:</strong> {total_records}
            </div>
"""

        # Format each provider section
        for provider_name, provider_results in providers.items():
            # Provider total calculations
            provider_total_quantity = sum(result.get("quantity", 0) for result in provider_results)
            provider_total_amount = sum(result.get("totalAmount", 0) for result in provider_results)

            # Add margin before provider name (except for first provider)
            margin_class = "mt-3" if list(providers.keys()).index(provider_name) > 0 else ""

            html_output += f"""
            <div class="mb-3 w-100 {margin_class}">
                <h5 style="text-align: center; color: #0066cc; font-weight: bold; margin: 20px 0 10px 0; font-size: 16px;">{provider_name}</h5>
                <table class="table table-bordered mb-1 w-100" style="width: 100% !important; table-layout: fixed; border-collapse: collapse;">
                    <thead style="background-color: #e9ecef;">
                        <tr>
                            <th scope="col" style="width: 25%; background-color: #e9ecef; border: 1px solid #dee2e6; padding: 8px; font-weight: bold;">AgeRange</th>
                            <th scope="col" class="text-end" style="width: 25%; background-color: #e9ecef; border: 1px solid #dee2e6; padding: 8px; font-weight: bold;">CapitationAmount</th>
                            <th scope="col" class="text-end" style="width: 25%; background-color: #e9ecef; border: 1px solid #dee2e6; padding: 8px; font-weight: bold;">Quantity</th>
                            <th scope="col" class="text-end" style="width: 25%; background-color: #e9ecef; border: 1px solid #dee2e6; padding: 8px; font-weight: bold;">TotalAmount</th>
                        </tr>
                    </thead>
                    <tbody>
"""

            # Add rows for this provider
            for result in provider_results:
                age_range = result.get("ageRange", "N/A")
                capitation_amount = result.get("capitationAmount", 0)
                quantity = result.get("quantity", 0)
                total_amount = result.get("totalAmount", 0)

                html_output += f"""
                        <tr style="background-color: #ffffff;">
                            <td style="border: 1px solid #dee2e6; padding: 8px; background-color: #f8f9fa;">{age_range}</td>
                            <td class="text-end" style="border: 1px solid #dee2e6; padding: 8px;">{capitation_amount:.2f}</td>
                            <td class="text-end" style="border: 1px solid #dee2e6; padding: 8px;">{quantity}</td>
                            <td class="text-end" style="border: 1px solid #dee2e6; padding: 8px;">{total_amount:.2f}</td>
                        </tr>
"""

            # Add total row for this provider
            html_output += f"""
                        <tr style="background-color: #f8f9fa; font-weight: bold;">
                            <td style="border: 1px solid #dee2e6; padding: 8px; background-color: #f8f9fa; font-weight: bold;">Total</td>
                            <td class="text-end" style="border: 1px solid #dee2e6; padding: 8px;"></td>
                            <td class="text-end" style="border: 1px solid #dee2e6; padding: 8px; font-weight: bold;">{provider_total_quantity}</td>
                            <td class="text-end" style="border: 1px solid #dee2e6; padding: 8px; font-weight: bold;">{provider_total_amount:.2f}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
"""

        # Close the HTML structure
        html_output += f"""
        </div>
    </div>
</div>
"""

        return html_output

    def _format_no_records_table(self, provider_name_filter: str = "") -> str:
        """
        Format a simple "No record found" message when no records are found.

        Args:
            provider_name_filter: Provider name that was searched for

        Returns:
            HTML formatted simple "No record found" message
        """
        provider_info = f" for this provider ({provider_name_filter})" if provider_name_filter else ""

        html_output = f"""
<div class="w-100" style="width: 100% !important; max-width: 100% !important;">
    <div class="alert alert-danger text-center" style="background-color: #f8d7da; border-color: #f5c6cb; color: #721c24; padding: 15px; border-radius: 8px; margin: 0;">
        <strong>No record found{provider_info}</strong>
    </div>
</div>
"""
        return html_output

    def format_print_report(self, report_data: Dict[str, Any]) -> str:
        """
        Format report data for printing with a clean, professional print layout.

        Args:
            report_data: The report response data

        Returns:
            HTML formatted print-ready report
        """
        if not report_data.get("success", True):
            return f'<div class="alert alert-danger">❌ Report generation failed: {report_data.get("error", "Unknown error")}</div>'

        data = report_data.get("data", {})
        if not data:
            return '<div class="alert alert-warning">❌ No report data received</div>'

        # Extract key information
        total_records = data.get("totalRecords", 0)
        results = data.get("results", [])
        provider_name_filter = data.get("providerName", "")
        date_from = data.get("dateFrom", "")
        date_to = data.get("dateTo", "")

        # Handle zero records case
        if not results or total_records == 0:
            provider_info = f" for provider '{provider_name_filter}'" if provider_name_filter else ""
            return f"""
<div class="print-container" style="margin: 20px 0;">
    <div class="alert alert-warning text-center">
        <strong>No records found{provider_info} for printing</strong>
    </div>
</div>
"""

        # Group results by provider
        providers = {}
        for result in results:
            provider_name = result.get("providerName", "Unknown")
            if provider_name not in providers:
                providers[provider_name] = []
            providers[provider_name].append(result)

        # Format period dates
        period_text = ""
        if date_from and date_to:
            try:
                from_date = date_from.split('T')[0] if 'T' in date_from else date_from
                to_date = date_to.split('T')[0] if 'T' in date_to else date_to
                period_text = f"Period Date: {from_date} to {to_date}"
            except:
                period_text = f"Period Date: {date_from} to {date_to}"

        # Build print-ready HTML (clean grouped format like your desired layout)
        print_html = f"""
<div class="print-container">
    <div class="print-header">
        <h2>Provider Capitation Report</h2>
        {f'<p>{period_text}</p>' if period_text else ''}
    </div>
"""

        # Add each provider section in the grouped format you want
        for provider_name, provider_results in providers.items():
            provider_total_quantity = sum(result.get("quantity", 0) for result in provider_results)
            provider_total_amount = sum(result.get("totalAmount", 0) for result in provider_results)

            # Extract provider type from name (e.g., "Doctor FINANCE - CN")
            provider_display = provider_name
            if " - " in provider_name:
                provider_display = f"{provider_name}"

            print_html += f"""
    <div class="provider-section">
        <div class="provider-header">
            <h3>{provider_display}</h3>
        </div>

        <div class="provider-data">
            <div class="data-row header-row">
                <span class="age-range">Age Range</span>
                <span class="capitation-amount">Capitation Amount</span>
                <span class="quantity">Quantity</span>
                <span class="total-amount">Total Amount</span>
            </div>
"""

            # Add provider results in clean row format
            for result in provider_results:
                age_range = result.get("ageRange", "N/A")
                capitation_amount = result.get("capitationAmount", 0)
                quantity = result.get("quantity", 0)
                total_amount = result.get("totalAmount", 0)

                print_html += f"""
            <div class="data-row">
                <span class="age-range">{age_range}</span>
                <span class="capitation-amount">{capitation_amount:.2f}</span>
                <span class="quantity">{quantity}</span>
                <span class="total-amount">{total_amount:.2f}</span>
            </div>
"""

            # Add provider total row
            print_html += f"""
            <div class="data-row total-row">
                <span class="age-range"><strong>Total</strong></span>
                <span class="capitation-amount"></span>
                <span class="quantity"><strong>{provider_total_quantity}</strong></span>
                <span class="total-amount"><strong>{provider_total_amount:.2f}</strong></span>
            </div>
        </div>
    </div>
"""

        print_html += """
</div>
"""

        return print_html

    def add_auto_print_popup(self, display_result: str, print_content: str) -> str:
        """
        Add a print popup trigger to the display result.

        Args:
            display_result: The formatted result to show in chat
            print_content: The print-ready content for popup

        Returns:
            Combined result with popup trigger
        """
        # Create a simple popup window approach that works reliably
        popup_trigger = f"""
<div class="print-popup-container" style="margin: 20px 0;">
    <div class="alert alert-success text-center">
        <i class="fas fa-print"></i> <strong>Print window will open automatically...</strong>
        <br><small>Click the button below if it doesn't open</small>
    </div>
    <div class="text-center mt-2">
        <button onclick="window.openPrintWindow()" class="btn btn-primary btn-lg">
            🖨️ Open Print Window
        </button>
    </div>
</div>

<!-- Hidden print content for extraction -->
<div id="printContent" style="display: none;">
{print_content}
</div>
"""

        return f"{display_result}\n\n{popup_trigger}"

    def format_income_providers_table(self, data: Dict[str, Any]) -> str:
        """
        Format income providers response as an HTML table.

        Args:
            data: API response data containing income providers list

        Returns:
            HTML formatted table of income providers
        """
        if not data:
            return '<div class="alert alert-warning">❌ No income providers data received</div>'

        # Extract key information
        total_records = data.get("totalRecords", 0)
        practice_id = data.get("practiceId", "N/A")
        practice_location_id = data.get("practiceLocationId", "N/A")
        results = data.get("results", [])
        retrieved_at = data.get("retrievedAt", "")

        # Handle zero records case
        if not results or total_records == 0:
            return f"""
<div class="w-100" style="width: 100% !important; max-width: 100% !important;">
    <div class="alert alert-info text-center" style="background-color: #d1ecf1; border-color: #bee5eb; color: #0c5460; padding: 15px; border-radius: 8px; margin: 0;">
        <strong>No income providers found for Practice ID: {practice_id}, Location ID: {practice_location_id}</strong>
    </div>
</div>
"""

        # Build HTML table output
        html_output = f"""
<div class="w-100" style="width: 100% !important; max-width: 100% !important;">
    <div class="card border-0 shadow-sm">
        <div class="card-header bg-success text-white">
            <h4 class="mb-0">👥 Income Providers List</h4>
        </div>
        <div class="card-body p-2 w-100">
            <div class="mb-2">
                <strong>Practice ID:</strong> {practice_id} &nbsp;&nbsp;&nbsp;
                <strong>Location ID:</strong> {practice_location_id} &nbsp;&nbsp;&nbsp;
                <strong>Total Records:</strong> {total_records}
            </div>

            <div class="table-responsive">
                <table class="table table-striped table-hover mb-0" style="font-size: 12px;">
                    <thead class="table-dark">
                        <tr>
                            <th style="width: 15%; text-align: center;">Patient ID</th>
                            <th style="width: 50%; text-align: left;">Provider Full Name</th>
                            <th style="width: 35%; text-align: center;">Provider ID (UUID)</th>
                        </tr>
                    </thead>
                    <tbody>
"""

        # Add table rows
        for result in results:
            patient_id = result.get("patientID", "N/A")
            full_name = result.get("fullName", "N/A")
            provider_id = result.get("providerID", "N/A")

            html_output += f"""
                        <tr style="background-color: #ffffff;">
                            <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; background-color: #f8f9fa;">{patient_id}</td>
                            <td style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">{full_name}</td>
                            <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center; font-family: monospace; font-size: 10px;">{provider_id}</td>
                        </tr>
"""

        html_output += f"""
                    </tbody>
                </table>
            </div>

            <div class="mt-2 text-muted" style="font-size: 11px;">
                <i class="fas fa-clock"></i> Retrieved: {retrieved_at}
            </div>
        </div>
    </div>
</div>
"""

        return html_output

    def format_income_providers_simple_table(self, data: Dict[str, Any]) -> str:
        """
        Format income providers response as a simple HTML table with only Provider Full Name.
        Used for Provider Capitation Report income providers list.

        Args:
            data: API response data containing income providers list

        Returns:
            HTML formatted simple table of provider names only
        """
        if not data:
            return '<div class="alert alert-warning">❌ No income providers data received</div>'

        # Extract key information
        total_records = data.get("totalRecords", 0)
        results = data.get("results", [])

        # Handle zero records case
        if not results or total_records == 0:
            return f"""
<div class="w-100" style="width: 100% !important; max-width: 100% !important;">
    <div class="alert alert-info text-center" style="background-color: #d1ecf1; border-color: #bee5eb; color: #0c5460; padding: 15px; border-radius: 8px; margin: 0;">
        <strong>No income providers found for Provider Capitation Report</strong>
    </div>
</div>
"""

        # Build simple HTML table output (only Provider Full Name)
        html_output = f"""
<div class="w-100" style="width: 100% !important; max-width: 100% !important;">
    <div class="card border-0 shadow-sm">
        <div class="card-header bg-info text-white">
            <h4 class="mb-0">👥 Income Providers for Provider Capitation Report</h4>
        </div>
        <div class="card-body p-2 w-100">
            <div class="mb-2">
                <strong>Total Providers:</strong> {total_records}
            </div>

            <div class="table-responsive">
                <table class="table table-striped table-hover mb-0" style="font-size: 14px;">
                    <thead class="table-dark">
                        <tr>
                            <th style="width: 100%; text-align: left;">Provider Full Name</th>
                        </tr>
                    </thead>
                    <tbody>
"""

        # Add table rows (only provider names)
        for result in results:
            full_name = result.get("fullName", "N/A")

            html_output += f"""
                        <tr style="background-color: #ffffff;">
                            <td style="border: 1px solid #dee2e6; padding: 12px; text-align: left; font-weight: 500;">{full_name}</td>
                        </tr>
"""

        html_output += f"""
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
"""

        return html_output

    async def ad_login(self, username: str, machine_ip: str = None) -> Dict[str, Any]:
        """
        Authenticate user via AD login endpoint.
        
        Args:
            username: User's email/username for AD authentication
            machine_ip: Optional machine IP address
            
        Returns:
            Dictionary containing user info, practices, and other AD login data
        """
        try:
            logger.info(f"Attempting AD login for user: {username}")
            
            # Prepare request payload
            payload = {
                "userName": username,
                "machineSignature": "MCP-Teams-Integration",
                "machineIP": machine_ip or "127.0.0.1"
            }
            
            # Make request to AD login endpoint
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/Login/AdLogin"
                logger.info(f"Calling AD login endpoint: {url}")
                
                async with session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"AD login successful for user: {username}")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"AD login failed for user {username}: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"AD login failed: {response.status}",
                            "details": error_text
                        }
                        
        except Exception as e:
            logger.error(f"Exception during AD login for user {username}: {str(e)}")
            return {
                "success": False,
                "error": f"AD login exception: {str(e)}"
            }

    def get_sample_queries(self) -> List[Dict[str, str]]:
        """Get sample queries for the chatbot interface."""
        return [
            # Provider Capitation Queries
            {
                "title": "Generate Monthly Report",
                "query": "Generate a Provider Capitation Report for the current month",
                "description": "Get current month's capitation report with smart defaults"
            },
            {
                "title": "Yearly Summary",
                "query": "Show me the Provider Capitation Report for the entire year 2024",
                "description": "Annual capitation summary with flexible date parsing"
            },
            {
                "title": "Print Provider Report",
                "query": "Show me the provider capitation report in print",
                "description": "Display and print provider capitation report"
            },
            {
                "title": "Provider List For Capitation",
                "query": "Show me the income provider list for provider capitation report",
                "description": "Get income providers list for Provider Capitation Report (simple table with names only)"
            },

            # Additional Queries (for future expansion)
            {
                "title": "Service Health Check",
                "query": "Check if the Provider Capitation Report service is healthy",
                "description": "Verify service status and connectivity"
            }
        ]

# Global instance
indici_tools = indiciAPITools()
