import Header from "./Header";
import Footer from "./Footer";

type Props = {
  children: React.ReactNode;
  showAmbient?: boolean;
};

export default function AppLayout({ children, showAmbient = false }: Props) {
  return (
    <div className="min-h-screen bg-sand dark:bg-[#0a0a0b] text-charcoal dark:text-white">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[60] focus:rounded-full focus:bg-charcoal focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
      >
        Skip to main content
      </a>
      {showAmbient ? (
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute left-[-180px] top-[-160px] h-[400px] w-[400px] rounded-full bg-[radial-gradient(circle,_#ff7a5c_0%,_rgba(255,122,92,0)_70%)] opacity-50 blur-3xl dark:opacity-0" />
          <div className="absolute right-[-120px] top-[20%] h-[350px] w-[350px] rounded-full bg-[radial-gradient(circle,_#1fb6b2_0%,_rgba(31,182,178,0)_70%)] opacity-50 blur-3xl dark:opacity-0" />
          <div className="absolute bottom-[10%] left-[20%] h-[300px] w-[300px] rounded-full bg-[radial-gradient(circle,_#ffe085_0%,_rgba(255,224,133,0)_72%)] opacity-50 blur-3xl dark:opacity-0" />
          <div className="absolute bottom-[-100px] right-[10%] h-[350px] w-[350px] rounded-full bg-[radial-gradient(circle,_#3a7f6b_0%,_rgba(58,127,107,0)_70%)] opacity-40 blur-3xl dark:opacity-0" />

          <div className="absolute inset-0 opacity-0 dark:opacity-100">
            <div className="absolute top-0 left-1/4 h-[600px] w-[600px] rounded-full bg-gradient-to-r from-purple-500/20 to-pink-500/20 blur-[128px] animate-pulse" />
            <div className="absolute bottom-1/4 right-0 h-[500px] w-[500px] rounded-full bg-gradient-to-r from-cyan-500/15 to-blue-500/15 blur-[128px] animate-pulse" style={{ animationDelay: "1s" }} />
            <div className="absolute top-1/2 left-0 h-[400px] w-[400px] rounded-full bg-gradient-to-r from-emerald-500/10 to-teal-500/10 blur-[128px] animate-pulse" style={{ animationDelay: "2s" }} />
            <div className="absolute bottom-0 right-1/4 h-[450px] w-[450px] rounded-full bg-gradient-to-r from-amber-500/10 to-orange-500/10 blur-[128px] animate-pulse" style={{ animationDelay: "3s" }} />
            <div
              className="absolute inset-0 opacity-[0.015]"
              style={{
                backgroundImage:
                  "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E\")",
              }}
            />
          </div>
        </div>
      ) : null}

      <div className="relative z-10 flex min-h-screen flex-col">
        <Header />
        <main id="main-content" className="flex-1">
          {children}
        </main>
        <Footer />
      </div>
    </div>
  );
}
