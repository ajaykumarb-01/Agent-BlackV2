import { useEffect } from "react";
import { useAppStore } from "@/lib/store";

export function useDarkMode() {
  const darkMode = useAppStore((s) => s.darkMode);
  const setDarkMode = useAppStore((s) => s.setDarkMode);

  useEffect(() => {
    if (typeof document === "undefined") return;
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const resolve = () =>
      darkMode === null ? mql.matches : darkMode;
    const apply = () => {
      document.documentElement.classList.toggle("dark", resolve());
    };
    apply();
    if (darkMode === null) {
      mql.addEventListener("change", apply);
      return () => mql.removeEventListener("change", apply);
    }
  }, [darkMode]);

  const isDark =
    typeof document !== "undefined" &&
    document.documentElement.classList.contains("dark");

  const toggle = () => setDarkMode(!isDark);
  return { darkMode, isDark, toggle, setDarkMode };
}
