// Contact Form Handling
document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.getElementById('contactForm');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(contactForm);
            const formObject = {};
            
            for (let [key, value] of formData.entries()) {
                formObject[key] = value;
            }
            
            // Validate required fields
            const requiredFields = ['name', 'email', 'case-type', 'message'];
            let isValid = true;
            
            requiredFields.forEach(field => {
                const input = document.getElementById(field);
                if (!formObject[field] || formObject[field].trim() === '') {
                    input.style.borderColor = 'var(--accent-color)';
                    isValid = false;
                } else {
                    input.style.borderColor = 'var(--success)';
                }
            });
            
            // Email validation
            const emailInput = document.getElementById('email');
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(formObject.email)) {
                emailInput.style.borderColor = 'var(--accent-color)';
                isValid = false;
            }
            
            if (!isValid) {
                showMessage('Please fill in all required fields correctly.', 'error');
                return;
            }
            
            // Show loading state
            const submitButton = contactForm.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            submitButton.textContent = 'Sending...';
            submitButton.disabled = true;
            
            // Submit form via fetch API to Formspree
            fetch('https://formspree.io/f/xpwzgvke', {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json'
                }
            })
            .then(response => {
                // Reset button
                submitButton.textContent = originalText;
                submitButton.disabled = false;
                
                if (response.ok) {
                    // Reset form
                    contactForm.reset();
                    
                    // Show success message
                    showMessage('Thank you for your consultation request. We will respond within 24 hours.', 'success');
                    
                    // Reset field borders
                    requiredFields.forEach(field => {
                        const input = document.getElementById(field);
                        input.style.borderColor = '';
                    });
                    emailInput.style.borderColor = '';
                } else {
                    response.json().then(data => {
                        if (data.errors) {
                            showMessage('Please check your form entries and try again.', 'error');
                        } else {
                            showMessage('There was an error sending your message. Please try again.', 'error');
                        }
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Reset button
                submitButton.textContent = originalText;
                submitButton.disabled = false;
                
                // Show error message
                showMessage('There was an error sending your message. Please try again or contact us directly.', 'error');
            });
        });
    }
    
    // Form field validation on blur
    const formInputs = document.querySelectorAll('#contactForm input, #contactForm select, #contactForm textarea');
    formInputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            // Clear error styling on input
            if (this.style.borderColor === 'var(--accent-color)') {
                this.style.borderColor = '';
            }
        });
    });
});

function validateField(field) {
    const value = field.value.trim();
    const fieldName = field.name;
    
    // Required field validation
    const requiredFields = ['name', 'email', 'case-type', 'message'];
    if (requiredFields.includes(fieldName) && value === '') {
        field.style.borderColor = 'var(--accent-color)';
        return false;
    }
    
    // Email validation
    if (fieldName === 'email') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            field.style.borderColor = 'var(--accent-color)';
            return false;
        }
    }
    
    // Phone validation (if provided)
    if (fieldName === 'phone' && value !== '') {
        const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
        const cleanPhone = value.replace(/[\s\-\(\)\.]/g, '');
        if (!phoneRegex.test(cleanPhone)) {
            field.style.borderColor = 'var(--accent-color)';
            return false;
        }
    }
    
    // Success styling
    if (value !== '') {
        field.style.borderColor = 'var(--success)';
    } else {
        field.style.borderColor = '';
    }
    
    return true;
}

function showMessage(message, type) {
    // Remove existing message
    const existingMessage = document.querySelector('.form-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `form-message ${type}`;
    messageDiv.textContent = message;
    
    // Style the message
    messageDiv.style.cssText = `
        padding: 1rem 1.5rem;
        border-radius: 6px;
        margin-bottom: 1.5rem;
        font-weight: 500;
        text-align: center;
        ${type === 'success' 
            ? 'background-color: #d1fae5; color: #065f46; border: 1px solid #a7f3d0;' 
            : 'background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5;'
        }
        animation: slideIn 0.3s ease-out;
    `;
    
    // Insert message
    const form = document.getElementById('contactForm');
    form.insertBefore(messageDiv, form.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.style.opacity = '0';
            messageDiv.style.transform = 'translateY(-10px)';
            setTimeout(() => messageDiv.remove(), 300);
        }
    }, 5000);
}

// Add CSS animation for message
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .form-message {
        transition: opacity 0.3s ease, transform 0.3s ease;
    }
`;
document.head.appendChild(style);