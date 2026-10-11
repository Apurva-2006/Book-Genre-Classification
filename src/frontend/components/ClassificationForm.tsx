"use client";

import { useState, type ChangeEvent, type InputEvent, type ReactNode } from "react";
import { LoaderCircle, Sparkles } from "lucide-react";
import {
  LIMITS,
  cleanInput,
  validateBook,
  validateField,
  type BookInput,
  type FieldErrors,
} from "@/lib/validation";

interface Props {
  onSubmit: (input: BookInput) => void;
  isLoading: boolean;
}

const EMPTY: BookInput = { bookName: "", authorName: "", description: "" };

const inputClasses = (hasError: boolean) =>
  `w-full rounded-sm border bg-white/45 px-4 py-3 text-[15px] text-ink placeholder:text-ink/40 transition focus:border-brass focus:outline-none focus:ring-2 focus:ring-brass/50 disabled:cursor-not-allowed disabled:opacity-60 ${
    hasError ? "border-burgundy" : "border-ink/25"
  }`;

function Field({
  id,
  label,
  error,
  hint,
  children,
}: {
  id: string;
  label: string;
  error?: string;
  hint?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="text-sm font-medium text-ink">
        {label}
      </label>
      {children}
      <div className="flex min-h-5 items-start justify-between gap-4 text-sm">
        {error ? (
          <p id={`${id}-error`} role="alert" className="text-burgundy">
            {error}
          </p>
        ) : (
          <span />
        )}
        {hint}
      </div>
    </div>
  );
}

export default function ClassificationForm({ onSubmit, isLoading }: Props) {
  const [values, setValues] = useState<BookInput>(EMPTY);
  const [errors, setErrors] = useState<FieldErrors>({});

  const handleChange =
    (field: keyof BookInput) =>
    (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      const value = e.target.value;
      setValues((prev) => ({ ...prev, [field]: value }));
      // Clear an existing error as soon as the field becomes valid
      if (errors[field]) {
        setErrors((prev) => ({ ...prev, [field]: validateField(field, value) }));
      }
    };

  const handleBlur = (field: keyof BookInput) => () => {
    setErrors((prev) => ({ ...prev, [field]: validateField(field, values[field]) }));
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isLoading) return;

    const found = validateBook(values);
    setErrors(found);

    const firstInvalid = (Object.keys(found) as (keyof BookInput)[])[0];
    if (firstInvalid) {
      document.getElementById(firstInvalid)?.focus();
      return;
    }
    onSubmit(cleanInput(values));
  };

  const descLength = values.description.length;

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="paper-texture relative rounded-md bg-paper p-6 text-ink shadow-[0_24px_60px_-20px_rgba(0,0,0,0.6)] sm:p-9"
    >
      {/* inner keyline, like a printed page border */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-2 rounded-sm border border-ink/10"
      />

      <div className="relative">
        <div className="flex items-start justify-between gap-4 border-b border-ink/20 pb-6">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-burgundy">
              Volume Details
            </p>
            <h2 className="mt-2 font-display text-2xl font-medium sm:text-3xl">
              Tell us about the book
            </h2>
          </div>
          <span
            aria-hidden="true"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-brass/50 font-display text-sm italic text-brass"
          >
            I
          </span>
        </div>

        <div className="mt-6 grid gap-x-5 gap-y-1 sm:grid-cols-2">
          <Field id="bookName" label="Book Name" error={errors.bookName}>
            <input
              id="bookName"
              name="bookName"
              type="text"
              autoComplete="off"
              placeholder="Enter the book title"
              value={values.bookName}
              onChange={handleChange("bookName")}
              onBlur={handleBlur("bookName")}
              disabled={isLoading}
              maxLength={LIMITS.bookName.max + 20}
              aria-invalid={!!errors.bookName}
              aria-describedby={errors.bookName ? "bookName-error" : undefined}
              className={inputClasses(!!errors.bookName)}
            />
          </Field>

          <Field id="authorName" label="Author Name" error={errors.authorName}>
            <input
              id="authorName"
              name="authorName"
              type="text"
              autoComplete="off"
              placeholder="Enter the author's name"
              value={values.authorName}
              onChange={handleChange("authorName")}
              onBlur={handleBlur("authorName")}
              disabled={isLoading}
              maxLength={LIMITS.authorName.max + 20}
              aria-invalid={!!errors.authorName}
              aria-describedby={errors.authorName ? "authorName-error" : undefined}
              className={inputClasses(!!errors.authorName)}
            />
          </Field>
        </div>

        <div className="mt-1">
          <Field
            id="description"
            label="Book Description"
            error={errors.description}
            hint={
              <span
                className={`shrink-0 tabular-nums ${
                  descLength > LIMITS.description.max ? "text-burgundy" : "text-ink/50"
                }`}
              >
                {descLength}/{LIMITS.description.max}
              </span>
            }
          >
            <textarea
              id="description"
              name="description"
              rows={6}
              placeholder="Describe the story, characters, themes, and central premise…"
              value={values.description}
              onChange={handleChange("description")}
              onBlur={handleBlur("description")}
              disabled={isLoading}
              aria-invalid={!!errors.description}
              aria-describedby={errors.description ? "description-error" : undefined}
              className={`${inputClasses(!!errors.description)} resize-y`}
            />
          </Field>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="mt-4 inline-flex w-full items-center justify-center gap-3 rounded-full bg-brass px-8 py-4 text-base font-semibold text-ink shadow-[0_10px_30px_-8px_rgba(197,138,74,0.7)] transition hover:brightness-110 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-70 sm:w-auto"
        >
          {isLoading ? (
            <>
              <LoaderCircle size={20} className="animate-spin" />
              Reading the story…
            </>
          ) : (
            <>
              <Sparkles size={20} />
              Discover Genres
            </>
          )}
        </button>
      </div>
    </form>
  );
}