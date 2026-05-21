import { useEffect } from 'react';
import { mediaApi } from '../api/instances';
import { Search as SearchIcon, Play, Pause, X } from 'lucide-react'; 
import { usePlayerStore } from '../store/usePlayerStore';
import { useSearchStore } from '../store/useSearchStore';
import { MediaImage } from '../components/MediaImage';
import { PlayingAnimation } from '../components/PlayingAnimation';
import { useNavigate } from 'react-router-dom';

export default function Search() {
  const { query, results, setQuery, setResults, clearSearch } = useSearchStore();
  
  const { openInfo, handlePlay, isPlaying, currentTrack } = usePlayerStore();

  const navigate = useNavigate()
  
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.length > 1) {
        try {
          const response = await mediaApi.get(`/tracks?search=${encodeURIComponent(query)}`);
          setResults(response.data.items || []);
        } catch (err) {
          console.error(err);
        }
      } else {
        setResults([]);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [query, setResults]); 

  return (
    <div className="p-8 text-white">
      <div className="relative max-w-md mb-8">
        <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" size={20} />
        
        <input 
          type="text" 
          placeholder="What do you want to play?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full bg-zinc-800 hover:bg-zinc-700 focus:bg-zinc-700 outline-none rounded-full py-3 pl-12 pr-10 text-sm transition-colors border border-transparent focus:border-zinc-500"
        />

        {query && (
          <button 
            onClick={clearSearch}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white"
          >
            <X size={20} />
          </button>
        )}
      </div>

      {results.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
          {results.map((track, index) => {
            const isCurrent = currentTrack?.id === track.id;

            return (
              <div 
                key={track.id} 
                onClick={() => openInfo(track)} 
                className="p-4 bg-zinc-900/40 hover:bg-zinc-800/60 rounded-xl transition-all group cursor-pointer relative"
              >
                <div className="relative aspect-square mb-4 shadow-lg">
                  <div className="w-full h-full rounded-md overflow-hidden flex-shrink-0">
                    <MediaImage imageKey={track.image_key} type="track" className="w-full h-full" />
                  </div> 

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
                          handlePlay(results, index); 
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
              <h3 className="font-bold truncate text-white">{track.title}</h3>
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
          )
        })}
        </div>
      ) : query.length > 1 ? (
        <div className="text-center mt-20">
          <h2 className="text-2xl font-bold">Nothing found</h2>
          <p className="text-zinc-400">Try another query</p>
        </div>
      ) : (
        <div className="text-center mt-20 text-zinc-500">
          <SearchIcon size={64} className="mx-auto mb-4 opacity-20" />
          <h2 className="text-xl font-medium">Search tracks</h2>
        </div>
      )}
    </div>
  );
}