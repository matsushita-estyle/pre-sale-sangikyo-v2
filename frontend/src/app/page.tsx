'use client';

import { useEffect, useState } from 'react';

export default function Home() {
  const [backendMessage, setBackendMessage] = useState<string>('Loading...');
  const [backendStatus, setBackendStatus] = useState<string>('');

  useEffect(() => {
    // バックエンドAPIを呼び出す
    const fetchBackend = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/hello?name=Next.js`);
        const data = await response.json();
        setBackendMessage(data.message);
        setBackendStatus('✅ Backend connected');
      } catch (error) {
        setBackendMessage('Failed to connect to backend');
        setBackendStatus('❌ Backend connection failed');
        console.error('Backend error:', error);
      }
    };

    fetchBackend();
  }, []);

  return (
    <main style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1>🚀 Sangikyo V2 - Hello World</h1>

      <div style={{ marginTop: '2rem', padding: '1rem', border: '1px solid #ddd', borderRadius: '8px' }}>
        <h2>Frontend (Next.js)</h2>
        <p>✅ Next.js is running!</p>
        <p style={{ fontSize: '0.9rem', color: '#666' }}>
          This page is served from Azure Static Web Apps
        </p>
      </div>

      <div style={{ marginTop: '1rem', padding: '1rem', border: '1px solid #ddd', borderRadius: '8px' }}>
        <h2>Backend (FastAPI)</h2>
        <p>{backendStatus}</p>
        <p><strong>Message from backend:</strong> {backendMessage}</p>
        <p style={{ fontSize: '0.9rem', color: '#666' }}>
          API URL: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
        </p>
      </div>

      <div style={{ marginTop: '2rem', padding: '1rem', backgroundColor: '#f0f0f0', borderRadius: '8px' }}>
        <h3>Next Steps:</h3>
        <ol>
          <li>Run Terraform to create Azure resources</li>
          <li>Push to GitHub to trigger deployment</li>
          <li>Verify both services are running in Azure</li>
        </ol>
      </div>
    </main>
  );
}
