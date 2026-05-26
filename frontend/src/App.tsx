import { Routes, Route, useLocation } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Player } from './components/Player';
import Home from './pages/Home'; 
import ArtistDetail from './pages/ArtistDetail';
import AlbumDetail from './pages/AlbumDetail';
import Search from './pages/Search';
import { TrackInfoSidebar } from './components/TrackInfoSidebar';
import Login from './pages/Login';
import Register from './pages/Register';
import { useAuthStore } from './store/useAuthStore';
import { useInteractionStore } from './store/useInteractionStore';
import { useEffect } from 'react';
import LikedTracks from './pages/LikedTracks';
import Library from './pages/Library';
import PlaylistDetail from './pages/PlaylistDetail';
import HistoryPage from './pages/HistoryPage';
import { usePlaylistStore } from './store/usePlaylistStore';
import Settings from './pages/Settings';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';

export default function App() {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';

  
  const { checkAuth, isAuthenticated } = useAuthStore();
  const { fetchLikes } = useInteractionStore();
  const { fetchPlaylists } = usePlaylistStore();

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      fetchLikes();
      fetchPlaylists();
    }
  }, [isAuthenticated]);

  if (isAuthPage) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-black overflow-hidden relative">
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 bg-gradient-to-b from-zinc-900 to-black overflow-y-auto pb-24">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/search" element={<Search />} />
            <Route path="/artist/:id" element={<ArtistDetail />} />
            <Route path="/album/:id" element={<AlbumDetail />} />
            <Route path="/library" element={<Library />} />
            <Route path="/library/liked" element={<LikedTracks />} />
            <Route path="/library/history" element={<HistoryPage />} /> 
            <Route path="/playlist/:id" element={<PlaylistDetail />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
          </Routes>
        </main>
        <TrackInfoSidebar />
      </div>
      <Player />
    </div>
  );
}