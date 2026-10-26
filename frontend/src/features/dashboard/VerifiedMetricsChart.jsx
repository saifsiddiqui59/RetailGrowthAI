import { Bar } from 'react-chartjs-2'
import { verifiedCounts } from './chart-model.mjs'
import { BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip } from 'chart.js'

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend)

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
