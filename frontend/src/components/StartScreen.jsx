import { useState, useRef, useEffect } from 'react'
import { useLanguage } from '../context/LanguageContext'

export default function StartScreen({ onVoiceInput, onSkipToCategory }) {
  const { lang, t, toggleLanguage } = useLanguage()
  const [isRecording, setIsRecording] = useState(false)
  const [status, setStatus] = useState('')
  const [statusType, setStatusType] = useState('') // '', 'listening', 'transcript', 'error'
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])

  useEffect(() => {
    playWelcomeAudio()
  }, [])

  const playWelcomeAudio = () => {
    const text = lang === 'hi'
      ? 'नमस्ते! माइक दबाएँ और बोलें'
      : 'Hello! Tap the mic and speak'
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
    utterance.rate = 0.9
    window.speechSynthesis.speak(utterance)
  }

  const hasSpeechRecognition = () => {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition)
  }

  const hasMicrophoneSupport = () => {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
  }

  const startRecording = async () => {
    if (hasSpeechRecognition()) {
      startSpeechRecognition()
      return
    }

    if (!hasMicrophoneSupport()) {
      setStatus(t('micNotFound'))
      setStatusType('error')
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
        // In production, send blob to AWS Transcribe
        const fallback = lang === 'hi' ? 'किसान योजना के बारे में बताएँ' : 'Tell me about farmer schemes'
        onVoiceInput(fallback)
      }

      mediaRecorderRef.current.start()
      setIsRecording(true)
      setStatus(t('listening'))
      setStatusType('listening')

      setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          stopRecording()
        }
      }, 5000)
    } catch (err) {
      console.error('Microphone error:', err)
      setStatus(t('micPermission'))
      setStatusType('error')
      setTimeout(() => onSkipToCategory(), 2000)
    }
  }

  const startSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()

    recognition.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
    recognition.continuous = false
    recognition.interimResults = false
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      setIsRecording(true)
      setStatus(t('listening'))
      setStatusType('listening')
    }

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      console.log('Transcript:', transcript)
      setStatus(`${t('youSaid')} "${transcript}"`)
      setStatusType('transcript')

      setTimeout(() => {
        onVoiceInput(transcript)
      }, 500)
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      setIsRecording(false)

      if (event.error === 'no-speech') {
        setStatus(t('noSpeechDetected'))
      } else if (event.error === 'not-allowed') {
        setStatus(t('micPermission'))
      } else {
        setStatus(t('tryAgain'))
      }
      setStatusType('error')
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
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop())
    }
    setIsRecording(false)
    setStatus(t('thinking'))
    setStatusType('listening')
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
      {/* Language toggle */}
      <button className="lang-toggle" onClick={toggleLanguage}>
        {t('langToggle')}
      </button>

      <div className="logo">{t('appName')}</div>
      <div className="tagline">{t('tagline')}</div>

      {/* Google-Assistant-style mic area */}
      <div className="ga-mic-area">
        {isRecording && (
          <div className="ga-rings">
            <span className="ga-ring ga-ring-1" />
            <span className="ga-ring ga-ring-2" />
            <span className="ga-ring ga-ring-3" />
          </div>
        )}
        <button
          className={`mic-button ${isRecording ? 'recording' : ''}`}
          onClick={handleMicClick}
          aria-label={isRecording ? 'Stop recording' : 'Tap to speak'}
        >
          {isRecording ? (
            <svg width="60" height="60" viewBox="0 0 24 24" fill="#FF6B35">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5z" />
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
          ) : (
            <span className="mic-emoji">🎤</span>
          )}
        </button>
      </div>

      <div className="instruction-text">
        {isRecording ? t('listening') : t('tapToSpeak')}
      </div>

      <div className="ask-hint">{t('askAnything')}</div>

      <div className={`status-text ${statusType}`}>{status}</div>

      {/* Browse categories button */}
      <button className="skip-button" onClick={onSkipToCategory}>
        {t('browseCategories')} →
      </button>
    </div>
  )
}
