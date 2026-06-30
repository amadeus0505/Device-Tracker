import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AdminPage() {
  const [users, setUsers] = useState([]);
  const [devices, setDevices] = useState([]);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [ownerName, setOwnerName] = useState('');
  const [fp, setFp] = useState('');

  async function refresh() {
    const [u, d] = await Promise.all([
      fetch(`${API}/admin/users`).then((r) => r.json()),
      fetch(`${API}/devices`).then((r) => r.json()),
    ]);
    setUsers(u);
    setDevices(d);
  }

  useEffect(() => { refresh(); }, []);

  async function createUser(e) {
    e.preventDefault();
    await fetch(`${API}/admin/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, is_admin: false }),
    });
    setUsername('');
    setPassword('');
    refresh();
  }

  async function createDevice(e) {
    e.preventDefault();
    await fetch(`${API}/devices`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ owner_name: ownerName, dhcp_fingerprint: fp }),
    });
    setOwnerName('');
    setFp('');
    refresh();
  }

  return (
    <main>
      <h1>Admin</h1>
      <section>
        <h2>Create user</h2>
        <form onSubmit={createUser}>
          <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
          <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button type="submit">Create</button>
        </form>
      </section>
      <section>
        <h2>Create known device</h2>
        <form onSubmit={createDevice}>
          <input placeholder="Owner name" value={ownerName} onChange={(e) => setOwnerName(e.target.value)} />
          <input placeholder="DHCP fingerprint" value={fp} onChange={(e) => setFp(e.target.value)} />
          <button type="submit">Add device</button>
        </form>
      </section>
      <section>
        <h2>Users</h2>
        <ul>{users.map((u) => <li key={u.id}>{u.username}{u.is_admin ? ' (admin)' : ''}</li>)}</ul>
      </section>
      <section>
        <h2>Devices</h2>
        <ul>{devices.map((d) => <li key={d.id}>{d.owner_name} — {d.connected ? 'connected' : 'offline'}</li>)}</ul>
      </section>
    </main>
  );
}
