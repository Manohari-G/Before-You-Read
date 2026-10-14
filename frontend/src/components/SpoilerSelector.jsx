const modes = [
  { value: 'NO_SPOILERS', label: '🟢 No Spoilers', note: 'Safe before reading' },
  { value: 'LIGHT_SPOILERS', label: '🟡 Light Spoilers', note: 'Minor plot details' },
  { value: 'FULL_DISCUSSION', label: '🔴 Full Discussion', note: 'Twists & ending allowed' },
];

export default function SpoilerSelector({ value, onChange }) {
  return (
    <div className="spoiler-box">
      <div className="spoiler-title">Spoiler control</div>
      <div className="spoiler-options">
        {modes.map((mode) => (
          <button
            key={mode.value}
            className={`spoiler-option ${value === mode.value ? 'selected' : ''}`}
            onClick={() => onChange(mode.value)}
          >
            <strong>{mode.label}</strong>
            <span>{mode.note}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
