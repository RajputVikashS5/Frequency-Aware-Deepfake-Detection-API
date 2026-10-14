import { useState } from 'react';
import { Mail, Send, Loader2, Info } from 'lucide-react';
import PageHeader from '@/components/common/PageHeader';
import { useToast } from '@/hooks/useToast';
import { config } from '@/config';

export default function ContactPage() {
  const { addToast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [values, setValues] = useState({
    name: '',
    email: '',
    message: '',
  });

  const validate = (): boolean => {
    const e: Record<string, string> = {};
    if (!values.message.trim()) {
      e.message = 'Message is required';
    } else if (values.message.trim().length < 10) {
      e.message = 'Message must be at least 10 characters';
    }
    if (values.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) {
      e.email = 'Please enter a valid email address';
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    // Demo mode — no backend to receive the form
    await new Promise((r) => setTimeout(r, 1200));
    setIsSubmitting(false);

    if (config.demoMode) {
      addToast('Demo mode: your message was not actually sent. This is a demo form.', 'info');
    } else {
      addToast('Thank you for your feedback!', 'success');
    }

    setValues({ name: '', email: '', message: '' });
  };

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader
        title="Contact & Feedback"
        subtitle="Share your thoughts, report issues, or suggest improvements."
        icon={<Mail size={20} />}
      />

      {config.demoMode && (
        <div className="mb-4 flex items-start gap-3 rounded-xl border border-amber-500/20 bg-amber-500/5 p-3">
          <Info size={16} className="mt-0.5 flex-shrink-0 text-amber-400" />
          <p className="text-xs leading-relaxed text-slate-400">
            This form is in demo mode. Your message will not be sent anywhere — it is for
            demonstrating the form workflow only.
          </p>
        </div>
      )}

      <div className="glass-card p-5 sm:p-6">
        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          <div>
            <label htmlFor="name" className="label-text">
              Name <span className="text-slate-600">(optional)</span>
            </label>
            <input
              id="name"
              type="text"
              value={values.name}
              onChange={(e) => setValues((v) => ({ ...v, name: e.target.value }))}
              disabled={isSubmitting}
              className="input-field"
              placeholder="Your name"
              aria-invalid={!!errors.name}
            />
            {errors.name && (
              <p className="mt-1.5 text-xs text-red-400" role="alert">
                {errors.name}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="email" className="label-text">
              Email <span className="text-slate-600">(optional)</span>
            </label>
            <input
              id="email"
              type="email"
              value={values.email}
              onChange={(e) => setValues((v) => ({ ...v, email: e.target.value }))}
              disabled={isSubmitting}
              className="input-field"
              placeholder="you@example.com"
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? 'email-error' : undefined}
            />
            {errors.email && (
              <p id="email-error" className="mt-1.5 text-xs text-red-400" role="alert">
                {errors.email}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="message" className="label-text">
              Message <span className="text-red-400">*</span>
            </label>
            <textarea
              id="message"
              rows={5}
              value={values.message}
              onChange={(e) => setValues((v) => ({ ...v, message: e.target.value }))}
              disabled={isSubmitting}
              className="input-field resize-y"
              placeholder="Your feedback or message..."
              aria-invalid={!!errors.message}
              aria-describedby={errors.message ? 'message-error' : undefined}
            />
            {errors.message && (
              <p id="message-error" className="mt-1.5 text-xs text-red-400" role="alert">
                {errors.message}
              </p>
            )}
          </div>

          <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
            {isSubmitting ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Send size={16} />
                Send Message
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
