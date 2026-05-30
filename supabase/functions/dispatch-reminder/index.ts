import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { Resend } from "npm:resend"
// @ts-ignore
import webpush from "npm:web-push"

const resend = new Resend(Deno.env.get("RESEND_API_KEY"))
const supabase = createClient(
  Deno.env.get("SUPABASE_URL") ?? "",
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
)

serve(async (req) => {
  const payload = await req.json()
  const { reminder_id, user_id, user_email, medicine_name, dosage, dose_label, scheduled_utc, attempt = 1 } = payload

  const results = { email: "pending", push: "pending" }

  const emailBody = `
    <h2>Time to take ${medicine_name}</h2>
    <p>Dosage: ${dosage}</p>
    <p>Time: ${dose_label}</p>
    <a href="https://adhera.app/doses/${reminder_id}/taken">Mark Taken</a>
    <br/>
    <a href="https://adhera.app/doses/${reminder_id}/missed">Mark Missed</a>
  `

  try {
    await resend.emails.send({
      from: "Adhera <reminders@adhera.app>",
      to: user_email,
      subject: `Time to take ${medicine_name}`,
      html: emailBody
    })
    results.email = "sent"
  } catch (err) {
    results.email = `failed: ${err.message}`
    if (attempt < 3) {
      await supabase.table("notification_retries").insert({
        reminder_id,
        user_id,
        payload,
        attempt: attempt + 1,
        next_retry_utc: new Date(Date.now() + 5 * 60000).toISOString()
      })
    }
  }

  // Push notification
  const { data: subData } = await supabase
    .table("push_subscriptions")
    .select("subscription")
    .eq("user_id", user_id)
    .single()

  if (subData?.subscription) {
    try {
      webpush.setVapidDetails(
        'mailto:reminders@adhera.app',
        Deno.env.get("VAPID_PUBLIC_KEY") ?? "",
        Deno.env.get("VAPID_PRIVATE_KEY") ?? ""
      )
      await webpush.sendNotification(
        subData.subscription,
        JSON.stringify({ medicine_name, dosage, reminder_id })
      )
      results.push = "sent"
    } catch {
      results.push = "failed"
    }
  }

  // Log to system_events
  await supabase.table("system_events").insert({
    event_type: "REMINDER_DISPATCH",
    target_id: reminder_id,
    metadata: results
  })

  return new Response(JSON.stringify(results), { headers: { "Content-Type": "application/json" } })
})
