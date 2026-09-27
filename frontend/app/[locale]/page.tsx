import { setRequestLocale, getTranslations } from "next-intl/server";
import SearchExperience from "@/app/components/SearchExperience";

export default async function Home({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("footer");

  return (
    <>
      <SearchExperience />
      <footer className="border-t border-hairline dark:border-white/10 py-8 mt-auto">
        <div className="max-w-5xl mx-auto px-6 md:px-10 flex flex-col gap-5">
          <p className="text-xs text-graphite-mute leading-relaxed max-w-3xl">
            {t("disclaimer")}
          </p>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 text-xs text-graphite-mute">
            <p>{t("copyright", { year: new Date().getFullYear() })}</p>
            <p className="tracking-wide">{t("cities")}</p>
          </div>
        </div>
      </footer>
    </>
  );
}
