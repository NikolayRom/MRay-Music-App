import { MoreVertical, Heart, ListMusic, Check } from 'lucide-react';
import { usePlaylistStore } from '../store/usePlaylistStore';
import { useInteractionStore } from '../store/useInteractionStore';

export const TrackActionMenu = ({ trackId, isOpen, onToggle }: { trackId: number, isOpen: boolean, onToggle: () => void }) => {
  const { playlists, addTrackToPlaylist, removeTrackFromPlaylist } = usePlaylistStore();
  const { toggleLike, likedTrackIds } = useInteractionStore();
  const isLiked = likedTrackIds.includes(trackId);

  return (
    <div className="relative">
      <button onClick={(e) => { e.stopPropagation(); onToggle(); }} className="p-2 text-zinc-400 hover:text-white transition-colors">
        <MoreVertical size={20} />
      </button>

      {isOpen && (
        <div className="absolute right-0 bottom-10 w-56 bg-[#282828] shadow-[0_16px_24px_rgba(0,0,0,0.3)] rounded-md z-[100] p-1 border border-zinc-700/50 animate-in fade-in zoom-in duration-100">
          <button onClick={(e) => {e.stopPropagation(); toggleLike(trackId)}} className="w-full flex items-center justify-between px-3 py-2.5 text-sm hover:bg-white/10 rounded-sm">
            <span>{isLiked ? 'Delete from favorite' : 'Like'}</span>
            <Heart size={16} className={isLiked ? "text-green-500" : ""} fill={isLiked ? "currentColor" : "none"} />
          </button>
          
          <div className="h-[1px] bg-zinc-700 my-1" />
          
          <div className="px-3 py-1.5 text-[11px] font-bold text-zinc-500 uppercase tracking-wider text-left">Add to playlist</div>
          <div className="max-h-48 overflow-y-auto">
            {playlists.map(pl => {
                const isInPlaylist = pl.track_ids.includes(trackId); 

                return (
                    <button
                    key={pl.id}
                    onClick={async (e) => {
                        e.stopPropagation();
                        if (isInPlaylist) {
                        await removeTrackFromPlaylist(pl.id, trackId);
                        } else {
                        await addTrackToPlaylist(pl.id, trackId);
                        }
                        
                        
                    }}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-white/10 rounded-sm flex items-center gap-2 group/item"
                    >
                    <ListMusic size={16} className="text-zinc-400 group-hover/item:text-white" />
                    <span className={`truncate ${isInPlaylist ? 'text-green-500' : 'text-zinc-300'}`}>
                        {pl.name}
                    </span>
                    
                    
                    {isInPlaylist && (
                        <Check size={14} className="ml-auto text-green-500" />
                    )}
                    </button>
                );
                })}
          </div>
        </div>
      )}
    </div>
  );
};