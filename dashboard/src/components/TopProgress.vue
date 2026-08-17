<script setup lang="ts">
defineProps<{ active: boolean }>()
</script>

<template>
  <div class="top-progress" :class="{ active }" aria-hidden="true">
    <div class="bar" />
  </div>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.top-progress {
  position: fixed;
  top: $header-h;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 25;
  overflow: hidden;
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;

  &.active { opacity: 1; }

  .bar {
    height: 100%;
    width: 40%;
    border-radius: 0 3px 3px 0;
    /*
     * Akzent statt Markenverlauf: Der Balken zeigt einen Zustand — dafür ist
     * die Akzentfarbe da. Die Marke ist eine Signatur und steht an der
     * Plakette, nicht an jedem bewegten Element.
     */
    background: $color-accent;
    animation: slide 1.1s ease-in-out infinite;
  }
}

@keyframes slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}
</style>
