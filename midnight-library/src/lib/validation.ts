export interface BookInput {
  bookName: string;
  authorName: string;
  description: string;
}

export type FieldErrors = Partial<Record<keyof BookInput, string>>;

export const LIMITS = {
  bookName: { min: 2, max: 150 },
  authorName: { min: 2, max: 100 },
  description: { min: 50, max: 5000 },
} as const;

const clean = (v: string) => v.replace(/\s+/g, " ").trim();

export function validateField(
  field: keyof BookInput,
  raw: string
): string | undefined {
  const value = clean(raw);
  const { min, max } = LIMITS[field];

  if (field === "bookName") {
    if (!value) return "Please enter the book title.";
    if (value.length < min) return `The title needs at least ${min} characters.`;
    if (value.length > max) return `The title must be ${max} characters or fewer.`;
  }

  if (field === "authorName") {
    if (!value) return "Please enter the author's name.";
    if (value.length < min) return `The name needs at least ${min} characters.`;
    if (value.length > max) return `The name must be ${max} characters or fewer.`;
    if (!/\p{L}/u.test(value)) return "The name must contain letters.";
  }

  if (field === "description") {
    if (!value) return "Please describe the story so we can read it.";
    if (value.length < min)
      return `Add a little more detail: at least ${min} characters (currently ${value.length}).`;
    if (raw.length > max)
      return `The description must be ${max} characters or fewer.`;
  }

  return undefined;
}

export function validateBook(input: BookInput): FieldErrors {
  const errors: FieldErrors = {};
  (Object.keys(LIMITS) as (keyof BookInput)[]).forEach((field) => {
    const message = validateField(field, input[field]);
    if (message) errors[field] = message;
  });
  return errors;
}

export function cleanInput(input: BookInput): BookInput {
  return {
    bookName: clean(input.bookName),
    authorName: clean(input.authorName),
    description: input.description.trim(),
  };
}