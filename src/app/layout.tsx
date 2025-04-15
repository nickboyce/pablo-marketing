import type { Metadata } from "next";
import { Space_Grotesk, Inter } from "next/font/google"; // Import Inter
import "./globals.css";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";

// Configure Inter for body
const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

// Configure Space Grotesk for headings
const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  weight: ['400', '700']
});

export const metadata: Metadata = {
  title: "Pablo - Facebook Ad Creation Made Easy",
  description: "Pablo makes ad creation 10× faster and eliminates errors. No more copy-pasting Meta Ads Manager.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      {/* Apply both font variables */}
      <body className={`${inter.variable} ${spaceGrotesk.variable} antialiased`}>
        <div className="flex flex-col min-h-screen">
          <Header />
          <main className="flex-1 container mx-auto px-4 py-8 max-w-4xl">
            {children}
          </main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
