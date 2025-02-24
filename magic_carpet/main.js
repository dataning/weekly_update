import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.js';
import ErrorBoundary from './ErrorBoundary.js';

const container = document.getElementById('root');
if (!container) throw new Error('Root element not found');

const root = createRoot(container);
root.render(
    React.createElement(ErrorBoundary, null,
        React.createElement(App)
    )
);