import "./globals.css";

export const metadata = {
  title: "DocStyle Web",
  description: "DocStyle Pro minimal web client",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
