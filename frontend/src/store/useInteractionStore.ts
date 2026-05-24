import { create } from 'zustand';
import { coreApi } from '../api/instances';

interface InteractionState {
  likedTrackIds: number[];
  fetchLikes: () => Promise<void>;
  toggleLike: (trackId: number) => Promise<void>;
  addToHistory: (trackId: number) => Promise<void>;
}

export const useInteractionStore = create<InteractionState>((set, get) => ({
  likedTrackIds: [],
  
  fetchLikes: async () => {
    try {
      const response = await coreApi.get('/likes/');
      
      const ids = response.data.items.map((item: any) => item.track_id);
      set({ likedTrackIds: ids });
    } catch (error) {
      console.error("Failed to upload likes:", error);
    }
  },

  
  toggleLike: async (trackId: number) => {
    try {
      
      await coreApi.post('/likes/', { track_id: trackId });
      
      const { likedTrackIds } = get();
      if (likedTrackIds.includes(trackId)) {
        set({ likedTrackIds: likedTrackIds.filter(id => id !== trackId) });
      } else {
        set({ likedTrackIds: [...likedTrackIds, trackId] });
      }
    } catch (error) {
      console.error("Error like:", error);
    }
  },

  
  addToHistory: async (trackId: number) => {
    try {
      await coreApi.post('/history/', { track_id: trackId });
    } catch (error) {
      
    }
  }
}));