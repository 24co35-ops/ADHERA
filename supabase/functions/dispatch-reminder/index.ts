import { serve } from "https://deno.land/std/http/server.ts"
import { Resend } from "npm:resend"

const resend = new Resend(Deno.env.get("RESEND_API_KEY"))

serve(async (req) => {
  const payload = await req.json()
  const { reminder_id, user_email, medicine_name, dosage } = payload

  console.log(`Dispatching reminder: ${medicine_name} for ${user_email}`)

  try {
    await resend.emails.send({
      from: "Adhera <reminders@adhera.app>",
      to: user_email,
      subject: `Time to take ${medicine_name}`,
      html: `<h1>Reminder</h1><p>It is time to take ${dosage} of ${medicine_name}.</p>`
    })
    return new Response(JSON.stringify({ status: "sent" }), { status: 200 })
  } catch (err) {
    console.error(err)
    return new Response(JSON.stringify({ status: "failed", error: err.message }), { status: 500 })
  }
})
