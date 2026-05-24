import { useState } from 'react';
import { X, Music } from 'lucide-react';
import { usePlaylistStore } from '../store/usePlaylistStore';
import { MediaImage } from './MediaImage';

interface Props {
  playlist: any;
  onClose: () => void;
}

export const EditPlaylistModal = ({ playlist, onClose }: Props) => {
  const [name, setName] = useState(playlist.name);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const updatePlaylist = usePlaylistStore(state => state.updatePlaylist);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await updatePlaylist(playlist.id, name, file || undefined);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[150] flex items-center justify-center p-4 text-white">
      <div className="bg-zinc-900 w-full max-w-lg rounded-2xl p-8 border border-zinc-800 shadow-2xl relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-zinc-400 hover:text-white"><X size={24} /></button>
        <h2 className="text-2xl font-bold mb-8">Edit playlist</h2>

        <form onSubmit={handleSubmit} className="flex gap-6">
            <div className="relative w-44 h-44 group">
                <label className="w-full h-full bg-zinc-800 rounded-lg flex flex-col items-center justify-center cursor-pointer overflow-hidden border border-zinc-700">
                {preview ? (
                    <img src={preview} className="w-full h-full object-cover" />
                ) : (
                    <MediaImage imageKey={playlist.image_key} type="playlist" className="w-full h-full" />
                )}
                <input 
                    type="file" 
                    className="hidden" 
                    accept="image/*" 
                    onChange={handleFileChange}
                    id="image-upload"
                />
                </label>
                
                
                <label 
                htmlFor="image-upload"
                className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center transition-opacity rounded-lg cursor-pointer"
                >
                <Music size={32} />
                <span className="text-[10px] font-bold uppercase mt-2">Choose photo</span>
                </label>
            </div>

            <div className="flex-1 flex flex-col justify-center gap-4">
                <input 
                type="text" 
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-zinc-800 border border-zinc-700 p-3 rounded-md outline-none focus:border-green-500 text-lg"
                placeholder="Name"
                />
                <button type="submit" className="bg-white text-black font-bold py-3 rounded-full hover:scale-105 transition-all">
                Save
                </button>
            </div>
        </form>
      </div>
    </div>
  );
};