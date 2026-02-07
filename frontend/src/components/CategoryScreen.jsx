import { useEffect } from 'react'
import { useLanguage } from '../context/LanguageContext'

const CATEGORIES = [
  {
    id: 'farmer',
    icon: '👨‍🌾',
    labelKey: 'farmer',
    descKey: 'farmerDesc',
    color: 'farmer',
  },
  {
    id: 'student',
    icon: '🎓',
    labelKey: 'student',
    descKey: 'studentDesc',
    color: 'student',
  },
  {
    id: 'woman',
    icon: '👩',
    labelKey: 'woman',
    descKey: 'womanDesc',
    color: 'woman',
  },
]

export default function CategoryScreen({ onSelect, onBack }) {
  const { lang, t } = useLanguage()

  useEffect(() => {
    const text =
      lang === 'hi'
        ? 'आप किसके बारे में जानना चाहते हैं? किसान, विद्यार्थी, या महिला?'
        : 'What would you like to know about? Farmer, Student, or Woman?'
    speakText(text)
  }, [lang])

  const speakText = (text) => {
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
    utterance.rate = 0.85
    window.speechSynthesis.speak(utterance)
  }

  const handleCardClick = (category) => {
    const feedback =
      lang === 'hi'
        ? `${t(category.labelKey)} योजनाओं की जानकारी ला रहे हैं`
        : `Fetching ${t(category.labelKey)} scheme information`
    speakText(feedback)

    setTimeout(() => {
      onSelect(category.id)
    }, 800)
  }

  return (
    <div className="screen category-screen">
      {/* Back button */}
      <button
        className="back-button"
        onClick={onBack}
        style={{ position: 'absolute', top: '20px', left: '20px' }}
        aria-label={t('back')}
      >
        ←
      </button>

      <div className="category-header">{t('chooseCategory')}</div>
      <div className="category-subheader">{t('chooseCategorySub')}</div>

      <div className="category-cards">
        {CATEGORIES.map((category) => (
          <div
            key={category.id}
            className={`category-card ${category.color}`}
            onClick={() => handleCardClick(category)}
            role="button"
            tabIndex={0}
            aria-label={t(category.labelKey)}
          >
            <div className="icon">{category.icon}</div>
            <div>
              <div className="label">{t(category.labelKey)}</div>
              <div className="label-hi">{t(category.descKey)}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
