# Security Guidelines

## 🔒 API Keys and Secrets

### ✅ DO:
- Store all API keys and secrets in `.env` file only
- Use `.env.example` as a template with placeholder values
- Keep `.env` file in `.gitignore` (already configured)
- Use environment variables in production deployments
- Rotate API keys regularly

### ❌ DON'T:
- Never commit `.env` file to version control
- Never hardcode API keys in source code
- Never share API keys in documentation or README files
- Never expose secrets in log files or error messages

## 🛡️ Current Security Measures

### Environment Variables
All sensitive information is stored in `.env`:
- `GROQ_API_KEY` - Groq API authentication
- `OPENROUTER_API_KEY` - OpenRouter API authentication  
- `AZURE_CLIENT_SECRET` - Azure AD client secret
- `AZURE_CLIENT_ID` - Azure AD client ID (less sensitive but still protected)
- `AZURE_TENANT_ID` - Azure AD tenant ID

### File Security
- `.gitignore` configured to exclude all sensitive files
- Virtual environments excluded from version control
- Test files and temporary documentation excluded
- Session files and cache directories excluded

### Teams SSO Security
- JWT token validation with Microsoft's public keys
- Secure token exchange using On-Behalf-Of flow
- Content Security Policy (CSP) headers for iframe protection
- Proper session management with secure cookies

## 🔍 Security Checklist

Before deploying or sharing code:

- [ ] All API keys are in `.env` file only
- [ ] `.env` file is not committed to git
- [ ] No hardcoded secrets in source code
- [ ] `.env.example` contains only placeholder values
- [ ] Production environment variables are set securely
- [ ] Azure AD app registration is properly configured
- [ ] Teams manifest contains no sensitive information
- [ ] CSP headers are configured for Teams embedding
- [ ] Session security is properly implemented

## 🚨 If Secrets Are Exposed

If you accidentally commit secrets:

1. **Immediately rotate all exposed API keys**
2. **Remove secrets from git history** (use `git filter-branch` or BFG Repo-Cleaner)
3. **Update all deployment environments** with new keys
4. **Review access logs** for any unauthorized usage
5. **Update `.gitignore`** to prevent future exposure

## 📞 Security Contacts

For security issues or questions:
- Review Azure AD security best practices
- Check API provider security documentation
- Follow OWASP security guidelines
- Implement regular security audits

## 🔄 Regular Security Tasks

- [ ] Rotate API keys quarterly
- [ ] Review and update dependencies
- [ ] Audit access logs
- [ ] Update security headers
- [ ] Review Teams app permissions
- [ ] Check for exposed secrets in git history
