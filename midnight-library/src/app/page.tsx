import Link from "next/link";
import { ArrowRight } from "lucide-react";
import Header from "@/components/Header";
import BookshelfIllustration from "@/components/BookshelfIllustration";

export default function Home() {
  return (
    <div className="flex min-h-dvh flex-col bg-ink">
      <Header />

      <main className="relative flex-1 overflow-hidden">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_78%_35%,rgba(197,138,74,0.14),transparent_55%)]"
        />

        <div className="relative mx-auto grid max-w-7xl items-center gap-10 px-6 py-12 lg:grid-cols-2 lg:gap-8 lg:py-20">
          <section className="animate-fade-up">
            <p className="flex items-center gap-3 text-xs font-medium uppercase tracking-[0.2em] text-brass">
              <span aria-hidden="true" className="h-px w-8 bg-brass" />
              An NLP-powered literary experience
            </p>

            <h1 className="mt-6 font-display text-6xl font-medium leading-[0.95] tracking-tight text-paper sm:text-7xl lg:text-[6.5rem]">
              Every story
              <br />
              belongs
              <br />
              <em className="font-normal text-brass">somewhere.</em>
            </h1>

            <p className="mt-8 max-w-xl text-base leading-relaxed text-paper/70 sm:text-lg">
              Discover the genres hidden within an audiobook&apos;s story. Using
              machine learning and natural language processing, this system
              analyses book details and descriptions to identify the genres that
              best represent the story.
            </p>

            <Link
              href="/classify"
              className="mt-10 inline-flex items-center gap-3 rounded-full bg-brass px-8 py-4 text-base font-medium text-ink shadow-[0_10px_30px_-8px_rgba(197,138,74,0.7)] transition hover:brightness-110 active:scale-[0.99]"
            >
              Enter the Library
              <ArrowRight size={18} />
            </Link>

            <p className="mt-8 font-display text-sm italic text-paper/45">
              ✦ One story, many possible shelves
            </p>
          </section>

          <div className="mx-auto w-full max-w-md lg:max-w-lg">
            <BookshelfIllustration variant="hero" className="h-auto w-full" />
          </div>
        </div>
      </main>
    </div>
  );
}