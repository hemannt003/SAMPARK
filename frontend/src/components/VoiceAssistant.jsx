import { useState, useRef, useEffect } from 'react'
import { useLanguage } from '../context/LanguageContext'

export default function VoiceAssistant({ onVoiceResult, isVisible = true }) {
  const { lang, t } = useLanguage()
  const [isOpen, setIsOpen] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [status, setStatus] = useState('idle') // idle, listening, processing, result
  const [dots, setDots] = useState('')
  const recognitionRef = useRef(null)

  // Animate dots while listening
  useEffect(() => {
    if (status === 'listening') {
      const interval = setInterval(() => {
        setDots((prev) => (prev.length >= 3 ? '' : prev + '.'))
      }, 500)
      return () => clearInterval(interval)
    }
    setDots('')
  }, [status])

  const hasSpeechRecognition = () => {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition)
  }

  const startListening = () => {
    if (!hasSpeechRecognition()) {
      setStatus('idle')
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()

    recognition.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
    recognition.continuous = false
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      setIsListening(true)
      setStatus('listening')
      setTranscript('')
    }

    recognition.onresult = (event) => {
      const current = event.results[0][0].transcript
      setTranscript(current)

      if (event.results[0].isFinal) {
        setStatus('processing')
        setTimeout(() => {
          onVoiceResult(current)
          setStatus('result')
          setTimeout(() => {
            setIsOpen(false)
            setStatus('idle')
            setTranscript('')
          }, 1500)
        }, 500)
      }
    }

    recognition.onerror = (event) => {
      console.error('Voice assistant error:', event.error)
      setIsListening(false)
      if (event.error === 'no-speech') {
        setStatus('idle')
        setTranscript(t('noSpeechDetected'))
      } else if (event.error === 'not-allowed') {
        setTranscript(t('micPermission'))
        setStatus('idle')
      } else {
        setTranscript(t('tryAgain'))
        setStatus('idle')
      }
      setTimeout(() => setTranscript(''), 2500)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognitionRef.current = recognition

    try {
      recognition.start()
    } catch (err) {
      console.error('Recognition start error:', err)
    }
  }

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
    setIsListening(false)
  }

  const handleFabClick = () => {
    if (isOpen) {
      if (isListening) {
        stopListening()
      }
      setIsOpen(false)
      setStatus('idle')
      setTranscript('')
    } else {
      setIsOpen(true)
    }
  }

  const handleMicClick = () => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }

  if (!isVisible) return null

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div className="va-overlay" onClick={handleFabClick} />
      )}

      {/* Expanded panel */}
      {isOpen && (
        <div className="va-panel">
          <div className="va-panel-header">
            <div className="va-dots-row">
              <span className="va-dot va-dot-blue" />
              <span className="va-dot va-dot-red" />
              <span className="va-dot va-dot-yellow" />
              <span className="va-dot va-dot-green" />
            </div>
          </div>

          <div className="va-panel-body">
            {status === 'idle' && !transcript && (
              <div className="va-hint">
                <p className="va-hint-main">{t('assistantHint')}</p>
                <div className="va-examples">
                  {t('exampleQueries').map((q, i) => (
                    <p key={i} className="va-example">{q}</p>
                  ))}
                </div>
              </div>
            )}

            {status === 'listening' && (
              <div className="va-listening">
                <div className="va-wave">
                  <span /><span /><span /><span /><span />
                </div>
                <p className="va-listening-text">{t('listening')}{dots}</p>
                {transcript && (
                  <p className="va-transcript-live">{transcript}</p>
                )}
              </div>
            )}

            {status === 'processing' && (
              <div className="va-processing">
                <div className="va-processing-spinner" />
                <p>{t('thinking')}</p>
                {transcript && <p className="va-transcript-final">"{transcript}"</p>}
              </div>
            )}

            {status === 'result' && (
              <div className="va-result">
                <p className="va-transcript-final">"{transcript}"</p>
                <div className="va-check">✓</div>
              </div>
            )}

            {status === 'idle' && transcript && (
              <p className="va-error-msg">{transcript}</p>
            )}
          </div>

          {/* Mic button inside panel */}
          <button
            className={`va-mic-btn ${isListening ? 'va-mic-active' : ''}`}
            onClick={handleMicClick}
          >
            {isListening ? (
              <svg width="28" height="28" viewBox="0 0 24 24" fill="white">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            ) : (
              <svg width="28" height="28" viewBox="0 0 24 24" fill="white">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5z"/>
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
              </svg>
            )}
          </button>
        </div>
      )}

      {/* Floating action button */}
      <button
        className={`va-fab ${isOpen ? 'va-fab-hidden' : ''}`}
        onClick={handleFabClick}
        aria-label={t('assistantHint')}
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="white">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
        </svg>
        <span className="va-fab-pulse" />
      </button>
    </>
  )
}
