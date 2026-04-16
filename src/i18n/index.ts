import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  ar: {
    translation: {
      app_title: "نيكستاسك — إدارة المرافق",
      login: "تسجيل الدخول",
      email: "البريد الإلكتروني",
      password: "كلمة المرور",
      logout: "خروج",
      dashboard: "لوحة التحكم",
      work_orders: "أوامر العمل",
      invoices: "الفواتير",
      welcome: "مرحباً",
      open_work_orders: "أوامر مفتوحة",
      language: "اللغة",
      save_report: "حفظ التقرير",
      submit_report: "إرسال التقرير",
      approve: "اعتماد",
      generate_invoice: "إنشاء فاتورة",
      status: "الحالة",
      title: "العنوان",
      no_report: "لم يبدأ التقرير بعد",
    },
  },
  en: {
    translation: {
      app_title: "NexTask FMS",
      login: "Sign in",
      email: "Email",
      password: "Password",
      logout: "Log out",
      dashboard: "Dashboard",
      work_orders: "Work orders",
      invoices: "Invoices",
      welcome: "Welcome",
      open_work_orders: "Open work orders",
      language: "Language",
      save_report: "Save report",
      submit_report: "Submit report",
      approve: "Approve",
      generate_invoice: "Generate invoice",
      status: "Status",
      title: "Title",
      no_report: "Report not started",
    },
  },
};

void i18n.use(initReactI18next).init({
  resources,
  lng: "ar",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;
