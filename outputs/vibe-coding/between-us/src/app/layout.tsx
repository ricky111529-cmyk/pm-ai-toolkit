import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Between Us | 서로의 장면을 듣는 시간",
  description: "같은 상황에 대한 두 사람의 속마음을 함께 여는 대화 카드 앱"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
