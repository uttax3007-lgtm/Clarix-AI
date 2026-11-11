import "./globals.css";
import { Inter, Plus_Jakarta_Sans, Noto_Sans_Devanagari } from "next/font/google";
import { AuthProvider } from "@/contexts/auth";
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jakarta = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-jakarta" });
const deva = Noto_Sans_Devanagari({ subsets: ["devanagari"] });
export const metadata = { title: "CLARIX AI", description: "Understand Anything. In Your Language." };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body className={`${inter.variable} ${jakarta.variable} ${deva.className}`}>
    <AuthProvider>{children}</AuthProvider></body></html>;
}
