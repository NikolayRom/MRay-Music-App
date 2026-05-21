import { Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Player } from './components/Player';
import Home from './pages/Home'; // Должно работать, если в Home.tsx есть export default
import ArtistDetail from './pages/ArtistDetail';
import AlbumDetail from './pages/AlbumDetail';
import Search from './pages/Search';
import { TrackInfoSidebar } from './components/TrackInfoSidebar';

export default function App() {
  return (
    <div className="h-screen flex flex-col bg-black overflow-hidden relative">
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        
        {/* Контент меняется здесь в зависимости от URL */}
        <main className="flex-1 bg-gradient-to-b from-zinc-900 to-black overflow-y-auto pb-24">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/artist/:id" element={<ArtistDetail />} />
            <Route path="/album/:id" element={<AlbumDetail />} />
            <Route path="/search" element={<Search />} />
          </Routes>
        </main>

        {/* Сайдбар с информацией */}
        <TrackInfoSidebar />

      </div>

      <Player />
    </div>
  );
}