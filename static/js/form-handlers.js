// Form handlers for LinkedIn Business Intelligence Extractor

document.addEventListener('DOMContentLoaded', function() {
    // Handle extract LinkedIn data form
    const extractForm = document.getElementById('extract-form');
    if (extractForm) {
        extractForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading indicator
            const loadingElement = document.getElementById('loading');
            if (loadingElement) {
                loadingElement.style.display = 'block';
            }
            
            // Get form data
            const formData = new FormData(extractForm);
            const url = formData.get('url');
            const mode = formData.get('mode') || 'direct';
            const useAuth = formData.get('use_auth') === 'on';
            
            // Submit the form
            extractForm.submit();
        });
    }
    
    // Handle batch process form
    const batchForm = document.getElementById('batch-form');
    if (batchForm) {
        batchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading indicator
            const loadingElement = document.getElementById('loading');
            if (loadingElement) {
                loadingElement.style.display = 'block';
            }
            
            // Get form data
            const formData = new FormData(batchForm);
            
            // Submit the form
            batchForm.submit();
        });
    }
    
    // Initialize any other UI components
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0) {
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
});