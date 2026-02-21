/**
 * Landing page — Hero + live search connected to DINUM API
 */
import { useState, useEffect, useRef } from "react";
import Head from "next/head";
import { useRouter } from "next/router";
import Link from "next/link";
import {
  Search,
  BarChart3,
  Zap,
  Shield,
  Globe,
  ChevronRight,
  Loader2,
} from "lucide-react";
import Layout from "@/components/layout/Layout";
import { searchCompanies, Company } from "@/services/api";

const STATS = [
  { label: "Entreprises indexées", value: "11M+" },
  { label: "Sources de données", value: "6" },
  { label: "Rapport généré en", value: "~30s" },
  { label: "Précision IA", value: "92%" },
];

const FEATURES = [
  {
    icon: <Search size={20} />,
    title: "Recherche instantanée",
    desc: "Par nom, SIREN ou SIRET — 11 millions d'entreprises françaises",
    color: "rgba(99,102,241,0.12)",
    iconColor: "#818cf8",
  },
  {
    icon: <BarChart3 size={20} />,
    title: "Analyse financière",
    desc: "Ratios, bilans, solvabilité extraits des données officielles",
    color: "rgba(16,185,129,0.1)",
    iconColor: "#10b981",
  },
  {
    icon: <Zap size={20} />,
    title: "Synthèse Gemini AI",
    desc: "Rapport structuré avec red flags et recommandation en 30 secondes",
    color: "rgba(245,158,11,0.1)",
    iconColor: "#f59e0b",
  },
  {
    icon: <Globe size={20} />,
    title: "Presse & réputation",
    desc: "Surveillance Google News, BODACC, annonces légales en temps réel",
    color: "rgba(244,63,94,0.1)",
    iconColor: "#f43f5e",
  },
  {
    icon: <Shield size={20} />,
    title: "Screening INPI",
    desc: "Dirigeants certifiés, actes officiels, procédures collectives",
    color: "rgba(99,102,241,0.1)",
    iconColor: "#a78bfa",
  },
  {
    icon: <Search size={20} />,
    title: "Chat IA RAG",
    desc: "Interroge le rapport en langage naturel — réponses sourcées",
    color: "rgba(16,185,129,0.08)",
    iconColor: "#34d399",
  },
];

export default function Home() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  // Debounced search
  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      setShowDropdown(false);
      return;
    }
    const t = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await searchCompanies(query);
        setResults(data.slice(0, 8));
        setShowDropdown(data.length > 0);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 350);
    return () => clearTimeout(t);
  }, [query]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  const handleCompanyClick = (siren: string) => {
    router.push(`/company/${siren}`);
  };

  return (
    <Layout>
      <Head>
        <title>DD Intelligence — Due Diligence pour entreprises françaises</title>
        <meta
          name="description"
          content="Analysez une entreprise française en 30 secondes — données DINUM, INPI, BODACC et synthèse Gemini AI."
        />
      </Head>

      {/* ── Hero ── */}
      <section className="relative overflow-hidden pt-24 pb-20">
        {/* Background glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 60% 50% at 50% 0%, rgba(99,102,241,0.15), transparent)",
          }}
        />

        <div className="container-app relative z-10">
          <div className="text-center max-w-3xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-indigo-500/20 bg-indigo-500/5 text-indigo-300 text-sm mb-8 animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
              Propulsé par Gemini 1.5 Flash + données officielles françaises
            </div>

            <h1 className="text-5xl md:text-7xl font-extrabold mb-6 leading-none tracking-tight">
              Due Diligence{" "}
              <span
                style={{
                  background: "linear-gradient(135deg, #818cf8, #34d399)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                intelligente
              </span>
            </h1>

            <p className="text-xl text-slate-400 mb-12 leading-relaxed">
              Analysez n'importe quelle entreprise française en 30 secondes.
              <br />
              Rapport complet, red flags identifiés, recommandation IA.
            </p>

            {/* Search bar */}
            <div className="relative max-w-2xl mx-auto">
              <form onSubmit={handleSubmit} className="relative">
                <Search
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"
                  size={18}
                />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onFocus={() => results.length > 0 && setShowDropdown(true)}
                  onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                  placeholder="Nom d'entreprise, SIREN ou SIRET..."
                  className="input-search pl-11 pr-32"
                  autoFocus
                />
                {loading && (
                  <Loader2
                    className="absolute right-24 top-1/2 -translate-y-1/2 text-indigo-400 animate-spin"
                    size={16}
                  />
                )}
                <button
                  type="submit"
                  className="btn btn-primary absolute right-2 top-1/2 -translate-y-1/2 text-sm px-4 py-2"
                >
                  Analyser
                </button>
              </form>

              {/* Autocomplete dropdown */}
              {showDropdown && (
                <div
                  className="absolute top-full mt-2 w-full z-50 rounded-2xl overflow-hidden"
                  style={{
                    background: "rgba(10,15,30,0.95)",
                    border: "1px solid rgba(99,102,241,0.2)",
                    backdropFilter: "blur(16px)",
                    boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
                  }}
                >
                  {results.map((c) => (
                    <button
                      key={c.siren}
                      onMouseDown={() => handleCompanyClick(c.siren)}
                      className="w-full flex items-center justify-between px-4 py-3 hover:bg-indigo-500/10 transition-colors text-left border-b border-slate-800/50 last:border-0"
                    >
                      <div>
                        <p className="text-sm font-medium text-white">
                          {c.nom_complet}
                        </p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          SIREN {c.siren} ·{" "}
                          {c.activite_principale || "NAF non précisé"}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {c.siege?.ville && (
                          <span className="text-xs text-slate-600">
                            {c.siege.ville}
                          </span>
                        )}
                        <ChevronRight size={14} className="text-slate-600" />
                      </div>
                    </button>
                  ))}
                  <button
                    onMouseDown={() =>
                      router.push(`/search?q=${encodeURIComponent(query)}`)
                    }
                    className="w-full px-4 py-3 text-sm text-indigo-400 hover:bg-indigo-500/5 flex items-center gap-2"
                  >
                    <Search size={14} />
                    Voir tous les résultats pour "{query}"
                  </button>
                </div>
              )}
            </div>

            <p className="mt-4 text-xs text-slate-600">
              Exemples :{" "}
              {["Carrefour", "LVMH", "TotalEnergies", "BNP Paribas"].map((n) => (
                <button
                  key={n}
                  onClick={() => setQuery(n)}
                  className="text-indigo-500 hover:text-indigo-300 mr-3 transition-colors"
                >
                  {n}
                </button>
              ))}
            </p>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-20 max-w-3xl mx-auto">
            {STATS.map((s) => (
              <div key={s.label} className="card p-4 text-center">
                <p className="text-2xl font-bold text-white mb-1">{s.value}</p>
                <p className="text-xs text-slate-500">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-20">
        <div className="container-app">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-3">
              Tout ce qu'il vous faut pour une due diligence complète
            </h2>
            <p className="text-slate-500">
              Sources officielles agrégées, IA générative, zéro infrastructure
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f) => (
              <div key={f.title} className="card p-6">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center mb-4"
                  style={{ background: f.color, color: f.iconColor }}
                >
                  {f.icon}
                </div>
                <h3 className="font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </Layout>
  );
}
