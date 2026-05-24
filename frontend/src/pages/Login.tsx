import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { coreApi } from '../api/instances';
import { useAuthStore } from '../store/useAuthStore';
import { ArrowLeft } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const setAuth = useAuthStore(state => state.setAuth);
  const navigate = useNavigate();

  
  const handleSubmit = async (e: React.SyntheticEvent) => {
    e.preventDefault(); 
    setIsLoading(true);
    setError('');

    try {
      
      const authHeader = btoa(`${username}:${password}`);
      
      const loginResponse = await coreApi.post('/auth/login', {}, {
        headers: { Authorization: `Basic ${authHeader}` }
      });

      const { access_token, refresh_token } = loginResponse.data;

      const userResponse = await coreApi.get('/user/profile', {
        headers: { Authorization: `Bearer ${access_token}` }
      });

      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      setAuth(userResponse.data, access_token, refresh_token);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authorization failed. Check your input.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4 text-white font-sans">
      <div className="w-full max-w-md bg-zinc-900 p-8 rounded-2xl border border-zinc-800 shadow-2xl">
        
        <div className="absolute top-8 left-8">
          <Link to="/" className="text-white hover:text-green-500 transition-colors flex items-center gap-2">
            <ArrowLeft size={20} /> 
            <span>Home</span>
          </Link>
        </div>
        
        <div className="text-center mb-10">
          <h1 className="text-4xl font-black tracking-tight mb-2">Sign in</h1>
          <p className="text-zinc-400 text-sm">We're glad to see you again!</p>
        </div>
        
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 text-red-500 rounded-xl text-sm animate-in fade-in duration-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-wider text-zinc-500 ml-1">Username</label>
            <input 
              type="text" 
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 p-3.5 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition-all placeholder:text-zinc-600"
              placeholder="Username"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-wider text-zinc-500 ml-1">Password</label>
            <input 
              type="password" 
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 p-3.5 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition-all placeholder:text-zinc-600"
              placeholder="••••••••"
            />
          </div>
          <button 
            type="submit"
            disabled={isLoading}
            className="w-full bg-green-500 text-black font-extrabold py-4 rounded-full hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 shadow-lg shadow-green-500/20 mt-6"
          >
            {isLoading ? '...' : 'SIGN IN'}
          </button>
        </form>

        <p className="mt-10 text-center text-zinc-500 text-sm">
          Still not in? <Link to="/register" className="text-white font-bold hover:text-green-400 transition-colors ml-1">Sign up</Link>
        </p>
      </div>
    </div>
  );
}