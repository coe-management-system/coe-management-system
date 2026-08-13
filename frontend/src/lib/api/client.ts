// API Client Abstraction Layer
// Standardized wrapper for simulated network calls in mock mode,
// easily swappable with fetch/axios for production FastAPI endpoints.

const MOCK_DELAY_MS = 250;

export async function mockApiCall<T>(data: T, delayMs: number = MOCK_DELAY_MS): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(data);
    }, delayMs);
  });
}
