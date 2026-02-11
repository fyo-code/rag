import type { Metadata } from "next";
import { Outfit, Playfair_Display, Lora } from "next/font/google";
import "./globals.css";

const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });
const playfair = Playfair_Display({ subsets: ["latin"], variable: "--font-playfair" });
const lora = Lora({ subsets: ["latin"], variable: "--font-lora" });

export const metadata: Metadata = {
  title: "Reclamații AI - Mobexpert Analytics",
  description: "AI-powered complaints analysis for Mobexpert",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ro" className="light">
      <body className={`${outfit.variable} ${playfair.variable} ${lora.variable} font-sans bg-gradient-to-br from-orange-50 via-white to-orange-100 min-h-screen text-stone-800 antialiased`}>{children}</body>
    </html>
  );
}
