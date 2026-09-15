<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budget') }}</h3>
        <span class="budget-value">{{ formatCurrency(budget, currentCurrency) }}</span>
      </div>
      <!--
        v-model updates `budget` on every drag step (native `input` event) so the
        formatted value above stays live, but recommendations are only fetched on
        `change` (drag release) to avoid firing an API request per pixel of drag.
      -->
      <input
        type="range"
        min="0"
        max="20000"
        step="250"
        v-model.number="budget"
        @change="loadRecommendations"
        class="budget-slider"
      />
      <p class="budget-hint">{{ t('restocking.budgetHint') }}</p>
    </div>

    <!-- Full-page loading only applies to the very first fetch; subsequent
         refreshes (slider release, post-submit reload) keep existing content
         visible with a subtle "updating" note instead of hiding everything. -->
    <div v-if="loading && !recommendations" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="recommendations">
      <p v-if="loading" class="updating-note">{{ t('common.loading') }}</p>
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ formatCurrency(budget, currentCurrency) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.recommendedTotal') }}</div>
          <div class="stat-value">{{ formatCurrencyWithDecimals(recommendations.total_cost, currentCurrency, 2) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ formatCurrencyWithDecimals(recommendations.remaining_budget, currentCurrency, 2) }}</div>
        </div>
        <div class="stat-card" :class="coverageClass">
          <div class="stat-label">{{ t('restocking.coverage') }}</div>
          <div class="stat-value">{{ coveragePercent }}%</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.items.length }})</h3>
        </div>
        <div v-if="recommendations.items.length === 0" class="empty-state">
          {{ t('restocking.noItemsFit') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.neededQty') }}</th>
                <th>{{ t('restocking.table.recommendedQty') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations.items" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>
                  {{ translateProductName(item.item_name) }}
                  <span v-if="!item.fully_covered" class="badge warning partial-badge">{{ t('restocking.partial') }}</span>
                </td>
                <td><span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span></td>
                <td>{{ formatCurrencyWithDecimals(item.unit_cost, currentCurrency, 2) }}</td>
                <td>{{ item.quantity_needed }}</td>
                <td>{{ item.recommended_quantity }}</td>
                <td>{{ formatCurrencyWithDecimals(item.line_total, currentCurrency, 2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card order-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.placeOrder') }}</h3>
        </div>

        <div v-if="submittedOrder" class="success-panel">
          <p>{{ t('restocking.orderPlaced', { orderNumber: submittedOrder.order_number }) }}</p>
          <p>{{ t('restocking.leadTime', { days: submittedOrder.lead_time_days }) }}</p>
          <p>{{ t('restocking.expectedDelivery') }}: {{ formatDeliveryDate(submittedOrder.expected_delivery) }}</p>
          <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
        </div>

        <div v-if="submitError" class="error">{{ submitError }}</div>

        <div class="order-controls">
          <div class="control-group">
            <label>{{ t('restocking.warehouse') }}</label>
            <select v-model="selectedWarehouse" class="warehouse-select">
              <option value="San Francisco">{{ t('warehouses.sanFrancisco') }}</option>
              <option value="London">{{ t('warehouses.london') }}</option>
              <option value="Tokyo">{{ t('warehouses.tokyo') }}</option>
            </select>
            <span class="lead-time-hint">{{ t('restocking.leadTime', { days: leadTimeDays }) }}</span>
          </div>

          <button
            class="po-button create"
            :disabled="!hasItemsToOrder || submitting || loading"
            @click="submitOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

// Lead times mirrored from the backend for display only - the server is the
// source of truth and validates the actual warehouse/lead-time pairing.
const LEAD_TIMES = {
  'San Francisco': 3,
  'London': 7,
  'Tokyo': 10
}

export default {
  name: 'Restocking',
  setup() {
    const { t, currentLocale, currentCurrency, translateProductName } = useI18n()

    const budget = ref(5000)
    const recommendations = ref(null)
    const loading = ref(false)
    const error = ref(null)

    const selectedWarehouse = ref('San Francisco')
    const submitting = ref(false)
    const submitError = ref(null)
    const submittedOrder = ref(null)

    const leadTimeDays = computed(() => LEAD_TIMES[selectedWarehouse.value])

    const hasItemsToOrder = computed(() => {
      return !!recommendations.value && recommendations.value.items.length > 0
    })

    // Coverage guards against a zero total_needed_cost (nothing needs
    // restocking), in which case there's nothing left to cover.
    const coveragePercent = computed(() => {
      if (!recommendations.value || !recommendations.value.total_needed_cost) return 100
      return Math.round((recommendations.value.total_cost / recommendations.value.total_needed_cost) * 100)
    })

    const coverageClass = computed(() => {
      if (coveragePercent.value >= 100) return 'success'
      if (coveragePercent.value >= 50) return 'warning'
      return 'danger'
    })

    // Two quick slider releases can trigger overlapping requests that resolve
    // out of order. Track a sequence number per request and ignore any
    // response that isn't from the most recently issued request, so a slow
    // response for an old budget can never clobber a newer one on screen.
    let requestSequence = 0

    const loadRecommendations = async () => {
      const thisRequest = ++requestSequence
      loading.value = true
      error.value = null
      try {
        const data = await api.getRestockRecommendations(budget.value)
        if (thisRequest !== requestSequence) return
        recommendations.value = data
      } catch (err) {
        if (thisRequest !== requestSequence) return
        error.value = 'Failed to load restock recommendations: ' + err.message
      } finally {
        if (thisRequest === requestSequence) {
          loading.value = false
        }
      }
    }

    const submitOrder = async () => {
      if (!hasItemsToOrder.value) return
      submitting.value = true
      submitError.value = null
      submittedOrder.value = null
      try {
        const payload = {
          warehouse: selectedWarehouse.value,
          budget: budget.value,
          items: recommendations.value.items.map(item => ({
            item_sku: item.item_sku,
            quantity: item.recommended_quantity
          }))
        }
        submittedOrder.value = await api.createRestockOrder(payload)
        await loadRecommendations()
      } catch (err) {
        submitError.value = err.response?.data?.detail || err.message
      } finally {
        submitting.value = false
      }
    }

    // The restock-orders API always returns expected_delivery as a plain
    // YYYY-MM-DD date-only string (unlike the general orders endpoint, which
    // uses full timestamps), so it's safe to always parse it as date-only
    // here. `new Date(str)` would parse that as UTC midnight, which can
    // display as the previous day in US time zones - so parse the parts and
    // build a local date instead.
    const formatDeliveryDate = (dateString) => {
      if (!dateString) return ''
      const [y, m, d] = dateString.split('-').map(Number)
      const date = new Date(y, m - 1, d)
      if (isNaN(date.getTime())) return ''
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' })
    }

    onMounted(loadRecommendations)

    return {
      t,
      currentCurrency,
      translateProductName,
      formatCurrency,
      formatCurrencyWithDecimals,
      budget,
      recommendations,
      loading,
      error,
      selectedWarehouse,
      leadTimeDays,
      hasItemsToOrder,
      coveragePercent,
      coverageClass,
      loadRecommendations,
      submitOrder,
      submitting,
      submitError,
      submittedOrder,
      formatDeliveryDate
    }
  }
}
</script>

<style scoped>
.budget-card {
  padding: 1.5rem;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  margin: 0.75rem 0 0.5rem;
  accent-color: #3b82f6;
  cursor: pointer;
}

.budget-hint {
  color: #64748b;
  font-size: 0.813rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.updating-note {
  color: #64748b;
  font-size: 0.813rem;
  margin-bottom: 0.75rem;
  font-style: italic;
}

.partial-badge {
  margin-left: 0.5rem;
}

.order-card {
  margin-bottom: 0;
}

.order-controls {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.control-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
}

.warehouse-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #0f172a;
  background: white;
  cursor: pointer;
  font-weight: 500;
  min-width: 160px;
}

.warehouse-select:hover {
  border-color: #94a3b8;
}

.warehouse-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.lead-time-hint {
  font-size: 0.813rem;
  color: #64748b;
}

/* .po-button styles mirrored from Dashboard.vue (scoped styles don't share across components) */
.po-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.po-button.create {
  background: #3b82f6;
  color: white;
}

.po-button.create:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.po-button.create:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.success-panel {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.938rem;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.success-panel a {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
  width: fit-content;
}

@media (max-width: 640px) {
  .order-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .po-button.create {
    width: 100%;
  }
}
</style>
