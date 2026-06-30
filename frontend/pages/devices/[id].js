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
        <pre>{JSON.stringify(stats, null, 2)}</pre>
      ) : (
        <p>Loading…</p>
      )}
    </main>
  );
}

export async function getServerSideProps(context) {
  return { props: { id: context.params.id } };
}
