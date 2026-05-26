import { Home, Search, Library, LogIn, UserPlus, LogOut, SettingsIcon } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { MediaImage } from './MediaImage';

export const Sidebar = () => {
  const location = useLocation();
  const {user, isAuthenticated, logout} = useAuthStore()
  const navItems = [
    { name: 'Home', icon: Home, path: '/' },
    { name: 'Search', icon: Search, path: '/search' },
    { name: 'Library', icon: Library, path: '/library' },
  ];

  return (
    <div className="w-64 bg-black h-full flex flex-col p-6 gap-6">
      <div className="text-white text-2xl font-bold mb-4">MRay</div>
      
      <nav className="flex flex-col gap-8">
        {navItems.map(item => (
          <Link 
            key={item.path}
            to={item.path} 
            className={`flex items-center gap-5 transition-all duration-200 py-2 ${
              location.pathname === item.path 
                ? "text-white" 
                : "text-zinc-400 hover:text-white hover:translate-x-1"
            }`}
          >
            <item.icon size={32} /> 
            <span className="font-semibold">{item.name}</span>
          </Link>
        ))}
      </nav>

      <div className="mt-auto flex flex-col gap-4 pb-24">
        {isAuthenticated && user ? (
          
          <div className="flex flex-col gap-4 p-4 bg-zinc-900 rounded-xl border border-zinc-800 transition-all hover:bg-zinc-800/50 group">
            {/* Кликабельная область профиля */}
            <Link to="/settings" className="flex items-center gap-3 cursor-pointer">
              <div className="relative">
                <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-black font-bold overflow-hidden">
                  {user.image_key ? (
                    <MediaImage imageKey={user.image_key} type="user" className="w-full h-full" />
                  ) : (
                    user.username[0].toUpperCase()
                  )}
                </div>
                {/* Иконка настроек, появляющаяся при наведении */}
                <div className="absolute inset-0 bg-black/40 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <SettingsIcon size={16} className="text-white" />
                </div>
              </div>
              
              <div className="overflow-hidden flex-1">
                <p className="text-white font-bold truncate group-hover:text-green-500 transition-colors">
                  {user.username}
                </p>
                <p className="text-zinc-500 text-xs truncate">{user.email}</p>
              </div>
            </Link>

            <div className="h-px bg-zinc-800 w-full" />

            <button 
              onClick={logout}
              className="flex items-center gap-2 text-zinc-400 hover:text-red-400 transition-colors text-sm font-semibold"
            >
              <LogOut size={18} /> Sign out
            </button>
          </div>
        ) : (
          
          <div className="flex flex-col gap-2">
            <Link to="/login" className="flex items-center gap-3 p-3 text-zinc-400 hover:text-white transition-colors font-bold">
              <LogIn size={20} /> Sign in
            </Link>
            <Link to="/register" className="flex items-center gap-3 p-3 bg-gradient-to-b from-green-600 to-green-400 text-black rounded-full hover:scale-105 transition-transform font-bold justify-center">
              <UserPlus size={20} /> Sign Up
            </Link>
          </div>
        )}
        <div className="pt-4 border-t border-zinc-800 text-[11px] text-zinc-500">
          MRay • FastAPI + React
        </div>
      </div>
    </div>
  );
};