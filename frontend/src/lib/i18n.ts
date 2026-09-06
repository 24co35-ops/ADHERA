import { create } from 'zustand';

export const translations: Record<string, Record<string, string>> = {
  en: {
    // Navigation
    'nav.dashboard': 'Dashboard',
    'nav.medicines': 'Medicines',
    'nav.wellness': 'Wellness',
    'nav.chat': 'Ask AI',
    'nav.clinical_ai': 'Clinical AI',
    'nav.feedback': 'Feedback',
    'nav.profile': 'Profile',
    'nav.provider': 'Provider Portal',
    'nav.admin': 'Admin Console',
    'nav.logout': 'Logout',
    'nav.language': 'Language',

    // Patient Dashboard Header & Alerts
    'dashboard.hello': 'Hello',
    'dashboard.patient': 'Patient',
    'dashboard.subtitle': 'Track your daily prescription adherence and insights',
    'dashboard.export_data': 'Export Data',
    'dashboard.exporting': 'Exporting...',
    'dashboard.adherence_warning_title': 'Adherence Warning (< 70%)',
    'dashboard.adherence_warning_msg': 'Your weekly adherence is at',
    'dashboard.adherence_warning_msg_end': '%. Please follow your daily schedule to stay on track with your doctor\'s recommendations.',

    // Stats
    'stat.overall_adherence': 'Overall Adherence',
    'stat.weekly_rate': 'Weekly rate',
    'stat.day_streak': 'Day Streak',
    'stat.consecutive_days': 'Consecutive days',
    'stat.keep_it_up': 'Keep it going!',
    'stat.missed_this_month': 'Missed This Month',
    'stat.doses_missed': 'Doses missed',
    'stat.this_month': 'This calendar month',
    'stat.due_today': 'Due Today',
    'stat.completed': 'Completed',

    // Schedule & Chart
    'schedule.title': "Today's Schedule",
    'schedule.scheduled_today': 'Scheduled doses for today',
    'schedule.manage_medicines': 'Manage Medicines',
    'schedule.all_done': "No doses pending today. You're all caught up!",
    'chart.weekly_adherence': 'Weekly Adherence',
    'chart.weekly_adherence_sub': 'Daily completion rates over the last 7 days',
    'chart.monthly_adherence': 'Monthly Adherence',
    'chart.low_adherence': 'Low Adherence (Below target)',

    // Buttons
    'btn.taken': 'Taken',
    'btn.snooze': 'Snooze',
    'btn.missed': 'Missed',
    'btn.edit': 'Edit',
    'btn.delete': 'Delete',
    'btn.save': 'Save',
    'btn.cancel': 'Cancel',
    'btn.add': 'Add',
    'btn.close': 'Close',
    'btn.search': 'Search',
    'btn.loading': 'Loading...',

    // Provider Card
    'provider.care_team_title': 'Healthcare Provider',
    'provider.care_team_sub': 'Clinical care team',
    'provider.connected': 'Connected',
    'provider.no_provider': 'No active provider assigned yet.',
    'provider.request_provider': 'Request Provider',

    // Mental Wellness
    'wellness.card_title': 'Mental Wellness',
    'wellness.resonance_badge': '3D Resonance',
    'wellness.card_desc': 'Calm your nervous system and reinforce treatment adherence with guided 3D resonance breathing.',
    'wellness.start_btn': 'Start Breathing Exercise',
    'wellness.page_title': 'Mental Wellness & Breathing',
    'wellness.page_subtitle': 'Grounded 3D resonance breathing to lower anxiety, improve focus, and reinforce treatment adherence.',
    'wellness.press_start': 'Press Start to Begin',
    'wellness.session_complete': 'Session Complete',
    'wellness.inhale': 'Inhale Deeply...',
    'wellness.hold': 'Hold Breath...',
    'wellness.exhale': 'Exhale Slowly...',
    'wellness.rest': 'Rest & Hold...',
    'wellness.start_session': 'Start Session',
    'wellness.pause': 'Pause',
    'wellness.resume': 'Resume',
    'wellness.reset': 'Reset',
    'wellness.patterns': 'Breathing Patterns',
    'wellness.custom_pattern': 'Custom Pattern',
    'wellness.recent_sessions': 'Recent Sessions',
    'wellness.no_sessions': 'No breathing sessions recorded yet.',

    // Chat AI
    'chat.title': 'Ask AI Assistant',
    'chat.subtitle': 'Verified clinical guidance and adherence support',
    'chat.input_placeholder': 'Ask about medications, side effects, or schedule...',
    'chat.send': 'Send',
    'chat.clear': 'Clear',
    'chat.disclaimer': 'Grounded in clinical knowledge. Always consult your doctor for emergency care.',

    // Feedback
    'feedback.title': 'Recent Feedback',
    'feedback.view_all': 'View all',
    'feedback.empty': 'No recent feedback reported.',
    'feedback.heading': 'Side Effects & Feedback',
    'feedback.subheading': 'Report adverse reactions or side effects for clinical review',
    'feedback.report_new': 'Report Side Effect',
    'feedback.severity': 'Severity Level',
    'feedback.severity_1': 'Mild (Grade 1)',
    'feedback.severity_2': 'Moderate (Grade 2)',
    'feedback.severity_3': 'Severe (Grade 3)',
    'feedback.severity_4': 'Emergency / Life-threatening (Grade 4)',

    // Export
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
  },
  es: {
    // Navigation
    'nav.dashboard': 'Panel',
    'nav.medicines': 'Medicamentos',
    'nav.wellness': 'Bienestar',
    'nav.chat': 'Consultar IA',
    'nav.clinical_ai': 'IA Clínica',
    'nav.feedback': 'Efectos Secundarios',
    'nav.profile': 'Perfil',
    'nav.provider': 'Portal Médico',
    'nav.admin': 'Consola Admin',
    'nav.logout': 'Cerrar Sesión',
    'nav.language': 'Idioma',

    // Patient Dashboard Header & Alerts
    'dashboard.hello': 'Hola',
    'dashboard.patient': 'Paciente',
    'dashboard.subtitle': 'Siga su adherencia diaria a las recetas y conocimientos',
    'dashboard.export_data': 'Exportar Datos',
    'dashboard.exporting': 'Exportando...',
    'dashboard.adherence_warning_title': 'Advertencia de Adherencia (< 70%)',
    'dashboard.adherence_warning_msg': 'Su adherencia semanal es del',
    'dashboard.adherence_warning_msg_end': '%. Siga su horario diario para cumplir con las recomendaciones de su médico.',

    // Stats
    'stat.overall_adherence': 'Adherencia General',
    'stat.weekly_rate': 'Tasa semanal',
    'stat.day_streak': 'Racha de Días',
    'stat.consecutive_days': 'Días consecutivos',
    'stat.keep_it_up': '¡Sigue así!',
    'stat.missed_this_month': 'Perdidas este mes',
    'stat.doses_missed': 'Dosis perdidas',
    'stat.this_month': 'Este mes calendario',
    'stat.due_today': 'Pendientes Hoy',
    'stat.completed': 'Completado',

    // Schedule & Chart
    'schedule.title': 'Horario de Hoy',
    'schedule.scheduled_today': 'Dosis programadas para hoy',
    'schedule.manage_medicines': 'Administrar Medicamentos',
    'schedule.all_done': '¡No hay dosis pendientes hoy!',
    'chart.weekly_adherence': 'Adherencia Semanal',
    'chart.weekly_adherence_sub': 'Tasas de finalización diaria en los últimos 7 días',
    'chart.monthly_adherence': 'Adherencia Mensual',
    'chart.low_adherence': 'Adherencia Baja (Bajo objetivo)',

    // Buttons
    'btn.taken': 'Tomada',
    'btn.snooze': 'Posponer',
    'btn.missed': 'Perdida',
    'btn.edit': 'Editar',
    'btn.delete': 'Eliminar',
    'btn.save': 'Guardar',
    'btn.cancel': 'Cancelar',
    'btn.add': 'Agregar',
    'btn.close': 'Cerrar',
    'btn.search': 'Buscar',
    'btn.loading': 'Cargando...',

    // Provider Card
    'provider.care_team_title': 'Proveedor de Atención Médica',
    'provider.care_team_sub': 'Equipo de atención clínica',
    'provider.connected': 'Conectado',
    'provider.no_provider': 'Aún no tiene un médico asignado.',
    'provider.request_provider': 'Solicitar Médico',

    // Mental Wellness
    'wellness.card_title': 'Bienestar Mental',
    'wellness.resonance_badge': 'Resonancia 3D',
    'wellness.card_desc': 'Calme su sistema nervioso y refuerce la adherencia al tratamiento con respiración guiada por resonancia 3D.',
    'wellness.start_btn': 'Iniciar Ejercicio de Respiración',
    'wellness.page_title': 'Bienestar Mental y Respiración',
    'wellness.page_subtitle': 'Respiración de resonancia 3D para reducir la ansiedad, mejorar la concentración y reforzar la adherencia al tratamiento.',
    'wellness.press_start': 'Presione Iniciar para Comenzar',
    'wellness.session_complete': 'Sesión Completada',
    'wellness.inhale': 'Inhale Profundamente...',
    'wellness.hold': 'Mantenga la Respiración...',
    'wellness.exhale': 'Exhale Lentamente...',
    'wellness.rest': 'Descanse y Mantenga...',
    'wellness.start_session': 'Iniciar Sesión',
    'wellness.pause': 'Pausar',
    'wellness.resume': 'Reanudar',
    'wellness.reset': 'Reiniciar',
    'wellness.patterns': 'Patrones de Respiración',
    'wellness.custom_pattern': 'Patrón Personalizado',
    'wellness.recent_sessions': 'Sesiones Recientes',
    'wellness.no_sessions': 'Aún no hay sesiones de respiración registradas.',

    // Chat AI
    'chat.title': 'Asistente de IA',
    'chat.subtitle': 'Orientación clínica verificada y apoyo para la adherencia',
    'chat.input_placeholder': 'Pregunte sobre medicamentos, efectos secundarios u horarios...',
    'chat.send': 'Enviar',
    'chat.clear': 'Limpiar',
    'chat.disclaimer': 'Basado en conocimientos clínicos. Consulte siempre a su médico para emergencias.',

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

    // Export
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
  },
  hi: {
    // Navigation
    'nav.dashboard': 'डैशबोर्ड',
    'nav.medicines': 'दवाएं',
    'nav.wellness': 'वेलनेस',
    'nav.chat': 'AI से पूछें',
    'nav.clinical_ai': 'क्लिनिकल AI',
    'nav.feedback': 'प्रतिक्रिया',
    'nav.profile': 'प्रोफ़ाइल',
    'nav.provider': 'डॉक्टर पोर्टल',
    'nav.admin': 'व्यवस्थापक',
    'nav.logout': 'लॉग आउट',
    'nav.language': 'भाषा',

    // Patient Dashboard Header & Alerts
    'dashboard.hello': 'नमस्ते',
    'dashboard.patient': 'रोगी',
    'dashboard.subtitle': 'अपने दैनिक दवा अनुपालन और अंतर्दृष्टि को ट्रैक करें',
    'dashboard.export_data': 'डेटा निर्यात करें',
    'dashboard.exporting': 'निर्यात हो रहा है...',
    'dashboard.adherence_warning_title': 'अनुपालन चेतावनी (< 70%)',
    'dashboard.adherence_warning_msg': 'आपका साप्ताहिक अनुपालन',
    'dashboard.adherence_warning_msg_end': '% है। अपने डॉक्टर की सिफारिशों के अनुसार ट्रैक पर रहने के लिए कृपया अपने दैनिक कार्यक्रम का पालन करें।',

    // Stats
    'stat.overall_adherence': 'समग्र अनुपालन',
    'stat.weekly_rate': 'साप्ताहिक दर',
    'stat.day_streak': 'दैनिक स्ट्रीक',
    'stat.consecutive_days': 'लगातार दिन',
    'stat.keep_it_up': 'जारी रखें!',
    'stat.missed_this_month': 'इस महीने छूटी',
    'stat.doses_missed': 'छूटी हुई खुराक',
    'stat.this_month': 'इस कैलेंडर माह में',
    'stat.due_today': 'आज की देय खुराक',
    'stat.completed': 'पूर्ण',

    // Schedule & Chart
    'schedule.title': 'आज का शेड्यूल',
    'schedule.scheduled_today': 'आज के लिए निर्धारित खुराक',
    'schedule.manage_medicines': 'दवाएं प्रबंधित करें',
    'schedule.all_done': 'आज कोई खुराक लंबित नहीं है!',
    'chart.weekly_adherence': 'साप्ताहिक अनुपालन',
    'chart.weekly_adherence_sub': 'पिछले 7 दिनों में दैनिक पूर्णता दर',
    'chart.monthly_adherence': 'मासिक अनुपालन',
    'chart.low_adherence': 'कम अनुपालन',

    // Buttons
    'btn.taken': 'ले ली',
    'btn.snooze': 'बाद में',
    'btn.missed': 'छूट गई',
    'btn.edit': 'संपादित करें',
    'btn.delete': 'हटाएं',
    'btn.save': 'सहेजें',
    'btn.cancel': 'रद्द करें',
    'btn.add': 'जोड़ें',
    'btn.close': 'बंद करें',
    'btn.search': 'खोजें',
    'btn.loading': 'लोड हो रहा है...',

    // Provider Card
    'provider.care_team_title': 'स्वास्थ्य सेवा प्रदाता',
    'provider.care_team_sub': 'क्लिनिकल देखभाल टीम',
    'provider.connected': 'जुड़ा हुआ',
    'provider.no_provider': 'अभी तक कोई डॉक्टर नियुक्त नहीं किया गया है।',
    'provider.request_provider': 'डॉक्टर का अनुरोध करें',

    // Mental Wellness
    'wellness.card_title': 'मानसिक स्वास्थ्य',
    'wellness.resonance_badge': '3D प्रतिध्वनि',
    'wellness.card_desc': 'निर्देशित 3D प्रतिध्वनि श्वास अभ्यास के साथ घबराहट शांत करें और दवा अनुपालन को सुदृढ़ करें।',
    'wellness.start_btn': 'श्वास व्यायाम शुरू करें',
    'wellness.page_title': 'मानसिक स्वास्थ्य और श्वास',
    'wellness.page_subtitle': 'चिंता कम करने, एकाग्रता बढ़ाने और दवा अनुपालन मजबूत करने के लिए 3D प्रतिध्वनि श्वास।',
    'wellness.press_start': 'शुरू करने के लिए स्टार्ट दबाएं',
    'wellness.session_complete': 'सत्र पूर्ण हुआ',
    'wellness.inhale': 'गहरी सांस अंदर लें...',
    'wellness.hold': 'सांस रोकें...',
    'wellness.exhale': 'धीरे-धीरे सांस छोड़ें...',
    'wellness.rest': 'विश्राम करें और रोकें...',
    'wellness.start_session': 'सत्र शुरू करें',
    'wellness.pause': 'रोकें',
    'wellness.resume': 'पुनः आरंभ करें',
    'wellness.reset': 'रीसेट',
    'wellness.patterns': 'श्वास पैटर्न',
    'wellness.custom_pattern': 'कस्टम पैटर्न',
    'wellness.recent_sessions': 'हाल के सत्र',
    'wellness.no_sessions': 'अभी तक कोई श्वास सत्र दर्ज नहीं हुआ है।',

    // Chat AI
    'chat.title': 'AI सहायक से पूछें',
    'chat.subtitle': 'सत्यापित नैदानिक मार्गदर्शन और अनुपालन सहायता',
    'chat.input_placeholder': 'दवाओं, दुष्प्रभावों या शेड्यूल के बारे में पूछें...',
    'chat.send': 'भेजें',
    'chat.clear': 'साफ़ करें',
    'chat.disclaimer': 'नैदानिक ज्ञान पर आधारित। आपातकालीन स्थिति में हमेशा अपने डॉक्टर से परामर्श लें।',

    // Feedback
    'feedback.title': 'हालिया रिपोर्ट',
    'feedback.view_all': 'सभी देखें',
    'feedback.empty': 'कोई हालिया रिपोर्ट नहीं।',
    'feedback.heading': 'दुष्प्रभाव और प्रतिक्रिया',
    'feedback.subheading': 'चिकित्सा समीक्षा के लिए प्रतिकूल प्रतिक्रियाएं दर्ज करें',
    'feedback.report_new': 'दुष्प्रभाव रिपोर्ट करें',
    'feedback.severity': 'गंभीरता का स्तर',
    'feedback.severity_1': 'हल्का (ग्रेड 1)',
    'feedback.severity_2': 'मध्यम (ग्रेड 2)',
    'feedback.severity_3': 'गंभीर (ग्रेड 3)',
    'feedback.severity_4': 'आपातकालीन / जानलेवा (ग्रेड 4)',

    // Export
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
