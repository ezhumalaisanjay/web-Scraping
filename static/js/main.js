// Initialize Feather icons
document.addEventListener('DOMContentLoaded', function() {
    feather.replace();
    
    // Handle mode selection for LinkedIn finder
    const directModeRadio = document.getElementById('mode-direct');
    const linkedinModeRadio = document.getElementById('mode-find-linkedin');
    const directModeDesc = document.getElementById('direct-mode-desc');
    const linkedinModeDesc = document.getElementById('linkedin-mode-desc');
    const urlInput = document.querySelector('input[name="url"]');
    
    if (directModeRadio && linkedinModeRadio) {
        // Function to update placeholder text based on selected mode
        function updatePlaceholder() {
            if (directModeRadio.checked) {
                urlInput.placeholder = "https://example.com or linkedin.com/company/microsoft";
                directModeDesc.style.display = 'block';
                linkedinModeDesc.style.display = 'none';
            } else {
                urlInput.placeholder = "Enter company website URL (e.g., https://microsoft.com)";
                directModeDesc.style.display = 'none';
                linkedinModeDesc.style.display = 'block';
            }
        }
        
        // Set initial state
        updatePlaceholder();
        
        // Add event listeners for radio buttons
        directModeRadio.addEventListener('change', updatePlaceholder);
        linkedinModeRadio.addEventListener('change', updatePlaceholder);
    }
    
    // Copy JSON data to clipboard
    const copyJsonBtn = document.getElementById('copyJson');
    if (copyJsonBtn) {
        copyJsonBtn.addEventListener('click', function() {
            const jsonData = document.getElementById('jsonData');
            
            // Create a temporary textarea to copy from
            const textarea = document.createElement('textarea');
            textarea.value = jsonData.textContent;
            document.body.appendChild(textarea);
            textarea.select();
            
            try {
                // Execute copy command
                document.execCommand('copy');
                
                // Show feedback
                const originalText = copyJsonBtn.innerHTML;
                copyJsonBtn.innerHTML = '<i data-feather="check"></i> Copied!';
                feather.replace();
                
                // Reset button text after 2 seconds
                setTimeout(function() {
                    copyJsonBtn.innerHTML = originalText;
                    feather.replace();
                }, 2000);
            } catch (err) {
                console.error('Failed to copy text: ', err);
            } finally {
                document.body.removeChild(textarea);
            }
        });
    }
    
    // Form validation
    const scrapeForm = document.querySelector('form[action="/scrape"]');
    if (scrapeForm) {
        scrapeForm.addEventListener('submit', function(event) {
            const urlInput = scrapeForm.querySelector('input[name="url"]');
            let url = urlInput.value.trim();
            
            // Basic URL validation
            if (!url) {
                event.preventDefault();
                showValidationError(urlInput, 'Please enter a URL');
                return;
            }
            
            // Add http:// prefix if not present
            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                urlInput.value = 'https://' + url;
            }
        });
    }
    
    function showValidationError(inputElement, message) {
        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger mt-2';
        errorDiv.innerHTML = `<i data-feather="alert-circle"></i> ${message}`;
        
        // Insert after input
        inputElement.parentNode.insertBefore(errorDiv, inputElement.nextSibling);
        
        // Initialize feather icon in the error message
        feather.replace();
        
        // Remove error after 3 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 3000);
        
        // Focus on the input
        inputElement.focus();
    }
});
