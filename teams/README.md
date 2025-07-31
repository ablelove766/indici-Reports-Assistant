# Microsoft Teams Integration for Indici Reports Assistant

## 📋 Overview

This directory contains the Microsoft Teams app package for the Indici Reports Assistant. The app allows users to access the AI-powered healthcare reports assistant directly within Microsoft Teams.

## 🎯 Features

- **Tab Integration**: Add as a tab in Teams channels or personal apps
- **Responsive Design**: Optimized for Teams interface
- **Secure Embedding**: Proper CSP headers and iframe security
- **Teams SDK Integration**: Full Teams context awareness
- **Healthcare Compliance**: HIPAA-compliant design

## 📁 Files Required

### 1. App Manifest
- `manifest.json` - Teams app configuration ✅

### 2. App Icons (Required)
You need to create these icon files:

- `color.png` - 192x192px color icon
- `outline.png` - 32x32px outline icon (white/transparent)

### 3. App Package
Create a ZIP file containing:
- manifest.json
- color.png  
- outline.png

## 🚀 Installation Steps

### Step 1: Create App Icons

Create two PNG files:

**color.png (192x192px)**
- Full color version of your app icon
- Should represent the Indici brand
- Recommended: Blue background (#2563eb) with white chart/analytics icon

**outline.png (32x32px)**  
- Simple outline version
- White or transparent background
- Monochrome design

### Step 2: Update Manifest URLs

Edit `manifest.json` and replace `0.0.0.0:10000` with your actual domain:

```json
{
  "developer": {
    "privacyUrl": "https://your-domain.com/teams/privacy",
    "termsOfUseUrl": "https://your-domain.com/teams/terms"
  },
  "configurableTabs": [{
    "configurationUrl": "https://your-domain.com/teams/config"
  }],
  "staticTabs": [{
    "contentUrl": "https://your-domain.com/teams"
  }],
  "validDomains": [
    "your-domain.com"
  ]
}
```

### Step 3: Create App Package

1. Create a ZIP file containing:
   - manifest.json
   - color.png
   - outline.png

2. Name it `indici-reports-assistant.zip`

### Step 4: Upload to Teams

1. Open Microsoft Teams
2. Go to Apps → Manage your apps
3. Click "Upload an app" → "Upload a custom app"
4. Select your ZIP file
5. Follow the installation prompts

## 🔧 Configuration

### Environment Variables

Ensure these are set in your `.env` file:

```bash
WEB_INTERFACE_HOST=0.0.0.0
WEB_INTERFACE_PORT=10000
```

### Teams-Specific Routes

The app provides these Teams-specific endpoints:

- `/teams` - Main Teams tab interface
- `/teams/config` - Tab configuration page
- `/teams/privacy` - Privacy policy
- `/teams/terms` - Terms of use

## 🛡️ Security Features

### Content Security Policy
- Allows iframe embedding from Teams domains
- Restricts script sources to trusted CDNs
- Prevents clickjacking attacks

### CORS Configuration
- Configured for Teams domains
- Supports both teams.microsoft.com and teams.live.com

### Teams SDK Integration
- Full Teams context awareness
- Theme detection and adaptation
- Proper initialization and error handling

## 🎨 Teams UI Adaptations

### Responsive Design
- Sidebar width optimized for Teams
- Mobile-friendly layout
- Proper scrolling behavior

### Theme Support
- Adapts to Teams light/dark themes
- Consistent with Teams design language
- Proper contrast ratios

## 📊 Usage Analytics

The app tracks:
- Teams context information
- Usage patterns within Teams
- Performance metrics
- Error rates

## 🔍 Troubleshooting

### Common Issues

1. **App won't load in Teams**
   - Check CSP headers
   - Verify HTTPS is enabled
   - Check console for errors

2. **Configuration page not working**
   - Ensure Teams SDK is loaded
   - Check network connectivity
   - Verify manifest URLs

3. **Icons not displaying**
   - Check icon file sizes (192x192 and 32x32)
   - Ensure PNG format
   - Verify files are in ZIP package

### Debug Mode

Add `?debug=true` to any URL to enable debug logging:
```
https://your-domain.com/teams?debug=true
```

## 📞 Support

For Teams integration support:
1. Check the browser console for errors
2. Verify all URLs in manifest.json are accessible
3. Test the app outside of Teams first
4. Contact your Teams administrator for deployment issues

## 🔄 Updates

To update the Teams app:
1. Modify the version in manifest.json
2. Recreate the ZIP package
3. Upload the new version to Teams
4. Users will be prompted to update
