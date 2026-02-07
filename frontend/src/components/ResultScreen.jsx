import { useState, useEffect, useRef } from 'react'
import { useLanguage } from '../context/LanguageContext'
import StepGuide from './StepGuide'

// Default scheme data — pure Hindi and English
const DEFAULT_SCHEMES = {
  farmer: {
    name: { hi: 'पीएम किसान सम्मान निधि', en: 'PM Kisan Samman Nidhi' },
    eligibility: {
      hi: 'छोटे एवं सीमांत किसान जिनके पास 2 हेक्टेयर से कम भूमि है',
      en: 'Small and marginal farmers with less than 2 hectares of land',
    },
    benefit: {
      hi: 'प्रति वर्ष ₹6,000 — तीन किस्तों में ₹2,000',
      en: '₹6,000 per year — ₹2,000 in three instalments',
    },
    documents: {
      hi: ['आधार कार्ड', 'बैंक खाता पासबुक', 'भूमि के कागज़ात', 'मोबाइल नंबर'],
      en: ['Aadhaar Card', 'Bank Account Passbook', 'Land Records', 'Mobile Number'],
    },
    steps: {
      hi: [
        { title: 'पीएम किसान की वेबसाइट खोलें', description: 'नीचे दिए गए लिंक पर क्लिक करें।', link: 'https://pmkisan.gov.in', linkLabel: 'pmkisan.gov.in खोलें', action: 'link' },
        { title: '"New Farmer Registration" पर क्लिक करें', description: 'दाईं ओर "New Farmer Registration" बटन पर क्लिक करें।', action: 'click' },
        { title: 'अपना आधार नंबर भरें', description: 'आधार नंबर वाले खाने में अपना 12 अंकों का आधार नंबर भरें।', inputLabel: 'आधार नंबर', inputPlaceholder: 'उदाहरण: 1234 5678 9012', action: 'fill' },
        { title: 'बैंक खाते की जानकारी भरें', description: 'अपना बैंक खाता नंबर और IFSC कोड भरें।', action: 'fill' },
        { title: 'भूमि की जानकारी भरें', description: 'अपनी ज़मीन का खसरा/खतौनी नंबर और क्षेत्रफल भरें।', action: 'fill' },
        { title: 'फ़ॉर्म जमा करें', description: '"Submit" बटन पर क्लिक करें।', action: 'submit' },
      ],
      en: [
        { title: 'Open PM Kisan website', description: 'Click the link below.', link: 'https://pmkisan.gov.in', linkLabel: 'Open pmkisan.gov.in', action: 'link' },
        { title: 'Click "New Farmer Registration"', description: 'Click the "New Farmer Registration" button on the right.', action: 'click' },
        { title: 'Enter your Aadhaar number', description: 'Type your 12-digit Aadhaar number.', inputLabel: 'Aadhaar Number', inputPlaceholder: 'Example: 1234 5678 9012', action: 'fill' },
        { title: 'Fill bank details', description: 'Enter your bank account number and IFSC code.', action: 'fill' },
        { title: 'Enter land details', description: 'Fill your Khasra/Khatauni number and area.', action: 'fill' },
        { title: 'Submit the form', description: 'Click the "Submit" button.', action: 'submit' },
      ],
    },
    govWebsite: 'https://pmkisan.gov.in',
    helpline: '155261',
  },
  student: {
    name: { hi: 'पीएम विद्यालक्ष्मी योजना', en: 'PM Vidyalakshmi Yojana' },
    eligibility: {
      hi: 'उच्च शिक्षा के लिए ऋण की आवश्यकता वाले विद्यार्थी',
      en: 'Students who need loans for higher education',
    },
    benefit: {
      hi: 'आसान प्रक्रिया से शिक्षा ऋण, कम ब्याज दर पर',
      en: 'Education loan through simple process at low interest rates',
    },
    documents: {
      hi: ['आधार कार्ड', 'प्रवेश पत्र', 'अंकतालिका', 'आय प्रमाण पत्र', 'बैंक खाता'],
      en: ['Aadhaar Card', 'Admission Letter', 'Marksheet', 'Income Certificate', 'Bank Account'],
    },
    steps: {
      hi: [
        { title: 'विद्यालक्ष्मी पोर्टल खोलें', description: 'नीचे दिए गए लिंक पर क्लिक करें।', link: 'https://www.vidyalakshmi.co.in', linkLabel: 'vidyalakshmi.co.in खोलें', action: 'link' },
        { title: 'नया खाता बनाएँ', description: '"Register" बटन पर क्लिक करें।', action: 'fill' },
        { title: 'कॉलेज और पाठ्यक्रम चुनें', description: 'सूची में से अपना कॉलेज खोजें।', action: 'click' },
        { title: 'ऋण की राशि भरें', description: 'आवश्यक ऋण राशि भरें।', inputLabel: 'ऋण राशि (₹)', inputPlaceholder: 'उदाहरण: 500000', action: 'fill' },
        { title: 'दस्तावेज़ अपलोड करें', description: 'अंकतालिका, प्रवेश पत्र की स्कैन कॉपी अपलोड करें।', action: 'fill' },
        { title: 'बैंक चुनें और आवेदन करें', description: 'बैंक चुनें और "Apply" पर क्लिक करें।', action: 'submit' },
      ],
      en: [
        { title: 'Open Vidyalakshmi Portal', description: 'Click the link below.', link: 'https://www.vidyalakshmi.co.in', linkLabel: 'Open vidyalakshmi.co.in', action: 'link' },
        { title: 'Create a new account', description: 'Click the "Register" button.', action: 'fill' },
        { title: 'Select college and course', description: 'Search for your college from the list.', action: 'click' },
        { title: 'Enter loan amount', description: 'Enter the loan amount you need.', inputLabel: 'Loan Amount (₹)', inputPlaceholder: 'Example: 500000', action: 'fill' },
        { title: 'Upload documents', description: 'Upload scanned copies of your marksheet and admission letter.', action: 'fill' },
        { title: 'Select bank and apply', description: 'Choose the bank and click "Apply".', action: 'submit' },
      ],
    },
    govWebsite: 'https://www.vidyalakshmi.co.in',
    helpline: '1800-180-2005',
  },
  woman: {
    name: { hi: 'प्रधानमंत्री उज्ज्वला योजना', en: 'Pradhan Mantri Ujjwala Yojana' },
    eligibility: {
      hi: 'बीपीएल परिवार की 18 वर्ष से अधिक आयु की महिलाएँ',
      en: 'Women above 18 years of age from BPL families',
    },
    benefit: {
      hi: 'निःशुल्क एलपीजी कनेक्शन, ₹1,600 की सब्सिडी',
      en: 'Free LPG connection with ₹1,600 subsidy',
    },
    documents: {
      hi: ['आधार कार्ड', 'बीपीएल राशन कार्ड', 'बैंक खाता पासबुक', 'पासपोर्ट साइज़ फ़ोटो'],
      en: ['Aadhaar Card', 'BPL Ration Card', 'Bank Account Passbook', 'Passport Size Photo'],
    },
    steps: {
      hi: [
        { title: 'नज़दीकी एलपीजी वितरक के पास जाएँ', description: 'इंडेन, भारत गैस या एचपी गैस वितरक पर जाएँ।', link: 'https://www.pmujjwalayojana.com', linkLabel: 'योजना की वेबसाइट खोलें', action: 'link' },
        { title: 'उज्ज्वला योजना का फ़ॉर्म लें', description: 'वितरक से आवेदन फ़ॉर्म माँगें।', action: 'click' },
        { title: 'फ़ॉर्म में जानकारी भरें', description: 'नाम, पता, आधार नंबर और बैंक खाता नंबर भरें।', inputLabel: 'आधार नंबर', inputPlaceholder: 'उदाहरण: 1234 5678 9012', action: 'fill' },
        { title: 'दस्तावेज़ संलग्न करें', description: 'आधार, राशन कार्ड, पासबुक की फ़ोटोकॉपी जमा करें।', action: 'fill' },
        { title: 'केवाईसी पूर्ण करें', description: 'वितरक पहचान सत्यापित करेगा। मूल आधार साथ रखें।', action: 'submit' },
        { title: 'कनेक्शन प्राप्त करें', description: '7 दिनों के भीतर एलपीजी कनेक्शन मिल जाएगा।', action: 'info' },
      ],
      en: [
        { title: 'Visit nearest LPG distributor', description: 'Go to Indane, Bharat Gas, or HP Gas distributor.', link: 'https://www.pmujjwalayojana.com', linkLabel: 'Open scheme website', action: 'link' },
        { title: 'Get the Ujjwala Yojana form', description: 'Ask the distributor for the application form.', action: 'click' },
        { title: 'Fill in your details', description: 'Enter name, address, Aadhaar number, and bank account.', inputLabel: 'Aadhaar Number', inputPlaceholder: 'Example: 1234 5678 9012', action: 'fill' },
        { title: 'Attach document copies', description: 'Submit photocopies of Aadhaar, ration card, and passbook.', action: 'fill' },
        { title: 'Complete KYC verification', description: 'The distributor will verify your identity.', action: 'submit' },
        { title: 'Receive your connection', description: 'You will receive the LPG connection within 7 days.', action: 'info' },
      ],
    },
    govWebsite: 'https://www.pmujjwalayojana.com',
    helpline: '1906',
  },
}

