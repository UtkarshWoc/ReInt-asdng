import {
  AccuracySummaryResponse,
  DailyAccuracyPoint,
  ForecastAtDecisionResponse,
  ForecastRevisionsResponse,
  HorizonAccuracyPoint,
  HourAccuracyPoint,
  MetaResponse,
  RiskBufferResponse,
} from "../types";

const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

async function fetchJson<T>(url: string): Promise<T> {
  const fullUrl = `${API_BASE}${url}`;
  const res = await fetch(fullUrl);
  if (!res.ok) {
    let errMessage = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const errObj = await res.json();
      if (errObj.detail) errMessage = errObj.detail;
    } catch {
      // ignore
    }
    throw new Error(errMessage);
  }

  const contentType = res.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    const preview = await res.text();
    throw new Error(
      `Received non-JSON response from API (${contentType}): ${preview.slice(0, 120)}`
    );
  }

  return res.json() as Promise<T>;
}

export const api = {
  getMeta: () => fetchJson<MetaResponse>("/api/meta"),

  getForecastAtDecision: (deliveryDate: string, cutoff: string = "09:00") =>
    fetchJson<ForecastAtDecisionResponse>(
      `/api/forecast/at-decision?delivery_date=${encodeURIComponent(deliveryDate)}&cutoff=${encodeURIComponent(cutoff)}`,
    ),

  getForecastRevisions: (targetTime: string, cutoff: string = "09:00") =>
    fetchJson<ForecastRevisionsResponse>(
      `/api/forecast/revisions?target_time=${encodeURIComponent(targetTime)}&cutoff=${encodeURIComponent(cutoff)}`,
    ),

  getAccuracySummary: (start?: string, end?: string, cutoff: string = "09:00") => {
    const params = new URLSearchParams({ cutoff });
    if (start) params.set("start", start);
    if (end) params.set("end", end);
    return fetchJson<AccuracySummaryResponse>(`/api/accuracy/summary?${params.toString()}`);
  },

  getAccuracyByHorizon: (start?: string, end?: string, cutoff: string = "09:00") => {
    const params = new URLSearchParams({ cutoff });
    if (start) params.set("start", start);
    if (end) params.set("end", end);
    return fetchJson<HorizonAccuracyPoint[]>(`/api/accuracy/by-horizon?${params.toString()}`);
  },

  getAccuracyByHour: (start?: string, end?: string, cutoff: string = "09:00") => {
    const params = new URLSearchParams({ cutoff });
    if (start) params.set("start", start);
    if (end) params.set("end", end);
    return fetchJson<HourAccuracyPoint[]>(`/api/accuracy/by-hour?${params.toString()}`);
  },

  getAccuracyTimeseries: (start?: string, end?: string, cutoff: string = "09:00") => {
    const params = new URLSearchParams({ cutoff });
    if (start) params.set("start", start);
    if (end) params.set("end", end);
    return fetchJson<DailyAccuracyPoint[]>(`/api/accuracy/timeseries?${params.toString()}`);
  },

  getRiskBuffer: (deliveryDate: string, quantile: number = 0.90, cutoff: string = "09:00") =>
    fetchJson<RiskBufferResponse>(
      `/api/accuracy/risk-buffer?delivery_date=${encodeURIComponent(deliveryDate)}&quantile=${quantile}&cutoff=${encodeURIComponent(cutoff)}`,
    ),
};
