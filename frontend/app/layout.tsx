import './globals.css';
import { Sidebar } from '@/components/layout/sidebar';

export const metadata = {
  title: 'DecrypTrace',
  description: 'Post-Quantum Watermarking System',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="flex h-screen overflow-hidden bg-[#0A0F1C] text-[#E2E8F0]">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-8">
          {children}
        </main>
      </body>
    </html>
  );
}
