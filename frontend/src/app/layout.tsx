import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Sangikyo V2',
  description: '営業支援AIエージェント',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
