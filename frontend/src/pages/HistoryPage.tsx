import { useEffect, useState } from 'react';
import { coreApi, mediaApi } from '../api/instances';
import { usePlayerStore } from '../store/usePlayerStore';
import { History, Play, Pause } from 'lucide-react';
import { formatTime } from '../utils/formatTime';
import { MediaImage } from '../components/MediaImage';
import type { Track } from '../types';
import { PlayingAnimation } from '../components/PlayingAnimation';
import { TrackActionMenu } from '../components/TrackActionMenu';

export default function HistoryPage() {
  const [tracks, setTracks] = useState<Track[]>([]);
  const { currentTrack, isPlaying, handlePlay, togglePlay } = usePlayerStore();
  
  const isThisListPlaying = tracks.some(t => t.id === currentTrack?.id);
  
  const isAnyTrackPlaying = tracks.some(t => t.id === currentTrack?.id) && isPlaying;
  const [activeMenuId, setActiveMenuId] = useState<number | null>(null);

  const handleHeaderPlay = () => {
    if (isThisListPlaying) {
      togglePlay(); 
    } else {
      handlePlay(tracks, 0); 
    }
  };

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await coreApi.get('/history/');
        
        const historyIds = res.data.items.map((i: any) => i.track_id).reverse();
        
        if (historyIds.length > 0) {
          const params = new URLSearchParams();
          historyIds.forEach((id: number) => params.append('ids', id.toString()));
          const trackRes = await mediaApi.get(`/tracks?${params.toString()}`);
          
          
          
          const sortedTracks = historyIds.map((id: number) => 
            trackRes.data.items.find((t: Track) => t.id === id)
          ).filter(Boolean);

          setTracks(sortedTracks);
        }
      } catch (err) { console.error(err); }
    };
    fetchHistory();
  }, []);

  return (
    <div className="text-white pb-24 p-8">
      <div className="flex items-center gap-6 mb-8">
        <div className="p-6 bg-zinc-800 rounded-full text-green-500"><History size={48} /></div>
        <h1 className="text-5xl font-black">Listening history</h1>
      </div>
      
      <div className="p-8">
            
            <div className="mb-8">
            <button 
                onClick={handleHeaderPlay}
                className="w-14 h-14 bg-green-500 rounded-full flex items-center justify-center hover:scale-105 transition-transform shadow-lg"
            >
                {isAnyTrackPlaying ? <Pause fill="black" stroke='none' /> : <Play fill="black" stroke='none' className="ml-1" />}
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