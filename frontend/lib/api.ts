const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export interface MetricsResponse {
  total_records?: number
  columns?: string[]
  date_range?: {
    start: string | null
    end: string | null
  }
  [key: string]: any
}

export interface Anomaly {
  date: string
  hrv?: number
  resting_hr?: number
  sleep_score?: number
  steps?: number
  is_anomalous?: boolean
  anomaly_severity?: number
  [key: string]: any
}

export interface ExplanationResponse {
  explanation: string
}

export interface BlobPathResponse {
  blob_path: string
}

export interface PipelineRunResponse {
  status: string
  recent_anomalies: Anomaly[]
  explanation: string
  parquet_path: string
  blob_path?: string
  metrics_count: number
}

export interface MetricsHistoryResponse {
  dates: string[]
  hrv: number[]
  resting_hr: number[]
  sleep_score: number[]
  steps: number[]
  recovery_index?: (number | null)[]
  movement_index?: (number | null)[]
  active_minutes?: (number | null)[]
  vo2_max?: (number | null)[]
  low_hrv_flag: boolean[]
  high_rhr_flag: boolean[]
  low_sleep_flag: boolean[]
  low_steps_flag: boolean[]
  is_anomalous: boolean[]
  anomaly_severity: number[]
  date_range: {
    start: string
    end: string
  }
  total_records: number
}

class ApiClient {
  private baseUrl: string

  constructor() {
    this.baseUrl = BASE_URL
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`
      try {
        const error = await response.json()
        errorMessage = error.detail || error.message || errorMessage
      } catch {
        // If response is not JSON, use status text
        errorMessage = response.statusText || errorMessage
      }
      const error = new Error(errorMessage)
      // Add status code to error for better handling
      ;(error as any).status = response.status
      throw error
    }

    return response.json()
  }

  async getMetrics(): Promise<MetricsResponse> {
    return this.fetch<MetricsResponse>('/pipeline/metrics')
  }

  async getAnomalies(): Promise<Anomaly[]> {
    return this.fetch<Anomaly[]>('/pipeline/anomalies')
  }

  async getExplanation(): Promise<ExplanationResponse> {
    return this.fetch<ExplanationResponse>('/pipeline/explanation')
  }

  async getBlobPath(): Promise<BlobPathResponse> {
    return this.fetch<BlobPathResponse>('/pipeline/blob-path')
  }

  async runPipeline(daysBack: number = 14): Promise<PipelineRunResponse> {
    // FastAPI accepts query parameters for POST requests
    return this.fetch<PipelineRunResponse>(`/pipeline/run?days_back=${daysBack}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
  }

  async healthCheck(): Promise<{ status: string }> {
    return this.fetch<{ status: string }>('/health')
  }

  async getMetricsHistory(params: { days?: number; end_date?: string }): Promise<MetricsHistoryResponse> {
    const queryParams = new URLSearchParams()
    if (params.days !== undefined && params.days !== null) {
      queryParams.append('days', params.days.toString())
    }
    if (params.end_date) {
      queryParams.append('end_date', params.end_date)
    }
    const queryString = queryParams.toString()
    const url = `/pipeline/metrics/history${queryString ? `?${queryString}` : ''}`
    return this.fetch<MetricsHistoryResponse>(url)
  }
}

export const apiClient = new ApiClient()

