import { create } from 'zustand';
import type { Track } from '../types';
import { persist, createJSONStorage } from 'zustand/middleware';

type RepeatMode = 'off' | 'one' | 'all';

const shuffleArray = (array: any[]) => {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
};

interface PlayerState {
    originalQueue: Track[];
    currentTrack: Track | null;
    queue: Track[];
    currentIndex: number;
    isPlaying: boolean;
    isShuffle: boolean;
    repeatMode: RepeatMode;
    volume: number;
    isMuted: boolean;
    previousVolume: number;
    isRightSidebarOpen: boolean;
    infoTrack: Track | null;
    
    toggleMute: () => void;
    setQueue: (tracks: Track[], startIndex: number) => void;
    nextTrack: () => void;
    prevTrack: (currentTime: number) => void;   
    toggleShuffle: () => void;
    toggleRepeat: () => void;
    setCurrentTrack: (track: Track) => void;
    setPlaying: (isPlaying: boolean) => void;
    setVolume: (volume: number) => void;
    togglePlay: () => void;
    openInfo: (track: Track) => void;
    closeInfo: () => void;
    handlePlay: (tracks: Track[], index: number) => void;
}

export const usePlayerStore = create<PlayerState>()(

  persist(
    (set, get) => ({
      currentTrack: null,
      queue: [],
      originalQueue: [],
      currentIndex: -1,
      isPlaying: false,
      isShuffle: false,
      repeatMode: 'off',
      volume: 0.5,
      isRightSidebarOpen: false,
      infoTrack: null,
      isMuted: false,
      previousVolume: 0.5,

      setQueue: (tracks, startIndex) => {
        const isShuffle = get().isShuffle;

        let currentQueue = [...tracks];
        let newIndex = startIndex;

        if (isShuffle) {
          const currentTrack = currentQueue.splice(startIndex, 1)[0];
          currentQueue = [currentTrack, ...shuffleArray(currentQueue)];
          newIndex = 0;
        }

        set({ 
          originalQueue: tracks, 
          queue: currentQueue, 
          currentIndex: newIndex, 
          currentTrack: currentQueue[newIndex],
          isPlaying: true 
        });
      },

      nextTrack: () => {
        const { queue, currentIndex, repeatMode } = get();
        let nextIndex = currentIndex + 1;

        if (nextIndex >= queue.length) {
          if (repeatMode === 'all') {
            nextIndex = 0;
          } else {
            set({ isPlaying: false });
            return;
          }
        }

        set({ 
          currentIndex: nextIndex, 
          currentTrack: queue[nextIndex], 
          isPlaying: true 
        });
      },

      prevTrack: (currentTime: number) => {
        const { currentIndex, queue } = get();
        
        if (currentTime > 5) {
          return; 
        }

        const nextIndex = Math.max(0, currentIndex - 1);
        set({ currentIndex: nextIndex, currentTrack: queue[nextIndex], isPlaying: true });
      },

      toggleShuffle: () => set((state) => {
        const newIsShuffle = !state.isShuffle;
        if (newIsShuffle) {
          const remainingTracks = state.queue.filter((_, i) => i !== state.currentIndex);
          const shuffled = [state.queue[state.currentIndex], ...shuffleArray(remainingTracks)];
          return { isShuffle: true, queue: shuffled, currentIndex: 0 };
        } else {
          const newIndex = state.originalQueue.findIndex(t => t.id === state.currentTrack?.id);
          return { isShuffle: false, queue: state.originalQueue, currentIndex: newIndex };
        }
      }),

      toggleRepeat: () => set((state) => {
        const modes: RepeatMode[] = ['off', 'all', 'one'];
        const nextMode = modes[(modes.indexOf(state.repeatMode) + 1) % 3];
        return { repeatMode: nextMode };
      }),

      setCurrentTrack: (track) => set({ currentTrack: track, isPlaying: true }),

      setPlaying: (isPlaying) => set({ isPlaying }),

      setVolume: (volume) => set({ volume }),

      togglePlay: () => set((state) => ({ isPlaying: !state.isPlaying })),
    
      toggleMute: () => set((state) => {
        if (state.isMuted) {
          return { isMuted: false, volume: state.previousVolume };
        } else {
          return { isMuted: true, previousVolume: state.volume, volume: 0 };
        }
      }),

      openInfo: (track: Track) => set((state) => {
        if (state.infoTrack?.id === track.id && state.isRightSidebarOpen) {
          return { isRightSidebarOpen: false };
        }
        return { infoTrack: track, isRightSidebarOpen: true };
      }),

      closeInfo: () => set({ isRightSidebarOpen: false }),

      handlePlay: (tracks, index) => {
        const { currentTrack, togglePlay, setQueue } = get();
        const clickedTrack = tracks[index];

        if (currentTrack?.id === clickedTrack.id) {
          togglePlay();
        } else {
          setQueue(tracks, index);
        }
      },
    }),

    {
      name: 'mray-player-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ 
        volume: state.volume, 
        isShuffle: state.isShuffle, 
        repeatMode: state.repeatMode,
        currentTrack: state.currentTrack,
        queue: state.originalQueue
      }),
    }
  )
);