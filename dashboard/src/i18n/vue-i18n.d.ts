/** Typisiert t()/$t global auf unser Message-Schema (fehlender Key = TS-Fehler). */
import type { MessageSchema } from './index'

declare module 'vue-i18n' {
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  export interface DefineLocaleMessage extends MessageSchema {}
}
