import { useState } from 'react';
import { X, Music } from 'lucide-react';
import { usePlaylistStore } from '../store/usePlaylistStore';

export const CreatePlaylistModal = ({ onClose }: { onClose: () => void }) => {
  const [name, setName] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const createPlaylist = usePlaylistStore(state => state.createPlaylist);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await createPlaylist(name, file || undefined);
      onClose();
    } catch (err) {
      alert("Failed to create playlist");
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="bg-zinc-900 w-full max-w-lg rounded-2xl p-8 border border-zinc-800 shadow-2xl relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-zinc-400 hover:text-white">
          <X size={24} />
        </button>

        <h2 className="text-2xl font-bold text-white mb-8">Create playlist</h2>

        <form onSubmit={handleSubmit} className="flex gap-6">
          
          <div className="flex flex-col gap-4">
            <label className="w-44 h-44 bg-zinc-800 rounded-lg flex flex-col items-center justify-center cursor-pointer hover:bg-zinc-700 transition-colors overflow-hidden border border-zinc-700 shadow-inner group">
              {preview ? (
                <img src={preview} className="w-full h-full object-cover" />
              ) : (
                <>
                  <Music size={48} className="text-zinc-600 mb-2 group-hover:text-zinc-400" />
                  <span className="text-[10px] font-bold uppercase text-zinc-500">Choose photo</span>
                </>
              )}
              <input type="file" className="hidden" accept="image/*" onChange={handleFileChange} />
            </label>
          </div>

          
          <div className="flex-1 flex flex-col justify-center gap-4">
            <input 
              type="text" 
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 p-3 rounded-md text-white outline-none focus:border-green-500 text-lg"
              autoFocus
            />
            <button 
              type="submit"
              disabled={!name.trim()}
              className="bg-green-500 text-black font-bold py-3 rounded-full hover:scale-105 transition-transform disabled:opacity-50"
            >
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};