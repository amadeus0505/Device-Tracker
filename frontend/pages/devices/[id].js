import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function DeviceDetailPage({ id }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch(`${API}/devices/${id}/stats`).then((r) => r.json()).then(setStats).catch(() => setStats(null));
  }, [id]);

  return (
    <main>
      <h1>Device {id}</h1>
      {stats ? (
        <>
          <p>Owner: {stats.owner_name}</p>
          <p>Connected: {String(stats.connected)}</p>
          <p>Total sessions: {stats.total_sessions}</p>
          <p>Last seen: {stats.last_seen || 'n/a'}</p>
          <h2>History</h2>
          <pre>{JSON.stringify(stats.history, null, 2)}</pre>
        </>
      ) : (
        <p>Loading…</p>
      )}
    </main>
  );
}

export async function getServerSideProps(context) {
  return { props: { id: context.params.id } };
}
