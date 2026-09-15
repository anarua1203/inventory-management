<template>
  <div class="language-switcher" :class="{ compact }">
    <button
      class="language-button"
      :aria-label="compact ? localeName : null"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 20 20"
        fill="none"
        class="globe-icon"
      >
        <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5"/>
        <path d="M3 10H17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 7.5 5.5 7.5 10C7.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 12.5 5.5 12.5 10C12.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
      </svg>
      <span class="language-label">{{ localeName }}</span>
      <span class="language-code">{{ currentLocale.toUpperCase() }}</span>
      <svg
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
      >
        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>

    <div v-if="isDropdownOpen" class="dropdown-menu" :class="placementClass">
      <button
        v-for="locale in availableLocales"
        :key="locale"
        class="dropdown-item"
        :class="{ active: currentLocale === locale }"
        @mousedown.prevent="selectLanguage(locale)"
      >
        <span class="language-name">{{ getLanguageName(locale) }}</span>
        <svg
          v-if="currentLocale === locale"
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          class="check-icon"
        >
          <path d="M4 9L7.5 12.5L14 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from '../composables/useI18n'

const props = defineProps({
  // 'bottom-end' opens the menu below/right (default); 'top-start' opens
  // it above/left, used when the switcher sits in the sidebar footer
  placement: {
    type: String,
    default: 'bottom-end'
  },
  // Compact rendering (locale code only) used in the collapsed sidebar rail
  compact: {
    type: Boolean,
    default: false
  }
})

const { currentLocale, setLocale, availableLocales, localeName } = useI18n()

const isDropdownOpen = ref(false)

const placementClass = computed(() => {
  return props.placement === 'top-start' ? 'placement-top-start' : ''
})

const languageNames = {
  en: 'English',
  ja: '日本語'
}

const getLanguageName = (locale) => {
  return languageNames[locale] || locale
}

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const handleBlur = () => {
  // Delay to allow mousedown events on dropdown items to fire first
  setTimeout(() => {
    isDropdownOpen.value = false
  }, 200)
}

const selectLanguage = (locale) => {
  setLocale(locale)
  isDropdownOpen.value = false
}
</script>

<style scoped>
.language-switcher {
  position: relative;
  width: 100%;
}

.language-button {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  font-size: 0.875rem;
  color: #334155;
}

.language-button:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-border-strong);
}

.globe-icon {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.language-label {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.language-code {
  display: none;
  font-weight: 600;
  font-size: 0.75rem;
  letter-spacing: 0.02em;
}

.chevron {
  color: var(--color-text-muted);
  transition: transform 0.2s ease;
  flex-shrink: 0;
  margin-left: auto;
}

.chevron-open {
  transform: rotate(180deg);
}

/* Compact rendering (collapsed sidebar rail): show only the locale code,
   desktop only so the mobile drawer always shows the full control */
@media (min-width: 1024px) {
  .language-switcher.compact .language-button {
    justify-content: center;
    padding: var(--space-2);
  }
  .language-switcher.compact .globe-icon,
  .language-switcher.compact .language-label,
  .language-switcher.compact .chevron {
    display: none;
  }
  .language-switcher.compact .language-code {
    display: inline;
  }
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + var(--space-2));
  right: 0;
  min-width: 160px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  z-index: 500;
  overflow: hidden;
}

.dropdown-menu.placement-top-start {
  top: auto;
  bottom: calc(100% + var(--space-2));
  left: 0;
  right: auto;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  color: #334155;
}

.dropdown-item:hover {
  background: #f8fafc;
}

.dropdown-item.active {
  background: #eff6ff;
  color: #2563eb;
}

.language-name {
  flex: 1;
}

.check-icon {
  color: #2563eb;
  flex-shrink: 0;
}
</style>
