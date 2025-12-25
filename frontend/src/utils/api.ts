/**
 * api.ts
 * Helper functions for API calls used across the frontend.
 * Provides `fetchFromAPI`, `postToAPI`, and `deleteFromAPI`.
 */

let API_BASE: string = '';

if (import.meta.env && import.meta.env.VITE_API_BASE_URL) {
  API_BASE = import.meta.env.VITE_API_BASE_URL as string;
} else {
  const hostname = window.location.hostname;
  API_BASE = `http://${hostname}:8000`;
}

export class ApiError extends Error {
  public status: number;
  public data: any;

  constructor(message: string, status: number, data: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

type QueryParams = Record<string, string | number | boolean | null | undefined | (string | number | boolean)[]>;

interface RequestOptions extends RequestInit {
  timeout?: number;
  params?: QueryParams;
  headers?: Record<string, string>;
}

// 4. Helper Functions
function buildUrl(endpoint: string, params?: QueryParams): string {
  const base = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  if (!params) return base;

  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null) return;
    if (Array.isArray(v)) {
      v.forEach((item) => usp.append(k, String(item)));
    } else {
      usp.append(k, String(v));
    }
  });

  const suffix = usp.toString();
  return suffix ? `${base}${base.includes('?') ? '&' : '?'}${suffix}` : base;
}

function getAuthHeader(): Record<string, string> {
  try {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}

async function parseResponseBody(res: Response): Promise<any> {
  const contentType = res.headers.get('content-type') || '';
  // 204 No Content
  if (!contentType || res.status === 204) return null;
  if (contentType.includes('application/json')) return res.json();
  return res.text();
}

function makeTimeoutController(timeout?: number, externalSignal?: AbortSignal) {
  if (externalSignal) return { signal: externalSignal, cancel: () => {} };
  if (!timeout) return { signal: undefined, cancel: () => {} };

  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  return { signal: controller.signal, cancel: () => clearTimeout(id) };
}

/**
 * Checks if the response body contains an explicit error field
 * (common in some API patterns even if status is 200)
 */
function isApiErrorPayload(data: any): boolean {
  if (!data || typeof data !== 'object') return false;
  if (data.error) return true;
  if (data.success === false) return true;
  if (typeof data.status === 'string' && data.status.toLowerCase() === 'error') return true;
  return false;
}

/**
 * Core wrapper around fetch to handle timeouts, parsing, and error throwing.
 */
async function callAPI<T>(url: string, options: RequestOptions): Promise<T> {
  const { timeout = 10000, signal: externalSignal, ...fetchOptions } = options;
  const { signal, cancel } = makeTimeoutController(timeout, externalSignal);

  try {
    const res = await fetch(url, { ...fetchOptions, signal });
    const data = await parseResponseBody(res);

    // Check for "soft" errors (200 OK but body says error)
    if (isApiErrorPayload(data)) {
      const message = (data && (data.message || data.detail)) || res.statusText || 'Request failed';
      throw new ApiError(message, res.status, data);
    }

    // Check for actual HTTP errors (4xx, 5xx)
    if (!res.ok) {
      let message = res.statusText || 'Request failed';

      if (data) {
        if (data.message) {
          message = data.message;
        } else if (data.detail) {
          // Handle FastAPI/Pydantic validation errors which are arrays
          if (Array.isArray(data.detail)) {
            try {
              message = data.detail
                .map((d: any) => {
                  const loc = Array.isArray(d.loc) ? d.loc.join('.') : d.loc || '';
                  return loc ? `${loc}: ${d.msg}` : d.msg;
                })
                .join('; ');
            } catch (e) {
              message = JSON.stringify(data.detail);
            }
          } else {
            message = String(data.detail);
          }
        } else {
          // Fallback to stringifying data if no specific message field
          try {
            message = JSON.stringify(data);
          } catch (e) {
            /* ignore */
          }
        }
      }
      throw new ApiError(message, res.status, data);
    }

    return data as T;
  } catch (err: any) {
    if (err.name === 'AbortError') {
      throw new ApiError('Request timed out', 0, null);
    }
    throw err;
  } finally {
    cancel();
  }
}

// 5. Exported Functions

export async function fetchFromAPI<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers = {}, ...restOptions } = options;
  const url = buildUrl(endpoint, params);
  const authHeader = getAuthHeader();

  return callAPI<T>(url, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      ...authHeader,
      ...headers,
    },
    ...restOptions,
  });
}

export async function postToAPI<T = any>(
  endpoint: string,
  body: any = {},
  options: RequestOptions = {}
): Promise<T> {
  const { headers = {}, ...restOptions } = options;
  const url = buildUrl(endpoint);
  const authHeader = getAuthHeader();

  const finalHeaders: Record<string, string> = {
    Accept: 'application/json',
    ...authHeader,
    ...headers,
  };

  const specifiedContentType =
    finalHeaders['Content-Type'] || finalHeaders['content-type'];

  // Default to JSON unless specified otherwise
  const contentType = specifiedContentType || 'application/json';

  let payload: BodyInit | null;

  if (contentType.includes('application/json')) {
    payload = JSON.stringify(body);
    if (!specifiedContentType) {
      finalHeaders['Content-Type'] = 'application/json';
    }
  } else {
    payload = body;
    // If sending FormData, let the browser set the Content-Type header with the boundary
    if (payload instanceof FormData && finalHeaders['Content-Type']) {
      delete finalHeaders['Content-Type'];
    }
  }

  return callAPI<T>(url, {
    method: 'POST',
    headers: finalHeaders,
    body: payload,
    ...restOptions,
  });
}

export async function deleteFromAPI<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { headers = {}, ...restOptions } = options;
  const url = buildUrl(endpoint);
  const authHeader = getAuthHeader();

  return callAPI<T>(url, {
    method: 'DELETE',
    headers: {
      Accept: 'application/json',
      ...authHeader,
      ...headers,
    },
    ...restOptions,
  });
}
