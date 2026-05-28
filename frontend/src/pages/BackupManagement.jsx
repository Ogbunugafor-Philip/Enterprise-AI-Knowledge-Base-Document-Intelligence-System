import React, { useEffect, useState } from "react";
import { DatabaseBackup, RefreshCw, ShieldCheck } from "lucide-react";
import { backupApi } from "../services/backupApi.js";

export default function BackupManagement() {
  const [history, setHistory] = useState({ backups: [], total_count: 0 });
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [selected, setSelected] = useState(null);
  const [integrity, setIntegrity] = useState({});
  const [dryRun, setDryRun] = useState(null);
  const [restore, setRestore] = useState({ type: "postgresql", path: "", collection_name: "", confirmation: "" });
  const [message, setMessage] = useState("");

  const load = async () => {
    setLoading(true);
    const res = await backupApi.getBackupHistory();
    if (res.ok) {
      setHistory(res.data);
      setSelected(res.data.backups?.[0] || null);
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const runBackup = async () => {
    setRunning(true);
    const res = await backupApi.runBackup();
    setMessage(res.ok ? "Backup completed." : res.error);
    await load();
    setRunning(false);
  };

  const check = async (id) => {
    const res = await backupApi.checkIntegrity(id);
    if (res.ok) setIntegrity({ ...integrity, [id]: res.data });
  };

  const runDryRun = async (id) => {
    const res = await backupApi.runDryRun(id);
    if (res.ok) setDryRun(res.data);
  };

  const doRestore = async () => {
    const body = { confirmation: restore.confirmation };
    let res;
    if (restore.type === "postgresql") res = await backupApi.restorePostgresql({ ...body, backup_file_path: restore.path });
    if (restore.type === "qdrant") res = await backupApi.restoreQdrant({ ...body, snapshot_file_path: restore.path, collection_name: restore.collection_name });
    if (restore.type === "documents") res = await backupApi.restoreDocuments({ ...body, backup_archive_path: restore.path });
    setMessage(res?.ok ? "Restore request completed." : res?.error || "Restore failed");
  };

  const last = history.backups?.[0];

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6">
      <div className="mx-auto max-w-7xl">
        <header className="mb-6 flex items-center justify-between border-b pb-5">
          <div>
            <h1 className="text-2xl font-semibold">Backup Management</h1>
            <p className="text-sm text-slate-500">Last backup: {last ? new Date(last.timestamp).toLocaleString() : "No backups found"}</p>
          </div>
          <button onClick={runBackup} disabled={running} className="inline-flex items-center gap-2 rounded bg-slate-900 px-3 py-2 text-sm text-white disabled:opacity-50">
            <DatabaseBackup className="h-4 w-4" /> {running ? "Running..." : "Run Backup Now"}
          </button>
        </header>

        {message && <div className="mb-4 rounded border bg-white p-3 text-sm text-slate-700">{message}</div>}

        <section className="mb-6 grid gap-4 md:grid-cols-3">
          <div className="rounded border bg-white p-4">
            <p className="text-xs font-medium text-slate-500">Total Backups</p>
            <p className="mt-2 text-3xl font-semibold">{history.total_count || 0}</p>
          </div>
          <div className="rounded border bg-white p-4">
            <p className="text-xs font-medium text-slate-500">Newest Backup</p>
            <p className="mt-2 text-sm">{history.newest_backup ? new Date(history.newest_backup).toLocaleString() : "-"}</p>
          </div>
          <div className="rounded border bg-white p-4">
            <p className="text-xs font-medium text-slate-500">Oldest Backup</p>
            <p className="mt-2 text-sm">{history.oldest_backup ? new Date(history.oldest_backup).toLocaleString() : "-"}</p>
          </div>
        </section>

        <section className="mb-6 overflow-x-auto rounded border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-slate-50">
              <tr><th className="px-3 py-3">Date</th><th>Size</th><th>Integrity</th><th>Components</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {loading ? <tr><td colSpan={5} className="p-6 text-center text-slate-400">Loading...</td></tr> : (history.backups || []).map((backup) => (
                <tr key={backup.backup_id} className="border-b">
                  <td className="px-3 py-3">{new Date(backup.timestamp).toLocaleString()}</td>
                  <td>{backup.total_size_mb} MB</td>
                  <td>{integrity[backup.backup_id]?.all_passed ? <span className="inline-flex items-center gap-1 text-emerald-700"><ShieldCheck className="h-4 w-4" /> Passed</span> : "Not checked"}</td>
                  <td>PostgreSQL, Qdrant ({backup.qdrant_backups.length}), Documents, Config</td>
                  <td className="space-x-2">
                    <button onClick={() => check(backup.backup_id)} className="text-blue-700 underline">Integrity</button>
                    <button onClick={() => runDryRun(backup.backup_id)} className="text-slate-700 underline">Dry Run</button>
                    <button onClick={() => setSelected(backup)} className="text-slate-700 underline">Select</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {dryRun && <pre className="mb-6 overflow-auto rounded border bg-white p-4 text-xs">{JSON.stringify(dryRun, null, 2)}</pre>}

        <section className="rounded border bg-white p-4">
          <div className="mb-3 flex items-center gap-2 font-semibold"><RefreshCw className="h-4 w-4" /> Restore</div>
          <div className="grid gap-3 md:grid-cols-5">
            <select className="rounded border px-3 py-2 text-sm" value={restore.type} onChange={(e) => setRestore({ ...restore, type: e.target.value })}>
              <option value="postgresql">PostgreSQL</option>
              <option value="qdrant">Qdrant</option>
              <option value="documents">Documents</option>
            </select>
            <input className="rounded border px-3 py-2 text-sm md:col-span-2" placeholder="Backup or snapshot path" value={restore.path} onChange={(e) => setRestore({ ...restore, path: e.target.value })} />
            {restore.type === "qdrant" && <input className="rounded border px-3 py-2 text-sm" placeholder="Collection name" value={restore.collection_name} onChange={(e) => setRestore({ ...restore, collection_name: e.target.value })} />}
            <input className="rounded border px-3 py-2 text-sm" placeholder="Type CONFIRM_RESTORE" value={restore.confirmation} onChange={(e) => setRestore({ ...restore, confirmation: e.target.value })} />
            <button onClick={doRestore} disabled={restore.confirmation !== "CONFIRM_RESTORE"} className="rounded bg-red-700 px-3 py-2 text-sm text-white disabled:opacity-40">Restore</button>
          </div>
          {selected && <p className="mt-3 text-xs text-slate-500">Selected backup: {selected.backup_id}</p>}
        </section>
      </div>
    </main>
  );
}
