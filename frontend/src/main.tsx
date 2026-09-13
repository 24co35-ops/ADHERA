import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App } from './App';
import { inject } from '@vercel/analytics';
import './styles/global.css';

// Initialize privacy-friendly Vercel Analytics if not explicitly opted-out
try {
  const consent = typeof window !== 'undefined' ? localStorage.getItem('adhera_cookie_consent') : null;
  if (consent !== 'essential') {
    inject();
  }
} catch {}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);
