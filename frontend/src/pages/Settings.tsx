import React, { useState } from 'react';
import axios from 'axios'; 
import { useAuthStore } from '../store/useAuthStore';
import { MediaImage } from '../components/MediaImage';
import { Camera, Lock, User as UserIcon, Mail } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Settings() {
  const { user, updateUserData, isAuthenticated } = useAuthStore();
  const navigate = useNavigate()

  if (!isAuthenticated) {
    navigate('/login')
  }

  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    oldPassword: '',
    newPassword: '',
    confirmNewPassword: '', 
  });
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [status, setStatus] = useState<{type: 'success' | 'error', msg: string} | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
    }
  };

  const handleUpdateProfile = async (e: React.SyntheticEvent) => {
    e.preventDefault();
    setStatus(null);

    if (formData.newPassword && !formData.confirmNewPassword) {
      setStatus({ type: 'error', msg: 'Enter new password again' });
      return;
    }

    
    if (formData.newPassword && formData.newPassword !== formData.confirmNewPassword) {
      setStatus({ type: 'error', msg: 'New passwords don\'t match' });
      return;
    }

    
    if (!formData.oldPassword) {
      setStatus({ type: 'error', msg: 'Enter old password for edit profile' });
      return;
    }

    const data = new FormData();
    if (formData.username !== user?.username) data.append('new_username', formData.username);
    if (formData.email !== user?.email) data.append('new_email', formData.email);
    if (file) data.append('avatar', file);
    if (formData.newPassword) {
      data.append('new_password', formData.newPassword);
      data.append('new_password2', formData.confirmNewPassword);
    }
    
    try {
      
      const authHeader = btoa(unescape(encodeURIComponent(`${user?.username}:${formData.oldPassword}`)));
      
      const response = await axios.patch(
          `${import.meta.env.VITE_CORE_API_URL}/user/profile`, data, {
        headers: { 
          'Authorization': `Basic ${authHeader}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      updateUserData(response.data);
      setStatus({ type: 'success', msg: 'Successfully update profile!' });
      setFormData({ ...formData, oldPassword: '', newPassword: '', confirmNewPassword: '' });
      setFile(null);
    } catch (err: any) {
      setStatus({ type: 'error', msg: err.response?.data?.detail || 'Incorrect password or user data' });
    }
  };

  return (
    <div className="p-8 text-white max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Profile Settings</h1>

      <form onSubmit={handleUpdateProfile} className="space-y-8">
        
        <div className="flex items-center gap-6 bg-zinc-900 p-6 rounded-2xl border border-zinc-800">
          <div className="relative group">
            <div className="w-32 h-32 rounded-full overflow-hidden border-2 border-zinc-700">
              {preview ? (
                <img src={preview} className="w-full h-full object-cover" />
              ) : (
                <MediaImage imageKey={user?.image_key} type="user" className="w-full h-full" />
              )}
            </div>
            <label className="absolute inset-0 flex items-center justify-center bg-black/60 opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity rounded-full">
              <Camera size={24} />
              <input type="file" className="hidden" accept="image/*" onChange={handleFileChange} />
            </label>
          </div>
          <div>
            <h3 className="font-bold text-xl">{user?.username}</h3>
            <p className="text-zinc-400 text-sm">Select photo</p>
          </div>
        </div>

        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase text-zinc-500 flex items-center gap-2"><UserIcon size={14}/>Username</label>
              <input 
                type="text" 
                value={formData.username}
                onChange={e => setFormData({...formData, username: e.target.value})}
                className="w-full bg-zinc-900 border border-zinc-800 p-3 rounded-xl outline-none focus:border-green-500"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase text-zinc-500 flex items-center gap-2"><Mail size={14}/> Email</label>
              <input 
                type="email" 
                value={formData.email}
                onChange={e => setFormData({...formData, email: e.target.value})}
                className="w-full bg-zinc-900 border border-zinc-800 p-3 rounded-xl outline-none focus:border-green-500"
              />
            </div>
          </div>

          <div className="h-px bg-zinc-800 my-6" />

          
          <h2 className="text-xl font-bold flex items-center gap-2"><Lock size={20}/>Security</h2>
          <p className="text-sm text-zinc-400">Enter old password for edit profile.</p>
          
          <input 
            type="password" 
            placeholder="Password"
            value={formData.oldPassword}
            onChange={e => setFormData({...formData, oldPassword: e.target.value})}
            className="w-full bg-zinc-900 border border-zinc-800 p-3 rounded-xl outline-none focus:border-green-500"
          />
          <div className="grid grid-cols-2 gap-4">
            <input 
              type="password" 
              placeholder="New Password (optional)"
              value={formData.newPassword}
              onChange={e => setFormData({...formData, newPassword: e.target.value})}
              className="w-full bg-zinc-900 border border-zinc-800 p-3 rounded-xl outline-none focus:border-green-500"
            />
            <input 
              type="password" 
              placeholder="New Password again (optional)"
              value={formData.confirmNewPassword}
              onChange={e => setFormData({...formData, confirmNewPassword: e.target.value})}
              className="w-full bg-zinc-900 border border-zinc-800 p-3 rounded-xl outline-none focus:border-green-500"
            />
          </div>
        </div>

        {status && (
          <div className={`p-4 rounded-xl text-sm ${status.type === 'success' ? 'bg-green-500/10 text-green-500 border border-green-500/50' : 'bg-red-500/10 text-red-500 border border-red-500/50'}`}>
            {status.msg}
          </div>
        )}

        <button type="submit" className="bg-white text-black font-bold px-8 py-3 rounded-full hover:scale-105 transition-all">
          Save
        </button>
      </form>
    </div>
  );
}