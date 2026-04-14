import type { Metadata } from "next";
import { Poppins } from "next/font/google";
import ThemeProvider from "@/components/theme-provider";
import ThemeToggle from "@/components/theme-toggle";
import "./globals.css";

const poppins = Poppins({
  variable: "--font-poppins",
  subsets: ["latin"],
  weight: ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
  display: "swap"
});

export const metadata: Metadata = {
  title: "lafleur IQ — Ask Questions, Get Cited Answers",
  description: "lafleur IQ uses AI-powered retrieval to search your documents and generate accurate, cited answers instantly.",
  icons: {
    icon: "/LOGO.png",
    shortcut: "/LOGO.png",
    apple: "/LOGO.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${poppins.variable} antialiased`}
      >
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
          {children}
          <div className="pointer-events-none fixed bottom-5 left-5 z-80">
            <ThemeToggle className="pointer-events-auto" />
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
