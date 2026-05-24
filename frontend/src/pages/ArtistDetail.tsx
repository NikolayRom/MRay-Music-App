import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { mediaApi } from '../api/instances';
import { usePlayerStore } from '../store/usePlayerStore';
import { Play, Pause } from 'lucide-react';
import { formatTime } from '../utils/formatTime';
import type { Artist } from '../types';
import { PlayingAnimation } from '../components/PlayingAnimation';
import { MediaImage } from '../components/MediaImage';
import { TrackActionMenu } from '../components/TrackActionMenu';

export default function ArtistDetail() {
  const { id } = useParams();
  const [artist, setArtist] = useState<Artist | null>(null);
  const navigate = useNavigate()
  
  const [activeMenuId, setActiveMenuId] = useState<number | null>(null);
  const { currentTrack, isPlaying, openInfo, togglePlay, handlePlay } = usePlayerStore();

  useEffect(() => {
    const fetchArtist = async () => {
      try {
        const response = await mediaApi.get(`/artist/${id}`);
        setArtist(response.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchArtist();
  }, [id]);

  if (!artist) return <div className="p-8 text-white"></div>;

  return (
    <div className="text-white pb-24">
      <div className="h-64 bg-gradient-to-b from-red-900 to-zinc-900 p-8 flex items-end gap-6">
        <div className="w-48 h-48 shadow-2xl rounded-full overflow-hidden flex-shrink-0 bg-zinc-800">
          
          <div className="w-48 h-48 shadow-2xl rounded-full overflow-hidden flex-shrink-0">
            <MediaImage imageKey={artist.image_key} type="artist" className="w-full h-full" />
          </div>
          
        </div>
        <div>
          <span className="text-xs font-bold uppercase">Artist</span>
          <h1 className="text-7xl font-black mt-2">{artist.name}</h1>
        </div>
      </div>

      <div className="p-8">
        <h2 className="text-2xl font-bold mb-4">Popular tracks</h2>
        
        <div className="flex flex-col">
          {artist.tracks?.map((track, index) => {
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
                  {track.album && (
                    <span 
                      className="text-sm text-zinc-400 mt-1 hover:underline hover:text-white"
                      onClick={(e) => {
                        e.stopPropagation(); 
                        navigate(`/album/${track.album?.id}`);
                      }}
                    >
                      {track.album?.name}
                    </span>
                  )}
                </div>

                <div 
                  onClick={(e) => {
                    e.stopPropagation();
                    if (isCurrent) {
                      togglePlay(); 
                    } else {
                      handlePlay(artist.tracks!, index); 
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