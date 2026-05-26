import React, { useState } from 'react';
import { X, Music, FileText, Upload } from 'lucide-react';
import { mediaApi } from '../api/instances';

interface Props {
  type: 'artists' | 'albums' | 'tracks';
  item?: any; 
  artists: any[];
  albums: any[];
  onClose: () => void;
  onRefresh: () => void;
}

export const AdminEntityModal = ({ type, item, artists, albums, onClose, onRefresh }: Props) => {
  const [loading, setLoading] = useState(false);
  
  
  const [name, setName] = useState(item?.name || item?.title || '');
  const [file, setFile] = useState<File | null>(null);
  
  
  const [artistId, setArtistId] = useState(item?.artist_id || '');
  const [albumId, setAlbumId] = useState(item?.album_id || '');
  const [genre, setGenre] = useState(item?.genre?.join(', ') || '');
  
  
  const [trackFile, setTrackFile] = useState<File | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); 
    setLoading(true);

    const formData = new FormData();
    const isEdit = !!item;

    try {
      if (type === 'artists') {
        formData.append('name', name);
        if (file) formData.append('file', file);
        
        if (isEdit) await mediaApi.patch(`/artist/${item.id}`, formData);
        else await mediaApi.post('/artist', formData);

      } else if (type === 'albums') {
        formData.append('name', name);
        formData.append('artist_id', artistId);
        if (file) formData.append('file', file);
        
        if (isEdit) await mediaApi.patch(`/album/${item.id}`, formData);
        else await mediaApi.post('/album', formData);

      } else if (type === 'tracks') {
        
        if (name) formData.append('title', name);
        if (artistId) formData.append('artist_id', artistId);
        if (albumId) formData.append('album_id', albumId);
        if (genre) formData.append('genre', JSON.stringify(genre.split(',').map((g: string) => g.trim())));
        
        if (trackFile) formData.append('file_track', trackFile);
        if (file) formData.append('file_cover', file);

        if (isEdit) await mediaApi.patch(`/track/${item.id}`, formData);
        else await mediaApi.post('/track', formData);
      }

      onRefresh();
      onClose();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed save item");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/90 backdrop-blur-sm z-[150] flex items-center justify-center p-4">
      <div className="bg-zinc-900 w-full max-w-2xl rounded-2xl p-8 border border-zinc-800 shadow-2xl relative max-h-[90vh] overflow-y-auto">
        <button onClick={onClose} className="absolute top-4 right-4 text-zinc-400 hover:text-white"><X /></button>
        
        <h2 className="text-2xl font-bold mb-8">{item ? 'Edit' : 'Add'} {type.slice(0, -1)}</h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase text-zinc-500">Name</label>
            {(type === 'tracks') ? (
                <input 
                className="w-full bg-zinc-800 p-3 rounded-lg outline-none focus:ring-2 focus:ring-green-500"
                value={name} onChange={e => setName(e.target.value)} 
                placeholder='Title'
                />
            ) : (
                 <input 
                className="w-full bg-zinc-800 p-3 rounded-lg outline-none focus:ring-2 focus:ring-green-500"
                value={name} onChange={e => setName(e.target.value)} required
                placeholder='Name' 
                />
            )}
          </div>

          
          {(type === 'albums' || type === 'tracks') && (
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase text-zinc-500">Artist</label>
              <select 
                className="w-full bg-zinc-800 p-3 rounded-lg outline-none"
                value={artistId}
                onChange={e => {
                    setArtistId(e.target.value);
                    setAlbumId(""); 
                }}
                required={type === 'albums'}
              >
                <option value="">Not selected</option>
                {artists.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
          )}

          
          {type === 'tracks' && (
            <>
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase text-zinc-500">Album</label>
                <select 
                  className="w-full bg-zinc-800 p-3 rounded-lg outline-none"
                  value={albumId} onChange={e => setAlbumId(e.target.value)}
                >
                  <option value="">Not selected</option>
                  {albums.filter(a => !artistId || a.artist_id === Number(artistId)).map(a => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase text-zinc-500">Genres (sep by commas)</label>
                <input 
                  className="w-full bg-zinc-800 p-3 rounded-lg outline-none"
                  value={genre} onChange={e => setGenre(e.target.value)}
                  placeholder="Pop, Rock"
                />
              </div>
            </>
          )}

          <div className="grid grid-cols-2 gap-6">
            
            <div className="space-y-2">
                <label className="text-xs font-bold uppercase text-zinc-500">Cover</label>
                <div className="relative">
                <input 
                    type="file" 
                    accept="image/*" 
                    onChange={e => setFile(e.target.files?.[0] || null)} 
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                    id="image-upload"
                />
                <label 
                    htmlFor="image-upload"
                    className="block w-full bg-zinc-800 border border-zinc-600 rounded-lg p-3 text-center cursor-pointer hover:border-green-500 transition-colors"
                >
                    {file ? (
                    <div className="flex items-center justify-center gap-2">
                        <FileText size={18} className="text-green-500" />
                        <span className="text-sm text-white truncate">{file.name}</span>
                    </div>
                    ) : (
                    <div className="flex items-center justify-center gap-2">
                        <Upload size={18} className="text-zinc-500" />
                        <span className="text-sm text-zinc-400">Select Image</span>
                    </div>
                    )}
                </label>
                </div>
            </div>

            
            {type === 'tracks' && !item && (
                <div className="space-y-2">
                    <label className="text-xs font-bold uppercase text-green-500">Select MP3 file</label>
                    <div className="relative">
                        <input 
                        type="file" 
                        accept="audio/mpeg" 
                        onChange={e => setTrackFile(e.target.files?.[0] || null)} 
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                        id="audio-upload"
                        required
                        />
                        <label 
                        htmlFor="audio-upload"
                        className="block w-full bg-zinc-800 border border-zinc-600 rounded-lg p-3 text-center cursor-pointer hover:border-green-500 transition-colors"
                        >
                        {trackFile ? (
                            <div className="flex items-center justify-center gap-2">
                            <Music size={18} className="text-green-500" />
                            <span className="text-sm text-white truncate">{trackFile.name}</span>
                            </div>
                        ) : (
                            <div className="flex items-center justify-center gap-2">
                            <Music size={18} className="text-zinc-500" />
                            <span className="text-sm text-zinc-400">Select MP3</span>
                            </div>
                        )}
                        </label>
                    </div>
                </div>
            )}
        </div>

          <button 
            type="submit" disabled={loading}
            className="w-full bg-green-500 text-black font-bold py-4 rounded-full hover:scale-[1.02] transition-all disabled:opacity-50"
          >
            {loading ? '...' : 'Save'}
          </button>
        </form>
      </div>
    </div>
  );
};