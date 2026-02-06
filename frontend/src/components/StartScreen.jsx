import { useState, useRef, useEffect } from 'react'

export default function StartScreen({ onVoiceInput, onSkipToCategory }) {
  const [isRecording, setIsRecording] = useState(false)
  const [status, setStatus] = useState('')
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])

  // Check for microphone support
  const hasMicrophoneSupport = () => {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
  }

  // Check for Speech Recognition support
  const hasSpeechRecognition = () => {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition)
  }

  const startRecording = async () => {
    // First try Web Speech API (works better for Hindi)
    if (hasSpeechRecognition()) {
      startSpeechRecognition()
      return
    }

    // Fallback to MediaRecorder
    if (!hasMicrophoneSupport()) {
      setStatus('Mic nahi mila')
      // Go to category screen after a delay
      setTimeout(() => onSkipToCategory(), 1500)
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorderRef.current = new MediaRecorder(stream)
      audioChunksRef.current = []

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data)
      }

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
        // In production, this would be sent to AWS Transcribe
        // For demo, we'll use fallback text
        onVoiceInput('kisan yojana ke baare mein batao')
      }

      mediaRecorderRef.current.start()
      setIsRecording(true)
      setStatus('Sun raha hoon...')

      // Auto stop after 5 seconds
      setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          stopRecording()
        }
      }, 5000)

    } catch (err) {
      console.error('Microphone error:', err)
      setStatus('Mic ki permission dijiye')
      setTimeout(() => onSkipToCategory(), 2000)
    }
  }

  const startSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    
    recognition.lang = 'hi-IN'
    recognition.continuous = false
    recognition.interimResults = false
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      setIsRecording(true)
      setStatus('Sun raha hoon...')
    }

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      console.log('Transcript:', transcript)
      setStatus(`Aapne kaha: "${transcript}"`)
      
      setTimeout(() => {
        onVoiceInput(transcript)
      }, 500)
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      setIsRecording(false)
      
      if (event.error === 'no-speech') {
        setStatus('Kuch sunai nahi diya')
      } else if (event.error === 'not-allowed') {
        setStatus('Mic ki permission dijiye')
      } else {
        setStatus('Phir se boliye')
      }
      
      // Go to category selection as fallback
      setTimeout(() => onSkipToCategory(), 2000)
    }

    recognition.onend = () => {
      setIsRecording(false)
    }

    try {
      recognition.start()
    } catch (err) {
      console.error('Recognition start error:', err)
      onSkipToCategory()
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop())
    }
    setIsRecording(false)
    setStatus('Samajh raha hoon...')
  }

  const handleMicClick = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  return (
    <div className="screen start-screen">
      <div className="logo">समpark AI</div>
      <div className="tagline">सरकारी योजना की जानकारी आपकी भाषा में</div>
      
      <button 
        className={`mic-button ${isRecording ? 'recording' : ''}`}
        onClick={handleMicClick}
        aria-label={isRecording ? 'Recording... tap to stop' : 'Tap to speak'}
      >
        🎤
      </button>
      
      <div className="instruction-text">
        {isRecording ? 'Boliye... Main sun raha hoon' : 'Mic dabaiye aur boliye'}
      </div>
      
      <div className="status-text">{status}</div>
      
      {/* Skip button for users who can't use voice */}
      <button 
        style={{
          marginTop: '30px',
          padding: '12px 24px',
          background: 'rgba(255,255,255,0.2)',
          border: '2px solid rgba(255,255,255,0.5)',
          borderRadius: '30px',
          color: 'white',
          fontSize: '1rem',
          cursor: 'pointer'
        }}
        onClick={onSkipToCategory}
      >
        Category se chunein →
      </button>
    </div>
  )
}
