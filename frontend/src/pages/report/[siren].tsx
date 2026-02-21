/**
 * /report/[siren] — Report generation with SSE streaming
 * Triggers report pipeline and displays sections as they stream in.
 */
import { useEffect, useState, useCallback } from "react";
import Head from "next/head";
import { useRouter } from "next/router";
import Link from "next/link";
import {
    FileText,
    MessageSquare,
    Loader2,
    CheckCircle2,
    XCircle,
    AlertTriangle,
    ChevronDown,
    ChevronUp,
    Building2,
    Newspaper,
    BarChart3,
    Users,
    Scale,
} from "lucide-react";
import Layout from "@/components/layout/Layout";
import {
    generateReport,
    streamReport,
    ReportSection,
    Synthesis,
} from "@/services/api";

// ── Icons per section type ──────────────────────────────────────────────────
const SECTION_META: Record<
    string,
    { label: string; icon: React.ReactNode; color: string }
> = {
    identity: { label: "Identité", icon: <Building2 size={14} />, color: "#818cf8" },
    dirigeants: { label: "Dirigeants (DINUM)", icon: <Users size={14} />, color: "#34d399" },
    inpi_dirigeants: { label: "Dirigeants (INPI)", icon: <Users size={14} />, color: "#6ee7b7" },
    finances: { label: "Données financières", icon: <BarChart3 size={14} />, color: "#f59e0b" },
    bodacc: { label: "Annonces BODACC", icon: <Scale size={14} />, color: "#f87171" },
    news: { label: "Presse", icon: <Newspaper size={14} />, color: "#a78bfa" },
    synthesis: { label: "Synthèse IA", icon: <FileText size={14} />, color: "#fbbf24" },
};

// ── Recommendation badge ────────────────────────────────────────────────────
function RecoBadge({ value }: { value?: string }) {
    if (!value) return null;
    const cls =
        value === "Favorable"
            ? "badge-favorable"
            : value === "Défavorable"
                ? "badge-defavorable"
                : "badge-prudence";
    return <span className={`badge ${cls} text-sm px-4 py-1.5`}>{value}</span>;
}

