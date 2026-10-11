import { CircleAlert, FlaskConical, RotateCw } from "lucide-react";
import type { ClassificationResult } from "@/lib/classifyBook";

export type Status = "idle" | "loading" | "success" | "error";

interface Props {
  status: Status;
  result: ClassificationResult | null;
  errorMessage: string;
  onRetry: () => void;
}

const CHIP_STYLES = [
  "border-brass/70 bg-brass/10",
  "border-sage/70 bg-sage/10",
  "border-burgundy/70 bg-burgundy/10",
];

export default function GenreResults({
  status,
  result,
  errorMessage,
  onRetry,
}: Props) {
  return (
    <section
      aria-labelledby="results-heading"
      aria-live="polite"
      aria-busy={status === "loading"}
      className={`relative overflow-hidden rounded-lg border bg-aubergine p-6 sm:p-8 ${
        status === "error" ? "border-burgundy/70" : "border-brass/20"
      }`}
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-brass/25 blur-3xl"
      />

      <div className="relative">
        <h2
          id="results-heading"
          className="font-serif text-2xl font-medium text-paper sm:text-3xl"
        >
          Genres Uncovered
        </h2>
        <div className="mt-3 h-px w-12 bg-brass" />

        <div className="mt-6">
          {status === "idle" && (
            <p className="font-serif text-lg italic leading-relaxed text-paper/70">
              The shelf is waiting. Submit a book to see where it belongs.
            </p>
          )}

          {status === "loading" && (
            <div role="status">
              <p className="font-serif text-lg italic text-paper/80">
                Reading the shelves…
              </p>
              <div className="mt-5 flex flex-wrap gap-3" aria-hidden="true">
                {[96, 112, 128].map((w) => (
                  <span
                    key={w}
                    style={{ width: w }}
                    className="h-11 animate-pulse rounded-full border border-paper/10 bg-paper/10"
                  />
                ))}
              </div>
            </div>
          )}

          {status === "error" && (
            <div role="alert">
              <div className="flex items-start gap-3 text-burgundy">
                <CircleAlert size={22} className="mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-paper">
                    We couldn&apos;t classify this book.
                  </p>
                  <p className="mt-1 text-sm leading-relaxed text-paper/70">
                    {errorMessage}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={onRetry}
                className="mt-5 inline-flex items-center gap-2 rounded-full border border-brass/60 px-5 py-2.5 text-sm font-medium text-brass transition hover:bg-brass hover:text-ink"
              >
                <RotateCw size={16} />
                Try again
              </button>
            </div>
          )}

          {status === "success" && result && (
            <div>
              {result.isDemo && (
                <div className="mb-5 flex items-start gap-3 rounded-sm border border-paper/15 bg-paper/5 p-3 text-sm leading-snug text-paper/80">
                  <FlaskConical size={16} className="mt-0.5 shrink-0 text-sage" />
                  <p>
                    Illustrative sample results. No trained model is connected,
                    so these tags were not derived from your input.
                  </p>
                </div>
              )}
              <ul className="flex flex-wrap gap-3">
                {result.genres.map((genre, i) => (
                  <li
                    key={genre.label}
                    style={{ animationDelay: `${i * 90}ms` }}
                    className={`animate-chip-in rounded-full border px-5 py-2.5 font-serif text-lg font-medium text-paper ${
                      CHIP_STYLES[i % CHIP_STYLES.length]
                    }`}
                  >
                    {genre.label}
                    {typeof genre.confidence === "number" && (
                      <span className="ml-2 font-sans text-xs text-paper/60">
                        {Math.round(
                          (genre.confidence <= 1
                            ? genre.confidence * 100
                            : genre.confidence)
                        )}
                        %
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}