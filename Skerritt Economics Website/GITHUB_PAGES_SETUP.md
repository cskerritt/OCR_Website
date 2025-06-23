# GitHub Pages Setup Instructions

## 📧 Contact Form Configuration

Your contact form is now configured to work with GitHub Pages using **Formspree**. Here's what you need to do:

### 1. Create Formspree Account
1. Go to [formspree.io](https://formspree.io)
2. Sign up for a free account using **christophertskerritt@gmail.com**
3. Create a new form and get your unique form ID

### 2. Update Form ID
Currently using placeholder: `xpwzgvke`

**Replace in contact/index.html:**
```html
<!-- Line 109: Change this URL -->
<form action="https://formspree.io/f/YOUR_ACTUAL_FORM_ID" method="POST">
```

**Replace in js/contact.js:**
```javascript
// Line 52: Change this URL
fetch('https://formspree.io/f/YOUR_ACTUAL_FORM_ID', {
```

### 3. Update Domain Reference
**In contact/index.html line 112:**
```html
<input type="hidden" name="_next" value="https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/contact/">
```

## 🚀 GitHub Pages Deployment

### 1. Create Repository
```bash
# Initialize git repository
git init
git add .
git commit -m "Initial website commit"

# Create GitHub repository and push
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### 2. Enable GitHub Pages
1. Go to repository Settings
2. Scroll to "Pages" section
3. Source: Deploy from branch
4. Branch: main
5. Folder: / (root)
6. Save

### 3. Custom Domain (Optional)
If you have a custom domain:
1. Add CNAME file with your domain
2. Configure DNS records
3. Enable "Enforce HTTPS"

## 📁 Files to Remove for GitHub Pages

Since GitHub Pages doesn't support PHP, you can remove these files:
- `contact-handler.php`
- `.htaccess` (GitHub Pages ignores this)

## ✅ What Works on GitHub Pages

✅ **Static HTML/CSS/JS** - All your pages will work perfectly  
✅ **Contact Form** - Via Formspree integration  
✅ **Professional Design** - All styling and animations  
✅ **Mobile Responsive** - Works on all devices  
✅ **SEO Optimized** - Meta tags and structured data  
✅ **Fast Loading** - CDN-delivered content  

## 🔧 After Deployment

1. **Test Contact Form**: Submit a test message to verify emails arrive
2. **Update Google Search Console**: Submit your sitemap
3. **Monitor Analytics**: Add Google Analytics if desired
4. **SSL Certificate**: GitHub Pages provides free HTTPS

## 📞 Contact Form Emails

Emails will be sent to: **christophertskerritt@gmail.com**

Email format includes:
- Contact information
- Case type and details
- Timeline requirements
- Professional formatting

## 💰 Formspree Pricing

- **Free Plan**: 50 submissions/month
- **Basic Plan**: $10/month for 1000 submissions
- Perfect for professional consultation requests

Your website is now ready for GitHub Pages hosting! 🎉