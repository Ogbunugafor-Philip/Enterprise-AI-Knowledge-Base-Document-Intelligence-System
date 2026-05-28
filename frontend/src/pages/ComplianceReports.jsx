import React, { useState } from 'react';
import { FileText, Download, Calendar, Shield, BarChart3, Users } from 'lucide-react';
import AppLayout from '../components/Layout/AppLayout.jsx';
import { complianceApi } from '../services/complianceApi.js';

const REPORT_TYPES = [
  {
    key: 'activity',
    icon: BarChart3,
    title: 'Activity Report',
    description: 'User actions, login events, and system interactions over a date range.',
    color: 'text-blue-600 bg-blue-50',
  },
  {
    key: 'access',
    icon: Users,
    title: 'Access Report',
    description: 'Document access patterns, permission usage, and user access history.',
    color: 'text-green-600 bg-green-50',
  },
  {
    key: 'document',
    icon: FileText,
    title: 'Document Report',
    description: 'Document upload, approval, and retrieval activity summary.',
    color: 'text-purple-600 bg-purple-50',
  },
  {
    key: 'security',
    icon: Shield,
    title: 'Security Report',
    description: 'Failed logins, locked accounts, and security events.',
    color: 'text-red-600 bg-red-50',
  },
];

const RECENT = [
  { type: 'Activity Report', date: '2026-05-27', format: 'PDF' },
  { type: 'Security Report', date: '2026-05-25', format: 'CSV' },
  { type: 'Access Report', date: '2026-05-20', format: 'PDF' },
];

export default function ComplianceReports() {
  const [selectedType, setSelectedType] = useState('activity');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [format, setFormat] = useState('PDF');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  async function handleGenerate() {
    if (!dateFrom || !dateTo) { setError('Please select a date range.'); return; }
    setError(''); setSuccess(''); setGenerating(true);
    const res = await complianceApi.generateReport({
      report_type: selectedType,
      date_from: dateFrom,
      date_to: dateTo,
      format: format.toLowerCase(),
    });
    setGenerating(false);
    if (res.ok) {
      const ext = format.toLowerCase();
      const url = URL.createObjectURL(res.blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedType}_report_${dateFrom}_${dateTo}.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
      setSuccess('Report generated and downloaded successfully.');
    } else {
      setError(res.error || 'Failed to generate report.');
    }
  }

  return (
    <AppLayout title="Compliance Reports" subtitle="Generate regulatory and audit reports">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Select Report Type</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {REPORT_TYPES.map(rt => (
                <button
                  key={rt.key}
                  onClick={() => setSelectedType(rt.key)}
                  className={`flex items-start gap-3 p-4 rounded-xl border-2 text-left transition-all ${selectedType === rt.key ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'}`}
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${rt.color}`}>
                    <rt.icon className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 text-sm">{rt.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{rt.description}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="card p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-4">Report Configuration</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">From Date</label>
                  <input type="date" className="input" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">To Date</label>
                  <input type="date" className="input" value={dateTo} onChange={e => setDateTo(e.target.value)} />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Format</label>
                <div className="flex items-center gap-4">
                  {['PDF', 'CSV'].map(f => (
                    <label key={f} className="flex items-center gap-2 cursor-pointer">
                      <input type="radio" name="format" value={f} checked={format === f} onChange={() => setFormat(f)} className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium text-gray-700">{f}</span>
                    </label>
                  ))}
                </div>
              </div>
              {error && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>}
              {success && <div className="p-3 bg-green-50 text-green-700 rounded-lg text-sm">{success}</div>}
              <button onClick={handleGenerate} disabled={generating} className="btn-primary flex items-center gap-2 w-full justify-center">
                <Download className="w-4 h-4" />
                {generating ? 'Generating…' : 'Generate Report'}
              </button>
            </div>
          </div>
        </div>

        <div className="card p-6 h-fit">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Recent Reports</h2>
          {RECENT.length === 0 ? (
            <p className="text-center text-gray-400 text-sm py-6">No recent reports</p>
          ) : (
            <div className="space-y-3">
              {RECENT.map((rep, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-start gap-2">
                    <FileText className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-gray-800">{rep.type}</p>
                      <p className="text-xs text-gray-400">{rep.date} · {rep.format}</p>
                    </div>
                  </div>
                  <button className="p-1.5 text-blue-600 hover:bg-blue-50 rounded" title="Download">
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
