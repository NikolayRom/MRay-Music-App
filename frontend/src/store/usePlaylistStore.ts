import { create } from 'zustand';
import { coreApi } from '../api/instances';

interface Playlist {
  id: number;
  name: string;
  image_key?: string;
  track_ids: number[];
}

interface PlaylistState {
  playlists: Playlist[];
  fetchPlaylists: () => Promise<void>;
  createPlaylist: (name: string, cover?: File) => Promise<void>;
  addTrackToPlaylist: (playlistId: number, trackId: number) => Promise<void>;
  updatePlaylist: (id: number, name: string, cover?: File) => Promise<void>;
  deletePlaylist: (id: number) => Promise<void>;
  removeTrackFromPlaylist: (playlistId: number, trackId: number) => Promise<void>;
}

export const usePlaylistStore = create<PlaylistState>((set, get) => ({
  playlists: [],

  fetchPlaylists: async () => {
    try {
      const response = await coreApi.get('/playlists/');
      set({ playlists: response.data.items });
    } catch (error) {
      console.error(error);
    }
  },

  createPlaylist: async (name: string, cover?: File) => {
    const formData = new FormData();
    formData.append('name', name);
    if (cover) formData.append('cover', cover);

    try {
      const response = await coreApi.post('/playlists/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      
      set((state) => ({ 
        playlists: [response.data, ...state.playlists] 
      }));
      return response.data;
    } catch (error) {
      console.error("Error during playlist create:", error);
      throw error;
    }
  },

  addTrackToPlaylist: async (playlistId, trackId) => {
    try {
      await coreApi.post(`/playlists/${playlistId}/`, { track_id: trackId });
      get().fetchPlaylists(); 
    } catch (error) {
        console.error(error);
    }
  },

  updatePlaylist: async (id, name, cover) => {
    const formData = new FormData();
    formData.append('name', name);
    if (cover) formData.append('cover', cover);

    try {
      const response = await coreApi.patch(`/playlists/${id}`, formData);
      set((state) => ({
        playlists: state.playlists.map(pl => pl.id === id ? response.data : pl)
      }));
    } catch (error) { console.error(error); }
  },

  deletePlaylist: async (id: number) => {
    try {
      await coreApi.delete(`/playlists/${id}`);
      set((state) => ({
        playlists: state.playlists.filter(pl => pl.id !== id)
      }));
    } catch (error) { console.error(error); }
  },

  removeTrackFromPlaylist: async (playlistId: number, trackId: number) => {
    try {
      await coreApi.delete(`/playlists/${playlistId}/${trackId}`);
      
      set((state) => ({
        playlists: state.playlists.map(pl => {
          if (pl.id === playlistId) {
            return { ...pl, track_ids: pl.track_ids.filter(tid => tid !== trackId) };
          }
          return pl;
        })
      }));
    } catch (error) { console.error(error); }
  },
}));