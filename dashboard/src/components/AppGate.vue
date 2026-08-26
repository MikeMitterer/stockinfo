<script setup lang="ts">
import { onMounted } from 'vue'

import AppDashboard from './AppDashboard.vue'
import MigrationGate from './MigrationGate.vue'
import { useMigration } from '../composables/useMigration'

/**
 * Die Weiche vor dem Dashboard: Umzug erledigen oder arbeiten.
 *
 * **Warum die Weiche über dem Dashboard steht und nicht darin.** `AppDashboard`
 * lädt beim Einhängen ein Dutzend Dinge — Instrumente, Börsen, Umgebung,
 * Devisen. Im Pending-Zustand weist der Guard jede dieser Anfragen mit `503`
 * ab; stünde die Weiche eine Ebene tiefer, liefe erst der ganze Schwung ins
 * Leere und der Benutzer sähe eine Oberfläche voller Fehlermeldungen, bevor
 * ihm jemand erklärt, was los ist.
 *
 * **Und nicht in `App.vue`.** Das ist der Rahmen — Theme-Brücke und Provider —,
 * und der Inhalt liegt bewusst eine Ebene tiefer, weil `useNotifier()` einen
 * Provider *über* sich braucht. Diese Weiche ist Inhalt.
 */
const { phase, preview, report, error, check, confirm } = useMigration()

onMounted(() => void check())
</script>

<template>
  <AppDashboard v-if="phase === 'serving'" />

  <!--
    `retry` geht auf dieselbe Handlung wie `confirm`, und das ist keine
    Bequemlichkeit: Im Backend *ist* der Wiederholungsweg ein weiteres
    `POST /migration/confirm` (`app/routers/migration.py`). Zwei Aufrufe hier
    hieße, dieselbe Fachregel ein zweites Mal auszulegen.

    `continue` fragt neu nach, statt die Lage selbst auf „läuft" zu setzen —
    ob der Betrieb wirklich freigegeben ist, weiß der Server, nicht das UI.
  -->
  <MigrationGate
    v-else
    :phase="phase"
    :preview="preview"
    :report="report"
    :error="error"
    @confirm="confirm"
    @retry="confirm"
    @continue="check"
  />
</template>
