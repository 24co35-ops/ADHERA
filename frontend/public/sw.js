const CACHE_NAME = 'adhera-v6';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/assets/favicons/favicon.ico',
  '/assets/favicons/favicon-192x192.png',
  '/assets/favicons/favicon-512x512.png',
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
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle GET requests
  if (request.method !== 'GET') return;

  // Never cache API requests
  if (url.pathname.startsWith('/v1/')) return;

  // For HTML page navigation, use Network First, fallback to cached index.html if offline
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => caches.match('/index.html'))
    );
    return;
  }

  // Only cache static assets (js, css, images, fonts)
  const isStatic =
    url.pathname.match(/\.(js|css|png|jpg|jpeg|svg|ico|woff2?|webmanifest)$/) ||
    url.hostname.includes('fonts.googleapis.com') ||
    url.hostname.includes('fonts.gstatic.com');

  if (!isStatic) return;

  // Network-first for fresh bundles, fallback to cache
  event.respondWith(
    fetch(request)
      .then((res) => {
        if (res.ok) {
          const clone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return res;
      })
      .catch(() => caches.match(request))
  );
});

// Push notification handling
self.addEventListener('push', function (event) {
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { body: event.data.text() };
    }
  }

  const title = data.title || 'Adhera Reminder';
  const reminderTag = data.tag || (data.reminder_id ? `adhera-reminder-${data.reminder_id}` : `adhera-reminder-${Date.now()}`);

  const options = {
    body:
      data.body ||
      (data.medicine_name
        ? `Time to take ${data.medicine_name}${data.dosage ? ' (' + data.dosage + ')' : ''}`
        : 'Time to take your scheduled medication.'),
    icon: '/assets/favicons/favicon-180x180.png',
    badge: '/assets/favicons/favicon-32x32.png',
    tag: reminderTag,
    renotify: true,
    data: {
      reminder_id: data.reminder_id,
      url: data.url || '/dashboard',
    },
    actions: data.actions || [
      { action: 'taken', title: '✅ Taken' },
      { action: 'missed', title: '❌ Missed' },
      { action: 'snooze', title: '⏰ Snooze' },
    ],
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();

  const reminderId = event.notification.data?.reminder_id;
  let targetUrl = event.notification.data?.url || '/dashboard';

  if (event.action === 'taken' && reminderId) {
    targetUrl = `/dashboard?action=taken&reminder_id=${encodeURIComponent(reminderId)}`;
  } else if (event.action === 'missed' && reminderId) {
    targetUrl = `/dashboard?action=missed&reminder_id=${encodeURIComponent(reminderId)}`;
  } else if (event.action === 'snooze' && reminderId) {
    targetUrl = `/dashboard?action=snooze&reminder_id=${encodeURIComponent(reminderId)}`;
  }

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
      for (let i = 0; i < clientList.length; i++) {
        let client = clientList[i];
        if (client.url && 'focus' in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
