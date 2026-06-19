/**
 * en.js — English locale strings for Adhera.
 *
 * Key convention: <section>.<identifier>
 *   nav.*         Navigation links
 *   stat.*        Dashboard stat card labels
 *   chart.*       Chart headings / badges
 *   schedule.*    Today's Schedule section
 *   btn.*         Button labels
 *   feedback.*    Recent Feedback section
 *   export.*      Export My Data section
 *   medicines.*   Medicines page headings & labels
 *   form.*        Form field labels
 *   timing.*      Timings sub-section
 *   recurrence.*  Recurrence select options
 *   route.*       Administration route options
 *   empty.*       Empty-state messages
 */
export const en = {
    // ── Navigation ──────────────────────────────────────────────────────────
    'nav.dashboard':        'Dashboard',
    'nav.medicines':        'Medicines',
    'nav.feedback':         'Feedback',
    'nav.profile':          'Profile',
    'nav.logout':           'Logout',

    // ── Stat cards ───────────────────────────────────────────────────────────
    'stat.overall_adherence': 'Overall Adherence',
    'stat.day_streak':        'Day Streak',
    'stat.missed_this_month': 'Missed This Month',
    'stat.due_today':         'Due Today',

    // ── Charts ───────────────────────────────────────────────────────────────
    'chart.weekly_adherence':  'Weekly Adherence',
    'chart.monthly_adherence': 'Monthly Adherence',
    'chart.low_adherence':     'Low Adherence (Below target)',

    // ── Today's Schedule ─────────────────────────────────────────────────────
    'schedule.title':       "Today's Schedule",
    'schedule.all_done':    "No doses pending today. You're all caught up!",

    // ── Dose action buttons ───────────────────────────────────────────────────
    'btn.taken':    'Taken',
    'btn.snooze':   'Snooze',
    'btn.missed':   'Missed',

    // ── Recent Feedback sidebar ───────────────────────────────────────────────
    'feedback.title':     'Recent Feedback',
    'feedback.view_all':  'View all',
    'feedback.empty':     'No recent feedback reported.',
    'feedback.sev':       'Sev',          // prefix: "Sev 2"

    // ── Export My Data ────────────────────────────────────────────────────────
    'export.title':        'Export My Data',
    'export.description':  'Download all your adherence records, medicines, and feedback.',
    'export.json':         'JSON',
    'export.csv':          'CSV',
    'export.generating':   'Generating…',
    'export.download':     'Download ready — click to save',
    'export.link_expires': 'Link expires in 15 minutes.',

    // ── Medicines page ────────────────────────────────────────────────────────
    'medicines.active_title':  'Active Medicines',
    'medicines.add_title':     'Add Medicine',
    'medicines.empty':         'No active medicines.',

    // ── Timing sub-section ────────────────────────────────────────────────────
    'timing.title':            'Timings',
    'timing.add_btn':          '+ Add Timing',
    'timing.empty':            'No timings configured.',
    'timing.advance_notify':   '10-Minute Advance Notification',
    'timing.advance_short':    '10m Advance',
    'timing.label_placeholder':'e.g. Morning',

    // ── Inline edit buttons ───────────────────────────────────────────────────
    'btn.edit':    'Edit',
    'btn.delete':  'Delete',
    'btn.save':    'Save',
    'btn.cancel':  'Cancel',
    'btn.add':     'Add',

    // ── Add Medicine form labels ──────────────────────────────────────────────
    'form.name':             'Name',
    'form.amount':           'Amount',
    'form.unit':             'Unit',
    'form.route':            'Route',
    'form.frequency':        'Frequency',
    'form.start_date':       'Start Date',
    'form.end_date':         'End Date (Optional)',
    'form.timing':           'Timing (Optional)',
    'form.scheduled_time':   'Scheduled Time (Optional)',
    'form.instructions':     'Instructions (Optional)',
    'form.add_submit':       'Add',

    // ── Recurrence options ────────────────────────────────────────────────────
    'recurrence.daily':     'Daily',
    'recurrence.weekday':   'Weekday',
    'recurrence.alternate': 'Alternate',
    'recurrence.prn':       'PRN',

    // ── Route options ─────────────────────────────────────────────────────────
    'route.oral':       'Oral',
    'route.topical':    'Topical',
    'route.injection':  'Injection',
    'route.inhaled':    'Inhaled',
    'route.other':      'Other',

    // ── Dosage unit options ───────────────────────────────────────────────────
    'unit.mg':    'mg',
    'unit.ml':    'ml',
    'unit.units': 'units',

    // ── Timing period options ─────────────────────────────────────────────────
    'timing.none':      'None',
    'timing.morning':   'Morning',
    'timing.afternoon': 'Afternoon',
    'timing.evening':   'Evening',
    'timing.night':     'Night',
};
