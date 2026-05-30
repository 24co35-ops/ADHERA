medicines = r'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Adhera - Medicines</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body { background: #111318; color: #e2e2e8; font-family: 'Inter', sans-serif; }
        .glass { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(24px); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 24px; }
        input, select, textarea { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.12) !important; color: #e2e2e8 !important; border-radius: 12px !important; }
        input:focus, select:focus, textarea:focus { outline: none !important; border-color: #00dbe7 !important; }
        [x-cloak] { display: none !important; }
    </style>
</head>
<body x-data="medicinesData()" class="min-h-screen flex flex-col">
    <nav class="glass p-4 sticky top-0 z-50 flex justify-between items-center mb-6 rounded-none border-t-0 border-l-0 border-r-0">
        <a href="dashboard.html" class="flex items-center" style="height:40px;overflow:visible;">
            <div style="transform:scale(0.25);transform-origin:left center;width:50px;">
                <svg width="200" height="200" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="glow" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#00F2FF"/><stop offset="100%" stop-color="#3B82F6"/></linearGradient></defs><circle cx="100" cy="100" r="80" fill="url(#glow)" fill-opacity="0.1" stroke="url(#glow)" stroke-width="2"/><circle cx="100" cy="100" r="60" fill="white" fill-opacity="0.05" stroke="white" stroke-opacity="0.2"/><path d="M100 60L135 140H115L100 105L85 140H65L100 60Z" fill="url(#glow)"/><rect x="92" y="110" width="16" height="4" rx="2" fill="white" fill-opacity="0.8"/></svg>
            </div>
            <span style="color:#00dbe7;font-weight:700;font-size:1.5rem;letter-spacing:-0.02em;">Adhera</span>
        </a>
        <div class="space-x-4 text-sm font-medium">
            <a href="dashboard.html" class="hover:text-cyan-400 transition-colors">Dashboard</a>
            <a href="medicines.html" class="text-cyan-400">Medicines</a>
            <a href="feedback.html" class="hover:text-cyan-400 transition-colors">Feedback</a>
            <button @click="logout" class="text-red-400 hover:text-red-300 ml-4">Logout</button>
        </div>
    </nav>

    <main class="flex-1 px-4 md:px-8 max-w-[1280px] mx-auto w-full space-y-6 pb-12">
        <div class="glass p-6 rounded-xl">
            <h2 class="text-2xl font-bold mb-4">Active Medicines</h2>
            <div x-show="loading" class="text-slate-400">Loading...</div>
            <div x-show="!loading && medicines.length === 0" class="text-slate-400 py-8 text-center">No active medicines.</div>
            <div class="space-y-4">
                <template x-for="med in medicines" :key="med.id">
                    <div class="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
                        <div class="p-4 cursor-pointer hover:bg-white/10 transition-colors flex justify-between items-center" @click="toggleMed(med.id)">
                            <div>
                                <div class="font-bold text-lg text-cyan-50" x-text="med.name"></div>
                                <div class="text-sm text-slate-400 mt-1" x-text="med.dosage_amount + ' ' + med.dosage_unit + ' • ' + med.route + ' • ' + med.frequency_type"></div>
                            </div>
                            <div class="flex items-center gap-3">
                                <button @click.stop="deleteMed(med.id)" class="text-red-400 hover:text-red-300 text-sm">Delete</button>
                                <svg class="w-5 h-5 text-slate-400 transition-transform duration-200" :class="expandedMed === med.id ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                        </div>
                        <!-- Timings Section -->
                        <div x-show="expandedMed === med.id" x-cloak>
                            <div class="p-4 border-t border-white/10 bg-black/20 space-y-3">
                                <h4 class="font-bold text-sm flex justify-between items-center">
                                    <span>Timings</span>
                                    <button @click="showAddTiming(med.id)" class="text-xs bg-cyan-900/50 text-cyan-400 px-3 py-1 rounded-lg border border-cyan-500/30 hover:bg-cyan-900/80">+ Add Timing</button>
                                </h4>
                                <div x-show="timingsLoading[med.id]" class="text-slate-500 text-sm">Loading timings...</div>
                                <div x-show="!timingsLoading[med.id] && !(timings[med.id]?.length)" class="text-slate-500 text-sm py-2">No timings configured.</div>
                                <template x-for="rem in (timings[med.id] || [])" :key="rem.id">
                                    <div class="bg-white/5 rounded-lg border border-white/5 p-3 flex justify-between items-center">
                                        <template x-if="editingReminder !== rem.id">
                                            <div class="flex justify-between items-center w-full">
                                                <div>
                                                    <span class="text-sm font-medium text-cyan-100" x-text="rem.dose_label"></span>
                                                    <span class="text-xs text-slate-400 ml-2" x-text="rem.dose_time_utc"></span>
                                                    <span class="text-xs text-slate-500 ml-2" x-text="rem.recurrence_type"></span>
                                                </div>
                                                <div class="flex gap-2">
                                                    <button @click="startEditReminder(rem)" class="text-xs text-cyan-400 hover:underline">Edit</button>
                                                    <button @click="deleteReminder(rem.id)" class="text-xs text-red-400 hover:underline">Delete</button>
                                                </div>
                                            </div>
                                        </template>
                                        <template x-if="editingReminder === rem.id">
                                            <div class="w-full space-y-2">
                                                <div class="grid grid-cols-3 gap-2">
                                                    <input type="text" x-model="editForm.dose_label" placeholder="Label" class="text-sm p-1.5">
                                                    <input type="time" x-model="editForm.dose_time_utc" class="text-sm p-1.5">
                                                    <select x-model="editForm.recurrence_type" class="text-sm p-1.5">
                                                        <option value="daily">Daily</option><option value="weekday">Weekday</option><option value="alternate">Alternate</option>
                                                    </select>
                                                </div>
                                                <div class="flex gap-2 justify-end">
                                                    <button @click="saveEditReminder(rem.id)" class="text-xs bg-emerald-600 text-white px-3 py-1 rounded-lg">Save</button>
                                                    <button @click="editingReminder=null" class="text-xs text-slate-400 px-3 py-1">Cancel</button>
                                                </div>
                                                <div x-show="editError" class="text-xs text-red-400" x-text="editError"></div>
                                            </div>
                                        </template>
                                    </div>
                                </template>
                                <!-- Add Timing Form -->
                                <div x-show="addingTimingFor === med.id" class="bg-white/5 rounded-lg border border-cyan-500/20 p-3 space-y-2" x-cloak>
                                    <div class="grid grid-cols-3 gap-2">
                                        <input type="text" x-model="addTimingForm.dose_label" placeholder="e.g. Morning" class="text-sm p-1.5" maxlength="50">
                                        <input type="time" x-model="addTimingForm.dose_time_utc" class="text-sm p-1.5">
                                        <select x-model="addTimingForm.recurrence_type" class="text-sm p-1.5">
                                            <option value="daily">Daily</option><option value="weekday">Weekday</option><option value="alternate">Alternate</option>
                                        </select>
                                    </div>
                                    <div class="flex gap-2 justify-end">
                                        <button @click="saveAddTiming(med.id)" class="text-xs bg-cyan-600 text-white px-3 py-1 rounded-lg">Add</button>
                                        <button @click="addingTimingFor=null" class="text-xs text-slate-400 px-3 py-1">Cancel</button>
                                    </div>
                                    <div x-show="addTimingError" class="text-xs text-red-400" x-text="addTimingError"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </template>
            </div>
        </div>

        <div class="glass p-6 rounded-xl">
            <h2 class="text-xl font-bold mb-4">Add Medicine</h2>
            <form @submit.prevent="addMed" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div><label class="block text-sm mb-1">Name</label><input type="text" x-model="form.name" class="w-full p-2 rounded" required></div>
                <div class="grid grid-cols-2 gap-2">
                    <div><label class="block text-sm mb-1">Amount</label><input type="number" x-model="form.dosage_amount" class="w-full p-2 rounded" required></div>
                    <div><label class="block text-sm mb-1">Unit</label><select x-model="form.dosage_unit" class="w-full p-2 rounded" required><option value="mg">mg</option><option value="ml">ml</option><option value="units">units</option></select></div>
                </div>
                <div><label class="block text-sm mb-1">Route</label><select x-model="form.route" class="w-full p-2 rounded" required><option value="oral">Oral</option><option value="topical">Topical</option><option value="injection">Injection</option><option value="inhaled">Inhaled</option><option value="other">Other</option></select></div>
                <div><label class="block text-sm mb-1">Frequency</label><select x-model="form.frequency_type" class="w-full p-2 rounded" required><option value="daily">Daily</option><option value="weekday">Weekday</option><option value="alternate">Alternate</option><option value="prn">PRN</option></select></div>
                <div><label class="block text-sm mb-1">Start Date</label><input type="date" x-model="form.start_date" class="w-full p-2 rounded" required></div>
                <div><label class="block text-sm mb-1">End Date (Optional)</label><input type="date" x-model="form.end_date" class="w-full p-2 rounded"></div>
                <div class="md:col-span-2"><label class="block text-sm mb-1">Instructions (Optional)</label><input type="text" x-model="form.instructions" class="w-full p-2 rounded"></div>
                <div class="md:col-span-2 flex justify-end"><button type="submit" class="bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-2 px-6 rounded-lg disabled:opacity-50" :disabled="actionLoading">Add</button></div>
            </form>
        </div>
    </main>

    <script>
        const config = { SUPABASE_URL: "http://localhost:8000" };
        function medicinesData() {
            return {
                token: sessionStorage.getItem('jwt'),
                medicines: [], loading: true, actionLoading: false,
                expandedMed: null, timings: {}, timingsLoading: {},
                editingReminder: null, editForm: {}, editError: '',
                addingTimingFor: null, addTimingForm: { dose_label: '', dose_time_utc: '', recurrence_type: 'daily', timezone: 'UTC' }, addTimingError: '',
                form: { name: '', dosage_amount: '', dosage_unit: 'mg', route: 'oral', frequency_type: 'daily', start_date: new Date().toISOString().split('T')[0], end_date: '', instructions: '' },
                async init() {
                    if (!this.token) return window.location.href = 'index.html';
                    const payload = JSON.parse(atob(this.token.split('.')[1]));
                    const role = payload.user_metadata?.role || 'patient';
                    if (role !== 'patient') {
                        if (role === 'provider') return window.location.href = 'provider-dashboard.html';
                        if (role === 'admin') return window.location.href = 'admin-dashboard.html';
                        return window.location.href = 'index.html';
                    }
                    await this.fetchMedicines();
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
                async fetchMedicines() { try { this.medicines = await this.api('/medicines/'); } catch(e){} finally { this.loading = false; } },
                async toggleMed(id) {
                    if (this.expandedMed === id) { this.expandedMed = null; return; }
                    this.expandedMed = id;
                    await this.fetchTimings(id);
                },
                async fetchTimings(medId) {
                    this.timingsLoading[medId] = true;
                    try { this.timings[medId] = await this.api(`/medicines/${medId}/reminders`); } catch(e) { this.timings[medId] = []; }
                    finally { this.timingsLoading[medId] = false; }
                },
                showAddTiming(medId) { this.addingTimingFor = medId; this.addTimingForm = { dose_label: '', dose_time_utc: '', recurrence_type: 'daily', timezone: 'UTC' }; this.addTimingError = ''; },
                async saveAddTiming(medId) {
                    if (!this.addTimingForm.dose_label || !this.addTimingForm.dose_time_utc) { this.addTimingError = 'Label and time required.'; return; }
                    try {
                        await this.api(`/medicines/${medId}/reminders`, 'POST', this.addTimingForm);
                        this.addingTimingFor = null;
                        await this.fetchTimings(medId);
                    } catch(e) {
                        this.addTimingError = e.message.includes('slot') ? 'This time slot already exists for this medicine.' : e.message;
                    }
                },
                startEditReminder(rem) { this.editingReminder = rem.id; this.editForm = { dose_label: rem.dose_label, dose_time_utc: rem.dose_time_utc, recurrence_type: rem.recurrence_type }; this.editError = ''; },
                async saveEditReminder(remId) {
                    try {
                        await this.api(`/reminders/${remId}`, 'PATCH', this.editForm);
                        this.editingReminder = null;
                        const medId = this.expandedMed;
                        await this.fetchTimings(medId);
                    } catch(e) { this.editError = e.message; }
                },
                async deleteReminder(remId) {
                    if (!confirm('Delete this timing?')) return;
                    try {
                        await this.api(`/reminders/${remId}`, 'DELETE');
                        const medId = this.expandedMed;
                        await this.fetchTimings(medId);
                    } catch(e) { console.error(e); }
                },
                async addMed() {
                    this.actionLoading = true;
                    try {
                        const payload = { ...this.form };
                        if (!payload.end_date) delete payload.end_date;
                        if (!payload.instructions) delete payload.instructions;
                        await this.api('/medicines/', 'POST', payload);
                        await this.fetchMedicines();
                        this.form.name = ''; this.form.dosage_amount = '';
                    } catch(e){} finally { this.actionLoading = false; }
                },
                async deleteMed(id) {
                    if (!confirm('Are you sure?')) return;
                    this.actionLoading = true;
                    try { await this.api(`/medicines/${id}`, 'DELETE'); await this.fetchMedicines(); } catch(e){} finally { this.actionLoading = false; }
                },
                logout() { sessionStorage.removeItem('jwt'); window.location.href = 'index.html'; }
            }
        }
    </script>
</body>
</html>'''

with open('frontend/medicines.html', 'w', encoding='utf-8') as f:
    f.write(medicines)
