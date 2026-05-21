import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom' 
import { mediaApi } from '../api/instances'
import { usePlayerStore } from '../store/usePlayerStore'
import { Play, Pause } from 'lucide-react'
import type { Track } from '../types'
import { PlayingAnimation } from '../components/PlayingAnimation';
import { MediaImage } from '../components/MediaImage';

export default function Home() {
  const [tracks, setTracks] = useState<Track[]>([])
  const { currentTrack, openInfo, isPlaying, handlePlay } = usePlayerStore();
  const navigate = useNavigate() 

  useEffect(() => {
    const fetchTracks = async () => {
      try {
        const response = await mediaApi.get('/tracks')
        setTracks(response.data.items || [])
      } catch (err) {
        console.error("Failed to upload tracks:", err)
      }
    }
    fetchTracks()
  }, [])

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-white mb-8">Welcome back!</h1>
      
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
        {tracks.map((track, index) => {
          const isCurrent = currentTrack?.id === track.id;

          return (
            
            <div 
              key={track.id} 
              onClick={() => openInfo(track)} 
              className="p-4 bg-zinc-900/40 hover:bg-zinc-800/60 rounded-xl transition-all group cursor-pointer relative"
            >

              <div className="relative aspect-square mb-4 shadow-lg">
                {
                  <div className="w-full h-full rounded-md overflow-hidden flex-shrink-0">
                    <MediaImage imageKey={track.image_key} type="track" className="w-full h-full" />
                  </div>
                }
                
                <div className="absolute top-2 right-2">
                  {isCurrent && isPlaying ? (
                    <PlayingAnimation />
                  ) : isCurrent ? (
                    <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    </div>
                  ) : null}
                </div>
                
                <div 
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePlay(tracks, index); 
                    }}
                    className="absolute bottom-2 right-2 p-3 bg-green-500 rounded-full text-black shadow-xl opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all hover:scale-110"
                  >
                    {isCurrent && isPlaying ? (
                      <Pause size={20} fill="black" />
                    ) : (
                      <Play size={20} fill="black" />
                    )}
                  </div>
              </div>
              
              <h3 className={`font-bold truncate ${isCurrent ? 'text-green-500' : 'text-white'}`}>
                {track.title}
              </h3>

              <span 
                className="text-sm text-zinc-400 mt-1 hover:underline hover:text-white"
                onClick={(e) => {
                  e.stopPropagation(); 
                  navigate(`/artist/${track.artist?.id}`);
                }}
              >
                {track.artist?.name}
              </span>
              <br/>
              <span 
                className="text-sm text-zinc-400 mt-1 hover:underline hover:text-white"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/album/${track.album?.id}`);
                }}
              >
                {track.album?.name}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  )
}