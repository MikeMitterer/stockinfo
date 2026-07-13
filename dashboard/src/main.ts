import { createApp } from 'vue'

import App from './App.vue'
import { useTheme } from './composables/useTheme'
import './styles/base.scss'

// Persistiertes Theme vor dem Mount setzen (kein Flash).
useTheme().init()

createApp(App).mount('#app')
