/**
 * /company/[siren] — Company profile page
 */
import { useEffect, useState } from "react";
import Head from "next/head";
import { useRouter } from "next/router";
import Link from "next/link";
import {
    Building2,
    FileText,
    MessageSquare,
    MapPin,
    Users,
    Calendar,
    Loader2,
    AlertCircle,
    ChevronRight,
} from "lucide-react";
import Layout from "@/components/layout/Layout";
import { searchCompanies, Company } from "@/services/api";

function InfoRow({ label, value }: { label: string; value?: string }) {
    if (!value) return null;
    return (
        <div className="flex items-start justify-between gap-4 py-3 border-b border-slate-800/60 last:border-0">
            <span className="text-sm text-slate-500 shrink-0">{label}</span>
            <span className="text-sm text-white text-right">{value}</span>
        </div>
    );
}

export default function CompanyPage() {
    const router = useRouter();
    const { siren } = router.query;
    const [company, setCompany] = useState<Company | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!siren || typeof siren !== "string") return;
        searchCompanies(siren)
            .then((results) => {
                if (results.length > 0) setCompany(results[0]);
                else setError("Entreprise introuvable");
            })
            .catch(() => setError("Erreur de chargement"))
            .finally(() => setLoading(false));
    }, [siren]);

    if (loading) {
        return (
            <Layout>
                <div className="container-app py-20 flex items-center gap-3 text-slate-500">
                    <Loader2 className="animate-spin text-indigo-400" size={20} />
                    Chargement…
                </div>
            </Layout>
        );
    }

    if (error || !company) {
        return (
            <Layout>
                <div className="container-app py-20">
                    <div className="flex items-center gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400">
                        <AlertCircle size={16} /> {error || "Entreprise introuvable"}
                    </div>
                </div>
            </Layout>
        );
    }

    const c = company;

    return (
        <Layout>
            <Head>
                <title>{c.nom_complet} — DD Intelligence</title>
            </Head>

            <div className="container-app py-10 max-w-4xl">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-start justify-between gap-4 mb-4">
                        <div>
                            <div className="flex items-center gap-2 mb-2">
                                <div
                                    className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm"
                                    style={{ background: "linear-gradient(135deg,#6366f1,#4f46e5)" }}
                                >
                                    {c.nom_complet.slice(0, 2).toUpperCase()}
                                </div>
                                <div>
                                    <h1 className="text-2xl font-bold text-white">{c.nom_complet}</h1>
                                    {c.sigle && (
                                        <span className="text-sm text-slate-500">{c.sigle}</span>
                                    )}
                                </div>
                            </div>
                            <p className="text-sm text-slate-500">
                                SIREN {c.siren}
                                {c.activite_principale && ` · NAF ${c.activite_principale}`}
                            </p>
                        </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex flex-wrap gap-3">
                        <Link
                            href={`/report/${c.siren}`}
                            className="btn btn-primary gap-2"
                        >
                            <FileText size={15} />
                            Générer un rapport IA
                        </Link>
                        <Link
                            href={`/chat/${c.siren}`}
                            className="btn btn-outline gap-2"
                        >
                            <MessageSquare size={15} />
                            Chat IA
                        </Link>
                    </div>
                </div>

                {/* Info cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    {/* Identity */}
                    <div className="card p-5">
                        <div className="flex items-center gap-2 mb-4">
                            <Building2 size={16} className="text-indigo-400" />
                            <h2 className="font-semibold text-white">Identité légale</h2>
                        </div>
                        <InfoRow label="SIREN" value={c.siren} />
                        <InfoRow label="Catégorie" value={c.categorie_entreprise} />
                        <InfoRow
                            label="Type"
                            value={c.is_entrepreneur_individuel ? "Entrepreneur individuel" : "Société"}
                        />
                        <InfoRow
                            label="Activité principale"
                            value={c.activite_principale}
                        />
                    </div>

                    {/* Location */}
                    <div className="card p-5">
                        <div className="flex items-center gap-2 mb-4">
                            <MapPin size={16} className="text-emerald-400" />
                            <h2 className="font-semibold text-white">Siège social</h2>
                        </div>
                        <InfoRow label="Adresse" value={c.siege?.adresse} />
                        <InfoRow label="Ville" value={c.siege?.ville} />
                        <InfoRow label="Code postal" value={c.siege?.code_postal} />
                        <InfoRow label="Département" value={c.siege?.departement} />
                        <InfoRow label="Région" value={c.siege?.region} />
                    </div>

                    {/* Staff */}
                    <div className="card p-5">
                        <div className="flex items-center gap-2 mb-4">
                            <Users size={16} className="text-amber-400" />
                            <h2 className="font-semibold text-white">Effectifs</h2>
                        </div>
                        <InfoRow
                            label="Tranche"
                            value={c.tranche_effectif_salarie ?? "Non disponible"}
                        />
                    </div>

                    {/* Dates */}
                    <div className="card p-5">
                        <div className="flex items-center gap-2 mb-4">
                            <Calendar size={16} className="text-rose-400" />
                            <h2 className="font-semibold text-white">Historique</h2>
                        </div>
                        <InfoRow
                            label="Date de création"
                            value={c.date_creation}
                        />
                        <InfoRow
                            label="Diffusion"
                            value={c.statut_diffusion === "O" ? "Publique" : "Restreinte"}
                        />
                    </div>
                </div>

                {/* CTA */}
                <div
                    className="mt-8 card p-6 flex items-center justify-between"
                    style={{ background: "rgba(99,102,241,0.06)" }}
                >
                    <div>
                        <h3 className="font-semibold text-white mb-1">
                            Prêt pour la due diligence complète ?
                        </h3>
                        <p className="text-sm text-slate-500">
                            Rapport Gemini AI avec identité, finances, BODACC & presse en ~30s
                        </p>
                    </div>
                    <Link href={`/report/${c.siren}`} className="btn btn-primary shrink-0">
                        Générer le rapport <ChevronRight size={14} />
                    </Link>
                </div>
            </div>
        </Layout>
    );
}
