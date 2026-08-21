'use client';

/**
 * AutoLogin — silently logs the user in as the demo user on first load.
 * If an auth token already exists in the Zustand store, this is a no-op.
 */
import { useEffect, useRef } from 'react';
import { useStore } from '@/store';
import { authApi } from '@/lib/api';

export default function AutoLogin() {
  const { accessToken, setAuth } = useStore();
  const attempted = useRef(false);

  useEffect(() => {
    // Already authenticated — nothing to do
    if (accessToken) return;
    // Prevent double-firing in strict mode
    if (attempted.current) return;
    attempted.current = true;

    authApi
      .demoLogin()
      .then((data: any) => {
        setAuth(
          {
            id: data.user_id,
            username: data.username,
            email: 'demo@ai-workforce.app',
            role: data.role,
          },
          data.access_token
        );
      })
      .catch(() => {
        // Silently fail — user can log in manually if needed
      });
  }, [accessToken, setAuth]);

  return null; // This component renders nothing
}
