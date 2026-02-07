// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://your-api-gateway-url.execute-api.ap-south-1.amazonaws.com/prod'

// Bilingual scheme data — Pure Hindi (Devanagari) and pure English. No Hinglish.
const DEFAULT_SCHEMES = {
  farmer: {
    scheme_id: 'PM_KISAN',
    name: { hi: 'पीएम किसान सम्मान निधि', en: 'PM Kisan Samman Nidhi' },
    category: 'farmer',
    eligibility: {
      hi: 'छोटे एवं सीमांत किसान जिनके पास 2 हेक्टेयर से कम भूमि है',
      en: 'Small and marginal farmers with less than 2 hectares of land'
    },
    benefit: {
      hi: 'प्रति वर्ष ₹6,000 — तीन किस्तों में ₹2,000',
      en: '₹6,000 per year — ₹2,000 in three instalments'
    },
    documents: {
      hi: ['आधार कार्ड', 'बैंक खाता पासबुक', 'भूमि के कागज़ात', 'मोबाइल नंबर'],
      en: ['Aadhaar Card', 'Bank Account Passbook', 'Land Records', 'Mobile Number']
    },
    steps: {
      hi: [
        {
          title: 'पीएम किसान की वेबसाइट खोलें',
          description: 'नीचे दिए गए लिंक पर क्लिक करें और पीएम किसान की आधिकारिक वेबसाइट खोलें।',
          link: 'https://pmkisan.gov.in',
          linkLabel: 'pmkisan.gov.in खोलें',
          action: 'link'
        },
        {
          title: '"New Farmer Registration" पर क्लिक करें',
          description: 'वेबसाइट खुलने के बाद, दाईं ओर "New Farmer Registration" बटन पर क्लिक करें।',
          screenshot: 'new-farmer-reg-btn',
          action: 'click'
        },
        {
          title: 'अपना आधार नंबर भरें',
          description: 'आधार नंबर वाले खाने में अपना 12 अंकों का आधार नंबर भरें।',
          inputLabel: 'आधार नंबर',
          inputPlaceholder: 'उदाहरण: 1234 5678 9012',
          action: 'fill'
        },
        {
          title: 'बैंक खाते की जानकारी भरें',
          description: 'अपना बैंक खाता नंबर और IFSC कोड भरें। यह जानकारी आपकी पासबुक पर लिखी होती है।',
          action: 'fill'
        },
        {
          title: 'भूमि की जानकारी भरें',
          description: 'अपनी ज़मीन का खसरा/खतौनी नंबर और क्षेत्रफल (हेक्टेयर में) भरें।',
          action: 'fill'
        },
        {
          title: 'फ़ॉर्म जमा करें',
          description: '"Submit" बटन पर क्लिक करें। आपको एक पंजीकरण संख्या मिलेगी — उसे सुरक्षित रखें।',
          action: 'submit'
        }
      ],
      en: [
        {
          title: 'Open PM Kisan website',
          description: 'Click the link below to open the official PM Kisan website.',
          link: 'https://pmkisan.gov.in',
          linkLabel: 'Open pmkisan.gov.in',
          action: 'link'
        },
        {
          title: 'Click on "New Farmer Registration"',
          description: 'After the website opens, click the "New Farmer Registration" button on the right side.',
          screenshot: 'new-farmer-reg-btn',
          action: 'click'
        },
        {
          title: 'Enter your Aadhaar number',
          description: 'Type your 12-digit Aadhaar number in the Aadhaar number field.',
          inputLabel: 'Aadhaar Number',
          inputPlaceholder: 'Example: 1234 5678 9012',
          action: 'fill'
        },
        {
          title: 'Fill in your bank details',
          description: 'Enter your bank account number and IFSC code. You can find these on your passbook.',
          action: 'fill'
        },
        {
          title: 'Enter your land details',
          description: 'Fill in your Khasra/Khatauni number and area (in hectares).',
          action: 'fill'
        },
        {
          title: 'Submit the form',
          description: 'Click the "Submit" button. You will receive a registration number — keep it safe.',
          action: 'submit'
        }
      ]
    },
    govWebsite: 'https://pmkisan.gov.in',
    helpline: '155261'
  },
  student: {
    scheme_id: 'PM_VIDYALAKSHMI',
    name: { hi: 'पीएम विद्यालक्ष्मी योजना', en: 'PM Vidyalakshmi Yojana' },
    category: 'student',
    eligibility: {
      hi: 'उच्च शिक्षा के लिए ऋण की आवश्यकता वाले विद्यार्थी',
      en: 'Students who need loans for higher education'
    },
    benefit: {
      hi: 'आसान प्रक्रिया से शिक्षा ऋण, कम ब्याज दर पर',
      en: 'Education loan through a simple process at low interest rates'
    },
    documents: {
      hi: ['आधार कार्ड', 'प्रवेश पत्र', 'अंकतालिका', 'आय प्रमाण पत्र', 'बैंक खाता'],
      en: ['Aadhaar Card', 'Admission Letter', 'Marksheet', 'Income Certificate', 'Bank Account']
    },
    steps: {
      hi: [
        {
          title: 'विद्यालक्ष्मी पोर्टल खोलें',
          description: 'नीचे दिए गए लिंक पर क्लिक करें।',
          link: 'https://www.vidyalakshmi.co.in',
          linkLabel: 'vidyalakshmi.co.in खोलें',
          action: 'link'
        },
        {
          title: 'नया खाता बनाएँ',
          description: '"Register" बटन पर क्लिक करें और अपना नाम, ईमेल और मोबाइल नंबर भरें।',
          action: 'fill'
        },
        {
          title: 'अपना कॉलेज और पाठ्यक्रम चुनें',
          description: 'सूची में से अपना कॉलेज खोजें और जिस पाठ्यक्रम में प्रवेश लिया है उसे चुनें।',
          action: 'click'
        },
        {
          title: 'ऋण की राशि भरें',
          description: 'आपको कितने ऋण की आवश्यकता है, वह राशि रुपयों में भरें।',
          inputLabel: 'ऋण राशि (₹)',
          inputPlaceholder: 'उदाहरण: 500000',
          action: 'fill'
        },
        {
          title: 'दस्तावेज़ अपलोड करें',
          description: 'अपनी अंकतालिका, प्रवेश पत्र और आय प्रमाण पत्र की स्कैन कॉपी अपलोड करें।',
          action: 'fill'
        },
        {
          title: 'बैंक चुनें और आवेदन करें',
          description: 'जिस बैंक से ऋण चाहिए उसे चुनें और "Apply" पर क्लिक करें।',
          action: 'submit'
        }
      ],
      en: [
        {
          title: 'Open Vidyalakshmi Portal',
          description: 'Click the link below to open the portal.',
          link: 'https://www.vidyalakshmi.co.in',
          linkLabel: 'Open vidyalakshmi.co.in',
          action: 'link'
        },
        {
          title: 'Create a new account',
          description: 'Click the "Register" button and fill in your name, email, and mobile number.',
          action: 'fill'
        },
        {
          title: 'Select your college and course',
          description: 'Search for your college from the list and select the course you have been admitted to.',
          action: 'click'
        },
        {
          title: 'Enter loan amount',
          description: 'Enter the amount of loan you need in rupees.',
          inputLabel: 'Loan Amount (₹)',
          inputPlaceholder: 'Example: 500000',
          action: 'fill'
        },
        {
          title: 'Upload documents',
          description: 'Upload scanned copies of your marksheet, admission letter, and income certificate.',
          action: 'fill'
        },
        {
          title: 'Select bank and apply',
          description: 'Choose the bank you want the loan from and click "Apply".',
          action: 'submit'
        }
      ]
    },
    govWebsite: 'https://www.vidyalakshmi.co.in',
    helpline: '1800-180-2005'
  },
  woman: {
    scheme_id: 'PM_UJJWALA',
    name: { hi: 'प्रधानमंत्री उज्ज्वला योजना', en: 'Pradhan Mantri Ujjwala Yojana' },
    category: 'woman',
    eligibility: {
      hi: 'बीपीएल परिवार की 18 वर्ष से अधिक आयु की महिलाएँ',
      en: 'Women above 18 years of age from BPL families'
    },
    benefit: {
      hi: 'निःशुल्क एलपीजी कनेक्शन, ₹1,600 की सब्सिडी',
      en: 'Free LPG connection with ₹1,600 subsidy'
    },
    documents: {
      hi: ['आधार कार्ड', 'बीपीएल राशन कार्ड', 'बैंक खाता पासबुक', 'पासपोर्ट साइज़ फ़ोटो'],
      en: ['Aadhaar Card', 'BPL Ration Card', 'Bank Account Passbook', 'Passport Size Photo']
    },
    steps: {
      hi: [
        {
          title: 'नज़दीकी एलपीजी वितरक के पास जाएँ',
          description: 'अपने क्षेत्र के नज़दीकी इंडेन, भारत गैस या एचपी गैस वितरक की दुकान पर जाएँ।',
          link: 'https://www.pmujjwalayojana.com',
          linkLabel: 'योजना की वेबसाइट खोलें',
          action: 'link'
        },
        {
          title: 'उज्ज्वला योजना का फ़ॉर्म लें',
          description: 'वितरक से "प्रधानमंत्री उज्ज्वला योजना" का आवेदन फ़ॉर्म माँगें।',
          action: 'click'
        },
        {
          title: 'फ़ॉर्म में अपनी जानकारी भरें',
          description: 'अपना नाम, पता, आधार नंबर और बैंक खाता नंबर भरें।',
          inputLabel: 'आधार नंबर',
          inputPlaceholder: 'उदाहरण: 1234 5678 9012',
          action: 'fill'
        },
        {
          title: 'दस्तावेज़ों की प्रति संलग्न करें',
          description: 'आधार कार्ड, राशन कार्ड, बैंक पासबुक और फ़ोटो की फ़ोटोकॉपी फ़ॉर्म के साथ जमा करें।',
          action: 'fill'
        },
        {
          title: 'केवाईसी पूर्ण करें',
          description: 'वितरक आपकी पहचान सत्यापित करेगा। अपना मूल आधार कार्ड साथ रखें।',
          action: 'submit'
        },
        {
          title: 'कनेक्शन प्राप्त करें',
          description: '7 दिनों के भीतर आपको एलपीजी कनेक्शन मिल जाएगा।',
          action: 'info'
        }
      ],
      en: [
        {
          title: 'Visit your nearest LPG distributor',
          description: 'Go to the nearest Indane, Bharat Gas, or HP Gas distributor shop in your area.',
          link: 'https://www.pmujjwalayojana.com',
          linkLabel: 'Open scheme website',
          action: 'link'
        },
        {
          title: 'Get the Ujjwala Yojana form',
          description: 'Ask the distributor for the "Pradhan Mantri Ujjwala Yojana" application form.',
          action: 'click'
        },
        {
          title: 'Fill in your details',
          description: 'Enter your name, address, Aadhaar number, and bank account number.',
          inputLabel: 'Aadhaar Number',
          inputPlaceholder: 'Example: 1234 5678 9012',
          action: 'fill'
        },
        {
          title: 'Attach copies of your documents',
          description: 'Submit photocopies of your Aadhaar card, ration card, bank passbook, and photo along with the form.',
          action: 'fill'
        },
        {
          title: 'Complete KYC verification',
          description: 'The distributor will verify your identity. Keep your original Aadhaar card with you.',
          action: 'submit'
        },
        {
          title: 'Receive your connection',
          description: 'You will receive the LPG connection within 7 days.',
          action: 'info'
        }
      ]
    },
    govWebsite: 'https://www.pmujjwalayojana.com',
    helpline: '1906'
  }
}

