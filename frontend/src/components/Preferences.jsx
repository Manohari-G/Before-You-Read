import { useState } from 'react';

const genres = ['Thriller','Mystery','Romance','Fantasy','Horror','Crime','Historical Fiction','Literary Fiction','Science Fiction','Contemporary'];
const wants = ['Big twist','Fast-paced','Emotional','Dark','Character-driven','Mystery-focused','Thought-provoking','Light/fun'];

export default function Preferences({ onRecommend, loading }) {
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [length, setLength] = useState('Any');
  const [difficulty, setDifficulty] = useState('Any');
  const [selectedWants, setSelectedWants] = useState([]);

  const toggle = (value, setter) => setter((current) => current.includes(value) ? current.filter((x) => x !== value) : [...current, value]);

  return (
    <div className="preference-panel">
      <div className="preference-group"><span>Genres</span><div className="chips">{genres.map((g) => <button key={g} className={`chip ${selectedGenres.includes(g) ? 'active' : ''}`} onClick={() => toggle(g, setSelectedGenres)}>{g}</button>)}</div></div>
      <div className="preference-row">
        <label>Length<select value={length} onChange={(e) => setLength(e.target.value)}><option>Any</option><option>Under 200 pages</option><option>200–300</option><option>300–400</option><option>400+</option></select></label>
        <label>Writing difficulty<select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}><option>Any</option><option>Easy</option><option>Medium</option><option>Advanced</option></select></label>
      </div>
      <div className="preference-group"><span>What do you want?</span><div className="chips">{wants.map((w) => <button key={w} className={`chip ${selectedWants.includes(w) ? 'active' : ''}`} onClick={() => toggle(w, setSelectedWants)}>{w}</button>)}</div></div>
      <button className="primary-button wide" disabled={loading} onClick={() => onRecommend({ genres: selectedGenres, length, difficulty, what_you_want: selectedWants })}>✨ Recommend Books</button>
    </div>
  );
}
