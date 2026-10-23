import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient, getCookie, ApiError } from '../api/client';

describe('apiClient and CSRF integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    // Clear cookies
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  });

  it('correctly extracts csrf_token from document.cookie', () => {
    document.cookie = 'other_val=123';
    document.cookie = 'csrf_token=test-csrf-secret-9988';
    document.cookie = 'another=abc';
    expect(getCookie('csrf_token')).toBe('test-csrf-secret-9988');
  });

  it('automatically attaches X-CSRF-Token on POST requests when csrf_token cookie exists', async () => {
    document.cookie = 'csrf_token=my-secret-csrf-token';

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ success: true }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await apiClient('/api/v1/auth/logout', { method: 'POST' });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/v1/auth/logout');
    expect(init.credentials).toBe('include');
    expect(init.headers.get('X-CSRF-Token')).toBe('my-secret-csrf-token');
  });

  it('does NOT attach X-CSRF-Token on GET requests', async () => {
    document.cookie = 'csrf_token=my-secret-csrf-token';

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: '123' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await apiClient('/api/v1/auth/me', { method: 'GET' });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers.get('X-CSRF-Token')).toBeNull();
  });

  it('throws structured ApiError when server returns non-ok status', async () => {
    const errorPayload = {
      error: 'Invalid username or password',
      code: 'HTTP_ERROR',
      request_id: 'req-12345',
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => errorPayload,
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      apiClient('/api/v1/auth/login', { method: 'POST', body: '{}' })
    ).rejects.toThrow(ApiError);
  });
});
