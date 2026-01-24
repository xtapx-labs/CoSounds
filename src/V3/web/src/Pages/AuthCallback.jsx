import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';

export const AuthCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const handleAuth = async () => {
      try {
        // Get the session after OAuth redirect
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        
        if (sessionError) {
          console.error('Session error:', sessionError);
          navigate('/login');
          return;
        }

        if (session) {
          // Check if user has non-default preferences in database
          try {
            const token = session.access_token;
            const response = await fetch(`${import.meta.env.VITE_API_URL}/api/preferences/exists`, {
              headers: { Authorization: `Bearer ${token}` }
            });
            const result = await response.json();

            if (result.exists && !result.isDefault) {
              navigate('/vote', { replace: true });
            } else {
              navigate('/preferences', { replace: true });
            }
          } catch {
            navigate('/preferences', { replace: true });
          }
        } else {
          navigate('/login');
        }
      } catch (error) {
        console.error('Auth callback error:', error);
        navigate('/login');
      }
    };

    handleAuth();
  }, [navigate]);

  return null;
};
