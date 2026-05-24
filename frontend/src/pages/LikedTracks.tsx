import { useEffect, useState } from 'react';
import { mediaApi } from '../api/instances';
import { useInteractionStore } from '../store/useInteractionStore';
import { usePlayerStore } from '../store/usePlayerStore';
import { Heart, Play, Pause } from 'lucide-react';
import { formatTime } from '../utils/formatTime';
import { PlayingAnimation } from '../components/PlayingAnimation';
import { MediaImage } from '../components/MediaImage';
import type { Track } from '../types';
import { TrackActionMenu } from '../components/TrackActionMenu';

export default function LikedTracks() {
  const [tracks, setTracks] = useState<Track[]>([]);
  const { likedTrackIds } = useInteractionStore();
  const { currentTrack, isPlaying, handlePlay, togglePlay } = usePlayerStore();
  const [activeMenuId, setActiveMenuId] = useState<number | null>(null);

  
  const isThisListPlaying = tracks.some(t => t.id === currentTrack?.id);

  const handleHeaderPlay = () => {
    if (isThisListPlaying) {
      togglePlay(); 
    } else {
      handlePlay(tracks, 0); 
    }
  };

  useEffect(() => {
    const fetchFullTracks = async () => {
      if (likedTrackIds.length === 0) {
        setTracks([]);
        return;
      }

      try {
        const params = new URLSearchParams();
        likedTrackIds.forEach(id => params.append('ids', id.toString()));
        const response = await mediaApi.get(`/tracks?${params.toString()}`);
        
        
        
        const sortedIds = [...likedTrackIds].reverse();
        
        
        const finalTracks = sortedIds.map(id => 
          response.data.items.find((t: Track) => t.id === id)
        ).filter((t): t is Track => !!t); 

        setTracks(finalTracks);
      } catch (err) {
        console.error(err);
      }
    };
    fetchFullTracks();
  }, [likedTrackIds]);

  
  const isAnyTrackPlaying = tracks.some(t => t.id === currentTrack?.id) && isPlaying;

  return (
    <div className="text-white pb-24">
      <div className="h-80 bg-gradient-to-b from-green-900 to-zinc-900 p-8 flex items-end gap-6">
        <div className="w-52 h-52 bg-gradient-to-br from-green-500 to-green-600 shadow-2xl rounded-lg flex items-center justify-center flex-shrink-0">
          <Heart size={100} fill="black" stroke='black' />
        </div>
        <div className="flex flex-col gap-2">
          <span className="text-sm font-bold uppercase">Playlist</span>
          <h1 className="text-7xl font-black mt-2">Favorite tracks</h1>
          <div className="flex items-center gap-2 mt-4 font-bold">
            <span>Your collection</span>
            <span className="text-zinc-400">• {tracks.length} tracks</span>
          </div>
        </div>
      </div>

      <div className="p-8">
        
        <div className="mb-8">
          <button 
            onClick={handleHeaderPlay}
            className="w-14 h-14 bg-green-500 rounded-full flex items-center justify-center hover:scale-105 transition-transform shadow-lg"
          >
            {isAnyTrackPlaying ? <Pause fill="black" stroke='black' /> : <Play fill="black" stroke='black' className="ml-1" />}
          </button> 
        </div>

        <div className="flex flex-col">
          {tracks.map((track, index) => {
            const isCurrent = currentTrack?.id === track.id;
            return (
              <div key={track.id} className="grid grid-cols-[16px_1fr_120px] gap-4 items-center p-3 rounded-md hover:bg-white/10 group cursor-pointer" onClick={() => handlePlay(tracks, index)}>
                <div className="w-4 flex justify-center">
                  {isCurrent && isPlaying ? <PlayingAnimation /> : <span className={isCurrent ? "text-green-500" : "text-zinc-400"}>{index + 1}</span>}
                </div>
                <div className="flex items-center gap-3">
                  <MediaImage imageKey={track.image_key} type="track" className="w-10 h-10 rounded" />
                  <div>
                    <div className={`font-medium ${isCurrent ? "text-green-500" : "text-white"}`}>{track.title}</div>
                    <div className="text-xs text-zinc-400">{track.artist?.name}</div>
                  </div>
                  
                  <div 
                      onClick={(e) => {
                      e.stopPropagation();
                      handlePlay(tracks, index);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-2 bg-green-500 rounded-full text-black transition-all hover:scale-110 ml-auto mr-4"
                  >
                      {isCurrent && isPlaying ? <Pause size={16} fill="black" /> : <Play size={16} fill="black" />}
                  </div>
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