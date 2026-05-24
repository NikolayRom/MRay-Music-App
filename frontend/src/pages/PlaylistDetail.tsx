import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { coreApi, mediaApi } from '../api/instances';
import { usePlayerStore } from '../store/usePlayerStore';
import { Play, Pause, MoreVertical, Edit2, Trash2, MinusCircle } from 'lucide-react';
import { MediaImage } from '../components/MediaImage';
import type { Track } from '../types';
import { PlayingAnimation } from '../components/PlayingAnimation';
import { formatTime } from '../utils/formatTime';
import { useNavigate } from 'react-router-dom';
import { usePlaylistStore } from '../store/usePlaylistStore';
import { EditPlaylistModal } from '../components/EditPlaylistModal';
import { ConfirmModal } from '../components/ConfirmModal';

export default function PlaylistDetail() {
  const { id } = useParams();
  const [playlist, setPlaylist] = useState<any>(null);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [showMenu, setShowMenu] = useState(false);
  const { handlePlay, isPlaying, currentTrack, togglePlay } = usePlayerStore();
  const { deletePlaylist, removeTrackFromPlaylist } = usePlaylistStore()
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [updateTrigger, setUpdateTrigger] = useState(0);

  const navigate = useNavigate()

  const isThisListPlaying = tracks.some(t => t.id === currentTrack?.id);
  
  const isAnyTrackPlaying = tracks.some(t => t.id === currentTrack?.id) && isPlaying;

  const handleHeaderPlay = () => {
    if (isThisListPlaying) {
      togglePlay(); 
    } else {
      handlePlay(tracks, 0); 
    }
  };

  useEffect(() => {
    const fetchPlaylistAndTracks = async () => {
        try {
        const plRes = await coreApi.get(`/playlists/${id}`);
        setPlaylist(plRes.data);

        if (plRes.data.track_ids && plRes.data.track_ids.length > 0) {
            const params = new URLSearchParams();
            plRes.data.track_ids.reverse().forEach((tid: number) => params.append('ids', tid.toString()));
            const trRes = await mediaApi.get(`/tracks?${params.toString()}`);
            
            
            const orderedTracks = plRes.data.track_ids.map((tid: number) => 
                trRes.data.items.find((t: any) => t.id === tid)
            ).filter(Boolean);

            setTracks(orderedTracks);
        } else {
            setTracks([]); 
        }
        } catch (err) {
        console.error(err);
        }
    };
    fetchPlaylistAndTracks();
    }, [id, updateTrigger]);

  if (!playlist) return <div className="p-8 text-white">...</div>;

  return (
    <div className="text-white pb-24">
      <div className="h-80 bg-gradient-to-b from-indigo-900 to-zinc-900 p-8 flex items-end gap-6">
        <div className="w-52 h-52 bg-zinc-800 shadow-2xl rounded-lg overflow-hidden flex-shrink-0">
          <MediaImage imageKey={playlist.image_key} type="playlist" className="w-full h-full" />
        </div>
        <div>
          <span className="text-sm font-bold uppercase">Playlist</span>
          <h1 className="text-7xl font-black mt-2">{playlist.name}</h1>
          <p className="text-zinc-400 mt-4">{tracks.length} tracks</p>
        </div>
      </div>
      
      <div className="p-8">
        
        <div className="mb-8 flex justify-between items-center">
          <button 
            onClick={handleHeaderPlay}
            className="w-14 h-14 bg-green-500 rounded-full flex items-center justify-center hover:scale-105 transition-transform shadow-lg"
          >
            {isAnyTrackPlaying ? <Pause fill="black" stroke='black' /> : <Play fill="black" stroke='black'  />}
          </button> 
        
            
          <button onClick={() => setShowMenu(!showMenu)} className="text-zinc-400 hover:text-white">
            <MoreVertical size={32} />
          </button>

          {showMenu && (
            <div className="absolute right-0 top-60 bg-zinc-800 border border-zinc-700 rounded shadow-xl z-50 p-1 w-48">
               <button onClick={() => { setIsEditModalOpen(true); setShowMenu(false); }} className="w-full text-left px-3 py-2 hover:bg-zinc-700 flex items-center gap-2">
                  <Edit2 size={16} /> Edit
                </button>
                <button onClick={() => { setIsDeleteConfirmOpen(true); setShowMenu(false); }} className="w-full text-left px-3 py-2 hover:bg-zinc-700 text-red-500 flex items-center gap-2">
                  <Trash2 size={16} /> Delete
                </button>
            </div>
          )}

          {isEditModalOpen && (
            <EditPlaylistModal 
              playlist={playlist} 
              onClose={() => {
                setIsEditModalOpen(false);
                setUpdateTrigger(prev => prev + 1); 
              }} 
            />
          )}

          {isDeleteConfirmOpen && (
            <ConfirmModal 
              title="Delete from library?"
              message={`Playlist "${playlist.name}" will be deleted from library.`}
              confirmText="Delete"
              isDanger={true}
              onConfirm={async () => {
                await deletePlaylist(playlist.id);
                navigate('/library');
              }}
              onCancel={() => setIsDeleteConfirmOpen(false)}
            />
          )}
        
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
                <div className="flex items-center justify-end gap-4">
                <span className="text-zinc-400 text-sm">{formatTime(track.duration_seconds)}</span>
                
                
                <button 
                  onClick={(e) => {
                    e.stopPropagation();
                    removeTrackFromPlaylist(Number(id), track.id);
                    setTracks(tracks.filter(t => t.id !== track.id)); 
                  }}
                  className="opacity-0 group-hover:opacity-100 text-zinc-400 hover:text-red-500 transition-all"
                >
                  <MinusCircle size={20} />
                </button>
              </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}