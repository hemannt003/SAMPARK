import { createContext, useContext, useState } from 'react'

const LanguageContext = createContext()

// All translations — pure Hindi (Devanagari) or pure English. No Hinglish.
const translations = {
  hi: {
    // App-level
    appName: 'समpark AI',
    tagline: 'सरकारी योजनाओं की जानकारी आपकी भाषा में',
    loading: 'जानकारी ला रहे हैं...',
    error: 'कुछ गड़बड़ हो गई। कृपया दोबारा कोशिश करें।',
    
    // Language toggle
    langToggle: 'English',
    
    // Start screen
    welcome: 'नमस्ते!',
    welcomeSub: 'मैं समpark AI हूँ — आपका सरकारी योजना सहायक',
    tapToSpeak: 'बोलने के लिए माइक दबाएँ',
    listening: 'सुन रहा हूँ... बोलिए',
    thinking: 'समझ रहा हूँ...',
    youSaid: 'आपने कहा:',
    noSpeechDetected: 'कुछ सुनाई नहीं दिया। कृपया दोबारा बोलें।',
    micPermission: 'कृपया माइक की अनुमति दें',
    tryAgain: 'कृपया दोबारा बोलें',
    micNotFound: 'माइक नहीं मिला',
    browseCategories: 'श्रेणी से चुनें',
    askAnything: 'कुछ भी पूछें — जैसे "क्या मेरे लिए कोई योजना है?"',
    
    // Voice assistant
    assistantHint: 'मुझसे कुछ भी पूछें',
    exampleQueries: [
      '"क्या किसानों के लिए कोई योजना है?"',
      '"मुझे छात्रवृत्ति चाहिए"',
      '"महिलाओं के लिए क्या सुविधाएँ हैं?"',
    ],
    
    // Category screen
    chooseCategory: 'श्रेणी चुनें',
    chooseCategorySub: 'आप किसके बारे में जानना चाहते हैं?',
    farmer: 'किसान',
    farmerDesc: 'कृषि और किसान योजनाएँ',
    student: 'विद्यार्थी',
    studentDesc: 'छात्रवृत्ति और शिक्षा योजनाएँ',
    woman: 'महिला',
    womanDesc: 'महिला सशक्तिकरण योजनाएँ',
    
    // Result screen
    listenExplanation: 'सुनें',
    stopAudio: 'रुकें',
    eligibility: 'कौन आवेदन कर सकता है',
    benefits: 'क्या मिलेगा',
    documentsNeeded: 'ज़रूरी दस्तावेज़',
    howToApply: 'आवेदन कैसे करें',
    nearestHelpCenter: 'नज़दीकी सहायता केंद्र',
    
    // Step guide
    stepGuideTitle: 'चरण-दर-चरण मार्गदर्शिका',
    stepGuideDesc: 'नीचे दिए गए चरणों का पालन करें। हर चरण पूरा करने पर उसे चिह्नित करें।',
    clickThisLink: 'इस लिंक पर क्लिक करें',
    fillHere: 'यहाँ भरें',
    markDone: 'पूरा हुआ',
    completed: 'पूर्ण',
    inProgress: 'जारी',
    notStarted: 'शेष',
    nextStep: 'अगला चरण',
    prevStep: 'पिछला चरण',
    needHelp: 'इस चरण में सहायता चाहिए?',
    progressLabel: 'प्रगति',
    
    // Scheme analysis
    checkEligibility: 'क्या यह योजना मेरे लिए है?',
    eligibilityResult: 'पात्रता जाँच परिणाम',
    youAreEligible: 'हाँ, आप इस योजना के लिए पात्र हैं!',
    youMayBeEligible: 'आप पात्र हो सकते हैं। कृपया नज़दीकी केंद्र पर जाँच करवाएँ।',
    schemeAvailable: 'यह योजना उपलब्ध है',
    govWebsite: 'सरकारी वेबसाइट',
    
    // Back
    back: 'वापस',
  },
  en: {
    // App-level
    appName: 'Sampark AI',
    tagline: 'Government scheme information in your language',
    loading: 'Fetching information...',
    error: 'Something went wrong. Please try again.',
    
    // Language toggle
    langToggle: 'हिन्दी',
    
    // Start screen
    welcome: 'Hello!',
    welcomeSub: 'I am Sampark AI — your government scheme assistant',
    tapToSpeak: 'Tap the mic to speak',
    listening: 'Listening... please speak',
    thinking: 'Understanding...',
    youSaid: 'You said:',
    noSpeechDetected: 'Could not hear anything. Please try again.',
    micPermission: 'Please allow microphone access',
    tryAgain: 'Please speak again',
    micNotFound: 'Microphone not found',
    browseCategories: 'Browse by category',
    askAnything: 'Ask anything — like "Is there a scheme for me?"',
    
    // Voice assistant
    assistantHint: 'Ask me anything',
    exampleQueries: [
      '"Are there any schemes for farmers?"',
      '"I need a scholarship"',
      '"What benefits are available for women?"',
    ],
    
    // Category screen
    chooseCategory: 'Choose a Category',
    chooseCategorySub: 'What would you like to know about?',
    farmer: 'Farmer',
    farmerDesc: 'Agriculture and farmer schemes',
    student: 'Student',
    studentDesc: 'Scholarships and education schemes',
    woman: 'Woman',
    womanDesc: 'Women empowerment schemes',
    
    // Result screen
    listenExplanation: 'Listen',
    stopAudio: 'Stop',
    eligibility: 'Who Can Apply',
    benefits: 'What You Get',
    documentsNeeded: 'Documents Required',
    howToApply: 'How to Apply',
    nearestHelpCenter: 'Nearest Help Centre',
    
    // Step guide
    stepGuideTitle: 'Step-by-Step Guide',
    stepGuideDesc: 'Follow the steps below. Mark each step as done when you complete it.',
    clickThisLink: 'Click this link',
    fillHere: 'Fill here',
    markDone: 'Mark as done',
    completed: 'Done',
    inProgress: 'In Progress',
    notStarted: 'Pending',
    nextStep: 'Next Step',
    prevStep: 'Previous Step',
    needHelp: 'Need help with this step?',
    progressLabel: 'Progress',
    
    // Scheme analysis
    checkEligibility: 'Is this scheme for me?',
    eligibilityResult: 'Eligibility Check Result',
    youAreEligible: 'Yes, you are eligible for this scheme!',
    youMayBeEligible: 'You may be eligible. Please verify at the nearest centre.',
    schemeAvailable: 'This scheme is available',
    govWebsite: 'Government Website',
    
    // Back
    back: 'Back',
  }
}

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState('hi') // Default Hindi

  const t = (key) => {
    return translations[lang]?.[key] || translations['en']?.[key] || key
  }

  const toggleLanguage = () => {
    setLang((prev) => (prev === 'hi' ? 'en' : 'hi'))
  }

  return (
    <LanguageContext.Provider value={{ lang, setLang, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}
