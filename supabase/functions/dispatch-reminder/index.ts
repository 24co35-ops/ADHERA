import { serve } from "https://deno.land/std/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"
import { Resend } from "npm:resend"

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
const resend = new Resend(Deno.env.get("RESEND_API_KEY"))

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

serve(async (req) => {
  console.log("Dispatching reminders...")

  // 1. Fetch due doses (Pending and due now)
  const { data: dueDoses, error: doseError } = await supabase
    .from('doses')
    .select(`
      id,
      scheduled_utc,
      status,
      user_id,
      reminders (
        id,
        dose_label,
        medicines (
          name,
          dosage_amount,
          dosage_unit
        )
      ),
      profiles:user_id (
        email,
        full_name
      )
    `)
    .eq('status', 'pending')
    .lte('scheduled_utc', new Date().toISOString())
    .is('last_notified_at', null)

  if (doseError) return new Response(JSON.stringify({ error: doseError.message }), { status: 500 })

  // 2. Fetch pending retries
  const { data: retries, error: retryError } = await supabase
    .from('notification_retries')
    .select(`
      id,
      dose_id,
      retry_count,
      doses (
        id,
        user_id,
        reminders (
          medicines (
            name,
            dosage_amount,
            dosage_unit
          )
        ),
        profiles:user_id (
          email
        )
      )
    `)
    .eq('is_resolved', false)
    .lte('next_attempt_at', new Date().toISOString())

  if (retryError) return new Response(JSON.stringify({ error: retryError.message }), { status: 500 })

  const allToProcess = [
    ...dueDoses.map(d => ({ dose: d, isRetry: false })),
    ...retries.map(r => ({ dose: r.doses, isRetry: true, retryId: r.id, count: r.retry_count }))
  ]

  for (const item of allToProcess) {
    const { dose, isRetry, retryId, count } = item
    const medicine = dose.reminders.medicines
    const user = dose.profiles

    try {
      // Send Email
      await resend.emails.send({
        from: "Adhera <reminders@adhera.app>",
        to: user.email,
        subject: `Reminder: ${medicine.name}`,
        html: `<p>Hi ${user.full_name || 'there'}, it is time to take your <b>${medicine.name}</b> (${medicine.dosage_amount} ${medicine.dosage_unit}).</p>`
      })

      // Update dose as notified
      await supabase.from('doses').update({ last_notified_at: new Date().toISOString() }).eq('id', dose.id)
      
      // 2. Browser Push (Placeholder - ADH-FR-23)
      // if (user.push_subscription) {
      //   await webpush.sendNotification(user.push_subscription, ...)
      // }

      if (isRetry) {
        await supabase.from('notification_retries').update({ is_resolved: true }).eq('id', retryId)
      }

    } catch (err) {
      console.error(`Failed to dispatch for dose ${dose.id}:`, err)
      
      if (!isRetry) {
        // Create first retry
        await supabase.from('notification_retries').insert({
          dose_id: dose.id,
          retry_count: 1,
          next_attempt_at: new Date(Date.now() + 5 * 60000).toISOString(),
          last_error: err.message
        })
      } else if (count < 3) {
        // Increment retry
        await supabase.from('notification_retries').update({
          retry_count: count + 1,
          next_attempt_at: new Date(Date.now() + 5 * 60000).toISOString(),
          last_error: err.message
        }).eq('id', retryId)
      } else {
        // Max retries reached
        await supabase.from('notification_retries').update({
          is_resolved: true,
          last_error: `Max retries reached: ${err.message}`
        }).eq('id', retryId)
      }
    }
  }

  return new Response(JSON.stringify({ processed: allToProcess.length }), { status: 200 })
})
