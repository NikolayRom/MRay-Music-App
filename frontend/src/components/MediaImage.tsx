import { Music, User, Disc } from 'lucide-react';

interface Props {
  imageKey?: string | null;
  type: 'track' | 'artist' | 'album';
  className?: string;
}

export const MediaImage = ({ imageKey, type, className }: Props) => {
  if (imageKey) {
    return (
      <img 
        src={`http://localhost:9000/media-assets/${imageKey}`} 
        className={`${className} object-cover`}
        alt="cover"
      />
    );
  }

  // Заглушки
  const icons = {
    track: <Music size="40%" className="text-zinc-600" />,
    artist: <User size="40%" className="text-zinc-600" />,
    album: <Disc size="40%" className="text-zinc-600" />,
  };

  return (
    <div className={`${className} bg-zinc-800 flex items-center justify-center shadow-inner`}>
      {icons[type]}
    </div>
  );
};