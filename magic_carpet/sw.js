// sw.js

const CACHE_NAME = "magic-carpet-cache-v1";
const urlsToCache = [
    "/", // assuming index.html is served at the root
    "/index.html",
    "/main.js",
    "/config.js",
    "/db.js",
    "/utils.js",
    "/MarkdownEditor.js",
    "/DexieModal.js",
    "/ExcalidrawModal.js",
    "/QuickAddModal.js",
    "/HelpModal.js",
    "/GanttChart.js",
    "/SummaryView.js",
    "/TaskCard.js",
    "/TaskBoard.js",
    "/ErrorBoundary.js",
    "/App.js",
    "/exportCSVHelper.js",
    "/customHooks.js",
    // Add any CSS files, images, or other assets your app uses
];

// Install event: Open the cache and cache all required files.
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log("Opened cache");
            return cache.addAll(urlsToCache);
        })
    );
});

// Fetch event: Try to serve from cache, falling back to network.
self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            // Return cached file if found, otherwise fetch from network.
            return response || fetch(event.request);
        })
    );
});

// Activate event: Cleanup old caches.
self.addEventListener("activate", (event) => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then((cacheNames) =>
            Promise.all(
                cacheNames.map((cacheName) => {
                    if (!cacheWhitelist.includes(cacheName)) {
                        return caches.delete(cacheName);
                    }
                })
            )
        )
    );
});