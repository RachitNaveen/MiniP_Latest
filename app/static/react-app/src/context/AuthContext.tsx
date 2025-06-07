import { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { useSecurity } from '@/context/SecurityContext';

interface User {
  id: string;
  username: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (username: string, password: string, email: string) => Promise<void>;
  error: string | null;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => {},
  logout: async () => {},
  register: async () => {},
  error: null
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { securityFeatures } = useSecurity();

  // Check if user is authenticated on mount
  useEffect(() => {
    // Check current authentication status
    fetch('/api/auth/check')
      .then(res => res.json())
      .then(data => {
        if (data.authenticated) {
          setUser({
            id: data.user.id,
            username: data.user.username
          });
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Error checking authentication:', err);
        setLoading(false);
      });
  }, []);
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        const response = await fetch('/auth/status');
        const data = await response.json();
        
        if (data.authenticated) {
          setUser({
            id: data.user.id,
            username: data.user.username
          });
        }
      } catch (err) {
        console.error('Error checking auth status:', err);
      } finally {
        setLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  // Login function
  const login = async (username: string, password: string, captchaResponse?: string) => {
    setError(null);
    setLoading(true);

    try {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

      const requestBody: any = { username, password };
      if (securityFeatures.requireCaptcha) {
        if (!captchaResponse) {
          throw new Error('CAPTCHA is required');
        }
        requestBody.captcha = captchaResponse;
      }

      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Login failed');
      }

      setUser({
        id: data.user.id,
        username: data.user.username
      });
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const logout = async () => {
    setError(null);
    setLoading(true);
    
    try {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      
      const response = await fetch('/auth/logout', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken
        }
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Logout failed');
      }
      
      setUser(null);
    } catch (err: any) {
      setError(err.message || 'Logout failed');
    } finally {
      setLoading(false);
    }
  };

  // Register function
  const register = async (username: string, password: string, email: string) => {
    setError(null);
    setLoading(true);
    
    try {
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      
      const response = await fetch('/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ username, password, email })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Registration failed');
      }
      
      setUser({
        id: data.user.id,
        username: data.user.username
      });
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        register,
        error
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
