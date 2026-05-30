import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { Resend } from "npm:resend"

const resend = new Resend(Deno.env.get("RESEND_API_KEY"))
const supabase = createClient(
  Deno.env.get("SUPABASE_URL") ?? "",
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
)

serve(async (req) => {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 55000)

  try {
    const { patient_id, provider_email, emergency_contact_email, medicine_name, description, severity } = await req.json()

    const subject = `EMERGENCY ALERT: Severity ${severity} side effect reported`
    const html = `
      <h2>Emergency Alert</h2>
      <p><strong>Patient ID:</strong> ${patient_id}</p>
      <p><strong>Medicine:</strong> ${medicine_name}</p>
      <p><strong>Severity:</strong> ${severity}</p>
      <p><strong>Description:</strong> ${description}</p>
    `

    // Email provider
    if (provider_email) {
      await resend.emails.send({
        from: "Adhera Alerts <alerts@adhera.app>",
        to: provider_email,
        subject,
        html
      })
      await supabase.table("audit_log").insert({
        actor_id: patient_id,
        action_code: "EMERGENCY_ALERT_SENT",
        target_id: null,
        reason: `Sent to provider: ${provider_email}`
      })
    }

    // Email emergency contact
    if (emergency_contact_email) {
      await resend.emails.send({
        from: "Adhera Alerts <alerts@adhera.app>",
        to: emergency_contact_email,
        subject,
        html
      })
      await supabase.table("audit_log").insert({
        actor_id: patient_id,
        action_code: "EMERGENCY_ALERT_SENT",
        target_id: null,
        reason: `Sent to contact: ${emergency_contact_email}`
      })
    }

    clearTimeout(timeoutId)
    return new Response(JSON.stringify({ success: true }), { headers: { "Content-Type": "application/json" } })

  } catch (error) {
    clearTimeout(timeoutId)
    return new Response(JSON.stringify({ error: error.message }), { status: 500, headers: { "Content-Type": "application/json" } })
  }
})
