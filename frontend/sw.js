const CACHE_NAME = 'adhera-v1';
const STATIC_ASSETS = [
  '/index.html',
  '/dashboard.html',
  '/medicines.html',
  '/feedback.html',
  '/profile.html',
  '/config.js',
  '/js/alpine.min.js',
  '/js/alpine-collapse.min.js',
  '/js/nav.js',
  '/assets/favicons/logo.svg',
  '/assets/favicons/favicon.ico',
  '/site.webmanifest',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle GET requests for same-origin or CDN assets
  if (request.method !== 'GET') return;

  // Skip API calls — never cache /v1/* responses
  if (url.pathname.startsWith('/v1/')) return;

  // Network-First strategy: try network, fall back to cache
  event.respondWith(
    fetch(request)
      .then((res) => {
        // Only cache successful same-origin responses
        if (res.ok && (url.origin === self.location.origin || url.hostname.includes('fonts.googleapis.com'))) {
          const clone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return res;
      })
      .catch(() => caches.match(request))
  );
});

// Push notification handling
self.addEventListener('push', function(event) {
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { body: event.data.text() };
    }
  }

  const title = data.title || 'Adhera Reminder';
  const options = {
    body: data.body || (data.medicine_name ? `Time to take ${data.medicine_name}${data.dosage ? ' (' + data.dosage + ')' : ''}` : 'Time to take your scheduled medicine.'),
    icon: '/adhera_logo/screen.png',
    badge: '/adhera_logo/screen.png',
    tag: 'adhera-reminder',
    data: {
      reminder_id: data.reminder_id,
      url: data.url || '/dashboard.html'
    }
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
      if (clientList.length > 0) {
        let client = clientList[0];
        for (let i = 0; i < clientList.length; i++) {
          if (clientList[i].focused) {
            client = clientList[i];
            break;
          }
        }
        return client.focus();
      }
      return clients.openWindow(event.notification.data?.url || '/dashboard.html');
    })
  );
});
