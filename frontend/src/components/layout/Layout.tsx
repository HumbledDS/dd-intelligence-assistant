/**
 * Shared layout — dark nav + footer
 */
import Link from "next/link";
import { useRouter } from "next/router";
import { Search, FileText, MessageSquare, BarChart3, Zap } from "lucide-react";

interface NavItem {
    href: string;
    label: string;
    icon: React.ReactNode;
}

const NAV: NavItem[] = [
    { href: "/", label: "Accueil", icon: <Zap size={15} /> },
];

export default function Layout({ children }: { children: React.ReactNode }) {
    const router = useRouter();

    return (
        <div className="min-h-screen flex flex-col">
            {/* ── Navbar ── */}
            <header
                style={{
                    background: "rgba(10,15,30,0.85)",
                    borderBottom: "1px solid rgba(99,102,241,0.12)",
                    backdropFilter: "blur(16px)",
                }}
                className="sticky top-0 z-50"
            >
                <div className="container-app flex items-center justify-between py-3">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2.5 group">
                        <div
                            className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold"
                            style={{ background: "linear-gradient(135deg,#6366f1,#4f46e5)" }}
                        >
                            DD
                        </div>
                        <span className="font-bold text-white tracking-tight">
                            DD Intelligence
                        </span>
                    </Link>

                    {/* Nav links */}
                    <nav className="hidden md:flex items-center gap-1">
                        {NAV.map((item) => (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`btn-ghost flex items-center gap-1.5 text-sm ${router.pathname === item.href
                                        ? "text-white"
                                        : "text-slate-400"
                                    }`}
                            >
                                {item.icon}
                                {item.label}
                            </Link>
                        ))}
                    </nav>

                    {/* CTA */}
                    <Link href="/" className="btn btn-primary text-xs px-4 py-2">
                        <Search size={13} />
                        Rechercher
                    </Link>
                </div>
            </header>

            {/* ── Content ── */}
            <main className="flex-1">{children}</main>

            {/* ── Footer ── */}
            <footer
                style={{ borderTop: "1px solid rgba(99,102,241,0.08)" }}
                className="py-6 mt-16"
            >
                <div className="container-app flex flex-col sm:flex-row items-center justify-between gap-3">
                    <p className="text-slate-500 text-sm">
                        © 2025 DD Intelligence Assistant — données DINUM, INPI, BODACC
                    </p>
                    <p className="text-slate-600 text-xs">
                        Powered by Gemini 1.5 Flash
                    </p>
                </div>
            </footer>
        </div>
    );
}
