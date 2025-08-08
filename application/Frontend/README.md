# Agora Marketplace - Svelte Frontend

This directory contains the Svelte implementation of the Agora Marketplace frontend for Team #2.

## Project Structure

```
Frontend/
├── dist/              # Production build folder
├── src/
│   ├── components/    # Reusable UI components
│   │   ├── AboutPage.svelte      # About page component
│   │   ├── DisclaimerBanner.svelte
│   │   ├── Header.svelte
│   │   ├── Home.svelte           # Home page with search
│   │   ├── ListingDetail.svelte  # Listing detail component
│   │   ├── Navigation.svelte     # Navigation menu
│   │   ├── Results.svelte        # Search results grid
│   │   └── SearchForm.svelte     # Search form component
│   ├── stores/        # State management
│   │   ├── categoryStore.js
│   │   ├── listingStore.js
│   │   └── searchStore.js
│   ├── App.svelte     # Main application component with routing
│   └── main.js        # Entry point
├── index.html         # HTML template
├── package.json       # Dependencies
├── svelte.config.js   # Svelte configuration
└── vite.config.mjs    # Vite build configuration
```

## Key Features

- **Modern Component Architecture**: Built with Svelte for efficient, reactive UI
- **Client-Side Routing**: Uses svelte-spa-router for navigation without page reloads
- **Cross-Server Compatibility**: Solves the display issues between different servers
- **Responsive Design**: Works well on all device sizes

## Cross-Server Solution

The implementation addresses the cross-server display issues by:

1. **Absolute URL Resolution**:
   ```javascript
   const API_BASE_URL = window.location.origin + '/api';
   ```

2. **Proper Image Path Handling**:
   ```javascript
   // Ensure image path is absolute
   if (imgPath.startsWith('/')) {
     imgPath = window.location.origin + imgPath;
   }
   ```

3. **Consistent API Integration** with endpoints:
   - `/api/search`: Get search results
   - `/api/categories`: Get categories
   - `/api/listings/{id}`: Get listing details

## Running Locally

To run the Svelte frontend with the backend:

```bash
# 1. Setup the backend (in project root)
cp env.rds .env
python3 -m uvicorn application.app:app --host 0.0.0.0 --port 8001

# 2. Start the frontend (in another terminal)
cd application/Frontend
npm run dev
```

Then access the application at http://localhost:5173/ (or the port shown in terminal).

## Deployment Instructions

For deployment to AWS servers:

1. **Build the application**:
   ```bash
   cd application/Frontend
   npm run build
   ```

2. **Copy files to server**:
   ```bash
   # Replace with your server paths
   scp -r dist/* user@18.223.28.173:/path/to/web/root/
   scp -r dist/* user@3.134.112.144:/path/to/web/root/
   ```

3. **Verify** that the application works correctly on both servers

## Troubleshooting

- If images fail to load, check the browser console for network errors
- For database connectivity issues, verify the `.env` file is using the correct database configuration
- If API requests fail, ensure the backend server is running and accessible

---

CSC 648-848 Spring 2025 - Team #2
