/**
 * Swagger UI Bundle - Local Stub
 * 
 * This file references the Swagger UI from CDN for production use.
 * For offline usage, download the full bundle from:
 * https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js
 * 
 * In production, serve the actual bundle file or use the CDN version.
 */

// Re-export from CDN for bundler compatibility
if (typeof module !== 'undefined' && module.exports) {
    module.exports = require('swagger-ui-dist');
}

// For browser usage, include this script tag in your HTML:
// <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>

console.log('Swagger UI Bundle stub loaded. Use CDN or download full bundle for production.');
