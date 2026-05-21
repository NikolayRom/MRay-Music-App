import { Home, Search, Library, PlusSquare, Heart } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

export const Sidebar = () => {
  const location = useLocation();

  const navItems = [
    { name: 'Home', icon: Home, path: '/' },
    { name: 'Search', icon: Search, path: '/search' },
    { name: 'Library', icon: Library, path: '/library' },
  ];

  return (
    <div className="w-64 bg-black h-full flex flex-col p-6 gap-6">
      <div className="text-white text-2xl font-bold mb-4">MRay</div>
      
      <nav className="flex flex-col gap-4">
        {navItems.map(item => (
          <Link 
            key={item.path}
            to={item.path} 
            className={`flex items-center gap-4 transition-colors ${
              location.pathname === item.path ? "text-white" : "text-zinc-400 hover:text-white"
            }`}
          >
            <item.icon size={24} /> 
            <span className="font-semibold">{item.name}</span>
          </Link>
        ))}
      </nav>

      <div className="mt-8 flex flex-col gap-4">
        <button className="flex items-center gap-4 text-zinc-400 hover:text-white transition-colors">
          <div className="bg-green-500 p-1 rounded-sm text-black">
            <PlusSquare size={16} />
          </div>
          <span className="font-semibold text-sm">Create playlist</span>
        </button>
        <button className="flex items-center gap-4 text-zinc-400 hover:text-white transition-colors">
          <div className="bg-green-500 p-1 rounded-sm text-black">
            <Heart size={16} fill="black" />  
          </div>
          <span className="font-semibold text-sm">Favorite tracks</span>
        </button>
      </div>
      
      <div className="mt-auto pt-4 border-t border-zinc-800 text-[11px] text-zinc-500">
        MRay • FastAPI + React
      </div>
    </div>
  );
};