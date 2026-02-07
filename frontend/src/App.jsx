import { useState } from 'react'
import { LanguageProvider, useLanguage } from './context/LanguageContext'
import StartScreen from './components/StartScreen'
import CategoryScreen from './components/CategoryScreen'
import ResultScreen from './components/ResultScreen'
import VoiceAssistant from './components/VoiceAssistant'
import { processVoiceQuery } from './services/api'

function AppContent() {
  const { t } = useLanguage()
  const [screen, setScreen] = useState('start')
  const [category, setCategory] = useState(null)
  const [schemeData, setSchemeData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)

  const handleVoiceInput = async (transcript) => {
    setLoading(true)
    setError(null)

    try {
      const response = await processVoiceQuery(transcript)
      setSchemeData(response.scheme)
      setAudioUrl(response.audioUrl)
      setCategory(response.category)
      setScreen('result')
    } catch (err) {
      console.error('Error processing voice:', err)
      setError(t('error'))
      setTimeout(() => setError(null), 3000)
    } finally {
      setLoading(false)
    }
  }

  const handleCategorySelect = async (selectedCategory) => {
    setLoading(true)
    setError(null)

    try {
      const response = await processVoiceQuery(selectedCategory)
      setSchemeData(response.scheme)
      setAudioUrl(response.audioUrl)
      setCategory(selectedCategory)
      setScreen('result')
    } catch (err) {
      console.error('Error fetching scheme:', err)
      setError(t('error'))
      setTimeout(() => setError(null), 3000)
    } finally {
      setLoading(false)
    }
  }

  const handleBack = () => {
    if (screen === 'result') {
      setScreen('category')
    } else if (screen === 'category') {
      setScreen('start')
    }
    setSchemeData(null)
    setAudioUrl(null)
  }

  const goToCategory = () => {
    setScreen('category')
  }

  return (
    <>
      {screen === 'start' && (
        <StartScreen
          onVoiceInput={handleVoiceInput}
          onSkipToCategory={goToCategory}
        />
      )}

      {screen === 'category' && (
        <CategoryScreen
          onSelect={handleCategorySelect}
          onBack={handleBack}
        />
      )}

      {screen === 'result' && (
        <ResultScreen
          category={category}
          scheme={schemeData}
          audioUrl={audioUrl}
          onBack={handleBack}
        />
      )}

      {/* Google-Assistant-style floating voice button (visible on all screens except start) */}
      <VoiceAssistant
        onVoiceResult={handleVoiceInput}
        isVisible={screen !== 'start'}
      />

      {/* Loading Overlay */}
      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner" />
          <div className="loading-text">{t('loading')}</div>
        </div>
      )}

      {/* Error Toast */}
      {error && <div className="error-toast">{error}</div>}
    </>
  )
}

export default function App() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  )
}
