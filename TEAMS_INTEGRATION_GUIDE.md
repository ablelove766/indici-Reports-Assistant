# Microsoft Teams Integration Guide

## 🎯 Overview

Your Indici Reports Assistant is now fully configured for Microsoft Teams integration! This guide explains what has been implemented and how to deploy it.

## ✅ What's Been Implemented

### 1. **Security & CSP Headers**
- ✅ Content Security Policy allowing Teams iframe embedding
- ✅ X-Frame-Options configured for Teams domains
- ✅ CORS settings for Teams origins
- ✅ Secure script and style source restrictions

### 2. **Teams SDK Integration**
- ✅ Microsoft Teams JavaScript SDK v2.0
- ✅ Teams context detection and theme adaptation
- ✅ Proper initialization and error handling
- ✅ Teams-specific event handlers

### 3. **Responsive Design**
- ✅ Teams-optimized sidebar width (280px)
- ✅ Mobile-responsive layout for Teams mobile
- ✅ Dark/light theme support
- ✅ Iframe-optimized styling

### 4. **Teams App Structure**
- ✅ App manifest (`teams/manifest.json`)
- ✅ Configuration page (`/teams/config`)
- ✅ Privacy policy page (`/teams/privacy`)
- ✅ Terms of use page (`/teams/terms`)
- ✅ Teams-specific routes and handlers

## 🚀 Deployment Steps

### Step 1: Update Your Domain

Replace `0.0.0.0:10000` in `teams/manifest.json` with your actual domain:

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

### Step 2: Create App Icons

Create these icon files in the `teams/` directory:

**color.png (192x192px)**
- Full color app icon
- Recommended: Blue background (#2563eb) with white analytics icon
- PNG format, exactly 192x192 pixels

**outline.png (32x32px)**
- Simple outline version
- White/transparent background
- PNG format, exactly 32x32 pixels

### Step 3: Create Teams App Package

1. Create a ZIP file containing:
   ```
   teams/
   ├── manifest.json
   ├── color.png
   └── outline.png
   ```

2. Name it `indici-reports-assistant.zip`

### Step 4: Deploy to Teams

1. **For Personal Use:**
   - Open Microsoft Teams
   - Go to Apps → Manage your apps
   - Click "Upload an app" → "Upload a custom app"
   - Select your ZIP file

2. **For Organization:**
   - Contact your Teams administrator
   - Provide the ZIP file for organization-wide deployment
   - Follow your organization's app approval process

## 🔧 Configuration Options

### Environment Variables

Your `.env` file should include:

```bash
# Server Configuration (already set)
WEB_INTERFACE_HOST=0.0.0.0
WEB_INTERFACE_PORT=10000

# Optional Teams-specific settings
TEAMS_APP_ID=indici-mcp-chatbot-app
TEAMS_TENANT_ID=your-tenant-id  # Optional
```

### Teams Tab Configuration

Users can configure:
- **Tab Name**: Custom name for the tab (max 16 characters)
- **Default View**: Full interface, compact, or chat-only
- **Default Practice ID**: Pre-populate practice ID for faster queries

## 🎨 Teams UI Features

### Responsive Design
- **Desktop**: Full sidebar + chat interface
- **Mobile**: Collapsible sidebar with mobile-optimized layout
- **Teams Mobile**: Optimized for Teams mobile app

### Theme Support
- **Light Theme**: Matches Teams light mode
- **Dark Theme**: Automatically adapts to Teams dark mode
- **High Contrast**: Supports Teams accessibility themes

### Teams-Specific Optimizations
- Sidebar width optimized for Teams layout
- Proper scrolling behavior in iframe
- Teams-compatible keyboard shortcuts
- Context-aware functionality

## 🛡️ Security Features

### Content Security Policy
```
default-src 'self' https://teams.microsoft.com;
script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
frame-ancestors https://teams.microsoft.com https://*.teams.microsoft.com;
```

### CORS Configuration
- Allows Teams domains: `teams.microsoft.com`, `*.teams.microsoft.com`
- Supports both commercial and government Teams instances
- Includes Teams mobile domains

## 📱 Usage Scenarios

### 1. **Channel Tab**
- Add to any Teams channel
- Shared access for team members
- Collaborative report analysis

### 2. **Personal App**
- Individual access in personal Teams
- Private report generation
- Personal analytics dashboard

### 3. **Meeting Tab**
- Add to Teams meetings
- Real-time report sharing during meetings
- Meeting-specific analytics

### 4. **Chat Tab**
- Add to group chats
- Quick report access in conversations
- Contextual data sharing

## 🔍 Testing

### Local Testing
1. Start your application: `python web/app.py`
2. Access Teams interface: `http://0.0.0.0:10000/teams`
3. Test configuration page: `http://0.0.0.0:10000/teams/config`

### Teams Testing
1. Upload app to Teams (development)
2. Add as personal app first
3. Test all functionality
4. Add to a test channel/chat

## 🐛 Troubleshooting

### Common Issues

1. **App won't load in Teams**
   - Check HTTPS is enabled (required for production)
   - Verify CSP headers are correct
   - Check browser console for errors

2. **Configuration page not working**
   - Ensure Teams SDK loads properly
   - Check network connectivity
   - Verify manifest URLs are accessible

3. **Theme not adapting**
   - Check Teams SDK initialization
   - Verify theme detection code
   - Test in different Teams themes

### Debug Mode
Add `?debug=true` to enable debug logging:
```
https://your-domain.com/teams?debug=true
```

## 📊 Analytics

The Teams integration tracks:
- Teams context information (tenant, user, channel)
- Usage patterns within Teams
- Performance metrics
- Error rates and debugging info

## 🔄 Updates

To update the Teams app:
1. Increment version in `manifest.json`
2. Recreate the ZIP package
3. Upload new version to Teams
4. Users will be prompted to update

## 📞 Support

For Teams integration support:
1. Check browser console for errors
2. Test the app outside Teams first
3. Verify all manifest URLs are accessible
4. Contact Teams administrator for deployment issues

## 🎉 Next Steps

1. **Create app icons** (color.png and outline.png)
2. **Update manifest.json** with your domain
3. **Create ZIP package** for Teams
4. **Test locally** before deploying
5. **Upload to Teams** for testing
6. **Deploy organization-wide** (if approved)

Your Indici Reports Assistant is now ready for Microsoft Teams! 🚀
