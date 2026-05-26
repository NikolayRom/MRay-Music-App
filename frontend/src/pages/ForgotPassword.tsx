import { useState } from 'react';
import { coreApi } from '../api/instances';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.SyntheticEvent) => {
    e.preventDefault();
    await coreApi.post('/auth/password/forgot', { email });
    setSent(true);
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4 text-white">
      <div className="w-full max-w-md bg-zinc-900 p-8 rounded-2xl border border-zinc-800 shadow-2xl">
        <h1 className="text-2xl font-bold mb-6">Password Reset</h1>
        {!sent ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <p className="text-zinc-400 text-sm">Enter email to get reset link.</p>
            <input 
              type="email" required value={email} onChange={e => setEmail(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 p-3 rounded-xl outline-none focus:border-green-500"
              placeholder="Email"
            />
            <button className="w-full bg-green-500 text-black font-bold py-3 rounded-full hover:scale-105 transition-all">
              Send
            </button>
          </form>
        ) : (
          <p className="text-green-500">Check your email!</p>
        )}
      </div>
    </div>
  );
}