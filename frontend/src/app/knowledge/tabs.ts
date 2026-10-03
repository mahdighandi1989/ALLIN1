import type { Section } from './content'
import { SECTIONS } from './content'
import { UAE_SECTIONS } from './content-uae'
import { INTL_SECTIONS } from './content-intl'
import { IRAN_SECTIONS } from './content-iran'
import { ISLAMIC_SECTIONS } from './content-islamic'

export type TabId = 'saderat' | 'uae' | 'intl' | 'iran' | 'islamic' | 'compare'

export interface KbTab {
  id: TabId
  label: string
  description: string
  /** مالک = فقط مالک ویرایش می‌کند؛ ناظر = ناظرِ دوره‌ای هر دور به‌روز می‌کند */
  maintainer: 'owner' | 'supervisor'
  sections: Section[]
}

export const KB_TABS: KbTab[] = [
  {
    id: 'saderat',
    label: 'بانک صادرات',
    description: 'آموزش‌ها و رویه‌های داخلی بانک صادرات ایران — سرپرستی امارات',
    maintainer: 'owner',
    sections: SECTIONS,
  },
  {
    id: 'uae',
    label: 'بانکداری امارات',
    description: 'دستورات، قوانین، مقررات بانک مرکزی امارات و آموزش‌های بانکی',
    maintainer: 'supervisor',
    sections: UAE_SECTIONS,
  },
  {
    id: 'intl',
    label: 'بانکداری بین‌المللی',
    description: 'مقررات جهانی و آموزش بانکداری بین‌الملل (بازل، ICC، FATF، SWIFT)',
    maintainer: 'supervisor',
    sections: INTL_SECTIONS,
  },
  {
    id: 'iran',
    label: 'بانکداری ایران',
    description: 'قوانین، مقررات و آموزش‌های بانکداری در ایران',
    maintainer: 'supervisor',
    sections: IRAN_SECTIONS,
  },
  {
    id: 'islamic',
    label: 'بانکداری اسلامی',
    description: 'آموزش، قوانین و مقررات بانکداری اسلامی بر مبنای فقه شیعهٔ دوازده‌امامی',
    maintainer: 'supervisor',
    sections: ISLAMIC_SECTIONS,
  },
  {
    id: 'compare',
    label: 'تطبیق',
    description: 'مقایسه و تطبیق مطالب همهٔ تب‌ها — تأیید، رد یا نیازمند بررسی',
    maintainer: 'supervisor',
    sections: [],
  },
]
