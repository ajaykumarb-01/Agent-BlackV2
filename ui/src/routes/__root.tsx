import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, useState, type ReactNode } from "react";

import appCss from "../styles.css?url";
import { Header } from "@/components/layout/Header";
import { SideDrawer } from "@/components/layout/SideDrawer";
import { useDarkMode } from "@/hooks/use-dark-mode";
import { SetupWalkthrough } from "@/components/setup/SetupWalkthrough";
import { api } from "@/lib/api";
import { useAppStore } from "@/lib/store";

function NotFoundComponent() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold">Page not found</h2>
        <p className="mt-2 text-sm text-text-secondary">
          The page you're looking for doesn't exist.
        </p>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  const router = useRouter();
  useEffect(() => {
    console.error("Root error:", error);
  }, [error]);
  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold">This page didn't load</h1>
        <p className="mt-2 text-sm text-text-secondary">Something went wrong.</p>
        <button
          onClick={() => {
            router.invalidate();
            reset();
          }}
          className="mt-4 rounded-md bg-foreground px-4 py-2 text-sm text-background hover:opacity-90"
        >
          Try again
        </button>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Agent Black" },
      { name: "description", content: "Agent Black — multi-agent research platform with a ChatGPT-style monochrome interface." },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "" },
      { rel: "stylesheet", href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function AppShell() {
  useDarkMode();
  const [showSetup, setShowSetup] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    api.getSettings().then((s) => {
      useAppStore.getState().setProvider(
        s.llm_provider as "gemini" | "openai" | "anthropic"
      );
    }).catch(() => {});
  }, []);

  useEffect(() => {
    api.setupStatus().then((s) => {
      if (!s.complete) setShowSetup(true);
    }).catch(() => {
      setShowSetup(true);
    }).finally(() => setChecking(false));
  }, []);

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <SideDrawer />
      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>
      {!checking && showSetup && (
        <SetupWalkthrough onComplete={() => setShowSetup(false)} />
      )}
    </div>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return (
    <QueryClientProvider client={queryClient}>
      <AppShell />
    </QueryClientProvider>
  );
}
