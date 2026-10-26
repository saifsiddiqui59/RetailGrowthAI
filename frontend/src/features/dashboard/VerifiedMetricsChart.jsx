import { Bar } from 'react-chartjs-2'
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip } from 'chart.js'

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend)

export function verifiedCounts(values, labels) {
  if (!Array.isArray(values) || !Array.isArray(labels) || values.length !== labels.length ||
      !values.length || !values.every(v => Number.isSafeInteger(v) && v >= 0)) return null
  return { labels, datasets: [{ label: 'Verified records', data: values,
    backgroundColor: ['#168467', '#4d8fc2', '#e2ab57', '#647d9a', '#7f6db7', '#62aaa6'].slice(0, values.length),
    borderRadius: 8, maxBarThickness: 46 }] }
}

export default function VerifiedMetricsChart({ values, labels, title }) {
  const data = verifiedCounts(values, labels)
  if (!data) return <p role="status">Analytics unavailable until all counts are verified by the server.</p>
  return <div className="rg-chart">
    <div className="rg-chart-canvas" role="img" aria-label={title + ': ' + labels.map((label, i) => label + ' ' + values[i]).join(', ')}>
      <Bar data={data} options={{ responsive: true, maintainAspectRatio: false,
        animation: false, plugins: { legend: { display: false }, tooltip: { enabled: true } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } }, x: { grid: { display: false } } } }} />
    </div>
    <p className="rg-chart-source">Counts are scoped to the current authorized report. No inferred trend, revenue or engagement.</p>
  </div>
}
