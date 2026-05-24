import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { coreApi } from '../api/instances';
import { ArrowLeft } from 'lucide-react';

export default function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.SyntheticEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await coreApi.post('/auth/registration', {
        username: formData.username,
        email: formData.email,
        password: formData.password
      });
      navigate('/login');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Username or email already exist.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4 text-white">
      <div className="w-full max-w-md bg-zinc-900 p-8 rounded-2xl border border-zinc-800 shadow-2xl">
        
        <div className="absolute top-8 left-8">
          <Link to="/" className="text-white hover:text-green-500 transition-colors flex items-center gap-2">
            <ArrowLeft size={20} /> 
            <span>Home</span>
          </Link>
        </div>
        
        <h1 className="text-3xl font-black mb-8 text-center">Sign up</h1>
        
        {error && <div className="mb-6 p-4 bg-red-500/10 border border-red-500 text-red-500 rounded-xl text-sm">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input 
            type="text" 
            placeholder="Username"
            required
            value={formData.username}
            onChange={(e) => setFormData({...formData, username: e.target.value})}
            className="w-full bg-zinc-800 border border-zinc-700 p-3.5 rounded-xl focus:ring-2 focus:ring-green-500 outline-none"
          />
          <input 
            type="email" 
            placeholder="Email"
            required
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            className="w-full bg-zinc-800 border border-zinc-700 p-3.5 rounded-xl focus:ring-2 focus:ring-green-500 outline-none"
          />
          <input 
            type="password" 
            placeholder="Password"
            required
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            className="w-full bg-zinc-800 border border-zinc-700 p-3.5 rounded-xl focus:ring-2 focus:ring-green-500 outline-none"
          />
          <button 
            type="submit"
            disabled={isLoading}
            className="w-full bg-green-500 text-black font-extrabold py-4 rounded-full hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 mt-6"
          >
            {isLoading ? '...' : 'SIGN UP'}
          </button>
        </form>

        <p className="mt-8 text-center text-zinc-500 text-sm">
          Already in? <Link to="/login" className="text-white font-bold hover:underline ml-1">Sign in</Link>
        </p>
      </div>
    </div>
  );
}