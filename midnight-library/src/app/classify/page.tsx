"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Header from "@/components/Header";
import BookshelfIllustration from "@/components/BookshelfIllustration";
import ClassificationForm from "@/components/ClassificationForm";
import GenreResults, { type Status } from "@/components/GenreResults";
import {
  classifyBook,
  ClassificationError,
  type ClassificationResult,
} from "@/lib/classifyBook";
import type { BookInput } from "@/lib/validation";

export default function ClassifyPage() {
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<ClassificationResult | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const lastInput = useRef<BookInput | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  // Cancel any in-flight request when leaving the page
  useEffect(() => () => controllerRef.current?.abort(), []);

  const run = useCallback(async (input: BookInput) => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    lastInput.current = input;
    setStatus("loading");
    setResult(null);
    setErrorMessage("");

    // On small screens the results sit below the form: bring them into view
    if (window.innerWidth < 1024) {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    try {
      const data = await classifyBook(input, controller.signal);
      if (controller.signal.aborted) return;
      setResult(data);
      setStatus("success");
    } catch (err) {
      if (controller.signal.aborted) return;
      setErrorMessage(
        err instanceof ClassificationError
          ? err.message
          : "Something went wrong while classifying this book."
      );
      setStatus("error");
    }
  }, []);

  const retry = useCallback(() => {
    if (lastInput.current) run(lastInput.current);
  }, [run]);

  return (
    <div className="flex min-h-dvh flex-col bg-ink">
      <Header showBack />

      <main className="relative flex-1">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_85%_10%,rgba(197,138,74,0.1),transparent_50%)]"
        />

        <div className="relative mx-auto max-w-7xl px-6 pb-16 pt-10 sm:pt-14">
          <section className="flex items-end justify-between gap-8">
            <div className="animate-fade-up">
              <p className="flex items-center gap-3 text-xs font-medium uppercase tracking-[0.2em] text-brass">
                <span aria-hidden="true" className="h-px w-8 bg-brass" />
                Classification Desk
              </p>
              <h1 className="mt-5 font-display text-4xl font-medium leading-tight tracking-tight text-paper sm:text-6xl">
                Let&apos;s uncover{" "}
                <em className="font-normal text-brass">the story.</em>
              </h1>
              <p className="mt-4 max-w-md text-base text-paper/65">
                Enter the book details below to discover its predicted genres.
              </p>
            </div>

            <BookshelfIllustration
              variant="row"
              className="hidden h-auto w-72 shrink-0 lg:block xl:w-80"
            />
          </section>

          <div className="mt-10 grid items-start gap-8 lg:grid-cols-[1.7fr_1fr]">
            <ClassificationForm onSubmit={run} isLoading={status === "loading"} />

            <div ref={resultsRef} className="scroll-mt-6 lg:sticky lg:top-6">
              <GenreResults
                status={status}
                result={result}
                errorMessage={errorMessage}
                onRetry={retry}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}