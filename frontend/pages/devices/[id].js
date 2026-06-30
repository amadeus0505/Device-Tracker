import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function DeviceDetailPage({ id }) {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API}/devices/${id}/stats`)
      .then((r) => {
        if (!r.ok) throw new Error('Failed to load stats');
        return r.json();
      })
      .then(setStats)
      .catch((err) => setError(err.message || 'Failed to load stats'));
  }, [id]);

  return (
    <main>
      <h1>Device {id}</h1>
      {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}
      {stats ? (
        <>
          <p>Owner: {stats.owner_name}</p>
          <p>Connected: {String(stats.connected)}</p>
          <p>Total sessions: {stats.total_sessions}</p>
          <p>Last seen: {stats.last_seen || 'n/a'}</p>
          <h2>History</h2>
          <pre>{JSON.stringify(stats.history || [], null, 2)}</pre>
        </>
      ) : !error ? (
        <p>Loading…</p>
      ) : null}
    </main>
  );
}

export async function getServerSideProps(context) {
  return { props: { id: context.params.id } };
}
