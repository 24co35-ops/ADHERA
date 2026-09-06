// @ts-nocheck
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { Resend } from "npm:resend"
import webpush from "npm:web-push"

const resend = new Resend(Deno.env.get("RESEND_API_KEY"))
const supabase = createClient(
  Deno.env.get("SUPABASE_URL") ?? "",
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
)

serve(async (req) => {
  try {
    const payload = await req.json()
    const {
      reminder_id,
      user_id,
      user_email,
      medicine_name,
      dosage,
      dose_label,
      scheduled_utc,
      attempt = 1,
      is_advance = false
    } = payload

    // 1. Idempotency Check (prevent duplicate sends within 10 minutes unless explicit retry)
    if (attempt === 1 && reminder_id) {
      const tenMinutesAgo = new Date(Date.now() - 10 * 60000).toISOString()
      const { data: existingEvents } = await supabase
        .table("system_events")
        .select("id")
        .eq("event_type", "REMINDER_DISPATCH")
        .eq("target_id", reminder_id)
        .gte("created_at", tenMinutesAgo)
        .limit(1)

      if (existingEvents && existingEvents.length > 0) {
        return new Response(
          JSON.stringify({ status: "already_dispatched", message: "Reminder recently sent for this dose" }),
          { headers: { "Content-Type": "application/json" } }
        )
      }
    }

    const results: { email: string; push: string } = { email: "skipped", push: "skipped" }

    // 2. Email Notification (via Resend)
    if (user_email) {
      const frontendUrl = Deno.env.get("FRONTEND_URL") || "https://adhera-seven.vercel.app"
      const takenUrl = `${frontendUrl}/dashboard?action=taken&reminder_id=${reminder_id}`
      const missedUrl = `${frontendUrl}/dashboard?action=missed&reminder_id=${reminder_id}`

      const emailHtml = `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background-color:#111318;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#e2e8f0;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="100%" style="max-width:540px;background-color:#181b22;border-radius:16px;border:1px solid rgba(255,255,255,0.08);padding:32px;">
          <tr>
            <td style="text-align:center;padding-bottom:20px;border-bottom:1px solid rgba(255,255,255,0.06);">
              <h1 style="margin:0;color:#00dbe7;font-size:20px;letter-spacing:-0.5px;">ADHERA MEDICATION REMINDER</h1>
            </td>
          </tr>
          <tr>
            <td style="padding-top:24px;">
              <h2 style="margin:0 0 12px;color:#ffffff;font-size:18px;">${is_advance ? `Reminder: ${medicine_name} in 10 minutes` : `Time to take ${medicine_name}`}</h2>
              <p style="margin:0 0 8px;font-size:14px;color:#94a3b8;"><strong>Dosage:</strong> ${dosage || 'As prescribed'}</p>
              <p style="margin:0 0 24px;font-size:14px;color:#94a3b8;"><strong>Scheduled Dose:</strong> ${dose_label || 'Scheduled'}</p>
              
              <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td align="center" style="padding-right:8px;">
                    <a href="${takenUrl}" style="display:block;background-color:#00dbe7;color:#111318;font-weight:700;font-size:13px;text-decoration:none;padding:12px 20px;border-radius:10px;text-align:center;">
                      ✅ Mark Taken
                    </a>
                  </td>
                  <td align="center" style="padding-left:8px;">
                    <a href="${missedUrl}" style="display:block;background-color:#2a2f3b;color:#f87171;font-weight:600;font-size:13px;text-decoration:none;padding:12px 20px;border-radius:10px;text-align:center;border:1px solid rgba(248,113,113,0.3);">
                      ❌ Mark Missed
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`

      try {
        await resend.emails.send({
          from: "Adhera <reminders@adhera.app>",
          to: user_email,
          subject: is_advance ? `Reminder: ${medicine_name} in 10 minutes` : `Time to take ${medicine_name}`,
          html: emailHtml
        })
        results.email = "sent"
      } catch (err: any) {
        results.email = `failed: ${err?.message || err}`
        if (attempt < 3) {
          await supabase.table("notification_retries").insert({
            reminder_id,
            user_id,
            payload,
            attempt: attempt + 1,
            status: "pending",
            error_message: String(err?.message || err),
            next_retry_utc: new Date(Date.now() + 5 * 60000).toISOString()
          })
        }
      }
    }

    // 3. Push Notification
    if (user_id) {
      const { data: subData } = await supabase
        .table("push_subscriptions")
        .select("endpoint, auth, p256dh, subscription")
        .eq("user_id", user_id)
        .single()

      let targetSubscription = subData?.subscription
      if (!targetSubscription && subData?.endpoint && subData?.auth && subData?.p256dh) {
        targetSubscription = {
          endpoint: subData.endpoint,
          keys: {
            auth: subData.auth,
            p256dh: subData.p256dh
          }
        }
      }

      if (targetSubscription && targetSubscription.endpoint) {
        try {
          webpush.setVapidDetails(
            'mailto:reminders@adhera.app',
            Deno.env.get("VAPID_PUBLIC_KEY") ?? "",
            Deno.env.get("VAPID_PRIVATE_KEY") ?? ""
          )

          const pushPayload = JSON.stringify({
            title: is_advance ? `Reminder: ${medicine_name} in 10 minutes` : 'Time for your medication',
            body: `${medicine_name}${dosage ? ' — ' + dosage : ''}${dose_label ? ' (' + dose_label + ')' : ''}`,
            medicine_name,
            dosage,
            reminder_id,
            tag: `adhera-reminder-${reminder_id || Date.now()}`,
            url: '/dashboard',
            actions: [
              { action: 'taken', title: '✅ Taken' },
              { action: 'missed', title: '❌ Missed' },
              { action: 'snooze', title: '⏰ Snooze' }
            ]
          })

          await webpush.sendNotification(targetSubscription, pushPayload)
          results.push = "sent"
        } catch (pushErr: any) {
          const errStatus = pushErr?.statusCode || pushErr?.status
          const errMsg = String(pushErr?.message || pushErr?.body || pushErr)

          // Expired or invalid subscription: clean up cleanly so not retried forever
          if (
            errStatus === 404 ||
            errStatus === 410 ||
            errMsg.includes("Gone") ||
            errMsg.includes("NotRegistered") ||
            errMsg.includes("unsubscribed") ||
            errMsg.includes("expired")
          ) {
            await supabase.table("push_subscriptions").delete().eq("user_id", user_id)
            results.push = "cleaned_expired_subscription"
          } else {
            results.push = `failed: ${errMsg}`
            if (attempt < 3 && results.email !== "sent") {
              await supabase.table("notification_retries").insert({
                reminder_id,
                user_id,
                payload,
                attempt: attempt + 1,
                status: "pending",
                error_message: errMsg,
                next_retry_utc: new Date(Date.now() + 5 * 60000).toISOString()
              })
            }
          }
        }
      }
    }

    // 4. Log to system_events
    await supabase.table("system_events").insert({
      event_type: "REMINDER_DISPATCH",
      target_id: reminder_id,
      metadata: { ...results, attempt, is_advance }
    })

    return new Response(JSON.stringify(results), {
      headers: { "Content-Type": "application/json" }
    })
  } catch (globalErr: any) {
    return new Response(
      JSON.stringify({ error: String(globalErr?.message || globalErr) }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    )
  }
})
