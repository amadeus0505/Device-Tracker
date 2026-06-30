import { useEffect, useState } from 'react';
import Link from 'next/link';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function DashboardPage() {
  const [devices, setDevices] = useState([]);
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetch(`${API}/auth/me`).then((r) => r.ok ? r.json() : null).then(setUser).catch(() => setUser(null));
    fetch(`${API}/devices`).then((r) => r.json()).then(setDevices).catch(() => setDevices([]));
  }, []);

  return (
    <main>
      <header style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <h1>Connected devices</h1>
        <Link href="/admin">Admin</Link>
        <Link href="/login">Login</Link>
        {user ? <span>Signed in as {user.username}</span> : <span>Not signed in</span>}
      </header>
      <ul>
        {devices.map((device) => (
          <li key={device.id}>
            <Link href={`/devices/${device.id}`}>{device.owner_name}</Link>
            {' '}— {device.connected ? 'connected' : 'offline'}
          </li>
        ))}
      </ul>
    </main>
  );
}
