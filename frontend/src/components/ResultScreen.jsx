import { useState, useEffect, useRef } from 'react'

// Default scheme data (used when API is not available)
const DEFAULT_SCHEMES = {
  farmer: {
    name: 'PM Kisan Samman Nidhi',
    nameHi: 'पीएम किसान सम्मान निधि',
    eligibility: 'Chhote aur seemant kisan jo 2 hectare se kam zameen rakhte hain',
    benefit: '₹6000 har saal, 3 kisht mein ₹2000',
    documents: ['Aadhaar Card', 'Bank Account', 'Zameen ke Kagaz', 'Mobile Number'],
    steps: [
      'PM Kisan website (pmkisan.gov.in) par jao',
      'New Farmer Registration par click karo',
      'Apna Aadhaar number daalo',
      'Bank details bharo',
      'Zameen ki jaankari do',
      'Submit karo'
    ]
  },
  student: {
    name: 'PM Vidyalakshmi Yojana',
    nameHi: 'पीएम विद्यालक्ष्मी योजना',
    eligibility: 'Jo students higher education ke liye loan chahte hain',
    benefit: 'Education loan easy process se, kam interest rate',
    documents: ['Aadhaar Card', 'Admission Letter', 'Marksheet', 'Income Proof', 'Bank Account'],
    steps: [
      'Vidyalakshmi Portal (vidyalakshmi.co.in) par jao',
      'Register karo apni details se',
      'College aur course select karo',
      'Loan amount daalo',
      'Documents upload karo',
      'Bank chunke apply karo'
    ]
  },
  woman: {
    name: 'Pradhan Mantri Ujjwala Yojana',
    nameHi: 'प्रधानमंत्री उज्ज्वला योजना',
    eligibility: 'BPL parivar ki mahilayen, 18 saal se upar',
    benefit: 'Free LPG connection, ₹1600 ki subsidy',
    documents: ['Aadhaar Card', 'BPL Ration Card', 'Bank Account', 'Passport Photo'],
    steps: [
      'Nazdeeki LPG distributor ke paas jao',
      'Ujjwala form bharke do',
      'Documents ki copy attach karo',
      'KYC complete karo',
      'Connection 7 din mein mil jayega'
    ]
  }
}

export default function ResultScreen({ category, scheme, audioUrl, onBack }) {
  const [isPlaying, setIsPlaying] = useState(false)
  const audioRef = useRef(null)
  const speechRef = useRef(null)

  // Use provided scheme or default
  const schemeData = scheme || DEFAULT_SCHEMES[category] || DEFAULT_SCHEMES.farmer

  useEffect(() => {
    // Auto-play explanation when screen loads
    playExplanation()
    
    return () => {
      // Cleanup
      window.speechSynthesis.cancel()
      if (audioRef.current) {
        audioRef.current.pause()
      }
    }
  }, [])

  const playExplanation = () => {
    // If we have an audio URL from Polly, use it
    if (audioUrl) {
      playAudioFile(audioUrl)
      return
    }

    // Otherwise use Web Speech API
    playWithSpeechSynthesis()
  }

  const playAudioFile = (url) => {
    setIsPlaying(true)
    const audio = new Audio(url)
    audioRef.current = audio
    
    audio.onended = () => setIsPlaying(false)
    audio.onerror = () => {
      setIsPlaying(false)
      // Fallback to speech synthesis
      playWithSpeechSynthesis()
    }
    
    audio.play()
  }

  const playWithSpeechSynthesis = () => {
    window.speechSynthesis.cancel()
    setIsPlaying(true)

    const explanation = generateExplanationText()
    const utterance = new SpeechSynthesisUtterance(explanation)
    utterance.lang = 'hi-IN'
    utterance.rate = 0.8
    
    utterance.onend = () => setIsPlaying(false)
    utterance.onerror = () => setIsPlaying(false)
    
    speechRef.current = utterance
    window.speechSynthesis.speak(utterance)
  }

  const generateExplanationText = () => {
    return `
      Yeh hai ${schemeData.name}.
      Is yojana mein aapko milega: ${schemeData.benefit}.
      Kaun apply kar sakta hai: ${schemeData.eligibility}.
      Documents chahiye: ${schemeData.documents.join(', ')}.
      Apply karne ke steps hain:
      ${schemeData.steps.map((step, i) => `${i + 1}. ${step}`).join('. ')}
    `
  }

  const toggleAudio = () => {
    if (isPlaying) {
      window.speechSynthesis.cancel()
      if (audioRef.current) {
        audioRef.current.pause()
      }
      setIsPlaying(false)
    } else {
      playExplanation()
    }
  }

  const openHelpCenter = () => {
    // In production, this would open Google Maps or show nearby CSC centers
    const utterance = new SpeechSynthesisUtterance(
      'Nazdeeki Jan Seva Kendra ke liye Google Maps khul raha hai'
    )
    utterance.lang = 'hi-IN'
    window.speechSynthesis.speak(utterance)
    
    // Open Google Maps search for CSC centers
    setTimeout(() => {
      window.open(
        'https://www.google.com/maps/search/Jan+Seva+Kendra+near+me',
        '_blank'
      )
    }, 1500)
  }

  return (
    <div className="screen result-screen">
      {/* Header */}
      <div className="result-header">
        <button className="back-button" onClick={onBack} aria-label="Go back">
          ←
        </button>
        <div className="scheme-title">{schemeData.name}</div>
      </div>

      {/* Play Audio Button */}
      <button 
        className={`play-audio-button ${isPlaying ? 'playing' : ''}`}
        onClick={toggleAudio}
        aria-label={isPlaying ? 'Stop audio' : 'Play explanation'}
      >
        <span className="icon">{isPlaying ? '⏸️' : '🔊'}</span>
        <span className="text">
          {isPlaying ? 'Roko' : 'Sunein'}
        </span>
      </button>

      {/* Eligibility Section */}
      <div className="info-section eligibility">
        <div className="section-header">
          <div className="section-icon">✅</div>
          <div className="section-title">Kaun Apply Kar Sakta Hai</div>
        </div>
        <div className="content">{schemeData.eligibility}</div>
      </div>

      {/* Benefit Section */}
      <div className="info-section eligibility">
        <div className="section-header">
          <div className="section-icon">🎁</div>
          <div className="section-title">Kya Milega</div>
        </div>
        <div className="content" style={{ fontSize: '1.3rem', fontWeight: '600', color: '#2E7D32' }}>
          {schemeData.benefit}
        </div>
      </div>

      {/* Documents Section */}
      <div className="info-section documents">
        <div className="section-header">
          <div className="section-icon">📄</div>
          <div className="section-title">Documents Chahiye</div>
        </div>
        <div className="content">
          <ul>
            {schemeData.documents.map((doc, index) => (
              <li key={index}>{doc}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Steps Section */}
      <div className="info-section steps">
        <div className="section-header">
          <div className="section-icon">📝</div>
          <div className="section-title">Kaise Apply Karein</div>
        </div>
        <div className="content">
          <ul>
            {schemeData.steps.map((step, index) => (
              <li key={index} data-step={index + 1} style={{ paddingLeft: '40px' }}>
                {step}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Help Center Button */}
      <button className="help-button" onClick={openHelpCenter}>
        <span className="icon">📍</span>
        <span className="text">Nazdeeki Help Center</span>
      </button>
    </div>
  )
}