// Category detection from transcript — supports both Hindi and English
function detectCategory(transcript) {
  const text = transcript.toLowerCase()

  // Farmer keywords (Hindi + English)
  if (
    text.includes('किसान') || text.includes('खेती') || text.includes('कृषि') ||
    text.includes('ज़मीन') || text.includes('फसल') || text.includes('भूमि') ||
    text.includes('farmer') || text.includes('agriculture') || text.includes('farming') ||
    text.includes('land') || text.includes('crop') || text.includes('kisan') ||
    text.includes('kheti') || text.includes('fasal')
  ) {
    return 'farmer'
  }

  // Student keywords
  if (
    text.includes('विद्यार्थी') || text.includes('छात्र') || text.includes('पढ़ाई') ||
    text.includes('छात्रवृत्ति') || text.includes('शिक्षा') || text.includes('कॉलेज') ||
    text.includes('student') || text.includes('scholarship') || text.includes('education') ||
    text.includes('school') || text.includes('college') || text.includes('loan') ||
    text.includes('padhai') || text.includes('vidya')
  ) {
    return 'student'
  }

  // Woman keywords
  if (
    text.includes('महिला') || text.includes('स्त्री') || text.includes('बेटी') ||
    text.includes('लड़की') || text.includes('माता') || text.includes('गैस') ||
    text.includes('woman') || text.includes('women') || text.includes('girl') ||
    text.includes('daughter') || text.includes('mother') || text.includes('gas') ||
    text.includes('mahila') || text.includes('beti')
  ) {
    return 'woman'
  }

  // Default to farmer if no clear match
  return 'farmer'
}

// Process voice query — calls backend API
export async function processVoiceQuery(transcript) {
  try {
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
    return processQueryLocally(transcript)
  }
}

// Local processing for demo / offline mode
function processQueryLocally(transcript) {
  const category = detectCategory(transcript)
  const scheme = DEFAULT_SCHEMES[category]

  return {
    category,
    scheme,
    audioUrl: null,
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

// Analyse eligibility for a user query
export function analyseEligibility(category, lang = 'hi') {
  const scheme = DEFAULT_SCHEMES[category]
  if (!scheme) return null

  return {
    schemeName: scheme.name[lang],
    eligibility: scheme.eligibility[lang],
    benefit: scheme.benefit[lang],
    govWebsite: scheme.govWebsite,
    helpline: scheme.helpline,
    isAvailable: true,
  }
}
