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

    // Check if we're in Teams environment - Enhanced detection
    const isTeams = window.location.href.includes('/teams') ||
                   window.navigator.userAgent.includes('Teams') ||
                   window.parent !== window ||
                   navigator.userAgent.includes('Teams') ||
                   navigator.userAgent.includes('MSTeams') ||
                   window.location.hostname.includes('teams') ||
                   (window.microsoftTeams && typeof window.microsoftTeams === 'object');

    if (isTeams) {
        // Teams-compatible print: Auto-open browser print dialog
        console.log('Teams environment detected, using auto-print...');
        createTeamsAutoPrint(printContent);
    } else {
        // Regular browser: Try popup window first, fallback to auto-print
        console.log('Regular browser, attempting popup window...');
        try {
            const printWindow = window.open('', '_blank', 'width=800,height=600,scrollbars=yes');
            if (printWindow && !printWindow.closed) {
                createPopupPrintWindow(printWindow, printContent);
            } else {
                throw new Error('Popup blocked');
            }
        } catch (error) {
            console.log('Popup blocked, falling back to auto-print...');
            createTeamsAutoPrint(printContent);
        }
    }
};

// Format print content into proper table structure
function formatPrintContent(htmlContent) {
    console.log('🖨️ TEAMS: Formatting print content for proper table structure');

    // Create a temporary div to parse the HTML content
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlContent;

    // Find all provider sections
    const providerSections = tempDiv.querySelectorAll('h3, .provider-section, .provider-name');
    let formattedHTML = '';

    // If we can't find structured data, try to parse the raw content
    if (providerSections.length === 0) {
        // Parse the content to extract provider data
        const lines = htmlContent.split('\n').filter(line => line.trim());
        let currentProvider = '';
        let providerData = {};

        lines.forEach(line => {
            const trimmedLine = line.trim();

            // Check if this is a provider name (usually appears as a heading)
            if (trimmedLine && !trimmedLine.includes('Age Range') && !trimmedLine.includes('Capitation') &&
                !trimmedLine.includes('Quantity') && !trimmedLine.includes('Total') &&
                !trimmedLine.match(/^\d/) && !trimmedLine.includes('0.00') &&
                trimmedLine.length > 3 && !trimmedLine.includes('<')) {

                if (currentProvider && providerData[currentProvider]) {
                    // Process previous provider data
                    formattedHTML += createProviderTable(currentProvider, providerData[currentProvider]);
                }

                currentProvider = trimmedLine.replace(/<[^>]*>/g, '').trim();
                providerData[currentProvider] = [];
            }
            // Check if this is age range data
            else if (trimmedLine.match(/^\d+[-\d\s]+/) || trimmedLine.includes('A3') || trimmedLine.includes('AZ') || trimmedLine.includes('C3') || trimmedLine.includes('Y3')) {
                if (currentProvider) {
                    const rowData = parseRowData(trimmedLine);
                    if (rowData) {
                        providerData[currentProvider].push(rowData);
                    }
                }
            }
        });

        // Process the last provider
        if (currentProvider && providerData[currentProvider]) {
            formattedHTML += createProviderTable(currentProvider, providerData[currentProvider]);
        }
    }

    return formattedHTML || htmlContent;
}

// Parse individual row data
function parseRowData(line) {
    // Remove HTML tags and clean the line
    const cleanLine = line.replace(/<[^>]*>/g, '').trim();

    // Try to extract age range, capitation amount, quantity, and total
    const parts = cleanLine.split(/\s+/);

    if (parts.length >= 4) {
        const ageRange = parts[0];
        const capAmount = parts[parts.length - 3] || '0.00';
        const quantity = parts[parts.length - 2] || '0';
        const totalAmount = parts[parts.length - 1] || '0.00';

        return {
            ageRange: ageRange,
            capitation: parseFloat(capAmount) || 0,
            quantity: parseInt(quantity) || 0,
            total: parseFloat(totalAmount) || 0
        };
    }

    return null;
}

