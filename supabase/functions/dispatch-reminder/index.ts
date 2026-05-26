import { serve } from "https://deno.land/std/http/server.ts"
import { Resend } from "npm:resend"
import webpush from "npm:web-push"

const resend = new Resend(Deno.env.get("RESEND_API_KEY"))

// Configure VAPID keys for Web Push
webpush.setVapidDetails(
  'mailto:support@adhera.com',
  Deno.env.get("VAPID_PUBLIC_KEY")!,
  Deno.env.get("VAPID_PRIVATE_KEY")!
)

serve(async (req) => {
  const payload = await req.json()
  const { reminder_id, user_email, medicine_name, dosage, push_subscription } = payload

  console.log(`Dispatching reminder: ${medicine_name} for ${user_email}`)

  try {
    // 1. Send Email
    await resend.emails.send({
      from: "Adhera <reminders@adhera.app>",
      to: user_email,
      subject: `Time to take ${medicine_name}`,
      html: `<h1>Reminder</h1><p>It is time to take ${dosage} of ${medicine_name}.</p>`
    })

    // 2. Send Browser Push Notification
    if (push_subscription) {
      await webpush.sendNotification(
        push_subscription,
        JSON.stringify({ title: 'Adhera Reminder', body: `Time to take ${dosage} of ${medicine_name}.` })
      )
    }

    return new Response(JSON.stringify({ status: "sent" }), { status: 200 })
  } catch (err) {
    console.error(err)
    return new Response(JSON.stringify({ status: "failed", error: err.message }), { status: 500 })
  }
})
