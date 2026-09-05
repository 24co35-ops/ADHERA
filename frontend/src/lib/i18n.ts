import { create } from 'zustand';

export const translations: Record<string, Record<string, string>> = {
  en: {
    // Navigation
    'nav.dashboard': 'Dashboard',
    'nav.medicines': 'Medicines',
    'nav.feedback': 'Feedback',
    'nav.profile': 'Profile',
    'nav.provider': 'Provider Portal',
    'nav.admin': 'Admin Console',
    'nav.logout': 'Logout',

    // Patient Dashboard
    'stat.overall_adherence': 'Overall Adherence',
    'stat.day_streak': 'Day Streak',
    'stat.missed_this_month': 'Missed This Month',
    'stat.due_today': 'Due Today',
    'chart.weekly_adherence': 'Weekly Adherence',
    'chart.monthly_adherence': 'Monthly Adherence',
    'chart.low_adherence': 'Low Adherence (Below target)',
    'schedule.title': "Today's Schedule",
    'schedule.all_done': "No doses pending today. You're all caught up!",
    'btn.taken': 'Taken',
    'btn.snooze': 'Snooze',
    'btn.missed': 'Missed',
    'feedback.title': 'Recent Feedback',
    'feedback.view_all': 'View all',
    'feedback.empty': 'No recent feedback reported.',
    'export.title': 'Export My Data',
    'export.description': 'Download all your adherence records, medicines, and feedback.',
    'export.json': 'Export JSON',
    'export.csv': 'Export CSV',

    // Medicines
    'medicines.active_title': 'Active Medicines',
    'medicines.add_title': 'Add Medicine',
    'medicines.empty': 'No active medicines.',
    'medicines.name': 'Medicine Name',
    'medicines.dosage': 'Dosage (e.g. 500mg)',
    'medicines.route': 'Route of Administration',
    'medicines.frequency': 'Frequency',
    'medicines.start_date': 'Start Date',
    'medicines.instructions': 'Instructions',
    'timing.title': 'Timings',
    'timing.add_btn': '+ Add Timing',

    // Profile & Emergency Contacts
    'profile.title': 'Patient Profile & Settings',
    'profile.subtitle': 'Personal medical info, emergency contacts, provider link, and alerts',
    'profile.personal_info': 'Personal Information',
    'profile.full_name': 'Full Name',
    'profile.dob': 'Date of Birth',
    'profile.blood_group': 'Blood Group',
    'profile.timezone': 'Timezone',
    'profile.allergies': 'Known Allergies (Press Enter to add)',
    'profile.conditions': 'Medical Conditions (Press Enter to add)',
    'profile.save_btn': 'Save Profile Changes',
    'profile.emergency_contacts': 'Emergency Contacts',
    'profile.emergency_subtitle': 'Notified automatically in case of Level 4 emergency side effects',
    'profile.add_contact': 'Add Contact',
    'profile.no_contacts': 'No emergency contacts configured yet.',
    'profile.contact_name': 'Contact Full Name',
    'profile.contact_phone': 'Phone Number',
    'profile.contact_email': 'Email Address',
    'profile.contact_rel': 'Relationship (e.g. Spouse, Parent)',
    'profile.provider_assignment': 'Healthcare Provider',
    'profile.push_notifications': 'Browser Push Notifications',

    // Feedback
    'feedback.heading': 'Side Effects & Feedback',
    'feedback.subheading': 'Report adverse reactions or side effects for clinical review',
    'feedback.report_new': 'Report Side Effect',
    'feedback.severity': 'Severity Level',
    'feedback.severity_1': 'Mild (Grade 1)',
    'feedback.severity_2': 'Moderate (Grade 2)',
    'feedback.severity_3': 'Severe (Grade 3)',
    'feedback.severity_4': 'Emergency / Life-threatening (Grade 4)',

    // Admin
    'admin.title': 'System Administration Console',
    'admin.subtitle': 'User management, provider approvals, platform statistics, and audit logs',
    'admin.users_tab': 'User Management',
    'admin.providers_tab': 'Provider Approvals',
    'admin.assignments_tab': 'Patient Assignments',
    'admin.audit_tab': 'Audit Logs',
    'admin.active': 'Active',
    'admin.suspended': 'Suspended',
    'admin.activate': 'Activate',
    'admin.deactivate': 'Deactivate',
    'admin.approve': 'Approve',
    'admin.reject': 'Reject',

    // Provider
    'provider.title': 'Healthcare Provider Portal',
    'provider.subtitle': 'Monitor patient adherence, review high-risk alerts, and manage care plans',
    'provider.patients': 'Assigned Patients',
    'provider.alerts': 'Adherence Alerts',

    // Common Buttons
    'btn.edit': 'Edit',
    'btn.delete': 'Delete',
    'btn.save': 'Save',
    'btn.cancel': 'Cancel',
    'btn.add': 'Add',
    'btn.close': 'Close',
    'btn.search': 'Search',
    'btn.loading': 'Loading...',
  },
  es: {
    // Navigation
    'nav.dashboard': 'Panel',
    'nav.medicines': 'Medicamentos',
    'nav.feedback': 'Efectos Secundarios',
    'nav.profile': 'Perfil',
    'nav.provider': 'Portal Médico',
    'nav.admin': 'Consola Admin',
    'nav.logout': 'Cerrar Sesión',

    // Patient Dashboard
    'stat.overall_adherence': 'Adherencia General',
    'stat.day_streak': 'Racha de Días',
    'stat.missed_this_month': 'Perdidas este mes',
    'stat.due_today': 'Pendientes Hoy',
    'chart.weekly_adherence': 'Adherencia Semanal',
    'chart.monthly_adherence': 'Adherencia Mensual',
    'chart.low_adherence': 'Adherencia Baja (Bajo objetivo)',
    'schedule.title': 'Horario de Hoy',
    'schedule.all_done': '¡No hay dosis pendientes hoy!',
    'btn.taken': 'Tomada',
    'btn.snooze': 'Posponer',
    'btn.missed': 'Perdida',
    'feedback.title': 'Comentarios Recientes',
    'feedback.view_all': 'Ver todos',
    'feedback.empty': 'No hay reportes recientes.',
    'export.title': 'Exportar Mis Datos',
    'export.description': 'Descarga tus registros de adherencia, medicamentos y comentarios.',
    'export.json': 'Exportar JSON',
    'export.csv': 'Exportar CSV',

    // Medicines
    'medicines.active_title': 'Medicamentos Activos',
    'medicines.add_title': 'Agregar Medicamento',
    'medicines.empty': 'Sin medicamentos activos.',
    'medicines.name': 'Nombre del Medicamento',
    'medicines.dosage': 'Dosis (ej. 500mg)',
    'medicines.route': 'Vía de Administración',
    'medicines.frequency': 'Frecuencia',
    'medicines.start_date': 'Fecha de Inicio',
    'medicines.instructions': 'Instrucciones',
    'timing.title': 'Horarios',
    'timing.add_btn': '+ Agregar Horario',

    // Profile & Emergency Contacts
    'profile.title': 'Perfil del Paciente y Configuración',
    'profile.subtitle': 'Información médica, contactos de emergencia y alertas',
    'profile.personal_info': 'Información Personal',
    'profile.full_name': 'Nombre Completo',
    'profile.dob': 'Fecha de Nacimiento',
    'profile.blood_group': 'Grupo Sanguíneo',
    'profile.timezone': 'Zona Horaria',
    'profile.allergies': 'Alergias Conocidas (Presione Enter)',
    'profile.conditions': 'Condiciones Médicas (Presione Enter)',
    'profile.save_btn': 'Guardar Cambios de Perfil',
    'profile.emergency_contacts': 'Contactos de Emergencia',
    'profile.emergency_subtitle': 'Notificado automáticamente en caso de efectos secundarios de Nivel 4',
    'profile.add_contact': 'Agregar Contacto',
    'profile.no_contacts': 'No hay contactos de emergencia configurados.',
    'profile.contact_name': 'Nombre Completo del Contacto',
    'profile.contact_phone': 'Teléfono',
    'profile.contact_email': 'Correo Electrónico',
    'profile.contact_rel': 'Parentesco (ej. Cónyuge, Padre)',
    'profile.provider_assignment': 'Médico Asignado',
    'profile.push_notifications': 'Notificaciones Push del Navegador',

    // Feedback
    'feedback.heading': 'Efectos Secundarios y Comentarios',
    'feedback.subheading': 'Reporte reacciones adversas para revisión médica',
    'feedback.report_new': 'Reportar Efecto Secundario',
    'feedback.severity': 'Nivel de Severidad',
    'feedback.severity_1': 'Leve (Grado 1)',
    'feedback.severity_2': 'Moderado (Grado 2)',
    'feedback.severity_3': 'Severo (Grado 3)',
    'feedback.severity_4': 'Emergencia / Crítico (Grado 4)',

    // Admin
    'admin.title': 'Consola de Administración del Sistema',
    'admin.subtitle': 'Gestión de usuarios, aprobación de médicos y registros de auditoría',
    'admin.users_tab': 'Gestión de Usuarios',
    'admin.providers_tab': 'Aprobación de Médicos',
    'admin.assignments_tab': 'Asignación de Pacientes',
    'admin.audit_tab': 'Registros de Auditoría',
    'admin.active': 'Activo',
    'admin.suspended': 'Suspendido',
    'admin.activate': 'Activar',
    'admin.deactivate': 'Desactivar',
    'admin.approve': 'Aprobar',
    'admin.reject': 'Rechazar',

    // Provider
    'provider.title': 'Portal de Profesionales Médicos',
    'provider.subtitle': 'Monitoreo de pacientes, alertas y planes de cuidado',
    'provider.patients': 'Pacientes Asignados',
    'provider.alerts': 'Alertas de Adherencia',

    // Common Buttons
    'btn.edit': 'Editar',
    'btn.delete': 'Eliminar',
    'btn.save': 'Guardar',
    'btn.cancel': 'Cancelar',
    'btn.add': 'Agregar',
    'btn.close': 'Cerrar',
    'btn.search': 'Buscar',
    'btn.loading': 'Cargando...',
  },
  hi: {
    // Navigation
    'nav.dashboard': 'डैशबोर्ड',
    'nav.medicines': 'दवाएं',
    'nav.feedback': 'प्रतिक्रिया',
    'nav.profile': 'प्रोफ़ाइल',
    'nav.provider': 'डॉक्टर पोर्टल',
    'nav.admin': 'व्यवस्थापक',
    'nav.logout': 'लॉग आउट',

    // Patient Dashboard
    'stat.overall_adherence': 'समग्र अनुपालन',
    'stat.day_streak': 'दैनिक स्ट्रीक',
    'stat.missed_this_month': 'इस महीने छूटी',
    'stat.due_today': 'आज की देय खुराक',
    'chart.weekly_adherence': 'साप्ताहिक अनुपालन',
    'chart.monthly_adherence': 'मासिक अनुपालन',
    'chart.low_adherence': 'कम अनुपालन',
    'schedule.title': 'आज का शेड्यूल',
    'schedule.all_done': 'आज कोई खुराक लंबित नहीं है!',
    'btn.taken': 'ले ली',
    'btn.snooze': 'बाद में',
    'btn.missed': 'छूट गई',
    'feedback.title': 'हालिया रिपोर्ट',
    'feedback.view_all': 'सभी देखें',
    'feedback.empty': 'कोई हालिया रिपोर्ट नहीं।',
    'export.title': 'डेटा निर्यात करें',
    'export.description': 'अपने सभी दवा और अनुपालन रिकॉर्ड डाउनलोड करें।',
    'export.json': 'JSON निर्यात करें',
    'export.csv': 'CSV निर्यात करें',

    // Medicines
    'medicines.active_title': 'सक्रिय दवाएं',
    'medicines.add_title': 'दवा जोड़ें',
    'medicines.empty': 'कोई सक्रिय दवा नहीं।',
    'medicines.name': 'दवा का नाम',
    'medicines.dosage': 'खुराक (जैसे 500mg)',
    'medicines.route': 'लेने का तरीका',
    'medicines.frequency': 'आवृत्ति',
    'medicines.start_date': 'शुरुआती तारीख',
    'medicines.instructions': 'निर्देश',
    'timing.title': 'समय',
    'timing.add_btn': '+ समय जोड़ें',

    // Profile & Emergency Contacts
    'profile.title': 'रोगी प्रोफ़ाइल और सेटिंग्स',
    'profile.subtitle': 'व्यक्तिगत चिकित्सा जानकारी, आपातकालीन संपर्क और अलर्ट',
    'profile.personal_info': 'व्यक्तिगत जानकारी',
    'profile.full_name': 'पूरा नाम',
    'profile.dob': 'जन्म तिथि',
    'profile.blood_group': 'रक्त समूह',
    'profile.timezone': 'समय क्षेत्र',
    'profile.allergies': 'ज्ञात एलर्जी (जोड़ने के लिए Enter दबाएं)',
    'profile.conditions': 'चिकित्सा स्थितियां (जोड़ने के लिए Enter दबाएं)',
    'profile.save_btn': 'प्रोफ़ाइल सहेजें',
    'profile.emergency_contacts': 'आपातकालीन संपर्क',
    'profile.emergency_subtitle': 'स्तर 4 गंभीर दुष्प्रभावों के मामले में स्वचालित सूचना',
    'profile.add_contact': 'संपर्क जोड़ें',
    'profile.no_contacts': 'कोई आपातकालीन संपर्क मौजूद नहीं है।',
    'profile.contact_name': 'संपर्क का पूरा नाम',
    'profile.contact_phone': 'फ़ोन नंबर',
    'profile.contact_email': 'ईमेल पता',
    'profile.contact_rel': 'संबंध (जैसे पति/पत्नी, माता-पिता)',
    'profile.provider_assignment': 'नियुक्त चिकित्सक',
    'profile.push_notifications': 'ब्राउज़र पुश सूचनाएं',

    // Feedback
    'feedback.heading': 'दुष्प्रभाव और प्रतिक्रिया',
    'feedback.subheading': 'चिकित्सा समीक्षा के लिए प्रतिकूल प्रतिक्रियाएं दर्ज करें',
    'feedback.report_new': 'दुष्प्रभाव रिपोर्ट करें',
    'feedback.severity': 'गंभीरता का स्तर',
    'feedback.severity_1': 'हल्का (ग्रेड 1)',
    'feedback.severity_2': 'मध्यम (ग्रेड 2)',
    'feedback.severity_3': 'गंभीर (ग्रेड 3)',
    'feedback.severity_4': 'आपातकालीन / जानलेवा (ग्रेड 4)',

    // Admin
    'admin.title': 'सिस्टम व्यवस्थापक कंसोल',
    'admin.subtitle': 'उपयोगकर्ता प्रबंधन, डॉक्टर अनुमोदन और ऑडिट लॉग',
    'admin.users_tab': 'उपयोगकर्ता प्रबंधन',
    'admin.providers_tab': 'डॉक्टर अनुमोदन',
    'admin.assignments_tab': 'रोगी असाइनमेंट',
    'admin.audit_tab': 'ऑडिट लॉग्स',
    'admin.active': 'सक्रिय',
    'admin.suspended': 'निलंबित',
    'admin.activate': 'सक्रिय करें',
    'admin.deactivate': 'निष्क्रिय करें',
    'admin.approve': 'स्वीकार करें',
    'admin.reject': 'अस्वीकार करें',

    // Provider
    'provider.title': 'स्वास्थ्य सेवा प्रदाता पोर्टल',
    'provider.subtitle': 'मरीजों का अनुपालन ट्रैक करें और अलर्ट देखें',
    'provider.patients': 'नियुक्त मरीज',
    'provider.alerts': 'अनुपालन अलर्ट',

    // Common Buttons
    'btn.edit': 'संपादित करें',
    'btn.delete': 'हटाएं',
    'btn.save': 'सहेजें',
    'btn.cancel': 'रद्द करें',
    'btn.add': 'जोड़ें',
    'btn.close': 'बंद करें',
    'btn.search': 'खोजें',
    'btn.loading': 'लोड हो रहा है...',
  },
};

interface I18nStore {
  locale: string;
  setLocale: (lang: string) => void;
  t: (key: string) => string;
}

export const useI18n = create<I18nStore>((set, get) => ({
  locale: typeof localStorage !== 'undefined' ? localStorage.getItem('adhera_lang') || 'en' : 'en',
  setLocale: (lang: string) => {
    try {
      localStorage.setItem('adhera_lang', lang);
    } catch {
      // ignore storage error
    }
    set({ locale: lang });
  },
  t: (key: string) => {
    const loc = get().locale;
    return translations[loc]?.[key] || translations.en?.[key] || key;
  },
}));
