import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { mediaApi } from '../api/instances';
import { usePlayerStore } from '../store/usePlayerStore';
import { Clock3, Play, Pause } from 'lucide-react';
import { formatTime } from '../utils/formatTime';
import type { Album } from '../types';
import { PlayingAnimation } from '../components/PlayingAnimation';
import { MediaImage } from '../components/MediaImage';
import { TrackActionMenu } from '../components/TrackActionMenu';

export default function AlbumDetail() {
  const { id } = useParams();
  const [album, setAlbum] = useState<Album | null>(null);
  const {isPlaying, currentTrack, openInfo, togglePlay, handlePlay} = usePlayerStore();
  const [activeMenuId, setActiveMenuId] = useState<number | null>(null);
  
  useEffect(() => {
    const fetchAlbum = async () => {
      try {
        const response = await mediaApi.get(`/album/${id}`);
        setAlbum(response.data);
      } catch (err) {
        console.error("Failed to upload album:", err);
      }
    };
    fetchAlbum();
  }, [id]);

  if (!album) return <div className="p-8 text-white animate-pulse"></div>;

  return (

    <div className="text-white pb-24">
      
      <div className="h-80 bg-gradient-to-b from-blue-900 to-zinc-900 p-8 flex items-end gap-8">
        <div className="w-52 h-52 shadow-[0_8px_40px_rgba(0,0,0,0.5)] flex-shrink-0 bg-zinc-800 rounded-lg overflow-hidden">
            <div className="w-full h-full rounded-md overflow-hidden flex-shrink-0">
              <MediaImage imageKey={album.image_key} type="album" className="w-full h-full" />
            </div>
        </div>
        <div className="flex flex-col gap-2">
          <span className="text-sm font-bold uppercase">Album</span>
          <h1 className="text-6xl font-black">{album.name}</h1>
          <div className="flex items-center gap-2 mt-2">
            <div className="w-6 h-6 rounded-full bg-zinc-700 overflow-hidden">
                {
                  <div className="w-48 h-48 shadow-2xl rounded-full overflow-hidden flex-shrink-0">
                    <MediaImage imageKey={album.artist?.image_key} type="artist" className="w-full h-full" />
                  </div>
                }
            </div>
            <Link to={`/artist/${album.artist?.id}`} className="font-bold hover:underline">
              {album.artist?.name}
            </Link>
            <span className="text-zinc-400">• {album.tracks?.length} tracks</span>
          </div>
        </div>
      </div>

      
      <div className="p-8 bg-black/20 backdrop-blur-sm">
        <div className="grid grid-cols-[16px_1fr_120px] gap-4 px-4 py-2 border-b border-zinc-800 text-zinc-400 text-sm mb-4">
          <span>#</span>
          <span>Title</span>
          <div className="flex justify-end"><Clock3 size={16} /></div>
        </div>

        <div className="flex flex-col">
          
          {album.tracks?.map((track, index) => {
            const isCurrent = currentTrack?.id === track.id;

            return (
              <div 
                key={track.id}
                onClick={() => openInfo(track)} 
                className="flex items-center gap-4 p-2 rounded-md hover:bg-white/10 group cursor-pointer"
              >
                
                <div className="w-8 flex justify-center">
                  {isCurrent && isPlaying ? (
                    <PlayingAnimation />
                  ) : isCurrent ? (
                  <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  </div>
                ) : <span className={`text-zinc-400 ${isCurrent ? 'text-green-500' : ''}`}>
                     {index + 1}
                    </span>}
                </div>
                <div className="flex-1">
                  <div className={`font-medium ${isCurrent ? 'text-green-500' : 'text-white'}`}>
                    {track.title}
                  </div>
                  <div className="text-xs text-zinc-400">{album.artist?.name}</div>
              </div>
              
                <div 
                  onClick={(e) => {
                    e.stopPropagation();
                    if (isCurrent) {
                      togglePlay(); 
                    } else {
                      handlePlay(album.tracks!, index); 
                    }
                  }}
                  className="opacity-0 group-hover:opacity-100 p-2 bg-green-500 rounded-full text-black group-hover:opacity-100 group-hover:translate-y-0 transition-all hover:scale-110"
                >
                  
                  {isCurrent && isPlaying ? (
                    <Pause size={14} fill="black" />
                  ) : (
                    <Play size={14} fill="black" />
                  )}
                </div>
              <div className="flex items-center gap-4">
                <div className="text-zinc-400 text-sm">{formatTime(track.duration_seconds)}</div>
                <TrackActionMenu 
                  trackId={track.id} 
                  isOpen={activeMenuId === track.id}
                  onToggle={() => setActiveMenuId(activeMenuId === track.id ? null : track.id)}
                />
              </div>
            </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}