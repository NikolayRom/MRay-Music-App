import { Heart } from 'lucide-react';
import { useInteractionStore } from '../store/useInteractionStore';
import { useAuthStore } from '../store/useAuthStore';

export const LikeButton = ({ trackId, size = 20 }: { trackId: number, size?: number }) => {
  const { isAuthenticated } = useAuthStore();
  const { likedTrackIds, toggleLike } = useInteractionStore();
  
  const isLiked = likedTrackIds.includes(trackId);

  if (!isAuthenticated) return null; // Гости не могут лайкать

  return (
    <button 
      onClick={(e) => {
        e.stopPropagation();
        toggleLike(trackId);
      }}
      className={`transition-transform active:scale-125 hover:scale-110 ${
        isLiked ? "text-green-500" : "text-zinc-400 hover:text-white"
      }`}
    >
      <Heart size={size} fill={isLiked ? "currentColor" : "none"} />
    </button>
  );
};