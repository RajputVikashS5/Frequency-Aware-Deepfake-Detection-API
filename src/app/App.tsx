import { ToastProvider } from '@/hooks/useToast';
import ToastContainer from '@/components/common/ToastContainer';
import AppRouter from '@/app/router';
import { useTheme } from '@/hooks/useTheme';

function App() {
  useTheme();

  return (
    <ToastProvider>
      <AppRouter />
      <ToastContainer />
    </ToastProvider>
  );
}

export default App;
