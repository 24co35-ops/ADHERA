import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface AdherenceChartProps {
  trendData?: { status: string; scheduled_utc: string }[];
  type?: 'line' | 'bar';
}

export const AdherenceChart: React.FC<AdherenceChartProps> = ({
  trendData = [],
  type = 'line',
}) => {
  // Aggregate last 7 days adherence
  const last7Days: string[] = [];
  const today = new Date();
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    last7Days.push(d.toISOString().slice(0, 10));
  }

  const dayCounts: Record<string, { taken: number; total: number }> = {};
  last7Days.forEach((d) => {
    dayCounts[d] = { taken: 0, total: 0 };
  });

  trendData.forEach((entry) => {
    const dateKey = entry.scheduled_utc?.slice(0, 10);
    if (dateKey && dayCounts[dateKey]) {
      dayCounts[dateKey].total += 1;
      if (entry.status === 'taken') {
        dayCounts[dateKey].taken += 1;
      }
    }
  });

  const labels = last7Days.map((d) => {
    const dateObj = new Date(d);
    return dateObj.toLocaleDateString(undefined, { weekday: 'short', month: 'numeric', day: 'numeric' });
  });

  const rates = last7Days.map((d) => {
    const { taken, total } = dayCounts[d];
    return total > 0 ? Math.round((taken / total) * 100) : 100;
  });

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Adherence Rate (%)',
        data: rates,
        borderColor: '#00dbe7',
        backgroundColor: (context: any) => {
          const ctx = context.chart.ctx;
          const gradient = ctx.createLinearGradient(0, 0, 0, 200);
          gradient.addColorStop(0, 'rgba(0, 219, 231, 0.4)');
          gradient.addColorStop(1, 'rgba(0, 219, 231, 0.0)');
          return gradient;
        },
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#00dbe7',
        pointBorderColor: '#111318',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: '#1e2024',
        titleColor: '#e2e2e8',
        bodyColor: '#00dbe7',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
        displayColors: false,
        callbacks: {
          label: (context) => `Adherence: ${context.parsed.y}%`,
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.04)',
        },
        ticks: {
          color: '#849495',
          font: { family: 'Inter', size: 11 },
        },
      },
      y: {
        min: 0,
        max: 100,
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
        ticks: {
          color: '#849495',
          font: { family: 'Inter', size: 11 },
          stepSize: 25,
          callback: (value) => `${value}%`,
        },
      },
    },
  };

  return (
    <div className="w-full h-48 sm:h-64">
      <Line data={chartData} options={options} />
    </div>
  );
};
