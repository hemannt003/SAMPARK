// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://your-api-gateway-url.execute-api.ap-south-1.amazonaws.com/prod'

// Default schemes for offline/demo mode
const DEFAULT_SCHEMES = {
  farmer: {
    scheme_id: 'PM_KISAN',
    name: 'PM Kisan Samman Nidhi',
    nameHi: 'पीएम किसान सम्मान निधि',
    category: 'farmer',
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
    scheme_id: 'PM_VIDYALAKSHMI',
    name: 'PM Vidyalakshmi Yojana',
    nameHi: 'पीएम विद्यालक्ष्मी योजना',
    category: 'student',
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
    scheme_id: 'PM_UJJWALA',
    name: 'Pradhan Mantri Ujjwala Yojana',
    nameHi: 'प्रधानमंत्री उज्ज्वला योजना',
    category: 'woman',
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

// Category detection from transcript
function detectCategory(transcript) {
  const text = transcript.toLowerCase()
  
  // Farmer keywords
  if (text.includes('kisan') || text.includes('kheti') || text.includes('farmer') || 
      text.includes('zameen') || text.includes('fasal') || text.includes('krishi')) {
    return 'farmer'
  }
  
  // Student keywords
  if (text.includes('student') || text.includes('padhai') || text.includes('vidya') ||
      text.includes('school') || text.includes('college') || text.includes('education') ||
      text.includes('scholarship') || text.includes('loan')) {
    return 'student'
  }
  
  // Woman keywords
  if (text.includes('mahila') || text.includes('woman') || text.includes('aurat') ||
      text.includes('mata') || text.includes('beti') || text.includes('ladki') ||
      text.includes('ujjwala') || text.includes('gas')) {
    return 'woman'
  }
  
  // Default to farmer if no clear match
  return 'farmer'
}

// Process voice query - calls backend API
export async function processVoiceQuery(transcript) {
  try {
    // Try to call the actual API
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ transcript }),
    })

    if (!response.ok) {
      throw new Error('API request failed')
    }

    const data = await response.json()
    return {
      category: data.category,
      scheme: data.scheme,
      audioUrl: data.audioUrl,
    }
  } catch (error) {
    console.log('API unavailable, using demo mode:', error.message)
    
    // Fallback to local processing for demo
    return processQueryLocally(transcript)
  }
}

// Local processing for demo/offline mode
function processQueryLocally(transcript) {
  const category = detectCategory(transcript)
  const scheme = DEFAULT_SCHEMES[category]
  
  return {
    category,
    scheme,
    audioUrl: null, // Will use Web Speech API
  }
}

// Get scheme by category
export async function getSchemeByCategory(category) {
  try {
    const response = await fetch(`${API_BASE_URL}/scheme/${category}`)
    
    if (!response.ok) {
      throw new Error('API request failed')
    }

    return await response.json()
  } catch (error) {
    console.log('Using offline scheme data')
    return DEFAULT_SCHEMES[category] || DEFAULT_SCHEMES.farmer
  }
}

// Send audio to Transcribe (for production)
export async function transcribeAudio(audioBlob) {
  try {
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.wav')

    const response = await fetch(`${API_BASE_URL}/transcribe`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error('Transcription failed')
    }

    const data = await response.json()
    return data.transcript
  } catch (error) {
    console.error('Transcription error:', error)
    throw error
  }
}

// Get audio explanation from Polly
export async function getAudioExplanation(schemeId) {
  try {
    const response = await fetch(`${API_BASE_URL}/audio/${schemeId}`)
    
    if (!response.ok) {
      throw new Error('Audio fetch failed')
    }

    const data = await response.json()
    return data.audioUrl
  } catch (error) {
    console.log('Audio URL unavailable, will use speech synthesis')
    return null
  }
}
