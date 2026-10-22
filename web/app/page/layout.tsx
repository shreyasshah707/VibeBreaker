import "./globals.css";

export default function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <main className="min-h-screen bg-dark bg-gradient from-dark via-dark to-dark p-6 antialiased">{children}</main>;
}