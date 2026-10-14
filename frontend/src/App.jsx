import { useState } from 'react';
import Chat from './components/Chat';
import Preferences from './components/Preferences';
import SpoilerSelector from './components/SpoilerSelector';

const API = 'http://127.0.0.1:8000';

async function callApi(path, body) {
  try {
    const response = await fetch(`${API}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(
        data.detail || 'The backend could not complete the request.'
      );
    }

    return data;
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        'Unable to connect to the book assistant. Please make sure the backend is running.'
      );
    }

    throw error;
  }
}

function cleanResponse(text) {
  if (!text) return '';

  return text
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/###\s*/g, '')
    .replace(/##\s*/g, '')
    .replace(/#\s*/g, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/^---+$/gm, '')
    .replace(/\|/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function Result({ title, children }) {
  if (!children) return null;

  return (
    <div className="result-card">
      <div className="result-title">{title}</div>
      <div className="result-text">{cleanResponse(children)}</div>
    </div>
  );
}

export default function App() {
  const [activePage, setActivePage] = useState('chat');

  const [spoilerMode, setSpoilerMode] = useState('NO_SPOILERS');

  const [query, setQuery] = useState('');
  const [recommendation, setRecommendation] = useState('');

  const [book, setBook] = useState('');
  const [beforeRead, setBeforeRead] = useState('');

  const [book1, setBook1] = useState('');
  const [book2, setBook2] = useState('');
  const [comparison, setComparison] = useState('');

  const [messages, setMessages] = useState([]);

  const [loadingKey, setLoadingKey] = useState('');
  const [error, setError] = useState('');

  const history = messages.map(({ role, content }) => ({
    role,
    content,
  }));

  const run = async (key, path, body, setter) => {
    setError('');
    setLoadingKey(key);

    try {
      const data = await callApi(path, body);
      setter(cleanResponse(data.answer));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoadingKey('');
    }
  };

  const sendChat = async (text) => {
    const next = [
      ...messages,
      {
        role: 'user',
        content: text,
      },
    ];

    setMessages(next);
    setError('');
    setLoadingKey('chat');

    try {
      const data = await callApi('/chat', {
        question: text,
        spoiler_mode: spoilerMode,
        history,
      });

      setMessages([
        ...next,
        {
          role: 'assistant',
          content: cleanResponse(data.answer),
        },
      ]);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoadingKey('');
    }
  };

  const preferenceRecommend = (preferences) =>
    run(
      'preferences',
      '/recommend/preferences',
      {
        preferences,
        spoiler_mode: spoilerMode,
      },
      setRecommendation
    );

  return (
    <div className="app-shell">

      {/* HERO */}
      <header className="hero">
        <div className="hero-inner">

          <div className="logo-mark">📚</div>

          <p className="eyebrow">
            Your spoiler-controlled reading companion
          </p>

          <h1>Before You Read</h1>

          <p className="tagline">
            Find your next book. Know what to expect.
            Read without unwanted spoilers.
          </p>

          <SpoilerSelector
            value={spoilerMode}
            onChange={setSpoilerMode}
          />

        </div>
      </header>


      {/* NAVIGATION */}
      <nav className="main-navigation">
        <div className="navigation-inner">

          <button
            className={`nav-button ${
              activePage === 'chat' ? 'active' : ''
            }`}
            onClick={() => setActivePage('chat')}
          >
            💬 Chat
          </button>

          <button
            className={`nav-button ${
              activePage === 'recommend' ? 'active' : ''
            }`}
            onClick={() => setActivePage('recommend')}
          >
            ✨ Recommendations
          </button>

          <button
            className={`nav-button ${
              activePage === 'before' ? 'active' : ''
            }`}
            onClick={() => setActivePage('before')}
          >
            📖 Before You Read
          </button>

          <button
            className={`nav-button ${
              activePage === 'compare' ? 'active' : ''
            }`}
            onClick={() => setActivePage('compare')}
          >
            ⚖️ Compare Books
          </button>

        </div>
      </nav>


      {/* MAIN CONTENT */}
      <main className="content">

        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}


        {/* CHAT */}
        {activePage === 'chat' && (
          <section className="card chat-card">

            <div className="section-heading">
              <div>
                <p className="eyebrow">Your Reading Companion</p>

                <h2>💬 Chat About Books</h2>

                <p>
                  Ask anything about the books in the collection.
                </p>
              </div>
            </div>

            <Chat
              messages={messages}
              onSend={sendChat}
              loading={loadingKey === 'chat'}
            />

          </section>
        )}


        {/* RECOMMENDATIONS */}
        {activePage === 'recommend' && (
          <section className="card">

            <div className="section-heading">
              <div>

                <p className="eyebrow">
                  Discover
                </p>

                <h2>
                  ✨ Find Your Next Book
                </h2>

                <p>
                  Describe the genre, mood, pace, or reading
                  experience you are looking for.
                </p>

              </div>
            </div>


            <div className="input-row">

              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="I want a psychological thriller with a huge twist..."
              />

              <button
                className="primary-button"
                disabled={
                  !query.trim() ||
                  loadingKey === 'recommend'
                }
                onClick={() =>
                  run(
                    'recommend',
                    '/recommend',
                    {
                      query,
                      spoiler_mode: spoilerMode,
                      history,
                    },
                    setRecommendation
                  )
                }
              >
                ✨ Recommend Books
              </button>

            </div>


            <Result title="📚 Recommendations">
              {recommendation}
            </Result>


            <Preferences
              onRecommend={preferenceRecommend}
              loading={loadingKey === 'preferences'}
            />

          </section>
        )}


        {/* BEFORE YOU READ */}
        {activePage === 'before' && (
          <section className="card">

            <div className="section-heading">
              <div>

                <p className="eyebrow">
                  Prepare
                </p>

                <h2>
                  📖 Before You Read
                </h2>

                <p>
                  Know what the reading experience is like
                  without ruining the story.
                </p>

              </div>
            </div>


            <div className="stack">

              <input
                value={book}
                onChange={(e) => setBook(e.target.value)}
                placeholder="Enter a book title..."
              />

              <button
                className="primary-button"
                disabled={
                  !book.trim() ||
                  loadingKey === 'before'
                }
                onClick={() =>
                  run(
                    'before',
                    '/before-read',
                    {
                      book,
                      spoiler_mode: spoilerMode,
                      history,
                    },
                    setBeforeRead
                  )
                }
              >
                📖 Tell Me Before I Read
              </button>

            </div>


            <Result title="Your Reading Guide">
              {beforeRead}
            </Result>

          </section>
        )}


        {/* COMPARE */}
        {activePage === 'compare' && (
          <section className="card">

            <div className="section-heading">
              <div>

                <p className="eyebrow">
                  Choose
                </p>

                <h2>
                  ⚖️ Compare Books
                </h2>

                <p>
                  Put two books side by side and find out
                  which one fits you better.
                </p>

              </div>
            </div>


            <div className="stack">

              <input
                value={book1}
                onChange={(e) => setBook1(e.target.value)}
                placeholder="First book — e.g. Never Lie"
              />

              <input
                value={book2}
                onChange={(e) => setBook2(e.target.value)}
                placeholder="Second book — e.g. The Silent Patient"
              />

              <button
                className="primary-button"
                disabled={
                  !book1.trim() ||
                  !book2.trim() ||
                  loadingKey === 'compare'
                }
                onClick={() =>
                  run(
                    'compare',
                    '/compare',
                    {
                      book1,
                      book2,
                      spoiler_mode: spoilerMode,
                      history,
                    },
                    setComparison
                  )
                }
              >
                ⚖️ Compare
              </button>

            </div>


            <Result title="Book Comparison">
              {comparison}
            </Result>

          </section>
        )}


        <footer>
          <span>📚 Before You Read</span>
          <span>
            RAG-powered book discovery · Local knowledge base · Spoiler-aware
          </span>
        </footer>

      </main>

    </div>
  );
}