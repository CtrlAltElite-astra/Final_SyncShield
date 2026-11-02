import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles/tokens.css'
import './styles/base.css'
import './styles/components.css'
import './styles/demo.css'
import './styles/syncshield.css'
import './styles/console.css'
import './styles/motion.css'
import './styles/scale.css'
import './styles/dark.css'
import { ThemeProvider } from './components/Theme'
import { initMotion } from './lib/motion'

initMotion()

createRoot(document.getElementById('root')!).render(<StrictMode><ThemeProvider><App /></ThemeProvider></StrictMode>)
