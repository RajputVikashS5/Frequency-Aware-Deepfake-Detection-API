import { Link } from 'react-router-dom';
import { Home, Search } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="mb-4">
        <span className="text-6xl font-bold gradient-text">404</span>
      </div>
      <h2 className="mb-2 text-xl font-semibold text-slate-100">Page not found</h2>
      <p className="mb-6 max-w-md text-sm text-slate-400">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <div className="flex gap-3">
        <Link to="/" className="btn-primary">
          <Home size={16} />
          Back to Dashboard
        </Link>
        <Link to="/analyze" className="btn-secondary">
          <Search size={16} />
          Analyze News
        </Link>
      </div>
    </div>
  );
}
