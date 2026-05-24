interface Props {
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmText?: string;
  isDanger?: boolean;
}

export const ConfirmModal = ({ title, message, onConfirm, onCancel, confirmText = "Confirm", isDanger = false }: Props) => {
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[200] flex items-center justify-center p-4">
      <div className="bg-zinc-900 w-full max-w-sm rounded-2xl p-6 border border-zinc-800 shadow-2xl">
        <h2 className="text-xl font-bold text-white mb-2">{title}</h2>
        <p className="text-zinc-400 mb-8 text-sm">{message}</p>
        
        <div className="flex justify-end gap-4">
          <button onClick={onCancel} className="px-4 py-2 text-white font-bold hover:scale-105 transition-all">
            Cancel
          </button>
          <button 
            onClick={onConfirm} 
            className={`px-6 py-2 rounded-full font-bold hover:scale-105 transition-all ${isDanger ? 'bg-red-600 text-white' : 'bg-white text-black'}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};