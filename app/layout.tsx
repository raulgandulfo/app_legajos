import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sistema RRHH · Cooperativa Agroindustrial",
  description: "Sistema de Gestión de Personal",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
