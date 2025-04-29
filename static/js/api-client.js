// API Client for LinkedIn Business Intelligence Extractor

// Function to check if running on Amplify deployment
function isAmplifyDeployment() {
    return window.location.hostname.includes('amplifyapp.com');
}

// Get the base API URL based on environment
function getApiBaseUrl() {
    if (isAmplifyDeployment()) {
        // For Amplify deployment, use the relative path
        return '';
    } else {
        // For local development, use localhost
        return window.location.origin;
    }
}

// Function to scrape a LinkedIn URL
async function scrapeLinkedInUrl(url, useAuth = false) {
    try {
        const apiUrl = `${getApiBaseUrl()}/api_scrape`;
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, use_auth: useAuth }),
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error scraping LinkedIn URL:', error);
        throw error;
    }
}

// Function to find a LinkedIn URL from a company website
async function findLinkedInUrl(url) {
    try {
        const apiUrl = `${getApiBaseUrl()}/api_find_linkedin`;
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url }),
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error finding LinkedIn URL:', error);
        throw error;
    }
}

// Function to process batch URLs
async function processBatchUrls(urls, format = 'json') {
    try {
        const apiUrl = `${getApiBaseUrl()}/api_batch_process`;
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ urls, format }),
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error processing batch URLs:', error);
        throw error;
    }
}

// Export the API functions
window.ApiClient = {
    scrapeLinkedInUrl,
    findLinkedInUrl,
    processBatchUrls,
    isAmplifyDeployment
};