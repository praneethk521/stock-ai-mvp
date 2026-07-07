const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export type ApiErrorPayload = {
  error: {
    code: string;
    message: string;
    status_code: number;
    request_id?: string | null;
    details?: unknown;
  };
};

export class ApiError extends Error {
  status: number;
  code: string;
  requestId?: string | null;

  constructor(payload: ApiErrorPayload, fallbackStatus: number) {
    super(payload.error.message);
    this.name = 'ApiError';
    this.status = payload.error.status_code || fallbackStatus;
    this.code = payload.error.code;
    this.requestId = payload.error.request_id;
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { next: { revalidate: 60 } });
  if (!res.ok) throw await toApiError(res);
  return res.json();
}

export async function apiSend<T>(path: string, init: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init.headers ?? {}),
    },
    cache: 'no-store',
  });
  if (!res.ok) throw await toApiError(res);
  return res.json();
}

export function apiErrorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return {
      title: `${error.code.replaceAll('_', ' ')} (${error.status})`,
      message: error.message,
      requestId: error.requestId,
    };
  }
  return {
    title: 'Request failed',
    message: error instanceof Error ? error.message : 'Unexpected API error',
    requestId: null,
  };
}

async function toApiError(res: Response) {
  try {
    const payload = await res.json() as ApiErrorPayload;
    if (payload.error?.message) return new ApiError(payload, res.status);
  } catch {
    // Fall through to the generic error below.
  }
  return new ApiError({
    error: {
      code: 'api_error',
      message: `API error: ${res.status}`,
      status_code: res.status,
      request_id: res.headers.get('x-request-id'),
    },
  }, res.status);
}
