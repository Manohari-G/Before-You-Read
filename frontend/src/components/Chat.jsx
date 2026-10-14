import { useState } from 'react';

export default function Chat({ messages, onSend, loading }) {
  const [text, setText] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    const value = text.trim();
    if (!value || loading) return;
    setText('');
    await onSend(value);
  };

  return (
    <div className="card chat-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Your reading companion</p>
          <h2>💬 Chat with Before You Read</h2>
        </div>
      </div>
      <div className="chat-window">
        {messages.length === 0 && (
          <div className="empty-chat">
            <div className="empty-icon">📖</div>
            <p>Ask anything about books in the collection.</p>
            <span>Try: “I liked Never Lie. What should I read next?”</span>
          </div>
        )}
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="message-label">{message.role === 'user' ? 'You' : 'Before You Read'}</div>
            <div className="message-body">{message.content}</div>
          </div>
        ))}
        {loading && <div className="message assistant"><div className="message-label">Before You Read</div><div className="message-body typing">Thinking about the best match…</div></div>}
      </div>
      <form className="chat-form" onSubmit={submit}>
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Ask about a book, mood, pace, or recommendation…" />
        <button className="primary-button" type="submit" disabled={loading || !text.trim()}>Send</button>
      </form>
    </div>
  );
}
