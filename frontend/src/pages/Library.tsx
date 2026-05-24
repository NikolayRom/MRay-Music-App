import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Heart, History, Plus, Play, ListMusic } from 'lucide-react';
import { usePlaylistStore } from '../store/usePlaylistStore';
import { MediaImage } from '../components/MediaImage';
import { CreatePlaylistModal } from '../components/CreatePlaylistModal';
import { useAuthStore } from '../store/useAuthStore';

export default function Library() {
  const { playlists } = usePlaylistStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center h-[80vh] text-center p-8">
        <div className="p-6 bg-zinc-900 rounded-full mb-6">
          <ListMusic size={64} className="text-zinc-500" />
        </div>
        <h1 className="text-3xl font-bold mb-4">Enjoy your favorite tracks</h1>
        <p className="text-zinc-400 mb-8 max-w-md">
          Log in to create playlists, like tracks, and view your listening history.
        </p>
        <div className="flex gap-4">
          <Link to="/login" className="bg-white text-black px-8 py-3 rounded-full font-bold hover:scale-105 transition-all">
            Sign in
          </Link>
          <Link to="/register" className="bg-zinc-900 text-white border border-zinc-700 px-8 py-3 rounded-full font-bold hover:scale-105 transition-all">
            Sign up
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 text-white pb-32">
      <h1 className="text-3xl font-bold mb-8">Your library</h1>
      
      
      <div className="flex gap-6 mb-12">
        <Link to="/library/liked" className="flex-1 bg-gradient-to-br from-green-500 to-green-900 p-6 rounded-xl hover:shadow-xl transition-all flex flex-col justify-end min-h-[200px] group relative">
           <Heart size={64} fill='black' stroke='black' className="mb-4" />
           <h2 className="text-4xl font-black">Favorite tracks</h2>
           <p className="font-medium mt-2">Your collection</p>
           <div className="absolute bottom-6 right-6 p-4 bg-green-500 rounded-full text-black shadow-2xl opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all hover:scale-110">
              <Play fill="black" />
           </div>
        </Link>

        <Link to="/library/history" className="w-64 bg-zinc-900 p-6 rounded-xl hover:bg-zinc-800 transition-all flex flex-col justify-center items-center gap-4 text-center group">
           <div className="p-4 bg-zinc-800 rounded-full text-green-500 group-hover:bg-zinc-700 transition-colors">
              <History size={48} />
           </div>
           <h2 className="text-xl font-bold">History</h2>
        </Link>
      </div>

      
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Your playlists</h2>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="p-2 bg-zinc-800 hover:bg-zinc-700 rounded-full transition-colors"
          title="Create playlist"
        >
          <Plus size={24} />
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
        {playlists.map(playlist => (
          <Link key={playlist.id} to={`/playlist/${playlist.id}`} className="p-4 bg-zinc-900/40 hover:bg-zinc-800/60 rounded-xl transition-all group cursor-pointer border border-transparent hover:border-zinc-700">
            <div className="aspect-square mb-4 shadow-lg rounded-md overflow-hidden relative">
              <MediaImage imageKey={playlist.image_key} type="playlist" className="w-full h-full" />
              <div className="absolute bottom-2 right-2 p-3 bg-green-500 rounded-full text-black shadow-xl opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all hover:scale-110">
                <Play fill="black" size={20} />
              </div>
            </div>
            <h3 className="font-bold truncate">{playlist.name}</h3>
            <p className="text-sm text-zinc-400 mt-1">Playlist</p>
          </Link>
        ))}
      </div>

      
      {isModalOpen && <CreatePlaylistModal onClose={() => setIsModalOpen(false)} />}
    </div>
  );
}