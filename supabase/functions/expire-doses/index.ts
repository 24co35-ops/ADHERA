import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const supabase = createClient(
  Deno.env.get("SUPABASE_URL") ?? "",
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
)

serve(async (_req) => {
  try {
    // Select doses that are pending or snoozed and older than 2 hours
    const { data: expiredDoses, error: fetchError } = await supabase
      .from('operational_state')
      .select('reminder_id, user_id, scheduled_utc')
      .in('status', ['pending', 'snoozed'])
      .lt('scheduled_utc', new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString())

    if (fetchError) throw fetchError
    if (!expiredDoses || expiredDoses.length === 0) {
      return new Response(JSON.stringify({ processed: 0 }), { headers: { "Content-Type": "application/json" } })
    }

    const missedInserts = expiredDoses.map(dose => ({
      reminder_id: dose.reminder_id,
      user_id: dose.user_id,
      scheduled_utc: dose.scheduled_utc,
      status: 'missed',
      outcome_utc: new Date().toISOString()
    }))

    // Bulk insert into adherence. No UPDATE/DELETE per append-only rules.
    const { error: insertError } = await supabase
      .from('adherence')
      .insert(missedInserts)

    if (insertError) throw insertError

    // Log to system_events
    await supabase.table("system_events").insert({
      event_type: "DOSES_EXPIRED",
      metadata: { count: expiredDoses.length }
    })

    return new Response(JSON.stringify({ processed: expiredDoses.length }), { headers: { "Content-Type": "application/json" } })

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500, headers: { "Content-Type": "application/json" } })
  }
})
