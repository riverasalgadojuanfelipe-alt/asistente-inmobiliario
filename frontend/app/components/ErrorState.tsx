"use client";

import { useTranslations } from "next-intl";

interface Props {
  message: string;
  onRetry: () => void;
}

export default function ErrorState({ message, onRetry }: Props) {
  const t = useTranslations("error");

  return (
    <div className="max-w-xl mx-auto text-center py-16 md:py-20 animate-fade-up">
      <div className="mx-auto mb-8 w-14 h-14 rounded-full border border-hairline dark:border-white/10 flex items-center justify-center">
        <svg viewBox="0 0 24 24" fill="none" className="w-7 h-7 text-bronze" aria-hidden>
          <path
            d="M12 8v4M12 16h.01"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      </div>
      <h2 className="font-serif text-3xl text-graphite dark:text-cream leading-snug">
        {t("title")}
      </h2>
      <p className="mt-4 text-graphite-soft dark:text-cream/70">{message}</p>
      <button
        onClick={onRetry}
        className="
          mt-8 inline-flex items-center gap-2 rounded-xl
          bg-forest text-cream px-5 py-3 text-sm font-medium
          hover:bg-forest-hover transition
        "
      >
        {t("retry")}
      </button>
    </div>
  );
}
