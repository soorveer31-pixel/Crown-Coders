/**
 * API Service layer for Campus Resource Autopilot.
 * Handles HTTP requests between the React frontend and FastAPI backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

/**
 * Fetch health status of the backend API.
 * @returns {Promise<Object>} Status object including service name, version, and database state.
 */
export async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Health check returned status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to communicate with backend health API:', error);
    throw error;
  }
}

/**
 * Fetch aggregated metrics summary for electricity, water, and waste.
 * @returns {Promise<Object>} Summary metrics containing current, average, total, and units.
 */
export async function getResourceSummary() {
  try {
    const response = await fetch(`${API_BASE_URL}/resources/summary`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch resource summary (status ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to fetch resource summary:', error);
    throw error;
  }
}

/**
 * Fetch historical time-series telemetry data for a specified resource.
 * @param {string} resource - 'electricity', 'water', or 'waste'
 * @param {string} range - '7d' or '30d'
 * @returns {Promise<Object>} Time series payload containing resource, unit, range, and data array.
 */
export async function getResourceHistory(resource = 'electricity', range = '7d') {
  try {
    const params = new URLSearchParams({ resource, range });
    const response = await fetch(`${API_BASE_URL}/resources/history?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to fetch history (status ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Failed to fetch telemetry history for ${resource}:`, error);
    throw error;
  }
}

/**
 * Fetch detected anomalies for a given resource and time range.
 * @param {string} resource - 'electricity', 'water', or 'waste'
 * @param {string} range - '7d' or '30d'
 * @returns {Promise<Object>} Anomaly payload with list of detected outlier readings.
 */
export async function getAnomalies(resource = 'electricity', range = '7d') {
  try {
    const params = new URLSearchParams({ resource, range });
    const response = await fetch(`${API_BASE_URL}/ml/anomalies?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to fetch anomalies (status ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Failed to fetch anomalies for ${resource}:`, error);
    throw error;
  }
}

/**
 * Fetch demand forecast points for the specified resource and horizon.
 * @param {string} resource - 'electricity', 'water', or 'waste'
 * @param {number} horizon - Number of time steps (default 24)
 * @returns {Promise<Object>} Forecast payload containing predicted demand points.
 */
export async function getForecast(resource = 'electricity', horizon = 24) {
  try {
    const params = new URLSearchParams({ resource, horizon: String(horizon) });
    const response = await fetch(`${API_BASE_URL}/ml/forecast?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to fetch forecast (status ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Failed to fetch forecast for ${resource}:`, error);
    throw error;
  }
}

/**
 * Fetch ML evaluation metrics (MAE, RMSE, Precision, Recall, F1) for the resource.
 * @param {string} resource - 'electricity', 'water', or 'waste'
 * @returns {Promise<Object>} Evaluation payload containing model performance metrics.
 */
export async function getMLEvaluation(resource = 'electricity') {
  try {
    const params = new URLSearchParams({ resource });
    const response = await fetch(`${API_BASE_URL}/ml/evaluation?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to fetch ML evaluation (status ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Failed to fetch ML evaluation for ${resource}:`, error);
    throw error;
  }
}

/**
 * Fetch explainable insights and actionable recommendations.
 * @param {string} resource - Optional 'electricity', 'water', or 'waste'
 * @param {string} range - '7d' or '30d'
 * @returns {Promise<Object>} Insights payload with detected issues and upcoming risks.
 */
export async function getInsights(resource = null, range = '7d') {
  try {
    const params = new URLSearchParams({ range });
    if (resource) {
      params.append('resource', resource);
    }

    const response = await fetch(`${API_BASE_URL}/insights?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to fetch insights (status ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to fetch insights:', error);
    throw error;
  }
}

/**
 * Create a facility intervention from an insight.
 * @param {number|string} insightId - Source insight ID
 * @param {string} [action] - Optional custom maintenance action
 * @param {string} [measurementType] - 'SIMULATED' or 'MEASURED'
 * @returns {Promise<Object>} Created intervention record with status PLANNED.
 */
export async function createIntervention(insightId, action = null, measurementType = 'SIMULATED') {
  try {
    const payload = {
      insight_id: Number(insightId),
      action: action || undefined,
      measurement_type: measurementType,
    };
    const response = await fetch(`${API_BASE_URL}/interventions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to create intervention (status ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to create intervention:', error);
    throw error;
  }
}

/**
 * Trigger a simulated demo resolution on an intervention.
 * @param {number|string} interventionId - ID of intervention
 * @param {number} [reductionFactor=0.85] - Mitigation factor
 * @returns {Promise<Object>} Updated intervention with COMPLETED status and simulated savings.
 */
export async function simulateIntervention(interventionId, reductionFactor = 0.85) {
  try {
    const response = await fetch(`${API_BASE_URL}/interventions/${interventionId}/simulate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ simulated_reduction_factor: reductionFactor }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Simulation failed (status ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Failed to simulate intervention ${interventionId}:`, error);
    throw error;
  }
}

/**
 * Finalize an intervention as completed.
 * @param {number|string} interventionId - ID of intervention
 * @param {number} [afterValue] - Optional measured physical value
 * @returns {Promise<Object>} Completed intervention.
 */
export async function completeIntervention(interventionId, afterValue = null) {
  try {
    let url = `${API_BASE_URL}/interventions/${interventionId}/complete`;
    if (afterValue !== null && afterValue !== undefined) {
      url += `?after_value=${encodeURIComponent(afterValue)}`;
    }
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Completion failed (status ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Failed to complete intervention ${interventionId}:`, error);
    throw error;
  }
}

/**
 * Fetch list of facility interventions.
 * @param {string} [resource] - Optional resource filter
 * @param {string} [status] - Optional status filter
 * @returns {Promise<Array>} List of intervention records.
 */
export async function getInterventions(resource = null, status = null) {
  try {
    const params = new URLSearchParams();
    if (resource) params.append('resource', resource);
    if (status) params.append('status', status);

    const queryStr = params.toString() ? `?${params.toString()}` : '';
    const response = await fetch(`${API_BASE_URL}/interventions${queryStr}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to fetch interventions (status ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to fetch interventions:', error);
    throw error;
  }
}

/**
 * Fetch aggregate campus impact and savings summary.
 * @returns {Promise<Object>} Summary payload for Water, Electricity, and Waste.
 */
export async function getImpactSummary() {
  try {
    const response = await fetch(`${API_BASE_URL}/impact/summary`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to fetch impact summary (status ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to fetch impact summary:', error);
    throw error;
  }
}

/**
 * Upload a campus telemetry CSV file for ingestion.
 * @param {File} file - The selected CSV file
 * @returns {Promise<Object>} Ingestion summary payload with row counts and error details.
 */
export async function uploadTelemetryCSV(file) {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/ingestion/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Upload failed with status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to upload telemetry CSV:', error);
    throw error;
  }
}

/**
 * Download the canonical CSV template.
 */
export async function downloadCSVTemplate() {
  try {
    const response = await fetch(`${API_BASE_URL}/ingestion/template`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to download template (status ${response.status})`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'campus_resource_template.csv';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Failed to download CSV template:', error);
    throw error;
  }
}
