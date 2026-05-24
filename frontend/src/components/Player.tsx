import { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipBack, SkipForward, Repeat, Repeat1, Shuffle, Volume2, VolumeX } from 'lucide-react';
import { usePlayerStore } from '../store/usePlayerStore';
import { formatTime } from '../utils/formatTime';
import { Link } from 'react-router-dom';
import { MediaImage } from './MediaImage';
import { useInteractionStore } from '../store/useInteractionStore';
import { LikeButton } from './LikeButton';
import { TrackActionMenu } from './TrackActionMenu';

export const Player = () => {
    const { currentTrack, isPlaying, volume, togglePlay, isMuted, toggleMute, setVolume, toggleShuffle, isShuffle, prevTrack, nextTrack, toggleRepeat, repeatMode, openInfo } = usePlayerStore();
    const audioRef = useRef<HTMLAudioElement>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const { addToHistory } = useInteractionStore();
    const [buffered, setBuffered] = useState(0);
    const [activeMenuId, setActiveMenuId] = useState<number | null>(null);

    const updateBuffer = (audio: HTMLAudioElement) => {
        if (audio.duration > 0) {
            const targetTime = audio.currentTime;
            const buffered = audio.buffered;

            for (let i = 0; i < buffered.length; i++) {
                if (buffered.start(i) <= targetTime && buffered.end(i) >= targetTime) {
                    setBuffered(buffered.end(i));
                    break;
                }
            }
        }
    };

    const onTimeUpdate = () => {
        if (audioRef.current) {
            setCurrentTime(audioRef.current.currentTime);
            updateBuffer(audioRef.current); 
        }
    };

    const onProgress = () => {
        if (audioRef.current) {
            updateBuffer(audioRef.current);
        }
    };

    const onLoadedMetadata = () => {
        if (audioRef.current) {
            setDuration(audioRef.current.duration);
        }
    };

    const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
        const time = parseFloat(e.target.value);
        if (audioRef.current) {
            audioRef.current.currentTime = time;
            setCurrentTime(time);
        }
    };

    const handlePrev = () => {
        const audio = audioRef.current;
        if (!audio) return;

        if (audio.currentTime > 5) {
            audio.currentTime = 0;
            if (!isPlaying) togglePlay(); 
        } else {
            prevTrack(audio.currentTime); 
        }
    };

    useEffect(() => {
        if (currentTrack && audioRef.current) {
            const streamUrl = `http://127.0.0.1:8000/stream/${currentTrack.id}`;
            audioRef.current.src = streamUrl;
            
            if (isPlaying) {
                audioRef.current.play().catch(e => console.error("Autoplay failed:", e));
            }
        }
    }, [currentTrack]);

    useEffect(() => {
        if (audioRef.current) {
            if (isPlaying) {
                audioRef.current.play().catch(() => {});
            } else {
                audioRef.current.pause();
            }
        }
    }, [isPlaying]);

    useEffect(() => {
        if (audioRef.current) {
            audioRef.current.volume = volume;
        }
    }, [volume]);

    useEffect(() => {
        if ('mediaSession' in navigator && currentTrack) {
            navigator.mediaSession.metadata = new MediaMetadata({
                title: currentTrack.title,
                artist: currentTrack.artist?.name,
                album: currentTrack.album?.name,
                artwork: [
                    { src: `http://localhost:9000/media-assets/${currentTrack.image_key}`, sizes: '512x512' }
                ]
            });

            navigator.mediaSession.setActionHandler('play', togglePlay);
            navigator.mediaSession.setActionHandler('pause', togglePlay);
            navigator.mediaSession.setActionHandler('nexttrack', nextTrack);
            navigator.mediaSession.setActionHandler('previoustrack', handlePrev);
            navigator.mediaSession.playbackState = isPlaying ? 'playing' : 'paused';
        }
    }, [currentTrack, isPlaying]);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.target instanceof HTMLInputElement) return;

            if (e.code === 'Space') {
                e.preventDefault();
                togglePlay();
            }
            if (e.code === 'ArrowRight') {
                if (audioRef.current) audioRef.current.currentTime += 10;
            }
            if (e.code === 'ArrowLeft') {
                if (audioRef.current) audioRef.current.currentTime -= 10;
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [togglePlay]);

    
    useEffect(() => {
        let timer: number;

        
        if (currentTrack && isPlaying) {
            timer = setTimeout(() => {
            addToHistory(currentTrack.id);
            }, 5000);
        }

        
        return () => {
            if (timer) {
            clearTimeout(timer);
            }
        };
    }, [currentTrack?.id, isPlaying]); 

    return (
        <div className={`
            fixed bottom-0 left-0 right-0 h-24 bg-black border-t border-zinc-900 px-4 
            flex items-center justify-between 
            transition-transform duration-700
            ${currentTrack ? 'translate-y-0' : 'translate-y-full'}
        `}>
            <audio 
                ref={audioRef} 
                onTimeUpdate={onTimeUpdate}
                onProgress={onProgress} 
                onLoadedMetadata={onLoadedMetadata}
                onEnded={() => {
                    const { repeatMode, queue, nextTrack } = usePlayerStore.getState();
                    
                    if (repeatMode === 'one' || (repeatMode === 'all' && queue.length === 1)) {
                        if (audioRef.current) {
                            audioRef.current.currentTime = 0;
                            audioRef.current.play();
                        }
                        return;
                    }

                    nextTrack();
                }}
            />

            {currentTrack ? (
            <>
                <div className="flex items-center gap-4 w-[30%]">
                    <div className="w-14 h-14 rounded-md overflow-hidden flex-shrink-0">
                        <MediaImage imageKey={currentTrack.image_key} type="track" className="w-full h-full" />
                    </div>
                    <div className="overflow-hidden">
                        <div 
                        onClick={() => openInfo(currentTrack)} 
                        className="text-sm text-white font-medium truncate hover:underline cursor-pointer"
                        >
                            {currentTrack.title}
                        </div>
                        <div className="flex gap-1 text-xs text-zinc-400 truncate">
                            <Link to={`/artist/${currentTrack.artist?.id}`} className="hover:underline hover:text-white">
                                {currentTrack.artist?.name}
                            </Link>
                            {currentTrack.album && (
                                <>
                                <span>•</span>
                                <Link to={`/album/${currentTrack.album.id}`} className="hover:underline hover:text-white">
                                    {currentTrack.album.name}
                                </Link>
                                </>
                            )}
                        </div>
                    </div>
                </div>

                <div className="flex flex-col items-center gap-2 w-[40%]">
                    <div className="flex items-center gap-6 text-zinc-400">
                        
                        <TrackActionMenu 
                        trackId={currentTrack.id} 
                        isOpen={activeMenuId === currentTrack.id}
                        onToggle={() => setActiveMenuId(activeMenuId === currentTrack.id ? null : currentTrack.id)}
                        />
                        
                        <Shuffle
                            size={20}
                            onClick={toggleShuffle} 
                            className={`transition-all hover:scale-110 active:scale-95 ${isShuffle ? "text-green-500" : "text-zinc-400"}`} 
                        />
                        <button onClick={handlePrev} className="text-zinc-400 hover:text-white transition-all hover:scale-110 active:scale-90">
                            <SkipBack size={24} fill="currentColor" />
                        </button>

                        <button onClick={togglePlay} className="bg-white text-black p-2 rounded-full hover:scale-105 transition-transform">
                            {isPlaying ? <Pause size={24} fill="black" /> : <Play size={24} fill="black" />}
                        </button>

                        <button onClick={nextTrack} className="text-zinc-400 hover:text-white transition-all hover:scale-110 active:scale-90">
                            <SkipForward size={24} fill="currentColor" />
                        </button>
                        <button 
                            onClick={toggleRepeat} 
                            className={`transition-all hover:scale-110 active:scale-95 ${repeatMode !== 'off' ? "text-green-500" : "text-zinc-400"}`}
                            >
                            {repeatMode === 'one' ? <Repeat1 size={20} /> : <Repeat size={20} />}
                        </button>
                        
                        <LikeButton trackId={currentTrack.id} />
                    </div>
                
                    <div className="w-full flex items-center gap-2 group">
                        <span className="text-[10px] text-zinc-500 w-8 text-right">{formatTime(currentTime)}</span>
                        
                        <div className="relative flex-1 h-1 flex items-center group">
                            <div className="absolute w-full h-full bg-zinc-800 rounded-full"></div>
                            
                            <div 
                            className="absolute h-full bg-zinc-600 rounded-full transition-all duration-300"
                            style={{ width: `${(buffered / duration) * 100}%` }}
                            ></div>
                            
                            <div 
                            className="absolute h-full bg-white group-hover:bg-green-500 rounded-full"
                            style={{ width: `${(currentTime / duration) * 100}%` }}
                            ></div>

                            <input 
                                type="range"
                                min="0"
                                max={duration || 0}
                                value={currentTime}
                                onChange={handleSeek}
                                className="absolute w-full h-full opacity-0 cursor-pointer z-10"
                            />
                        </div>

                        <span className="text-[10px] text-zinc-500 w-8">{formatTime(duration)}</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-3 w-[30%] justify-end text-zinc-400">
                        <button onClick={toggleMute} className="hover:text-white transition-colors">
                            {isMuted || volume === 0 ? <VolumeX size={20} /> : <Volume2 size={20} />}
                        </button>
                        
                        <div className="relative w-24 h-1 flex items-center group">
                            <div className="absolute w-full h-full bg-zinc-800 rounded-full"></div>
                            <div 
                            className="absolute h-full bg-white group-hover:bg-green-500 rounded-full"
                            style={{ width: `${volume * 100}%` }}
                            ></div>
                            <input 
                            type="range" 
                            min="0" max="1" step="0.01" 
                            value={volume}
                            onChange={(e) => setVolume(parseFloat(e.target.value))}
                            className="absolute w-full h-full opacity-0 cursor-pointer z-10"
                            />
                        </div>
                    </div>
                </>
                ) : (
                <div className="w-full flex items-center justify-center text-zinc-500">
                    Select track to play
                </div>
            )}
        </div>
    );
};