// Create formatted table for each provider
function createProviderTable(providerName, data) {
    if (!data || data.length === 0) return '';

    let totalQuantity = 0;
    let totalAmount = 0;

    let tableRows = '';
    data.forEach(row => {
        totalQuantity += row.quantity;
        totalAmount += row.total;

        tableRows += `
            <tr>
                <td style="padding: 8px 12px; border: 1px solid #333; text-align: left;">${row.ageRange}</td>
                <td style="padding: 8px 12px; border: 1px solid #333; text-align: right;">${row.capitation.toFixed(2)}</td>
                <td style="padding: 8px 12px; border: 1px solid #333; text-align: center;">${row.quantity}</td>
                <td style="padding: 8px 12px; border: 1px solid #333; text-align: right;">${row.total.toFixed(2)}</td>
            </tr>
        `;
    });

    return `
        <div style="margin-bottom: 40px; page-break-inside: avoid;">
            <h2 style="margin: 0 0 15px 0; padding: 10px 0; border-bottom: 2px solid #333; font-size: 18px; font-weight: bold; color: #333;">${providerName}</h2>
            <table style="width: 100%; border-collapse: collapse; margin: 0; font-size: 12px;">
                <thead>
                    <tr style="background-color: #f5f5f5;">
                        <th style="padding: 12px; border: 1px solid #333; text-align: left; font-weight: bold; background-color: #f0f0f0;">Age Range</th>
                        <th style="padding: 12px; border: 1px solid #333; text-align: center; font-weight: bold; background-color: #f0f0f0;">Capitation Amount</th>
                        <th style="padding: 12px; border: 1px solid #333; text-align: center; font-weight: bold; background-color: #f0f0f0;">Quantity</th>
                        <th style="padding: 12px; border: 1px solid #333; text-align: center; font-weight: bold; background-color: #f0f0f0;">Total Amount</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
                <tfoot>
                    <tr style="background-color: #f9f9f9; font-weight: bold;">
                        <td style="padding: 10px 12px; border: 1px solid #333; text-align: left; font-weight: bold;">Total</td>
                        <td style="padding: 10px 12px; border: 1px solid #333; text-align: right;"></td>
                        <td style="padding: 10px 12px; border: 1px solid #333; text-align: center; font-weight: bold;">${totalQuantity}</td>
                        <td style="padding: 10px 12px; border: 1px solid #333; text-align: right; font-weight: bold;">${totalAmount.toFixed(2)}</td>
                    </tr>
                </tfoot>
            </table>
        </div>
    `;
}

// Teams auto-print function - automatically opens browser print dialog
function createTeamsAutoPrint(printContent) {
    console.log('🖨️ TEAMS: Creating auto-print view for Teams');

    // Create temporary print container
    const printContainer = document.createElement('div');
    printContainer.id = 'teams-auto-print-container';
    printContainer.style.cssText = `
        position: fixed;
        top: -9999px;
        left: -9999px;
        width: 210mm;
        background: white;
        font-family: Arial, sans-serif;
        font-size: 12px;
        line-height: 1.4;
        color: #333;
        padding: 20mm;
        box-sizing: border-box;
    `;

    // Format content for clean printing with proper table structure
    const formattedContent = formatPrintContent(printContent);
    printContainer.innerHTML = `
        <div class="auto-print-content">
            <div class="print-header" style="text-align: center; margin-bottom: 30px; border-bottom: 3px solid #333; padding-bottom: 20px;">
                <h1 style="margin: 0; font-size: 28px; color: #333; font-weight: bold;">Provider Capitation Report</h1>
                <p style="margin: 15px 0 0 0; color: #666; font-size: 14px; font-weight: 500;">Period Date: 1825-08-05 to 2025-08-05</p>
            </div>
            <div class="print-body">
                ${formattedContent}
            </div>
        </div>
    `;

    // Add print-specific styles
    const printStyles = document.createElement('style');
    printStyles.id = 'teams-auto-print-styles';
    printStyles.innerHTML = `
        @media print {
            body * {
                visibility: hidden;
            }
            #teams-auto-print-container,
            #teams-auto-print-container * {
                visibility: visible;
            }
            #teams-auto-print-container {
                position: absolute !important;
                left: 0 !important;
                top: 0 !important;
                width: 100% !important;
                height: auto !important;
                padding: 20px !important;
                margin: 0 !important;
                background: white !important;
                font-family: Arial, sans-serif !important;
                font-size: 12px !important;
                line-height: 1.4 !important;
                color: #333 !important;
            }
            .auto-print-content {
                width: 100% !important;
                max-width: none !important;
            }
            .auto-print-content table {
                width: 100% !important;
                border-collapse: collapse !important;
                margin: 20px 0 !important;
                font-size: 11px !important;
                page-break-inside: avoid !important;
                border: 1px solid #333 !important;
            }
            .auto-print-content table th {
                background: #f0f0f0 !important;
                color: #333 !important;
                padding: 10px 8px !important;
                text-align: center !important;
                font-weight: bold !important;
                border: 1px solid #333 !important;
                font-size: 11px !important;
                vertical-align: middle !important;
            }
            .auto-print-content table td {
                padding: 8px !important;
                border: 1px solid #333 !important;
                background: white !important;
                font-size: 11px !important;
                vertical-align: middle !important;
            }
            .auto-print-content table tfoot td {
                background: #f9f9f9 !important;
                font-weight: bold !important;
            }
            .auto-print-content h1 {
                font-size: 24px !important;
                margin: 0 0 10px 0 !important;
                text-align: center !important;
                color: #333 !important;
                font-weight: bold !important;
            }
            .auto-print-content h2 {
                font-size: 16px !important;
                margin: 30px 0 15px 0 !important;
                padding: 8px 0 !important;
                border-bottom: 2px solid #333 !important;
                color: #333 !important;
                font-weight: bold !important;
            }
            .print-header {
                text-align: center !important;
                margin-bottom: 30px !important;
                border-bottom: 3px solid #333 !important;
                padding-bottom: 20px !important;
                page-break-after: avoid !important;
            }
            .print-header p {
                margin: 15px 0 0 0 !important;
                color: #666 !important;
                font-size: 12px !important;
                font-weight: 500 !important;
            }
        }
    `;
    document.head.appendChild(printStyles);
    document.body.appendChild(printContainer);

    // Auto-trigger print dialog after a short delay
    setTimeout(() => {
        console.log('🖨️ TEAMS: Auto-triggering browser print dialog');
        window.print();

        // Clean up after printing
        setTimeout(() => {
            const container = document.getElementById('teams-auto-print-container');
            const styles = document.getElementById('teams-auto-print-styles');
            if (container) container.remove();
            if (styles) styles.remove();
            console.log('🖨️ TEAMS: Auto-print cleanup completed');
        }, 1000);
    }, 500);
}

