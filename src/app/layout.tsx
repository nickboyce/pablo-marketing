import type { Metadata } from "next";
import { Space_Grotesk, Inter } from "next/font/google"; // Import Inter
import Script from "next/script";
import "./globals.css";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { PostHogProvider } from "@/components/providers/posthog-provider";

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
  title: "Pablo - 10× faster Facebook ad creation",
  description: "Pablo makes ad creation 10× faster and eliminates errors. No more copy-pasting Meta Ads Manager.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        {/* Meta Pixel Code */}
        <noscript>
          <img 
            height="1" 
            width="1" 
            style={{display: 'none'}}
            src="https://www.facebook.com/tr?id=1121736923151899&ev=PageView&noscript=1"
            alt=""
          />
        </noscript>
      </head>
      {/* Apply both font variables */}
      <body className={`${inter.variable} ${spaceGrotesk.variable} antialiased`}>
        {/* Meta Pixel Script */}
        <Script
          id="meta-pixel"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              !function(f,b,e,v,n,t,s)
              {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
              n.callMethod.apply(n,arguments):n.queue.push(arguments)};
              if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
              n.queue=[];t=b.createElement(e);t.async=!0;
              t.src=v;s=b.getElementsByTagName(e)[0];
              s.parentNode.insertBefore(t,s)}(window, document,'script',
              'https://connect.facebook.net/en_US/fbevents.js');
              fbq('init', '1121736923151899');
              fbq('track', 'PageView');
            `,
          }}
        />
        
        <PostHogProvider>
          <div className="flex flex-col min-h-screen">
            <Header />
            <main className="flex-1 container mx-auto px-4 py-8 max-w-4xl">
              {children}
            </main>
            <Footer />
          </div>
        </PostHogProvider>
      </body>
    </html>
  );
}
