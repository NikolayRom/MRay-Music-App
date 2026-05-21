import { create } from 'zustand';
import type { Track } from '../types';

interface SearchState {
  query: string;
  results: Track[];
  // Функции для обновления
  setQuery: (query: string) => void;
  setResults: (results: Track[]) => void;
  clearSearch: () => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  query: '',
  results: [],
  setQuery: (query) => set({ query }),
  setResults: (results) => set({ results }),
  clearSearch: () => set({ query: '', results: [] }),
}));