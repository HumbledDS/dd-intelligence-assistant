/**
 * /search?q=... — Full-page search results from DINUM API
 */
import { useState, useEffect } from "react";
import Head from "next/head";
import { useRouter } from "next/router";
import Link from "next/link";
import { Search, Loader2, Building2, ChevronRight, AlertCircle } from "lucide-react";
import Layout from "@/components/layout/Layout";
import { searchCompanies, Company } from "@/services/api";

function effectifLabel(code?: string) {
    const map: Record<string, string> = {
        "NN": "Non disponible", "00": "0 salarié", "01": "1-2", "02": "3-5",
        "03": "6-9", "11": "10-19", "12": "20-49", "21": "50-99",
        "22": "100-199", "31": "200-249", "32": "250-499", "41": "500-999",
        "42": "1000-1999", "51": "2000-4999", "52": "5000-9999", "53": "10000+",
    };
    return map[code ?? "NN"] ?? code ?? "N/A";
}

function CompanyCard({ c }: { c: Company }) {
    return (
        <Link href={`/company/${c.siren}`}>
            <div className="card p-5 cursor-pointer group">
                <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                            <Building2 size={14} className="text-indigo-400 shrink-0" />
                            <h3 className="font-semibold text-white truncate group-hover:text-indigo-300 transition-colors">
                                {c.nom_complet}
                            </h3>
                            {c.sigle && (
                                <span className="badge badge-gray shrink-0">{c.sigle}</span>
                            )}
                        </div>
                        <p className="text-xs text-slate-500 mb-3">
                            SIREN {c.siren}
                            {c.activite_principale && ` · ${c.activite_principale}`}
                            {c.date_creation && ` · Créée ${c.date_creation.slice(0, 4)}`}
                        </p>
                        <div className="flex flex-wrap gap-2">
                            {c.categorie_entreprise && (
                                <span className="badge badge-gray">{c.categorie_entreprise}</span>
                            )}
                            <span className="badge badge-gray">
                                {effectifLabel(c.tranche_effectif_salarie)} salariés
                            </span>
                            {c.siege?.ville && (
                                <span className="badge badge-gray">
                                    📍 {c.siege.ville} {c.siege.code_postal}
                                </span>
                            )}
                        </div>
                    </div>
                    <ChevronRight
                        size={16}
                        className="text-slate-600 group-hover:text-indigo-400 transition-colors shrink-0 mt-1"
                    />
                </div>
            </div>
        </Link>
    );
}

export default function SearchPage() {
    const router = useRouter();
    const { q } = router.query;
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<Company[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        if (typeof q === "string") setQuery(q);
    }, [q]);

    useEffect(() => {
        if (!query.trim()) return;
        setLoading(true);
        setError("");
        searchCompanies(query)
            .then(setResults)
            .catch(() => setError("Erreur lors de la recherche. Réessayez."))
            .finally(() => setLoading(false));
    }, [query]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            router.push(`/search?q=${encodeURIComponent(query.trim())}`);
        }
    };

    return (
        <Layout>
            <Head>
                <title>Recherche: {q} — DD Intelligence</title>
            </Head>

            <div className="container-app py-10">
                {/* Search bar */}
                <form onSubmit={handleSearch} className="relative max-w-2xl mb-10">
                    <Search
                        className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500"
                        size={16}
                    />
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="input-search pl-10 pr-28"
                        placeholder="Rechercher une entreprise..."
                    />
                    <button
                        type="submit"
                        className="btn btn-primary absolute right-2 top-1/2 -translate-y-1/2 text-sm px-4 py-2"
                    >
                        Rechercher
                    </button>
                </form>

                {/* State: loading */}
                {loading && (
                    <div className="flex items-center gap-3 text-slate-500 py-8">
                        <Loader2 size={18} className="animate-spin text-indigo-400" />
                        <span>Recherche en cours…</span>
                    </div>
                )}

                {/* State: error */}
                {error && (
                    <div className="flex items-center gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400">
                        <AlertCircle size={16} />
                        {error}
                    </div>
                )}

                {/* Results */}
                {!loading && !error && (
                    <>
                        {results.length > 0 ? (
                            <>
                                <p className="text-sm text-slate-500 mb-4">
                                    {results.length} résultat{results.length > 1 ? "s" : ""} pour «{" "}
                                    <span className="text-white">{q}</span> »
                                </p>
                                <div className="grid gap-3">
                                    {results.map((c) => (
                                        <CompanyCard key={c.siren} c={c} />
                                    ))}
                                </div>
                            </>
                        ) : query && !loading ? (
                            <div className="text-center py-20 text-slate-600">
                                <Building2 size={40} className="mx-auto mb-4 opacity-30" />
                                <p className="font-medium text-slate-500">Aucune entreprise trouvée</p>
                                <p className="text-sm mt-1">Essayez un SIREN ou un autre nom</p>
                            </div>
                        ) : null}
                    </>
                )}
            </div>
        </Layout>
    );
}
