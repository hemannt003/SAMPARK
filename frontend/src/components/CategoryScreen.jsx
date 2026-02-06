import { useEffect } from 'react'

const CATEGORIES = [
  {
    id: 'farmer',
    icon: '👨‍🌾',
    label: 'Kisan',
    labelHi: 'किसान',
    color: 'farmer',
    audioText: 'Kisan yojana ke baare mein jaankari'
  },
  {
    id: 'student',
    icon: '🎓',
    label: 'Student',
    labelHi: 'विद्यार्थी',
    color: 'student',
    audioText: 'Chhatra yojana ke baare mein jaankari'
  },
  {
    id: 'woman',
    icon: '👩',
    label: 'Mahila',
    labelHi: 'महिला',
    color: 'woman',
    audioText: 'Mahila yojana ke baare mein jaankari'
  }
]

export default function CategoryScreen({ onSelect, onBack }) {
  
  useEffect(() => {
    // Play category selection audio on mount
    speakText('Aap kis category ke baare mein jaanna chahte hain? Kisan, Student, ya Mahila?')
  }, [])

  const speakText = (text) => {
    // Cancel any ongoing speech
    window.speechSynthesis.cancel()
    
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'hi-IN'
    utterance.rate = 0.85
    window.speechSynthesis.speak(utterance)
  }

  const handleCardClick = (category) => {
    // Play audio feedback
    speakText(category.audioText)
    
    // Wait a bit for audio to start, then proceed
    setTimeout(() => {
      onSelect(category.id)
    }, 800)
  }

  const handleCardHover = (category) => {
    // On touch/hover, speak the category name
    speakText(category.label)
  }

  return (
    <div className="screen category-screen">
      {/* Back button */}
      <button 
        className="back-button"
        onClick={onBack}
        style={{ position: 'absolute', top: '20px', left: '20px' }}
        aria-label="Go back"
      >
        ←
      </button>

      <div className="category-header">Category Chunein</div>
      <div className="category-subheader">Aap kis ke baare mein jaanna chahte hain?</div>

      <div className="category-cards">
        {CATEGORIES.map((category) => (
          <div
            key={category.id}
            className={`category-card ${category.color}`}
            onClick={() => handleCardClick(category)}
            onTouchStart={() => handleCardHover(category)}
            role="button"
            tabIndex={0}
            aria-label={`${category.label} - ${category.labelHi}`}
          >
            <div className="icon">{category.icon}</div>
            <div>
              <div className="label">{category.label}</div>
              <div className="label-hi">{category.labelHi}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
