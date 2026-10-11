import type { BookInput } from "./validation";

export interface GenrePrediction {
  label: string;
  /** 0 to 1, optional */
  confidence?: number;
}

export interface ClassificationResult {
  genres: GenrePrediction[];
  /** true when results are illustrative samples, not model output */
  isDemo: boolean;
}

export class ClassificationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ClassificationError";
  }
}

const API_URL = process.env.NEXT_PUBLIC_CLASSIFY_API_URL?.trim();
const TIMEOUT_MS = 30_000;

const DEMO_GENRES: GenrePrediction[] = [
  { label: "Fantasy" },
  { label: "Adventure" },
  { label: "Coming-of-Age" },
];

function sleep(ms: number, signal?: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(timer);
        reject(new DOMException("Aborted", "AbortError"));
      },
      { once: true }
    );
  });
}

/**
 * Accepted API response shapes:
 *   { "genres": ["Fantasy", "Mystery"] }
 *   { "genres": [{ "label": "Fantasy", "confidence": 0.91 }] }
 */
function normalise(data: unknown): GenrePrediction[] {
  const raw = (data as { genres?: unknown } | null)?.genres;
  if (!Array.isArray(raw)) {
    throw new ClassificationError(
      "The classification service returned an unexpected response."
    );
  }

  const genres: GenrePrediction[] = [];
  for (const item of raw) {
    if (typeof item === "string" && item.trim()) {
      genres.push({ label: item.trim() });
    } else if (
      item &&
      typeof item === "object" &&
      typeof (item as { label?: unknown }).label === "string"
    ) {
      const { label, confidence } = item as { label: string; confidence?: unknown };
      genres.push({
        label: label.trim(),
        confidence: typeof confidence === "number" ? confidence : undefined,
      });
    }
  }

  if (genres.length === 0) {
    throw new ClassificationError(
      "No genres could be identified. Try adding a fuller description."
    );
  }

  return genres.sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0));
}

export async function classifyBook(
  input: BookInput,
  signal?: AbortSignal
): Promise<ClassificationResult> {
  // No model connected yet: clearly labelled demonstration results
  if (!API_URL) {
    await sleep(1600, signal);
    return { genres: DEMO_GENRES, isDemo: true };
  }

  const controller = new AbortController();
  let timedOut = false;
  const onAbort = () => controller.abort();
  signal?.addEventListener("abort", onAbort, { once: true });
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, TIMEOUT_MS);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        book_name: input.bookName,
        author_name: input.authorName,
        description: input.description,
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new ClassificationError(
        `The classification service responded with an error (${response.status}).`
      );
    }

    const data = await response.json();
    return { genres: normalise(data), isDemo: false };
  } catch (err) {
    if (err instanceof ClassificationError) throw err;
    if (timedOut) {
      throw new ClassificationError(
        "The request took too long. Please try again."
      );
    }
    if (signal?.aborted) throw err; // cancelled by the user/page
    throw new ClassificationError(
      "We couldn't reach the classification service. Check your connection and try again."
    );
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", onAbort);
  }
}