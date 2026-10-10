import Link from "next/link";
import { ArrowLeft, BookOpen } from "lucide-react";

export default function Header({ showBack = false }: { showBack?: boolean }) {
  return (
    <header className="border-b border-brass/10 bg-aubergine/70 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 sm:h-20">
        <Link
          href="/"
          className="flex items-center gap-3 sm:gap-4"
          aria-label="Midnight Library home"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-full border border-brass/60 text-brass sm:h-10 sm:w-10">
            <BookOpen size={18} strokeWidth={1.6} />
          </span>
          <span className="font-serif text-base font-medium uppercase tracking-[0.28em] text-paper sm:text-xl">
            Midnight Library
          </span>
        </Link>

        {showBack && (
          <Link
            href="/"
            className="flex items-center gap-2 text-sm text-brass transition hover:text-paper"
          >
            <ArrowLeft size={16} />
            <span className="hidden sm:inline">Back to Library</span>
            <span className="sm:hidden">Back</span>
          </Link>
        )}
      </div>
    </header>
  );
}