// Teams-compatible modal print window function (DEPRECATED - keeping for fallback)
function createInlinePrintView(printContent) {
    console.log('🖨️ TEAMS: Creating Teams-compatible print modal window');

    // Create modal overlay that looks like a separate window
    const printModal = document.createElement('div');
    printModal.id = 'teams-print-modal';
    printModal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        box-sizing: border-box;
        backdrop-filter: blur(3px);
        -webkit-backdrop-filter: blur(3px);
    `;

    // Create the modal window content
    const modalWindow = document.createElement('div');
    modalWindow.style.cssText = `
        background: white;
        border-radius: 12px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        width: 90%;
        max-width: 900px;
        max-height: 90%;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        position: relative;
        border: 1px solid #e0e0e0;
    `;

    // Create window header (like a browser window)
    const windowHeader = document.createElement('div');
    windowHeader.style.cssText = `
        background: linear-gradient(135deg, #6264a7, #5a5fc7);
        color: white;
        padding: 15px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid #e0e0e0;
        border-radius: 12px 12px 0 0;
        font-weight: 600;
        font-size: 16px;
    `;

    windowHeader.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 12px; height: 12px; background: #ff5f57; border-radius: 50%;"></div>
            <div style="width: 12px; height: 12px; background: #ffbd2e; border-radius: 50%;"></div>
            <div style="width: 12px; height: 12px; background: #28ca42; border-radius: 50%;"></div>
            <span style="margin-left: 15px;">🖨️ Provider Capitation Report - Print Preview</span>
        </div>
        <button onclick="closeTeamsPrintModal()" style="
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: background 0.2s;
        " onmouseover="this.style.background='rgba(255, 255, 255, 0.3)'" onmouseout="this.style.background='rgba(255, 255, 255, 0.2)'">
            ×
        </button>
    `;

    // Create scrollable content area
    const contentArea = document.createElement('div');
    contentArea.style.cssText = `
        flex: 1;
        overflow-y: auto;
        padding: 30px;
        background: white;
        font-family: Arial, sans-serif;
        line-height: 1.6;
    `;

    contentArea.innerHTML = `
        <div class="teams-print-content">
            <div class="print-header" style="text-align: center; margin-bottom: 30px; border-bottom: 3px solid #6264a7; padding-bottom: 15px;">
                <h1 style="margin: 0; font-size: 28px; color: #333; font-weight: 700;">Provider Capitation Report</h1>
                <p style="margin: 10px 0 0 0; color: #666; font-size: 14px;">Generated on ${new Date().toLocaleDateString()}</p>
            </div>
            <div class="print-body">
                ${printContent}
            </div>
        </div>
    `;

    // Create action buttons footer
    const actionFooter = document.createElement('div');
    actionFooter.style.cssText = `
        background: #f8f9fa;
        padding: 20px 30px;
        border-top: 1px solid #e0e0e0;
        display: flex;
        justify-content: center;
        gap: 15px;
        border-radius: 0 0 12px 12px;
    `;

    actionFooter.innerHTML = `
        <button onclick="printTeamsModal()" style="
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
            transition: all 0.2s;
        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(0, 123, 255, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(0, 123, 255, 0.3)'">
            🖨️ Print Report
        </button>
        <button onclick="closeTeamsPrintModal()" style="
            background: linear-gradient(135deg, #6c757d, #545b62);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(108, 117, 125, 0.3);
            transition: all 0.2s;
        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(108, 117, 125, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(108, 117, 125, 0.3)'">
            ❌ Close
        </button>
    `;

    // Assemble the modal
    modalWindow.appendChild(windowHeader);
    modalWindow.appendChild(contentArea);
    modalWindow.appendChild(actionFooter);
    printModal.appendChild(modalWindow);

    // Add Teams-specific print styles
    const teamsModalPrintStyles = document.createElement('style');
    teamsModalPrintStyles.id = 'teams-modal-print-styles';
    teamsModalPrintStyles.innerHTML = `
        /* Teams Modal Print Styles */
        .teams-print-content table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }

        .teams-print-content table th {
            background: linear-gradient(135deg, #6264a7, #5a5fc7);
            color: white;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #4e54b8;
        }

        .teams-print-content table td {
            padding: 10px 15px;
            border-bottom: 1px solid #e0e0e0;
            background: white;
        }

        .teams-print-content table tr:nth-child(even) td {
            background: #f8f9fa;
        }

        .teams-print-content table tr:hover td {
            background: #e3f2fd;
        }

        .teams-print-content .provider-section {
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background: #fafafa;
        }

        .teams-print-content .provider-section h3 {
            margin: 0 0 15px 0;
            color: #6264a7;
            font-size: 20px;
            font-weight: 700;
            border-bottom: 2px solid #6264a7;
            padding-bottom: 8px;
        }

        @media print {
            body * {
                visibility: hidden;
            }
            #teams-print-modal, #teams-print-modal * {
                visibility: visible;
            }
            #teams-print-modal {
                position: absolute !important;
                left: 0 !important;
                top: 0 !important;
                width: 100% !important;
                height: 100% !important;
                padding: 0 !important;
                margin: 0 !important;
                background: white !important;
                backdrop-filter: none !important;
                -webkit-backdrop-filter: none !important;
            }
            #teams-print-modal > div {
                width: 100% !important;
                max-width: 100% !important;
                height: 100% !important;
                max-height: 100% !important;
                border-radius: 0 !important;
                box-shadow: none !important;
                border: none !important;
            }
            #teams-print-modal .print-header {
                border-bottom: 3px solid #333 !important;
                margin-bottom: 20px !important;
            }
            #teams-print-modal button,
            #teams-print-modal .print-controls,
            .print-controls {
                display: none !important;
            }
            .teams-print-content table {
                page-break-inside: avoid;
                break-inside: avoid;
            }
            .provider-section {
                page-break-inside: avoid;
                break-inside: avoid;
            }
        }
    `;
    document.head.appendChild(teamsModalPrintStyles);

    // Add Teams modal functions to global scope
    window.closeTeamsPrintModal = function() {
        console.log('🖨️ TEAMS: Closing Teams print modal');
        const modal = document.getElementById('teams-print-modal');
        if (modal) {
            modal.remove();
        }
        // Remove print styles
        const styles = document.getElementById('teams-modal-print-styles');
        if (styles && styles.parentNode) {
            styles.parentNode.removeChild(styles);
        }
        delete window.closeTeamsPrintModal;
        delete window.printTeamsModal;
    };

    window.printTeamsModal = function() {
        console.log('🖨️ TEAMS: Triggering print for Teams modal');
        window.print();
    };

    // Add click outside to close
    printModal.addEventListener('click', function(e) {
        if (e.target === printModal) {
            window.closeTeamsPrintModal();
        }
    });

    // Add escape key to close
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            window.closeTeamsPrintModal();
        }
    });

    document.body.appendChild(printModal);
    console.log('✅ TEAMS: Teams-compatible print modal window created successfully');
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
            }, 500);
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


        } catch (error) {
            console.error('Error loading system status:', error);
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
