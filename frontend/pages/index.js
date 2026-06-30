import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function DashboardPage() {
  const [devices, setDevices] = useState([]);
  const [user, setUser] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('device_tracker_token');
    if (!token) {
      window.location.href = '/login';
      return;
    }

    Promise.all([
      fetch(`${API}/auth/me`, { headers: { Authorization: `Bearer ${token}` } }),
      fetch(`${API}/devices`, { headers: { Authorization: `Bearer ${token}` } }),
    ])
      .then(async ([userRes, devicesRes]) => {
        if (!userRes.ok) throw new Error('Session abgelaufen');
        const userData = await userRes.json();
        const devicesData = await devicesRes.json();
        setUser(userData);
        setDevices(devicesData);
      })
      .catch((err) => {
        setError(err.message || 'Fehler beim Laden');
        localStorage.removeItem('device_tracker_token');
        window.location.href = '/login';
      });
  }, []);

  return (
    <main>
      <header style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <h1>Connected devices</h1>
        {user ? <span>Signed in as {user.username}</span> : null}
      </header>
      {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}
      <ul>
        {devices.map((device) => (
          <li key={device.id}>
            <a href={`/devices/${device.id}`}>{device.owner_name}</a>
            {' '}— {device.connected ? 'connected' : 'offline'}
          </li>
        ))}
      </ul>
    </main>
  );
}
