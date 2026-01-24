import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';

export const AuthTest = () => {
  const [status, setStatus] = useState({
    supabaseConnected: false,
    sessionExists: false,
    userInfo: null,
    error: null,
    redirectUrl: '',
    currentUrl: '',
  });

  useEffect(() => {
    const testAuth = async () => {
      try {
        // Test Supabase connection
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();

        setStatus({
          supabaseConnected: !sessionError,
          sessionExists: !!session,
          userInfo: session?.user || null,
          error: sessionError?.message || null,
          redirectUrl: `${window.location.origin}/auth/callback`,
          currentUrl: window.location.href,
        });
      } catch (err) {
        setStatus(prev => ({
          ...prev,
          error: err.message,
        }));
      }
    };

    testAuth();
  }, []);

  const testGoogleLogin = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      });

      if (error) {
        setStatus(prev => ({ ...prev, error: error.message }));
      }
    } catch (err) {
      setStatus(prev => ({ ...prev, error: err.message }));
    }
  };

  return (
    <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto', fontFamily: 'monospace' }}>
      <h1 style={{ color: '#fff' }}>🔍 Authentication Diagnostic</h1>

      <div style={{ background: '#1a1a1a', padding: '20px', borderRadius: '8px', marginTop: '20px' }}>
        <h2 style={{ color: '#4ade80', marginTop: 0 }}>Connection Status</h2>

        <div style={{ marginBottom: '10px' }}>
          <strong style={{ color: '#fff' }}>Supabase Connected: </strong>
          <span style={{ color: status.supabaseConnected ? '#4ade80' : '#ef4444' }}>
            {status.supabaseConnected ? '✓ Yes' : '✗ No'}
          </span>
        </div>

        <div style={{ marginBottom: '10px' }}>
          <strong style={{ color: '#fff' }}>Session Exists: </strong>
          <span style={{ color: status.sessionExists ? '#4ade80' : '#ef4444' }}>
            {status.sessionExists ? '✓ Yes' : '✗ No'}
          </span>
        </div>

        <div style={{ marginBottom: '10px' }}>
          <strong style={{ color: '#fff' }}>Current URL: </strong>
          <span style={{ color: '#60a5fa' }}>{status.currentUrl}</span>
        </div>

        <div style={{ marginBottom: '10px' }}>
          <strong style={{ color: '#fff' }}>Redirect URL: </strong>
          <span style={{ color: '#60a5fa' }}>{status.redirectUrl}</span>
        </div>

        {status.error && (
          <div style={{ marginTop: '20px', padding: '15px', background: '#ef4444', borderRadius: '4px' }}>
            <strong style={{ color: '#fff' }}>Error: </strong>
            <span style={{ color: '#fff' }}>{status.error}</span>
          </div>
        )}

        {status.userInfo && (
          <div style={{ marginTop: '20px', padding: '15px', background: '#4ade80', color: '#000', borderRadius: '4px' }}>
            <strong>Logged in as: </strong>
            {status.userInfo.email}
          </div>
        )}
      </div>

      <div style={{ marginTop: '30px' }}>
        <h2 style={{ color: '#fff' }}>Instructions:</h2>
        <ol style={{ color: '#9ca3af', lineHeight: '1.8' }}>
          <li>Make sure this URL is added to Supabase redirect URLs: <code style={{ color: '#60a5fa' }}>{status.redirectUrl}</code></li>
          <li>Make sure Google OAuth is enabled in Supabase dashboard</li>
          <li>Make sure <code style={{ color: '#60a5fa' }}>https://bjieozmcptbxgbvzpfyc.supabase.co/auth/v1/callback</code> is in Google OAuth settings</li>
          <li>Click the button below to test Google login</li>
        </ol>
      </div>

      <button
        onClick={testGoogleLogin}
        style={{
          background: 'linear-gradient(135deg, #4285F4 0%, #357ae8 100%)',
          border: 'none',
          borderRadius: '8px',
          padding: '12px 24px',
          color: 'white',
          fontSize: '16px',
          fontWeight: '600',
          cursor: 'pointer',
          marginTop: '20px',
        }}
      >
        Test Google Login
      </button>
    </div>
  );
};
