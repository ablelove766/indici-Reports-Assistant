# Microsoft Teams Deployment Checklist

## 🎯 Pre-Deployment Verification

Your Indici Reports Assistant is configured for: `https://indici-reports-assistant.onrender.com/`

### ✅ Configuration Status

| Component | Status | Details |
|-----------|--------|---------|
| **Manifest URLs** | ✅ **Updated** | All URLs point to Render domain |
| **CSP Headers** | ✅ **Configured** | Teams iframe embedding allowed |
| **CORS Settings** | ✅ **Updated** | Teams domains whitelisted |
| **Teams SDK** | ✅ **Integrated** | v2.0 with proper initialization |
| **Responsive Design** | ✅ **Optimized** | Teams-specific styling |
| **Required Routes** | ✅ **Created** | Config, privacy, terms, remove |

## 🚀 Deployment Steps

### Step 1: Create App Icons

Run the icon creation script:
```bash
cd teams/
python create_icons.py
```

Or create manually:
- `color.png` (192x192px) - Full color brand icon
- `outline.png` (32x32px) - Simple outline version

### Step 2: Test Your Deployment

Before creating the Teams package, verify these URLs work:

#### Core Application
- ✅ Main app: https://indici-reports-assistant.onrender.com/
- ✅ Teams interface: https://indici-reports-assistant.onrender.com/teams

#### Teams-Specific Pages
- ✅ Configuration: https://indici-reports-assistant.onrender.com/teams/config
- ✅ Privacy policy: https://indici-reports-assistant.onrender.com/teams/privacy
- ✅ Terms of use: https://indici-reports-assistant.onrender.com/teams/terms
- ✅ Remove page: https://indici-reports-assistant.onrender.com/teams/remove

#### API Endpoints
- ✅ Health check: https://indici-reports-assistant.onrender.com/api/health
- ✅ Sample queries: https://indici-reports-assistant.onrender.com/api/samples

### Step 3: Create Teams App Package

1. **Verify files in `teams/` directory:**
   ```
   teams/
   ├── manifest.json     ✅ Updated for Render
   ├── color.png         📝 Create this (192x192px)
   ├── outline.png       📝 Create this (32x32px)
   └── create_icons.py   ✅ Helper script
   ```

2. **Create ZIP package:**
   - Select: `manifest.json`, `color.png`, `outline.png`
   - Create ZIP file: `indici-reports-assistant.zip`
   - **Important:** Don't include the folder, just the files

### Step 4: Upload to Microsoft Teams

#### For Personal Testing:
1. Open Microsoft Teams
2. Go to **Apps** → **Manage your apps**
3. Click **"Upload an app"** → **"Upload a custom app"**
4. Select your `indici-reports-assistant.zip` file
5. Click **"Add"** to install

#### For Organization Deployment:
1. Contact your Teams administrator
2. Provide the ZIP file and this documentation
3. Request organization-wide deployment
4. Follow your organization's app approval process

## 🔧 Environment Configuration

### Required Environment Variables

Ensure these are set in your Render deployment:

```bash
# API Keys (from your .env)
GROQ_API_KEY=your_groq_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# Server Configuration
WEB_INTERFACE_HOST=0.0.0.0
WEB_INTERFACE_PORT=10000

# Optional Teams Settings
TEAMS_APP_ID=indici-mcp-chatbot-app
```

### Render-Specific Settings

In your Render dashboard:
1. **Environment**: Set to `Production`
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `python web/app.py`
4. **Port**: Should auto-detect from `WEB_INTERFACE_PORT`

## 🧪 Testing Scenarios

### 1. Standalone Testing
- ✅ Test outside Teams: https://indici-reports-assistant.onrender.com/
- ✅ Verify all functionality works
- ✅ Check API connections

### 2. Teams Integration Testing
- ✅ Test Teams interface: https://indici-reports-assistant.onrender.com/teams
- ✅ Verify Teams SDK loads
- ✅ Check theme adaptation
- ✅ Test configuration page

### 3. Teams App Testing
- ✅ Upload app to Teams
- ✅ Add as personal app
- ✅ Test in channel/chat
- ✅ Verify all features work

## 🛡️ Security Verification

### CSP Headers Check
Your app includes these security headers:
- ✅ Content-Security-Policy (Teams iframe embedding)
- ✅ X-Frame-Options: ALLOWALL
- ✅ X-Content-Type-Options: nosniff
- ✅ Referrer-Policy: strict-origin-when-cross-origin

### CORS Configuration
- ✅ Teams domains whitelisted
- ✅ Render domain included
- ✅ WebSocket connections allowed

## 📱 Mobile Compatibility

Your Teams app supports:
- ✅ **Teams Desktop** - Full interface
- ✅ **Teams Web** - Full interface  
- ✅ **Teams Mobile** - Responsive layout
- ✅ **Teams Mobile App** - Optimized experience

## 🔍 Troubleshooting

### Common Issues & Solutions

1. **App won't load in Teams**
   - ✅ Check HTTPS is enabled (Render provides this)
   - ✅ Verify all URLs in manifest are accessible
   - ✅ Check browser console for CSP errors

2. **Configuration page not working**
   - ✅ Ensure Teams SDK loads (check network tab)
   - ✅ Verify JavaScript console for errors
   - ✅ Test configuration URL directly

3. **WebSocket connection issues**
   - ✅ Render supports WebSockets
   - ✅ Check CORS settings include wss://
   - ✅ Verify SocketIO configuration

### Debug URLs

Add `?debug=true` to any URL for debug mode:
- https://indici-reports-assistant.onrender.com/teams?debug=true
- https://indici-reports-assistant.onrender.com/teams/config?debug=true

## 📊 Monitoring

### Health Checks
- ✅ App health: https://indici-reports-assistant.onrender.com/api/health
- ✅ Render dashboard monitoring
- ✅ Teams app usage analytics

### Performance
- ✅ Render provides performance metrics
- ✅ Teams SDK includes usage tracking
- ✅ WebSocket connection monitoring

## 🎉 Go Live Checklist

Before final deployment:

- [ ] **Icons created** (color.png, outline.png)
- [ ] **All URLs tested** and working
- [ ] **ZIP package created** with correct files
- [ ] **Teams app uploaded** and tested
- [ ] **Functionality verified** in Teams
- [ ] **Mobile experience tested**
- [ ] **Security headers confirmed**
- [ ] **Performance acceptable**
- [ ] **Documentation updated**
- [ ] **Team trained** on usage

## 📞 Support

### For Technical Issues:
1. Check Render deployment logs
2. Test URLs individually
3. Verify environment variables
4. Check browser console errors

### For Teams Deployment:
1. Contact your Teams administrator
2. Provide this checklist and ZIP file
3. Reference Microsoft Teams app policies
4. Follow organizational approval process

---

**Your Indici Reports Assistant is ready for Microsoft Teams! 🚀**

Next step: Create the icons and ZIP package for deployment.
