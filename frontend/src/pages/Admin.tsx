import { useState, useEffect } from 'react';
import { mediaApi } from '../api/instances';
import { Plus, Trash2, Edit2} from 'lucide-react';
import { ConfirmModal } from '../components/ConfirmModal';
import { useAuthStore } from '../store/useAuthStore';
import { useNavigate } from 'react-router-dom';
import { AdminEntityModal } from '../components/AdminEntityModal';

export default function Admin() {
    const { user } = useAuthStore();
    const [activeTab, setActiveTab] = useState<'artists' | 'albums' | 'tracks'>('artists');
    const [items, setItems] = useState<any[]>([]);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [allArtists, setAllArtists] = useState<any[]>([]);
    const [allAlbums, setAllAlbums] = useState<any[]>([]);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [editingItem, setEditItem] = useState<any>(null);
    const navigate = useNavigate()

  
    if (!user?.is_superuser) navigate('/');

    const fetchItems = async () => {
        try {
        const endpoint = activeTab === 'tracks' ? '/tracks' : `/${activeTab}`;
        const response = await mediaApi.get(endpoint);
        
        setItems(response.data.items || response.data); 
        } catch (err) { console.error(err); }
    };

    const fetchHelpers = async () => {
        try {
            const [artRes, albRes] = await Promise.all([
                mediaApi.get('/artists?limit=100'),
                mediaApi.get('/albums?limit=100')
            ]);
            setAllArtists(artRes.data.items || []);
            setAllAlbums(albRes.data.items || []);
        } catch (err) { console.error(err); }
    };

    useEffect(() => {
        fetchItems();
        fetchHelpers();
    }, [activeTab]);

  const handleDelete = async () => {
    if (!selectedId) return;
    try {
      const endpoint = activeTab === 'tracks' ? `/track/${selectedId}` : `/${activeTab.slice(0, -1)}/${selectedId}`;
      await mediaApi.delete(endpoint);
      setIsDeleteModalOpen(false);
      fetchItems();
    } catch (err) { alert("Failed delete item"); }
  };

  return (
    <div className="p-8 text-white pb-32">
      <h1 className="text-3xl font-bold mb-8 flex items-center gap-3">
        Control Panel<span className="text-xs bg-green-500 text-black px-2 py-1 rounded">Superuser</span>
      </h1>

      
      <div className="flex gap-4 mb-8 border-b border-zinc-800">
        {(['artists', 'albums', 'tracks'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-4 px-2 capitalize transition-colors ${activeTab === tab ? 'text-green-500 border-b-2 border-green-500' : 'text-zinc-500'}`}
          >
            {tab}
          </button>
        ))}
      </div>

      
      <button 
        onClick={() => { setEditItem(null); setIsEditModalOpen(true); }}
        className="mb-6 flex items-center gap-2 bg-white text-black px-4 py-2 rounded-full font-bold hover:scale-105 transition-all"
      >
        <Plus size={20} />Add{activeTab.slice(0, -1)}
      </button>

      
      <div className="bg-zinc-900 rounded-xl overflow-hidden border border-zinc-800">
        <table className="w-full text-left">
          <thead className="bg-zinc-800/50 text-zinc-400 text-xs uppercase">
            <tr>
              <th className="p-4">ID</th>
              <th className="p-4">Name</th>
              <th className="p-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {items.map(item => (
              <tr key={item.id} className="hover:bg-white/5 transition-colors group">
                <td className="p-4 text-zinc-500">{item.id}</td>
                <td className="p-4 font-medium">{item.name || item.title}</td>
                <td className="p-4 text-right">
                  <div className="flex justify-end gap-3">
                    <button className="text-zinc-400 hover:text-white" onClick={() => { setEditItem(item); setIsEditModalOpen(true); }}><Edit2 size={18} /></button>
                    <button 
                      onClick={() => { setSelectedId(item.id); setIsDeleteModalOpen(true); }}
                      className="text-zinc-400 hover:text-red-500"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

        {isDeleteModalOpen && (
            <ConfirmModal 
            title="Delete item"
            message="Are you sure? This action may delete 1 or more related items"
            confirmText="Delete"
            isDanger={true}
            onConfirm={handleDelete}
            onCancel={() => setIsDeleteModalOpen(false)}
            />
        )}
      
        {isEditModalOpen && (
        <AdminEntityModal 
            type={activeTab}
            item={editingItem}
            artists={allArtists}
            albums={allAlbums}
            onClose={() => setIsEditModalOpen(false)}
            onRefresh={fetchItems}
        />
        )}
    </div>
  );
}