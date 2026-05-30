html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Adhera - Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body { background: #111318; color: #e2e2e8; font-family: 'Inter', sans-serif; }
        .glass { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(24px); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 24px; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1); }
        input, select, textarea { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.12) !important; color: #e2e2e8 !important; border-radius: 12px !important; }
        input:focus, select:focus, textarea:focus { outline: none !important; border-color: #00dbe7 !important; }
        button[type="submit"], button.bg-cyan-600 { background: #00dbe7 !important; color: #002022 !important; border-radius: 12px !important; }
        button.bg-slate-700 { background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.12) !important; border-radius: 12px !important; }
        [x-cloak] { display: none !important; }
    </style>
</head>
<body x-data="dashboardData()" class="min-h-screen flex flex-col">
    <!-- Nav Header -->
    <nav class="glass p-4 sticky top-0 z-50 flex justify-between items-center mb-6 rounded-none border-t-0 border-l-0 border-r-0">
        <a href="dashboard.html" class="flex items-center" style="height: 40px; overflow: visible;">
            <div style="transform: scale(0.25); transform-origin: left center; width: 50px;">
                <svg width="200" height="200" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <defs>
                    <linearGradient id="glow" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stop-color="#00F2FF" />
                      <stop offset="100%" stop-color="#3B82F6" />
                    </linearGradient>
                    <filter id="blur" x="-20%" y="-20%" width="140%" height="140%">
                      <feGaussianBlur in="SourceGraphic" stdDeviation="5" />
                    </filter>
                  </defs>
                  <circle cx="100" cy="100" r="80" fill="url(#glow)" fill-opacity="0.1" stroke="url(#glow)" stroke-width="2" />
                  <circle cx="100" cy="100" r="60" fill="white" fill-opacity="0.05" style="backdrop-filter: blur(10px)" stroke="white" stroke-opacity="0.2" />
                  <path d="M100 60L135 140H115L100 105L85 140H65L100 60Z" fill="url(#glow)" />
                  <rect x="92" y="110" width="16" height="4" rx="2" fill="white" fill-opacity="0.8" />
                </svg>
            </div>
            <span style="color: #00dbe7; font-weight: 700; font-size: 1.5rem; letter-spacing: -0.02em;">Adhera</span>
        </a>
        <div class="space-x-4 font-medium text-sm">
            <a href="dashboard.html" class="text-cyan-400">Dashboard</a>
            <a href="medicines.html" class="hover:text-cyan-400 transition-colors">Medicines</a>
            <a href="feedback.html" class="hover:text-cyan-400 transition-colors">Feedback</a>
            <button @click="logout" class="text-red-400 hover:text-red-300 ml-4">Logout</button>
        </div>
    </nav>

    <main class="flex-1 px-4 md:px-8 max-w-[1280px] mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-6 pb-12">
        
        <!-- Main Content Column -->
        <div class="lg:col-span-8 space-y-6">
            
            <!-- Stat Cards -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="glass p-4 rounded-xl flex flex-col justify-center items-center text-center h-28 relative overflow-hidden">
                    <div x-show="loading" class="absolute inset-0 bg-white/5 animate-pulse"></div>
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Overall Adherence</span>
                    <span class="text-3xl font-bold text-cyan-300" x-text="adherence.overall_percentage !== undefined ? adherence.overall_percentage + '%' : '--'"></span>
                </div>
                <div class="glass p-4 rounded-xl flex flex-col justify-center items-center text-center h-28 relative overflow-hidden">
                    <div x-show="loading" class="absolute inset-0 bg-white/5 animate-pulse"></div>
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Day Streak</span>
                    <span class="text-3xl font-bold text-white" x-text="stats.streak !== undefined ? stats.streak : '--'"></span>
                </div>
                <div class="glass p-4 rounded-xl flex flex-col justify-center items-center text-center h-28 relative overflow-hidden">
                    <div x-show="loading" class="absolute inset-0 bg-white/5 animate-pulse"></div>
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Missed This Month</span>
                    <span class="text-3xl font-bold text-red-400" x-text="stats.missed_this_month !== undefined ? stats.missed_this_month : '--'"></span>
                </div>
                <div class="glass p-4 rounded-xl flex flex-col justify-center items-center text-center h-28 relative overflow-hidden">
                    <div x-show="dosesLoading" class="absolute inset-0 bg-white/5 animate-pulse"></div>
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Due Today</span>
                    <span class="text-3xl font-bold text-yellow-400" x-text="doses.length !== undefined ? doses.length : '--'"></span>
                </div>
            </div>

            <!-- Charts -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="glass p-6 rounded-xl relative">
                    <div x-show="loading" class="absolute inset-0 bg-white/5 animate-pulse rounded-xl z-10"></div>
                    <h3 class="text-lg font-bold mb-4 flex items-center justify-between">
                        Weekly Adherence
                        <span x-show="adherence.weekly_percentage < 70" class="bg-red-900/30 text-red-400 text-xs px-2 py-1 rounded-full border border-red-500/30 flex items-center gap-1" x-cloak>
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                            Below target
                        </span>
                    </h3>
                    <div class="relative h-48 w-full"><canvas id="weeklyChart"></canvas></div>
                </div>
                <div class="glass p-6 rounded-xl relative">
                    <div x-show="loading" class="absolute inset-0 bg-white/5 animate-pulse rounded-xl z-10"></div>
                    <h3 class="text-lg font-bold mb-4">Monthly Adherence</h3>
                    <div class="relative h-48 w-full"><canvas id="monthlyChart"></canvas></div>
                </div>
            </div>

            <!-- Today's Schedule -->
            <div class="glass p-6 rounded-xl relative">
                <h2 class="text-2xl font-bold mb-4">Today's Schedule</h2>
                <div x-show="dosesLoading" class="absolute inset-0 bg-white/5 animate-pulse rounded-xl z-10"></div>
                <div x-show="!dosesLoading && doses.length === 0" class="text-slate-400 py-8 text-center bg-white/5 rounded-lg border border-white/10">No doses pending today. You're all caught up!</div>
                <div class="space-y-3">
                    <template x-for="dose in doses" :key="dose.id">
                        <div class="bg-white/5 p-4 rounded-xl border border-white/10 flex justify-between items-center hover:bg-white/10 transition-colors">
                            <div>
                                <div class="font-bold text-lg text-cyan-50" x-text="dose.reminders?.medicines?.name"></div>
                                <div class="text-sm text-slate-400 mt-1 flex items-center gap-2">
                                    <span class="bg-white/10 px-2 py-0.5 rounded text-xs" x-text="dose.reminders?.dose_label"></span>
                                    <span x-text="dose.reminders?.medicines?.dosage_amount + ' ' + dose.reminders?.medicines?.dosage_unit"></span>
                                    <span>•</span>
                                    <span x-text="new Date(dose.scheduled_utc).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})"></span>
                                </div>
                            </div>
                            <div class="flex space-x-2">
                                <button @click="action(dose.id, 'taken')" class="bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/30 px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50" :disabled="actionLoading === dose.id">Taken</button>
                                <button @click="action(dose.id, 'snoozed')" class="bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 border border-amber-500/30 px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50" :disabled="actionLoading === dose.id || dose.snooze_count >= 3">Snooze</button>
                                <button @click="action(dose.id, 'missed')" class="bg-rose-500/20 text-rose-400 hover:bg-rose-500/30 border border-rose-500/30 px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50" :disabled="actionLoading === dose.id">Missed</button>
                            </div>
                        </div>
                    </template>
                </div>
            </div>

        </div>

        <!-- Sidebar -->
        <div class="lg:col-span-4 space-y-6">
            <div class="glass p-6 rounded-xl relative">
                <h3 class="text-lg font-bold mb-4 flex items-center justify-between">
                    Recent Feedback
                    <a href="feedback.html" class="text-xs text-cyan-400 hover:underline font-medium">View all</a>
                </h3>
                <div x-show="fbLoading" class="absolute inset-0 bg-white/5 animate-pulse rounded-xl z-10"></div>
                <div x-show="!fbLoading && feedback.length === 0" class="text-slate-400 text-sm italic">No recent feedback reported.</div>
                <div class="space-y-3">
                    <template x-for="fb in feedback" :key="fb.id">
                        <div class="text-sm bg-white/5 p-4 rounded-xl border border-white/10">
                            <div class="flex justify-between items-start mb-2">
                                <div class="font-medium text-cyan-100" x-text="fb.medicines?.name || 'General'"></div>
                                <span class="text-xs px-2 py-0.5 rounded-full font-medium" 
                                      :class="{
                                          'bg-rose-500/20 text-rose-400 border border-rose-500/30': fb.severity >= 3,
                                          'bg-amber-500/20 text-amber-400 border border-amber-500/30': fb.severity === 2,
                                          'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30': fb.severity === 1
                                      }"
                                      x-text="'Sev ' + fb.severity"></span>
                            </div>
                            <div class="text-slate-300 mb-2 truncate" x-text="fb.description"></div>
                            <div class="text-slate-500 text-xs" x-text="new Date(fb.occurred_at).toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'})"></div>
                        </div>
                    </template>
                </div>
            </div>
        </div>
    </main>

    <script>
        const config = { SUPABASE_URL: "http://localhost:8000", SUPABASE_JS_URL: "https://olsgvrmxqsftymsbeqve.supabase.co", SUPABASE_ANON: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9sc2d2cm14cXNmdHltc2JlcXZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzk2OTA0MjksImV4cCI6MjA5NTI2NjQyOX0.aZLBUgVPtRaCKbjHu8ljvsKOYWU6TDXO1gAE79jq9cM" };
        
        function dashboardData() {
            return {
                token: sessionStorage.getItem('jwt'),
                doses: [], dosesLoading: true, actionLoading: null,
                stats: {}, adherence: {}, trend: [],
                feedback: [], fbLoading: true, loading: true,
                charts: {},
                
                async init() {
                    if (!this.token) return window.location.href = 'index.html';
                    const payload = JSON.parse(atob(this.token.split('.')[1]));
                    const role = payload.user_metadata?.role || 'patient';
                    if (role !== 'patient') {
                        if (role === 'provider') return window.location.href = 'provider-dashboard.html';
                        if (role === 'admin') return window.location.href = 'admin-dashboard.html';
                        return window.location.href = 'index.html';
                    }
                    
                    Chart.defaults.color = '#849495';
                    Chart.defaults.font.family = 'Inter';
                    
                    this.initCharts();
                    await this.fetchAll();
                    this.setupRealtime();
                },
                async fetchAll() {
                    await Promise.all([this.fetchDoses(), this.fetchData(), this.fetchFeedback()]);
                },
                async api(path, method = 'GET', body = null) {
                    const opts = { method, headers: { 'Authorization': `Bearer ${this.token}`, 'Content-Type': 'application/json' } };
                    if (body) opts.body = JSON.stringify(body);
                    const res = await fetch(`${config.SUPABASE_URL}/v1${path}`, opts);
                    if (res.status === 401) { sessionStorage.removeItem('jwt'); window.location.href = 'index.html'; }
                    const data = await res.json();
                    if (!data.success) throw new Error(data.error?.message || "API Error");
                    return data.data;
                },
                async fetchDoses() {
                    this.dosesLoading = true;
                    try { this.doses = await this.api('/doses/upcoming'); } catch(e){ console.error(e); } finally { this.dosesLoading = false; }
                },
                async fetchData() {
                    this.loading = true;
                    try {
                        const [st, ad, tr] = await Promise.all([
                            this.api('/analytics/dashboard'),
                            this.api('/analytics/adherence'),
                            this.api('/analytics/trend')
                        ]);
                        this.stats = st;
                        this.adherence = ad;
                        this.trend = tr;
                        this.updateCharts();
                    } catch(e) { console.error(e); }
                    finally { this.loading = false; }
                },
                async fetchFeedback() {
                    this.fbLoading = true;
                    try { const res = await this.api('/feedback/'); this.feedback = res.slice(0,3); } catch(e){ console.error(e); }
                    finally { this.fbLoading = false; }
                },
                async action(doseId, status) {
                    this.actionLoading = doseId;
                    try { await this.api(`/doses/${doseId}/${status}`, 'POST'); await this.fetchAll(); } catch(e){ console.error(e); }
                    finally { this.actionLoading = null; }
                },
                logout() { sessionStorage.removeItem('jwt'); window.location.href = 'index.html'; },
                
                processTrendData(days) {
                    const now = new Date();
                    const map = {};
                    for(let i=days-1; i>=0; i--) {
                        const d = new Date(now);
                        d.setDate(d.getDate() - i);
                        map[d.toISOString().split('T')[0]] = { taken: 0, total: 0 };
                    }
                    
                    this.trend.forEach(t => {
                        const dateStr = t.scheduled_utc.split('T')[0];
                        if(map[dateStr]) {
                            map[dateStr].total++;
                            if(t.status === 'taken') map[dateStr].taken++;
                        }
                    });
                    
                    const labels = [];
                    const data = [];
                    for(const [date, counts] of Object.entries(map)) {
                        const d = new Date(date);
                        labels.push(d.toLocaleDateString(undefined, {month:'short', day:'numeric'}));
                        data.push(counts.total > 0 ? Math.round((counts.taken / counts.total) * 100) : 0);
                    }
                    return { labels, data };
                },
                
                initCharts() {
                    const commonOptions = {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { stepSize: 25, callback: (v) => v + '%' } },
                            x: { grid: { display: false } }
                        },
                        plugins: { legend: { display: false }, tooltip: { backgroundColor: 'rgba(17, 19, 24, 0.9)', titleColor: '#fff', bodyColor: '#fff', borderColor: 'rgba(255,255,255,0.12)', borderWidth: 1, padding: 10, displayColors: false, callbacks: { label: (ctx) => ctx.raw + '%' } } }
                    };
                    
                    const wc = document.getElementById('weeklyChart');
                    if(wc) {
                        this.charts.weekly = new Chart(wc, { 
                            type: 'bar', 
                            data: { labels: [], datasets: [{ data: [], backgroundColor: 'rgba(0, 219, 231, 0.8)', hoverBackgroundColor: '#00dbe7', borderRadius: 4 }] }, 
                            options: commonOptions 
                        });
                    }
                    
                    const mc = document.getElementById('monthlyChart');
                    if(mc) {
                        this.charts.monthly = new Chart(mc, { 
                            type: 'line', 
                            data: { labels: [], datasets: [{ data: [], borderColor: '#0566d9', backgroundColor: 'rgba(5, 102, 217, 0.1)', borderWidth: 3, tension: 0.4, fill: true, pointBackgroundColor: '#111318', pointBorderColor: '#0566d9', pointBorderWidth: 2, pointRadius: 3, pointHoverRadius: 6 }] }, 
                            options: commonOptions 
                        });
                    }
                },
                updateCharts() {
                    const weekly = this.processTrendData(7);
                    if (this.charts.weekly) { 
                        this.charts.weekly.data.labels = weekly.labels;
                        this.charts.weekly.data.datasets[0].data = weekly.data; 
                        this.charts.weekly.update(); 
                    }
                    
                    const monthly = this.processTrendData(30);
                    if (this.charts.monthly) { 
                        this.charts.monthly.data.labels = monthly.labels;
                        this.charts.monthly.data.datasets[0].data = monthly.data; 
                        this.charts.monthly.update(); 
                    }
                },
                setupRealtime() {
                    try {
                        if (!window.supabase?.createClient) return;
                        const sb = window.supabase.createClient(config.SUPABASE_JS_URL, config.SUPABASE_ANON);
                        const user_id = JSON.parse(atob(this.token.split('.')[1])).sub;
                        sb.channel('adherence_changes')
                            .on('postgres_changes', { event: '*', schema: 'public', table: 'adherence', filter: `user_id=eq.${user_id}` }, () => {
                                this.fetchAll();
                            }).subscribe();
                    } catch(e) { console.warn('Realtime setup skipped:', e.message); }
                }
            }
        }
    </script>
</body>
</html>
"""

with open('frontend/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
