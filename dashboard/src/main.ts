import { createApp } from 'vue'

import App from './App.vue'
import { useTheme } from './composables/useTheme'
import { i18n, initLanguage } from './i18n'
import './styles/base.scss'

// Persistiertes Theme und Sprache vor dem Mount setzen (kein Flash).
useTheme().init()
initLanguage()

createApp(App).use(i18n).mount('#app')
