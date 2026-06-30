import { useEffect, useMemo, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const REFRESH_MS = 4000;

function formatDuration(seconds) {
  const totalMinutes = Math.floor(seconds / 60);
  const days = Math.floor(totalMinutes / (60 * 24));
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
  const minutes = totalMinutes % 60;
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m`;
  return `${seconds}s`;
}

function badgeColor(connected) {
  return connected ? 'bg-emerald-100 text-emerald-700 ring-1 ring-emerald-200' : 'bg-slate-100 text-slate-600 ring-1 ring-slate-200';
}

function SectionCard({ title, subtitle, children, action }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white/80 p-6 shadow-sm backdrop-blur">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          {subtitle ? <p className="mt-1 text-sm text-slate-500">{subtitle}</p> : null}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function DeviceRow({ device, statsHref }) {
  return (
    <a href={statsHref} className="group flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50/70 px-4 py-3 transition hover:border-indigo-200 hover:bg-indigo-50/40">
      <div>
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-900">{device.owner_name}</span>
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${badgeColor(device.connected)}`}>
            {device.connected ? 'connected' : 'offline'}
          </span>
        </div>
        <div className="mt-1 text-xs text-slate-500">{device.mac || 'no MAC'} · {device.ip || 'no IP'}</div>
      </div>
      <span className="text-sm font-medium text-indigo-600 group-hover:text-indigo-700">Details →</span>
    </a>
  );
}

export default function AdminPage() {
  const [overview, setOverview] = useState(null);
  const [users, setUsers] = useState([]);
  const [devices, setDevices] = useState([]);
  const [unknownCandidates, setUnknownCandidates] = useState([]);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [ownerName, setOwnerName] = useState('');
  const [fp, setFp] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState('');
  const [message, setMessage] = useState('');

  async function authFetch(url, options = {}) {
    const token = localStorage.getItem('device_tracker_token');
    return fetch(url, {
      ...options,
      headers: {
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`,
      },
    });
  }

  async function refresh() {
    const [ov, u, d, unk] = await Promise.all([
      authFetch(`${API}/devices/overview`).then((r) => r.json()),
      authFetch(`${API}/admin/users`).then((r) => r.json()),
      authFetch(`${API}/devices`).then((r) => r.json()),
      authFetch(`${API}/devices/connected-unknown`).then((r) => r.json()),
    ]);
    setOverview(ov);
    setUsers(u);
    setDevices(d);
    setUnknownCandidates(unk);
  }

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, REFRESH_MS);
    return () => clearInterval(timer);
  }, []);

  const knownConnectedCount = useMemo(() => devices.filter((d) => d.connected).length, [devices]);

  async function createUser(e) {
    e.preventDefault();
    await authFetch(`${API}/admin/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, is_admin: false }),
    });
    setUsername('');
    setPassword('');
    setMessage('User created');
    refresh();
  }

  async function createDevice(e) {
    e.preventDefault();
    const chosen = unknownCandidates.find((c) => c.mac === selectedCandidate);
    await authFetch(`${API}/devices`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        owner_name: ownerName,
        dhcp_fingerprint: fp || chosen?.current_fingerprint || '',
        mac: chosen?.mac || null,
        ip: chosen?.ip || null,
      }),
    });
    setOwnerName('');
    setFp('');
    setSelectedCandidate('');
    setMessage('Device created');
    refresh();
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50 text-slate-900">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.2em] text-indigo-600">Device Tracker</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">Admin Dashboard</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">Live overview of connected devices, unknown candidates, and managed known devices.</p>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <div className="text-2xl font-semibold">{devices.length}</div>
              <div className="text-xs text-slate-500">Known</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <div className="text-2xl font-semibold">{knownConnectedCount}</div>
              <div className="text-xs text-slate-500">Connected</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <div className="text-2xl font-semibold">{unknownCandidates.length}</div>
              <div className="text-xs text-slate-500">Unknown</div>
            </div>
          </div>
        </div>

        {message ? <div className="mb-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</div> : null}

        <div className="grid gap-6 lg:grid-cols-2">
          <SectionCard title="Add known device" subtitle="Pick a currently connected, unrecognized device or enter details manually.">
            <form onSubmit={createDevice} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <input className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none transition focus:border-indigo-400" placeholder="Owner name" value={ownerName} onChange={(e) => setOwnerName(e.target.value)} />
                <input className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none transition focus:border-indigo-400" placeholder="DHCP fingerprint" value={fp} onChange={(e) => setFp(e.target.value)} />
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">Connected but unknown devices</label>
                <select className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none transition focus:border-indigo-400" value={selectedCandidate} onChange={(e) => {
                  setSelectedCandidate(e.target.value);
                  const chosen = unknownCandidates.find((c) => c.mac === e.target.value);
                  if (chosen) {
                    setFp(chosen.current_fingerprint || fp);
                  }
                }}>
                  <option value="">Select a device…</option>
                  {unknownCandidates.map((device) => (
                    <option key={device.mac} value={device.mac}>
                      {device.mac} {device.ip ? `· ${device.ip}` : ''} · connected {device.connected_since_label} ago
                    </option>
                  ))}
                </select>
                <p className="mt-2 text-xs text-slate-500">These devices are online right now but not yet known.</p>
              </div>
              <button type="submit" className="inline-flex items-center rounded-xl bg-indigo-600 px-4 py-3 font-medium text-white shadow-sm transition hover:bg-indigo-700">Create device</button>
            </form>
          </SectionCard>

          <SectionCard title="Live unknown candidates" subtitle="Devices that are connected but not yet assigned to a known profile.">
            <div className="space-y-3">
              {unknownCandidates.length === 0 ? (
                <p className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-500">No unknown connected devices right now.</p>
              ) : unknownCandidates.map((device) => (
                <div key={device.mac} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium text-slate-900">{device.mac}</div>
                      <div className="mt-1 text-sm text-slate-500">{device.ip || 'no IP'} · connected for {device.connected_since_label}</div>
                    </div>
                    <button type="button" onClick={() => {
                      setSelectedCandidate(device.mac);
                      setFp(device.current_fingerprint || '');
                    }} className="rounded-lg border border-indigo-200 bg-white px-3 py-2 text-sm font-medium text-indigo-700 transition hover:bg-indigo-50">
                      Use
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-2">
          <SectionCard title="Known devices" subtitle="Live list of all known devices and their current state.">
            <div className="space-y-3">
              {devices.map((device) => (
                <DeviceRow key={device.id} device={device} statsHref={`/devices/${device.id}`} />
              ))}
            </div>
          </SectionCard>

          <SectionCard title="Users" subtitle="Admin-managed user accounts.">
            <form onSubmit={createUser} className="mb-4 grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
              <input className="rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none transition focus:border-indigo-400" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
              <input className="rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none transition focus:border-indigo-400" placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
              <button type="submit" className="rounded-xl bg-slate-900 px-4 py-3 font-medium text-white transition hover:bg-slate-800">Create</button>
            </form>
            <div className="space-y-2">
              {users.map((u) => (
                <div key={u.id} className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <span className="font-medium">{u.username}</span>
                  <span className="text-sm text-slate-500">{u.is_admin ? 'admin' : 'user'}</span>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      </div>
    </main>
  );
}
