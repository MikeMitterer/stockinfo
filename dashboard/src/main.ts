import { createApp } from 'vue'

import App from './App.vue'
import { useTheme } from './composables/useTheme'
import { i18n, initLanguage } from './i18n'
import './styles/base.scss'
import { initScrollbarAutoHide } from './utils/scrollbarActivity'

// Persistiertes Theme und Sprache vor dem Mount setzen (kein Flash).
useTheme().init()
initLanguage()
initScrollbarAutoHide()

createApp(App).use(i18n).mount('#app')
