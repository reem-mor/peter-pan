import { useState } from "react";
import type { FormEvent, ReactNode } from "react";

/**
 * "Get a demo" lead form. Client-side validation mirrors the server's
 * LeadRequest bounds; the POST goes to `${VITE_API_BASE}/leads` (ppos :8005;
 * vite dev proxy forwards /leads — see vite.config.ts)
 * (relative by default, so a reverse proxy can route it to the PPOS
 * service without a rebuild).
 */

const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";
const LEADS_ENDPOINT = `${API_BASE}/leads`;

interface LeadValues {
  name: string;
  email: string;
  company: string;
  message: string;
}

type FieldName = keyof LeadValues;
type FieldErrors = Partial<Record<FieldName, string>>;
type Status = "idle" | "submitting" | "success" | "error";

const EMPTY: LeadValues = { name: "", email: "", company: "", message: "" };

// Same shape check the server enforces (something@domain.tld).
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Mirror of the server-side LeadRequest max lengths.
const MAX_LENGTHS: Record<FieldName, number> = {
  name: 120,
  email: 254,
  company: 200,
  message: 2000,
};

function validate(values: LeadValues): FieldErrors {
  const errors: FieldErrors = {};
  if (!values.name.trim()) errors.name = "Please tell us your name.";
  if (!values.email.trim()) {
    errors.email = "Please enter your work email.";
  } else if (!EMAIL_PATTERN.test(values.email.trim())) {
    errors.email = "That doesn't look like an email address.";
  }
  if (!values.company.trim()) errors.company = "Please tell us where you work.";
  for (const field of Object.keys(MAX_LENGTHS) as FieldName[]) {
    if (values[field].length > MAX_LENGTHS[field]) {
      errors[field] = `Keep this under ${MAX_LENGTHS[field]} characters.`;
    }
  }
  return errors;
}

const INPUT_CLASSES =
  "mt-1 w-full rounded-lg border border-ink/20 bg-surface-raised px-3 py-2 text-ink " +
  "placeholder:text-ink-soft/60 aria-[invalid=true]:border-red-700";

interface FieldProps {
  name: FieldName;
  label: string;
  error?: string;
  children: (props: {
    id: string;
    name: FieldName;
    "aria-invalid": boolean;
    "aria-describedby": string | undefined;
    className: string;
  }) => ReactNode;
}

function Field({ name, label, error, children }: FieldProps) {
  const id = `lead-${name}`;
  const errorId = `${id}-error`;
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-semibold">
        {label}
      </label>
      {children({
        id,
        name,
        "aria-invalid": Boolean(error),
        "aria-describedby": error ? errorId : undefined,
        className: INPUT_CLASSES,
      })}
      {error && (
        <p id={errorId} className="mt-1 text-sm font-medium text-red-800">
          {error}
        </p>
      )}
    </div>
  );
}

export function LeadForm() {
  const [values, setValues] = useState<LeadValues>(EMPTY);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [status, setStatus] = useState<Status>("idle");

  const setField = (field: FieldName, value: string) => {
    setValues((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextErrors = validate(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setStatus("submitting");
    try {
      const response = await fetch(LEADS_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: values.name.trim(),
          email: values.email.trim(),
          company: values.company.trim(),
          message: values.message.trim(),
        }),
      });
      setStatus(response.ok ? "success" : "error");
    } catch {
      setStatus("error");
    }
  };

  if (status === "success") {
    return (
      <div
        role="status"
        className="rounded-xl border border-ink/10 bg-surface-raised p-8 text-center"
      >
        <h3 className="text-xl font-bold">Thanks — request received.</h3>
        <p className="mx-auto mt-3 max-w-md text-ink-soft">
          We&apos;ll reach out to schedule a walkthrough of the demo path — it runs
          fixture-first, so there&apos;s nothing to install and no accounts to create.
        </p>
      </div>
    );
  }

  return (
    <form
      onSubmit={(event) => {
        void handleSubmit(event);
      }}
      noValidate
      className="grid gap-4 rounded-xl border border-ink/10 bg-surface-raised p-6 sm:grid-cols-2 sm:p-8"
    >
      <Field name="name" label="Name" error={errors.name}>
        {(props) => (
          <input
            {...props}
            type="text"
            autoComplete="name"
            value={values.name}
            onChange={(e) => setField("name", e.target.value)}
          />
        )}
      </Field>
      <Field name="email" label="Work email" error={errors.email}>
        {(props) => (
          <input
            {...props}
            type="email"
            autoComplete="email"
            value={values.email}
            onChange={(e) => setField("email", e.target.value)}
          />
        )}
      </Field>
      <div className="sm:col-span-2">
        <Field name="company" label="Company" error={errors.company}>
          {(props) => (
            <input
              {...props}
              type="text"
              autoComplete="organization"
              value={values.company}
              onChange={(e) => setField("company", e.target.value)}
            />
          )}
        </Field>
      </div>
      <div className="sm:col-span-2">
        <Field name="message" label="What should the demo cover? (optional)" error={errors.message}>
          {(props) => (
            <textarea
              {...props}
              rows={4}
              value={values.message}
              onChange={(e) => setField("message", e.target.value)}
            />
          )}
        </Field>
      </div>
      {status === "error" && (
        <p role="alert" className="text-sm font-medium text-red-800 sm:col-span-2">
          Something went wrong sending your request. Please try again in a moment.
        </p>
      )}
      <div className="sm:col-span-2">
        <button
          type="submit"
          disabled={status === "submitting"}
          className="w-full rounded-lg bg-accent-strong px-6 py-3 font-semibold text-white transition-colors hover:bg-accent-deep disabled:opacity-60 sm:w-auto"
        >
          {status === "submitting" ? "Sending…" : "Get a demo"}
        </button>
      </div>
    </form>
  );
}
