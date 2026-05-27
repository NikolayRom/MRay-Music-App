import { Music, User, Disc, ListMusic } from 'lucide-react';

interface Props {
  imageKey?: string | null;
  type: 'track' | 'artist' | 'album' | 'playlist' | 'user'; 
  className?: string;
}

export const MediaImage = ({ imageKey, type, className }: Props) => {
  const bucket = (type === 'playlist' || type === 'user') ? 'core-assets' : 'media-assets';

  if (imageKey) {
    const baseUrl = import.meta.env.VITE_S3_PUBLIC_URL;
    // Если это Supabase (содержит supabase.co), добавляем путь /object/public/
    const isSupabase = baseUrl.includes('supabase.co');
    const fullUrl = isSupabase 
      ? `${baseUrl}/object/public/${bucket}/${imageKey}`
      : `${baseUrl}/${bucket}/${imageKey}`;

    return <img src={fullUrl} className={`${className} object-cover`} alt="cover" />;
  }

  const icons = {
    track: <Music size="40%" className="text-zinc-600" />,
    artist: <User size="40%" className="text-zinc-600" />,
    album: <Disc size="40%" className="text-zinc-600" />,
    playlist: <ListMusic size="40%" className="text-zinc-600" />,
    user: <User size="40%" className="text-zinc-600" />,
  };

  return (
    <div className={`${className} bg-zinc-800 flex items-center justify-center shadow-inner`}>
      {icons[type]}
    </div>
  );
};