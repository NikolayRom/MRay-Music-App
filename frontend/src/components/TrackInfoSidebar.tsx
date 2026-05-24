import { X, Play, Clock3, Disc, Pause } from 'lucide-react';
import { usePlayerStore } from '../store/usePlayerStore';
import { formatTime } from '../utils/formatTime';
import { Link } from 'react-router-dom';
import { MediaImage } from './MediaImage';
import { TrackActionMenu } from './TrackActionMenu';
import { useState } from 'react';
import { LikeButton } from './LikeButton';

export const TrackInfoSidebar = () => {
  const { infoTrack, isRightSidebarOpen, closeInfo, isPlaying, handlePlay, currentTrack } = usePlayerStore();

  if (!infoTrack) return null;

  const [activeMenuId, setActiveMenuId] = useState<number | null>(null);

  return (
    <div className={`
      fixed top-0 right-0 h-[calc(100%-6rem)] w-[30%] bg-zinc-900 border-l border-zinc-800 
      transition-transform duration-400 z-40 shadow-2xl p-6 overflow-y-auto
      ${isRightSidebarOpen ? 'translate-x-0' : 'translate-x-full'}
    `}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white">About track</h2>
        <button onClick={closeInfo} className="text-zinc-400 hover:text-white transition-colors">
          <X size={24} />
        </button>
      </div>

      <div className="flex flex-col gap-6">
        <div className="aspect-square w-full bg-zinc-800 rounded-lg overflow-hidden shadow-lg">
          {
            <div className="w-full h-full rounded-md overflow-hidden flex-shrink-0">
              <MediaImage imageKey={infoTrack.image_key} type="track" className="w-full h-full" />
            </div>
          }
        </div>

        <div className="flex items-start justify-between">
          <div className="flex-1 mr-4">
            <h1 className="text-2xl font-black text-white">{infoTrack.title}</h1>
            <Link to={`/artist/${infoTrack.artist?.id}`} onClick={closeInfo} className="text-lg text-zinc-400 hover:underline hover:text-white">
              {infoTrack.artist?.name}
            </Link>
          </div>

          <div className="flex items-center gap-3 mt-2">
            {/* Кнопка Play */}
            <button 
              onClick={() => handlePlay([infoTrack], 0)}
              className="bg-green-500 text-black p-2 rounded-full hover:scale-105 transition-all shadow-lg"
            >
              {currentTrack?.id === infoTrack.id && isPlaying ? <Pause fill="black" /> : <Play fill="black" />}
            </button>

            {/* Кнопка Лайк */}
            <div className="p-2 rounded-full hover:border-white transition-colors cursor-pointer">
              <LikeButton trackId={infoTrack.id} size={35} />
            </div>

            {/* Меню добавления в плейлист */}
            <div className="text-white rounded-full hover:border-white transition-colors">
              <TrackActionMenu 
                  trackId={infoTrack.id} 
                  isOpen={activeMenuId === infoTrack.id}
                  onToggle={() => setActiveMenuId(activeMenuId === infoTrack.id ? null : infoTrack.id)}
              />
            </div>
          </div>
        </div>

        <div className="h-px bg-zinc-800 w-full" />

        <div className="flex flex-col gap-4 text-sm text-zinc-300">
          {infoTrack.album && (
            <div className="flex items-center gap-3">
              <Disc size={18} className="text-green-500" />
              <span>Album: 
                <Link to={`/album/${infoTrack.album.id}`} onClick={closeInfo} className="ml-1 hover:underline text-white font-medium">
                  {infoTrack.album.name}
                </Link>
              </span>
            </div>
          )}
          <div className="flex items-center gap-3">
            <Clock3 size={18} className="text-green-500" />
            <span>Duration: {formatTime(infoTrack.duration_seconds)}</span>
          </div>
          <div className="mt-2">
             <h4 className="text-zinc-500 mb-2 uppercase text-[10px] font-bold tracking-widest">Genres: </h4>
             <div className="flex flex-wrap gap-2">
                {infoTrack.genre.map(g => (
                  <span key={g} className="px-3 py-1 bg-zinc-800 rounded-full border border-zinc-700">{g}</span>
                ))}
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};