'use client'

import Layout from '@/components/Layout'
import Link from 'next/link'
import { Printer, FileSignature, ArrowLeft } from 'lucide-react'

// Central hub for printable forms. Adding a new form = adding one entry here
// (a card), NOT a new top-level navigation tab. Group with `category` so the
// hub stays organised as the catalogue of forms grows.
type FormDef = {
  href: string
  title: string
  subtitle?: string
  description: string
  icon: typeof Printer
  category: string
  ready: boolean
}

const FORMS: FormDef[] = [
  {
    href: '/voucher',
    title: 'Securities / Per-Contra Voucher',
    subtitle: 'سند انتظامی چک ضمانتی',
    description: 'دو سند انتظامی (SECURITIES + PER CONTRA) برای چک‌های ضمانتی؛ با شماره‌حساب، نام و حساب‌های دفتری خودکار پر می‌شود و روی A4 (دو A5) چاپ می‌شود.',
    icon: Printer,
    category: 'Vouchers',
    ready: true,
  },
  {
    href: '/offer-letter',
    title: 'Offer Letter',
    subtitle: 'نامهٔ پیشنهادِ تسهیلات (Credit Facility)',
    description: 'نامهٔ پیشنهادِ اعتباریِ سه‌صفحه‌ای (A4) با سربرگ، جدولِ تسهیلات، مدارکِ تضمینی و ۲۵ شرط؛ داده‌ها تا حدِ ممکن از پروفایلِ حساب پر می‌شوند و دقیقاً مثلِ قالبِ Word چاپ می‌شود.',
    icon: FileSignature,
    category: 'Credit',
    ready: true,
  },
  {
    href: '/credit-file-retail',
    title: 'Credit File Summary (Retail)',
    subtitle: 'خلاصهٔ فایلِ اعتباری (حقیقی)',
    description: 'فرمِ خلاصهٔ فایلِ اعتباری برای مشتریانِ حقیقی؛ شامل اطلاعاتِ حساب، K.Y.C، تسهیلات، ضمانت‌ها و گمانکنندگان برای چاپِ A4.',
    icon: FileSignature,
    category: 'Credit',
    ready: true,
  },
  {
    href: '/credit-file-corporate',
    title: 'Credit File Summary (Corporate)',
    subtitle: 'خلاصهٔ فایلِ اعتباری (حقوقی)',
    description: 'فرمِ خلاصهٔ فایلِ اعتباری برای مشتریانِ حقوقی؛ شامل اطلاعاتِ شرکت، K.Y.C، شرکا، تسهیلات، ضمانت‌ها و اسناد گمانکنندگان برای چاپِ A4.',
    icon: FileSignature,
    category: 'Credit',
    ready: true,
  },
]

export default function FormsPage() {
  const categories = Array.from(new Set(FORMS.map((f) => f.category)))

  return (
    <Layout>
      <div dir="rtl" className="max-w-5xl mx-auto">
        <div className="flex items-center gap-3 mb-1">
          <div className="bg-blue-600 text-white rounded-xl p-2.5"><FileSignature size={22} /></div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">فرم‌ها (Forms)</h1>
            <p className="text-gray-500 text-sm">همهٔ فرم‌های چاپیِ سیستم اینجا جمع‌اند. فرم‌های جدید همین‌جا به‌صورت کارت اضافه می‌شوند — نه به‌صورت تبِ جداگانه.</p>
          </div>
        </div>

        {categories.map((cat) => (
          <div key={cat} className="mt-6">
            <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">{cat}</div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {FORMS.filter((f) => f.category === cat).map((f) => {
                const Icon = f.icon
                return (
                  <Link
                    key={f.href}
                    href={f.href}
                    className="group bg-white border border-gray-200 rounded-xl p-5 hover:border-blue-300 hover:shadow-sm transition-all flex flex-col"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="bg-blue-50 text-blue-600 rounded-lg p-2 group-hover:bg-blue-100 transition-colors">
                        <Icon size={20} />
                      </div>
                      <ArrowLeft size={16} className="text-gray-300 group-hover:text-blue-500" />
                    </div>
                    <div className="font-bold text-gray-900">{f.title}</div>
                    {f.subtitle && <div className="text-sm text-gray-500 mt-0.5">{f.subtitle}</div>}
                    <p className="text-xs text-gray-500 leading-6 mt-2 flex-1">{f.description}</p>
                  </Link>
                )
              })}
            </div>
          </div>
        ))}

        <p className="text-xs text-gray-400 mt-8 text-center">
          فرم‌های بعدی (نامه‌ها، چک‌لیست‌ها، رسیدها و …) به همین مرکز اضافه می‌شوند و در دسته‌بندیِ خود قرار می‌گیرند.
        </p>
      </div>
    </Layout>
  )
}
