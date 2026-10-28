const API_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

export async function fetchAnalysis(month) {
  const response = await fetch(
    `${API_BASE}/api/analysis?month=${encodeURIComponent(month)}`
  );

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`API request failed (${response.status}): ${detail.slice(0, 180)}`);
  }

  return response.json();
}
