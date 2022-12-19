import React from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from 'react-query';
import App from './components/App';

const container = document.getElementById('app');
const root = createRoot(container);
const queryClient = new QueryClient();
root.render(<QueryClientProvider client={queryClient} contextSharing><App /></QueryClientProvider>);
