import { createApp } from 'vue'

import App from './App.vue'
import { useTheme } from './composables/useTheme'
import { i18n, initLanguage } from './i18n'
/*
 * Reihenfolge ist nicht beliebig: Schriften und Token zuerst, dann der Reset.
 * Der Reset greift auf Token zu, und die Schrift soll stehen, bevor das erste
 * Zeichen gemalt wird.
 */
import '@mmit/ux-foundation/styles/fonts.css'
import '@mmit/ux-foundation/styles/tokens.css'
import '@mmit/ux-foundation/styles/reset.css'
import './styles/base.scss'
import { initScrollbarAutoHide } from './utils/scrollbarActivity'

// Persistiertes Theme und Sprache vor dem Mount setzen (kein Flash).
useTheme().init()
initLanguage()
initScrollbarAutoHide()

createApp(App).use(i18n).mount('#app')