export default function ResultScreen({ category, scheme, audioUrl, onBack }) {
  const { lang, t } = useLanguage()
  const [isPlaying, setIsPlaying] = useState(false)
  const [showStepGuide, setShowStepGuide] = useState(false)
  const audioRef = useRef(null)
  const speechRef = useRef(null)

  // Use provided scheme or default
  const schemeData = scheme || DEFAULT_SCHEMES[category] || DEFAULT_SCHEMES.farmer

  // Helper to get localised value
  const localize = (field) => {
    if (!field) return ''
    if (typeof field === 'string') return field
    return field[lang] || field['en'] || ''
  }

  const localizeArray = (field) => {
    if (!field) return []
    if (Array.isArray(field)) return field
    return field[lang] || field['en'] || []
  }

  useEffect(() => {
    playExplanation()
    return () => {
      window.speechSynthesis.cancel()
      if (audioRef.current) audioRef.current.pause()
    }
  }, [])

  const playExplanation = () => {
    if (audioUrl) {
      playAudioFile(audioUrl)
      return
    }
    playWithSpeechSynthesis()
  }

  const playAudioFile = (url) => {
    setIsPlaying(true)
    const audio = new Audio(url)
    audioRef.current = audio
    audio.onended = () => setIsPlaying(false)
    audio.onerror = () => {
      setIsPlaying(false)
      playWithSpeechSynthesis()
    }
    audio.play()
  }

  const playWithSpeechSynthesis = () => {
    window.speechSynthesis.cancel()
    setIsPlaying(true)

    const explanation = generateExplanationText()
    const utterance = new SpeechSynthesisUtterance(explanation)
    utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
    utterance.rate = 0.8

    utterance.onend = () => setIsPlaying(false)
    utterance.onerror = () => setIsPlaying(false)

    speechRef.current = utterance
    window.speechSynthesis.speak(utterance)
  }

  const generateExplanationText = () => {
    const name = localize(schemeData.name)
    const benefit = localize(schemeData.benefit)
    const eligibility = localize(schemeData.eligibility)
    const docs = localizeArray(schemeData.documents).join(', ')

    if (lang === 'hi') {
      return `यह है ${name}। इस योजना में आपको मिलेगा: ${benefit}। कौन आवेदन कर सकता है: ${eligibility}। आवश्यक दस्तावेज़: ${docs}।`
    }
    return `This is ${name}. You will get: ${benefit}. Who can apply: ${eligibility}. Documents required: ${docs}.`
  }

  const toggleAudio = () => {
    if (isPlaying) {
      window.speechSynthesis.cancel()
      if (audioRef.current) audioRef.current.pause()
      setIsPlaying(false)
    } else {
      playExplanation()
    }
  }

  const openHelpCenter = () => {
    const text =
      lang === 'hi'
        ? 'नज़दीकी जन सेवा केंद्र खोज रहे हैं'
        : 'Searching for nearest Jan Seva Kendra'
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
    window.speechSynthesis.speak(utterance)

    setTimeout(() => {
      window.open('https://www.google.com/maps/search/Jan+Seva+Kendra+near+me', '_blank')
    }, 1500)
  }

  if (showStepGuide) {
    return (
      <StepGuide
        steps={localizeArray(schemeData.steps)}
        schemeName={localize(schemeData.name)}
        govWebsite={schemeData.govWebsite}
        onBack={() => setShowStepGuide(false)}
      />
    )
  }

  return (
    <div className="screen result-screen">
      {/* Header */}
      <div className="result-header">
        <button className="back-button" onClick={onBack} aria-label={t('back')}>
          ←
        </button>
        <div className="scheme-title">{localize(schemeData.name)}</div>
      </div>

      {/* Play Audio Button */}
      <button
        className={`play-audio-button ${isPlaying ? 'playing' : ''}`}
        onClick={toggleAudio}
        aria-label={isPlaying ? t('stopAudio') : t('listenExplanation')}
      >
        <span className="icon">{isPlaying ? '⏸️' : '🔊'}</span>
        <span className="text">{isPlaying ? t('stopAudio') : t('listenExplanation')}</span>
      </button>

      {/* Eligibility */}
      <div className="info-section eligibility">
        <div className="section-header">
          <div className="section-icon">✅</div>
          <div className="section-title">{t('eligibility')}</div>
        </div>
        <div className="content">{localize(schemeData.eligibility)}</div>
      </div>

      {/* Benefit */}
      <div className="info-section eligibility">
        <div className="section-header">
          <div className="section-icon">🎁</div>
          <div className="section-title">{t('benefits')}</div>
        </div>
        <div className="content" style={{ fontSize: '1.3rem', fontWeight: '600', color: '#2E7D32' }}>
          {localize(schemeData.benefit)}
        </div>
      </div>

      {/* Documents */}
      <div className="info-section documents">
        <div className="section-header">
          <div className="section-icon">📄</div>
          <div className="section-title">{t('documentsNeeded')}</div>
        </div>
        <div className="content">
          <ul>
            {localizeArray(schemeData.documents).map((doc, index) => (
              <li key={index}>{doc}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Government Website Link */}
      {schemeData.govWebsite && (
        <a
          href={schemeData.govWebsite}
          target="_blank"
          rel="noopener noreferrer"
          className="gov-website-link"
        >
          <span className="icon">🌐</span>
          <span className="text">{t('govWebsite')}: {schemeData.govWebsite}</span>
        </a>
      )}

      {/* Step-by-Step Guide button */}
      <button className="step-guide-button" onClick={() => setShowStepGuide(true)}>
        <span className="icon">📝</span>
        <span className="text">{t('howToApply')} — {t('stepGuideTitle')}</span>
      </button>

      {/* Eligibility Check */}
      <button className="eligibility-check-button" onClick={() => {
        const text = lang === 'hi'
          ? `हाँ, ${localize(schemeData.name)} योजना उपलब्ध है। ${localize(schemeData.eligibility)}।`
          : `Yes, ${localize(schemeData.name)} scheme is available. ${localize(schemeData.eligibility)}.`
        const utterance = new SpeechSynthesisUtterance(text)
        utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
        utterance.rate = 0.85
        window.speechSynthesis.speak(utterance)
      }}>
        <span className="icon">🔍</span>
        <span className="text">{t('checkEligibility')}</span>
      </button>

      {/* Help Center Button */}
      <button className="help-button" onClick={openHelpCenter}>
        <span className="icon">📍</span>
        <span className="text">{t('nearestHelpCenter')}</span>
      </button>
    </div>
  )
}
