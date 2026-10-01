import { Link } from 'react-router-dom'
import { Activity, BarChart3, MessageSquare } from 'lucide-react'
import Card from '../components/Card'

export default function HomePage() {
  const quickActions = [
    {
      title: 'Coverage Prediction',
      description: 'Predict coverage class from network features',
      icon: BarChart3,
      href: '/predict',
      color: 'bg-primary-500 hover:bg-primary-600'
    },
    {
      title: 'QoS Prediction',
      description: 'Predict QoS class from RSRP/RSRQ and throughput',
      icon: Activity,
      href: '/qos',
      color: 'bg-indigo-500 hover:bg-indigo-600'
    },
    {
      title: 'AI Assistant',
      description: 'Ask questions with RAG-powered AI',
      icon: MessageSquare,
      href: '/chat',
      color: 'bg-green-500 hover:bg-green-600'
    },
  ]

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Quick Actions */}
      <Card title="Quick Actions">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 stagger">
          {quickActions.map((action) => (
            <Link
              key={action.title}
              to={action.href}
              className="group p-4 rounded-xl border border-gray-200/80 dark:border-gray-700 hover:-translate-y-1 hover:shadow-lg transition-all"
            >
              <div className={`w-12 h-12 rounded-lg ${action.color} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
                <action.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                {action.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {action.description}
              </p>
              <span className="mt-3 inline-flex items-center gap-2 text-xs font-semibold text-primary-600 opacity-0 transition-opacity group-hover:opacity-100">
                Open
                <span className="h-1.5 w-1.5 rounded-full bg-primary-600" />
              </span>
            </Link>
          ))}
        </div>
      </Card>

      <Card title="Operations Brief">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              This workspace unifies coverage and QoS prediction with guided AI analysis
              so teams can move from raw KPIs to decisions quickly and consistently.
            </p>
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-gray-200/70 bg-white/70 p-3 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Coverage pipeline
                </p>
                <p className="mt-2 text-sm text-gray-600">
                  Classify coverage quality and surface likely signal drivers.
                </p>
              </div>
              <div className="rounded-xl border border-gray-200/70 bg-white/70 p-3 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  QoS pipeline
                </p>
                <p className="mt-2 text-sm text-gray-600">
                  Classify QoS levels from live radio and throughput signals.
                </p>
              </div>
            </div>
          </div>
          <div className="rounded-2xl border border-gray-200/80 bg-white/80 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
              Recommended flow
            </p>
            <div className="mt-3 space-y-2 text-sm text-gray-600">
              <div className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-primary-400" />
                <span>Prepare KPI inputs and validate ranges.</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-primary-400" />
                <span>Run a prediction and review confidence.</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-primary-400" />
                <span>Use the assistant to validate findings.</span>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link to="/admin" className="btn-secondary px-3 py-1.5 text-sm">
                Admin console
              </Link>
              <Link to="/chat" className="btn-primary px-3 py-1.5 text-sm">
                Ask the assistant
              </Link>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
