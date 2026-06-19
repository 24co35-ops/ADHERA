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
    body: data.body || (data.medicine_name ? `Time to take ${data.medicine_name} (${data.dosage || ''})` : 'Time to take your scheduled medicine.'),
    icon: '/logo.html', // placeholder for icon
    badge: '/logo.html',
    tag: 'adhera-reminder',
    data: {
      reminder_id: data.reminder_id
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
      return clients.openWindow('/dashboard.html');
    })
  );
});
