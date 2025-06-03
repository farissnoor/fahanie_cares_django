// Service Worker for #FahanieCares PWA

const CACHE_NAME = 'fahaniecares-v1';
const urlsToCache = [
  '/',
  '/static/css/output.css',
  '/static/css/mobile.css',
  '/static/js/main.js',
  '/static/js/mobile.js',
  '/static/images/logo.png',
  '/static/images/favicon-32x32.png',
  '/services/',
  '/referrals/',
  '/mobile/offline/'
];

// Install event - cache resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }

        // Clone the request
        var fetchRequest = event.request.clone();

        return fetch(fetchRequest).then(
          response => {
            // Check if we received a valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone the response
            var responseToCache = response.clone();

            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });

            return response;
          }
        ).catch(() => {
          // Return offline page if fetch fails
          if (event.request.destination === 'document') {
            return caches.match('/mobile/offline/');
          }
        });
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background sync for offline form submissions
self.addEventListener('sync', event => {
  if (event.tag === 'sync-offline-data') {
    event.waitUntil(syncOfflineData());
  }
});

async function syncOfflineData() {
  try {
    // Get all offline forms from IndexedDB
    const db = await openDB();
    const tx = db.transaction('offlineForms', 'readonly');
    const store = tx.objectStore('offlineForms');
    const forms = await store.getAll();

    // Send each form to server
    for (const form of forms) {
      const response = await fetch('/api/mobile/sync/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(form.data)
      });

      if (response.ok) {
        // Remove from IndexedDB after successful sync
        const deleteTx = db.transaction('offlineForms', 'readwrite');
        const deleteStore = deleteTx.objectStore('offlineForms');
        await deleteStore.delete(form.id);
      }
    }
  } catch (error) {
    console.error('Error syncing offline data:', error);
  }
}

// Helper function to open IndexedDB
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('FahanieCares', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = event => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('offlineForms')) {
        db.createObjectStore('offlineForms', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

// Helper function to get cookie value
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Push notification support
self.addEventListener('push', event => {
  const options = {
    body: event.data.text(),
    icon: '/static/images/favicon-192x192.png',
    badge: '/static/images/favicon-72x72.png',
    vibrate: [200, 100, 200],
    tag: 'fahanie-cares',
    renotify: true
  };

  event.waitUntil(
    self.registration.showNotification('#FahanieCares Update', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow('/')
  );
});