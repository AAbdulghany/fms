import { BrowserRouter } from "react-router-dom";
import { NotificationProvider } from "@/contexts/NotificationContext";
import type { ReactNode } from "react";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <BrowserRouter>
      <NotificationProvider>{children}</NotificationProvider>
    </BrowserRouter>
  );
}
