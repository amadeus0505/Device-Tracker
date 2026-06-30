import { useEffect, useState } from 'react';
import Link from 'next/link';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function DashboardPage() {
  const [devices, setDevices] = useState([]);

  useEffect(() => {
    fetch(`${API}/devices`).then((r) => r.json()).then(setDevices).catch(() => setDevices([]));
  }, []);

  return (
    <main>
      <h1>Connected devices</h1>
      <Link href="/admin">Admin</Link>
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