// ── Single streaming section card ───────────────────────────────────────────
function SectionCard({ section }: { section: ReportSection }) {
    const [open, setOpen] = useState(section.type === "synthesis");
    const meta = SECTION_META[section.type];

    if (section.type === "synthesis") {
        const synthesis = section.data as Synthesis;
        return (
            <div className="card p-6" style={{ borderColor: "rgba(251,191,36,0.25)" }}>
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <span style={{ color: "#fbbf24" }}>{meta?.icon}</span>
                        <h3 className="font-semibold text-white">{meta?.label}</h3>
                    </div>
                    <RecoBadge value={synthesis.recommendation} />
                </div>

                {synthesis.red_flags?.length > 0 && (
                    <div className="mb-4 p-4 rounded-xl bg-rose-500/8 border border-rose-500/15">
                        <p className="text-xs font-semibold text-rose-400 mb-2 flex items-center gap-1.5">
                            <AlertTriangle size={12} /> Red Flags ({synthesis.red_flags.length})
                        </p>
                        <ul className="space-y-1">
                            {synthesis.red_flags.map((rf, i) => (
                                <li key={i} className="text-sm text-rose-300">{rf}</li>
                            ))}
                        </ul>
                    </div>
                )}

                <p className="text-sm text-slate-300 mb-4 leading-relaxed">
                    {synthesis.executive_summary}
                </p>

                {synthesis.sections && (
                    <div className="grid gap-3">
                        {Object.entries(synthesis.sections).map(([key, text]) => (
                            text ? (
                                <div key={key} className="p-3 rounded-lg bg-slate-800/40">
                                    <p className="text-xs font-semibold text-slate-500 uppercase mb-1">{key}</p>
                                    <p className="text-sm text-slate-300 leading-relaxed">{text as string}</p>
                                </div>
                            ) : null
                        ))}
                    </div>
                )}

                <div className="mt-4 flex items-center justify-between">
                    <p className="text-xs text-slate-600">
                        Indice de confiance : {synthesis.confidence_score
                            ? `${Math.round(synthesis.confidence_score * 100)}%`
                            : "N/A"}
                    </p>
                </div>
            </div>
        );
    }

    // Generic section (collapsible)
    return (
        <div className="card overflow-hidden">
            <button
                className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-white/2 transition-colors"
                onClick={() => setOpen((v) => !v)}
            >
                <div className="flex items-center gap-2">
                    <span style={{ color: meta?.color ?? "#94a3b8" }}>{meta?.icon}</span>
                    <span className="text-sm font-medium text-white">{meta?.label ?? section.type}</span>
                    <CheckCircle2 size={12} className="text-emerald-400 ml-1" />
                </div>
                {open ? (
                    <ChevronUp size={14} className="text-slate-600" />
                ) : (
                    <ChevronDown size={14} className="text-slate-600" />
                )}
            </button>
            {open && (
                <div className="px-5 pb-4 border-t border-slate-800/60">
                    <pre className="text-xs text-slate-400 mt-3 whitespace-pre-wrap font-mono leading-relaxed overflow-auto max-h-64">
                        {JSON.stringify(section.data, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
}

// ── Main page ────────────────────────────────────────────────────────────────
export default function ReportPage() {
    const router = useRouter();
    const { siren } = router.query;

    const [sections, setSections] = useState<ReportSection[]>([]);
    const [status, setStatus] = useState<
        "idle" | "queued" | "processing" | "completed" | "failed"
    >("idle");
    const [error, setError] = useState("");
    const [jobId, setJobId] = useState<string | null>(null);
    const [reportType, setReportType] = useState<"quick" | "standard" | "full">("standard");

    const PHASES = [
        "Identité DINUM",
        "Dirigeants & finances",
        "INPI officiel",
        "BODACC & presse",
        "Synthèse Gemini",
    ];
    const progress = Math.min(
        Math.round((sections.length / PHASES.length) * 100),
        95
    );

    const startReport = useCallback(async () => {
        if (!siren || typeof siren !== "string") return;
        setSections([]);
        setStatus("queued");
        setError("");

        try {
            const job = await generateReport(siren, reportType);

            if (job.status === "cache_hit" && job.report) {
                setSections((job.report as any).sections ?? []);
                setStatus("completed");
                return;
            }

            if (!job.job_id) {
                setError("Erreur de démarrage");
                setStatus("failed");
                return;
            }

            setJobId(job.job_id);
            setStatus("processing");

            // Connect SSE
            const cleanup = streamReport(
                job.job_id,
                (section) => setSections((prev) => [...prev, section]),
                (finalStatus) => setStatus(finalStatus)
            );

            return cleanup;
        } catch (e: any) {
            setError(e.message ?? "Erreur inconnue");
            setStatus("failed");
        }
    }, [siren, reportType]);

    useEffect(() => {
        if (!siren) return;
        const cleanup = startReport();
        return () => {
            if (cleanup instanceof Function) cleanup();
        };
    }, [siren]);

    const synthesis = sections.find((s) => s.type === "synthesis");

    return (
        <Layout>
            <Head>
                <title>Rapport SIREN {siren} — DD Intelligence</title>
            </Head>

            <div className="container-app py-10 max-w-4xl">
                {/* Header */}
                <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
                    <div>
                        <h1 className="text-xl font-bold text-white">
                            Rapport due diligence
                        </h1>
                        <p className="text-sm text-slate-500">SIREN {siren}</p>
                    </div>
                    <div className="flex items-center gap-3">
                        {/* Report type selector */}
                        <select
                            value={reportType}
                            onChange={(e) => setReportType(e.target.value as any)}
                            disabled={status === "processing" || status === "queued"}
                            className="bg-slate-800/60 border border-slate-700 text-slate-300 rounded-xl text-sm px-3 py-2 focus:outline-none focus:border-indigo-500"
                        >
                            <option value="quick">Aperçu rapide</option>
                            <option value="standard">Standard</option>
                            <option value="full">Complet</option>
                        </select>

                        {(status === "completed" || status === "failed") && (
                            <button onClick={() => startReport()} className="btn btn-outline text-sm">
                                Regénérer
                            </button>
                        )}
                        {status === "completed" && (
                            <Link href={`/chat/${siren}`} className="btn btn-primary text-sm">
                                <MessageSquare size={14} /> Chat IA
                            </Link>
                        )}
                    </div>
                </div>

                {/* Progress bar */}
                {(status === "processing" || status === "queued") && (
                    <div className="card p-5 mb-6">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="pulse-dot" />
                            <p className="text-sm font-medium text-white">
                                {status === "queued" ? "En attente…" : "Collecte des données en cours"}
                            </p>
                            <span className="text-xs text-slate-600 ml-auto">{progress}%</span>
                        </div>
                        <div className="progress-bar">
                            <div className="progress-fill" style={{ width: `${progress}%` }} />
                        </div>
                        <div className="flex gap-4 mt-3 overflow-x-auto">
                            {PHASES.map((phase, i) => (
                                <div key={i} className="flex items-center gap-1.5 shrink-0">
                                    {i < sections.length ? (
                                        <CheckCircle2 size={12} className="text-emerald-400" />
                                    ) : i === sections.length ? (
                                        <Loader2 size={12} className="animate-spin text-indigo-400" />
                                    ) : (
                                        <div className="w-3 h-3 rounded-full border border-slate-700" />
                                    )}
                                    <span
                                        className={`text-xs ${i < sections.length
                                                ? "text-emerald-400"
                                                : i === sections.length
                                                    ? "text-indigo-400"
                                                    : "text-slate-600"
                                            }`}
                                    >
                                        {phase}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Completed banner */}
                {status === "completed" && (
                    <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/8 border border-emerald-500/20 text-emerald-400 mb-6">
                        <CheckCircle2 size={16} />
                        <span className="text-sm font-medium">Rapport généré avec succès</span>
                    </div>
                )}

                {/* Failed banner */}
                {status === "failed" && (
                    <div className="flex items-center gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 mb-6">
                        <XCircle size={16} />
                        <span className="text-sm">
                            {error || "Échec de génération — vérifiez la clé GEMINI_API_KEY"}
                        </span>
                    </div>
                )}

                {/* Synthesis first */}
                {synthesis && (
                    <div className="mb-5">
                        <SectionCard section={synthesis} />
                    </div>
                )}

                {/* Remaining sections */}
                <div className="grid gap-3">
                    {sections
                        .filter((s) => s.type !== "synthesis")
                        .map((s, i) => (
                            <SectionCard key={i} section={s} />
                        ))}
                </div>

                {/* Placeholder while loading */}
                {sections.length === 0 && status !== "failed" && (
                    <div className="space-y-3">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="skeleton h-16 w-full" />
                        ))}
                    </div>
                )}
            </div>
        </Layout>
    );
}
