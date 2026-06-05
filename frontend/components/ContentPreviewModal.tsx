'use client';

import { useEffect, useState } from 'react';
import type { AiContent, Board } from '@/lib/api';
import { getPinterestBoards, createPinterestBoard } from '@/lib/api';

const CATEGORY_BOARDS: Record<string, string> = {
  fashion: 'Fashion Picks',
  beauty: 'Beauty Faves',
  home: 'Home Finds',
  kitchen: 'Kitchen Essentials',
  food: 'Foodie Finds',
  baby: 'Baby Must-Haves',
  electronics: 'Tech Gadgets',
  tech: 'Tech Gadgets',
  office: 'Office Upgrades',
  sports: 'Sports & Outdoors',
  outdoors: 'Sports & Outdoors',
  automotive: 'Auto & Tools',
  tools: 'Tools & Workshop',
  pet: 'Pet Loves',
  toys: 'Toy Box',
  books: 'Book Nook',
  music: 'Sounds & Vibes',
};

function getSuggestedBoard(category?: string): string {
  if (!category) return 'Finds & Faves';
  for (const [key, name] of Object.entries(CATEGORY_BOARDS)) {
    if (category.toLowerCase().includes(key)) return name;
  }
  return 'Finds & Faves';
}

interface ContentPreviewModalProps {
  product: { asin: string; title: string; image_url?: string; category?: string };
  content: AiContent;
  generatedImageUrl?: string;
  onConfirm: (content: AiContent, boardId?: string, boardName?: string) => void;
  onCancel: () => void;
  loading?: boolean;
}

export default function ContentPreviewModal({
  product,
  content,
  generatedImageUrl,
  onConfirm,
  onCancel,
  loading,
}: ContentPreviewModalProps) {
  const [title, setTitle] = useState(content.title);
  const [description, setDescription] = useState(content.description);
  const [hashtags, setHashtags] = useState(content.hashtags.join(' '));
  const [imageUrl, setImageUrl] = useState(generatedImageUrl || product.image_url || '');
  const [boards, setBoards] = useState<Board[]>([]);
  const [selectedBoard, setSelectedBoard] = useState('');
  const [creatingBoard, setCreatingBoard] = useState(false);
  const [newBoardName, setNewBoardName] = useState('');

  const previewImage = imageUrl.startsWith('/') ? `http://localhost:8000${imageUrl}` : imageUrl;
  const suggestedBoard = getSuggestedBoard(product.category);

  useEffect(() => {
    loadBoards();
  }, []);

  async function loadBoards() {
    try {
      const result = await getPinterestBoards();
      setBoards(result.boards);
      const suggestion = suggestedBoard;
      const match = result.boards.find((b) => b.name.toLowerCase() === suggestion.toLowerCase());
      if (match) {
        setSelectedBoard(match.id);
      }
    } catch {
      setBoards([]);
    }
  }

  async function handleCreateBoard() {
    const name = newBoardName.trim() || suggestedBoard;
    if (!name) return;
    setCreatingBoard(true);
    try {
      const board = await createPinterestBoard(name);
      setBoards((prev) => [...prev, { id: board.id, name: board.name }]);
      setSelectedBoard(board.id);
      setNewBoardName('');
    } catch (err) {
      console.error('Failed to create board:', err);
    } finally {
      setCreatingBoard(false);
    }
  }

  function handleConfirm() {
    const board = boards.find((b) => b.id === selectedBoard);
    onConfirm(
      {
        title,
        description,
        hashtags: hashtags.split(' ').filter((t) => t.startsWith('#')),
      },
      selectedBoard || undefined,
      board?.name || suggestedBoard,
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto m-4">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900">Preview Pin Content</h2>
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
              AI Generated
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">{product.title?.slice(0, 80)}</p>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Pin Image</label>
              <div className="aspect-[2/3] bg-gray-100 rounded-xl overflow-hidden border border-gray-200">
                <img
                  src={previewImage}
                  alt="Pin preview"
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = product.image_url || '';
                  }}
                />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Pin Title
                <span className="text-gray-400 ml-1">({title.length}/100)</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={100}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Hashtags</label>
              <input
                type="text"
                value={hashtags}
                onChange={(e) => setHashtags(e.target.value)}
                placeholder="#tag1 #tag2 ..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="text-xs text-gray-400 mt-1">Separate tags with spaces</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Board
                <span className="text-gray-400 ml-1 font-normal">— suggested: {suggestedBoard}</span>
              </label>
              <select
                value={selectedBoard}
                onChange={(e) => setSelectedBoard(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Auto ({suggestedBoard})</option>
                {boards.map((board) => (
                  <option key={board.id} value={board.id}>
                    {board.name}
                  </option>
                ))}
              </select>
              <div className="flex items-center space-x-2 mt-2">
                <input
                  type="text"
                  value={newBoardName}
                  onChange={(e) => setNewBoardName(e.target.value)}
                  placeholder="Or create new board..."
                  className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-xs focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <button
                  onClick={handleCreateBoard}
                  disabled={creatingBoard || !newBoardName.trim()}
                  className="px-3 py-1.5 text-xs font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {creatingBoard ? '...' : 'Create'}
                </button>
              </div>
            </div>

            <div className="flex items-center space-x-2 pt-2">
              <input
                type="text"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                placeholder="Image URL (optional)"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        <div className="p-6 border-t border-gray-200 flex items-center justify-end space-x-3">
          <button
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading}
            className="px-6 py-2 text-sm font-medium text-white bg-pinterest-red rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Queuing...' : 'Queue to Pinterest'}
          </button>
        </div>
      </div>
    </div>
  );
}
