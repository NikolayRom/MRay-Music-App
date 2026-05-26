import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { coreApi } from '../api/instances';
import toast from 'react-hot-toast';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const [passwords, setPasswords] = useState({ new: '', confirm: '' });
  const [error, setError] = useState('');
  const token = searchParams.get('token');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.SyntheticEvent) => {
    e.preventDefault();
    if (passwords.new !== passwords.confirm) {
      setError('Passwords don\'t match');
      return;
    }

    try {
      await coreApi.post('/auth/password/reset', { 
        token, 
        new_password: passwords.new 
      });
      toast.success('Successfully change password! Redirect to /login.');
      setTimeout(() => navigate('/login'), 1500);
    } catch (err) {
      setError('Incorrect link or token expired');
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4 text-white">
      <div className="w-full max-w-md bg-zinc-900 p-8 rounded-2xl border border-zinc-800 shadow-2xl">
        <h1 className="text-2xl font-bold mb-6">Setting new password</h1>
        {error && <div className="mb-4 text-red-500 text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input 
            type="password" placeholder="New Password" required
            className="w-full bg-zinc-800 border border-zinc-700 p-3 rounded-xl outline-none focus:border-green-500"
            value={passwords.new}
            onChange={e => setPasswords({...passwords, new: e.target.value})}
          />
          <input 
            type="password" placeholder="New Password again" required
            className="w-full bg-zinc-800 border border-zinc-700 p-3 rounded-xl outline-none focus:border-green-500"
            value={passwords.confirm}
            onChange={e => setPasswords({...passwords, confirm: e.target.value})}
          />
          <button className="w-full bg-green-500 text-black font-bold py-3 rounded-full hover:scale-105 transition-all">
            Save
          </button>
        </form>
      </div>
    </div>
  );
}