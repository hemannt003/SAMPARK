import { useState, useEffect } from 'react'
import { useLanguage } from '../context/LanguageContext'

export default function StepGuide({ steps, schemeName, govWebsite, onBack }) {
  const { lang, t } = useLanguage()
  const [currentStep, setCurrentStep] = useState(0)
  const [completedSteps, setCompletedSteps] = useState(new Set())
  const [userIssues, setUserIssues] = useState([]) // Track where user faces issues

  const totalSteps = steps.length
  const progress = Math.round((completedSteps.size / totalSteps) * 100)

  useEffect(() => {
    // Speak the current step
    speakStep(currentStep)
  }, [currentStep])

  const speakStep = (index) => {
    window.speechSynthesis.cancel()
    const step = steps[index]
    if (!step) return

    const text = `${lang === 'hi' ? 'चरण' : 'Step'} ${index + 1}: ${step.title}. ${step.description}`
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
    utterance.rate = 0.85
    window.speechSynthesis.speak(utterance)
  }

  const markComplete = (index) => {
    setCompletedSteps((prev) => {
      const next = new Set(prev)
      next.add(index)
      return next
    })

    // Auto-advance to next step
    if (index < totalSteps - 1) {
      setTimeout(() => setCurrentStep(index + 1), 400)
    }
  }

  const handleNeedHelp = (index) => {
    const step = steps[index]
    setUserIssues((prev) => [
      ...prev,
      { stepIndex: index, stepTitle: step.title, timestamp: new Date().toISOString() },
    ])

    // Speak detailed help
    const helpText =
      lang === 'hi'
        ? `${step.title} — ${step.description}। अगर समस्या हो तो नज़दीकी जन सेवा केंद्र पर जाएँ।`
        : `${step.title} — ${step.description}. If you face any issue, visit your nearest Jan Seva Kendra.`
    const utterance = new SpeechSynthesisUtterance(helpText)
    utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'
    utterance.rate = 0.8
    window.speechSynthesis.speak(utterance)
  }

  const getActionIcon = (action) => {
    switch (action) {
      case 'link': return '🔗'
      case 'click': return '👆'
      case 'fill': return '✍️'
      case 'submit': return '✅'
      case 'info': return 'ℹ️'
      default: return '📌'
    }
  }

  const step = steps[currentStep]

  return (
    <div className="screen step-guide-screen">
      {/* Header */}
      <div className="sg-header">
        <button className="back-button" onClick={onBack} aria-label={t('back')}>
          ←
        </button>
        <div className="sg-title">{schemeName}</div>
      </div>

      {/* Progress bar */}
      <div className="sg-progress-area">
        <div className="sg-progress-label">
          {t('progressLabel')}: {completedSteps.size}/{totalSteps}
        </div>
        <div className="sg-progress-bar">
          <div className="sg-progress-fill" style={{ width: `${progress}%` }} />
        </div>
        <div className="sg-step-dots">
          {steps.map((_, i) => (
            <button
              key={i}
              className={`sg-dot ${i === currentStep ? 'sg-dot-active' : ''} ${completedSteps.has(i) ? 'sg-dot-done' : ''}`}
              onClick={() => setCurrentStep(i)}
              aria-label={`${lang === 'hi' ? 'चरण' : 'Step'} ${i + 1}`}
            >
              {completedSteps.has(i) ? '✓' : i + 1}
            </button>
          ))}
        </div>
      </div>

      {/* Current step card */}
      {step && (
        <div className="sg-step-card">
          <div className="sg-step-number">
            <span className="sg-step-badge">{getActionIcon(step.action)}</span>
            <span>
              {lang === 'hi' ? 'चरण' : 'Step'} {currentStep + 1} / {totalSteps}
            </span>
          </div>

          <h3 className="sg-step-title">{step.title}</h3>
          <p className="sg-step-desc">{step.description}</p>

          {/* Link action */}
          {step.link && (
            <a
              href={step.link}
              target="_blank"
              rel="noopener noreferrer"
              className="sg-link-btn"
            >
              🔗 {step.linkLabel || t('clickThisLink')}
            </a>
          )}

          {/* Input field demo */}
          {step.inputLabel && (
            <div className="sg-input-demo">
              <label className="sg-input-label">{step.inputLabel}</label>
              <input
                type="text"
                className="sg-input-field"
                placeholder={step.inputPlaceholder || ''}
                readOnly
              />
              <span className="sg-input-hint">
                ↑ {t('fillHere')}
              </span>
            </div>
          )}

          {/* Action buttons */}
          <div className="sg-step-actions">
            {!completedSteps.has(currentStep) ? (
              <button
                className="sg-done-btn"
                onClick={() => markComplete(currentStep)}
              >
                ✓ {t('markDone')}
              </button>
            ) : (
              <div className="sg-completed-badge">✅ {t('completed')}</div>
            )}

            <button
              className="sg-help-btn"
              onClick={() => handleNeedHelp(currentStep)}
            >
              🆘 {t('needHelp')}
            </button>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="sg-nav">
        <button
          className="sg-nav-btn"
          disabled={currentStep === 0}
          onClick={() => setCurrentStep((prev) => Math.max(0, prev - 1))}
        >
          ← {t('prevStep')}
        </button>
        <button
          className="sg-nav-btn sg-nav-next"
          disabled={currentStep === totalSteps - 1}
          onClick={() => setCurrentStep((prev) => Math.min(totalSteps - 1, prev + 1))}
        >
          {t('nextStep')} →
        </button>
      </div>

      {/* Issue tracker summary (shown if user requested help) */}
      {userIssues.length > 0 && (
        <div className="sg-issues">
          <div className="sg-issues-title">
            {lang === 'hi' ? 'आपने इन चरणों में सहायता माँगी:' : 'You requested help on these steps:'}
          </div>
          {userIssues.map((issue, i) => (
            <div key={i} className="sg-issue-item">
              <span className="sg-issue-dot">•</span>
              {lang === 'hi' ? 'चरण' : 'Step'} {issue.stepIndex + 1}: {issue.stepTitle}
            </div>
          ))}
        </div>
      )}

      {/* Government website footer */}
      {govWebsite && (
        <a
          href={govWebsite}
          target="_blank"
          rel="noopener noreferrer"
          className="sg-gov-link"
        >
          🌐 {t('govWebsite')}: {govWebsite}
        </a>
      )}
    </div>
  )
}
