/**
 * /chat/[siren] — RAG-powered IA chat over a generated report
 */
import { useState, useRef, useEffect } from "react";
import Head from "next/head";
import { useRouter } from "next/router";
import Link from "next/link";
import {
    Send,
    Loader2,
    FileText,
    Bot,
    User,
    AlertCircle,
    ChevronRight,
} from "lucide-react";
import Layout from "@/components/layout/Layout";
import { sendChatMessage } from "@/services/api";

interface Message {
    role: "user" | "assistant";
    content: string;
    sources?: { content: string; section_type: string }[];
    error?: boolean;
}

const SUGGESTED = [
    "Quels sont les principaux risques ?",
    "Qui sont les dirigeants ?",
    "Quelle est la santé financière ?",
    "Y a-t-il des procédures collectives ?",
    "Quelle est la recommandation finale ?",
];

export default function ChatPage() {
    const router = useRouter();
    const { siren } = router.query;
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const send = async (question?: string) => {
        const q = question ?? input.trim();
        if (!q || !siren || typeof siren !== "string") return;

        setMessages((prev) => [...prev, { role: "user", content: q }]);
        setInput("");
        setLoading(true);

        try {
            const res = await sendChatMessage(siren, q);
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: res.answer, sources: res.sources },
            ]);
        } catch (e: any) {
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content:
                        e.message?.includes("404")
                            ? "Aucun rapport trouvé pour ce SIREN. Générez d'abord un rapport IA."
                            : `Erreur : ${e.message}`,
                    error: true,
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Layout>
            <Head>
                <title>Chat IA — SIREN {siren} — DD Intelligence</title>
            </Head>

            <div className="container-app max-w-3xl py-6 flex flex-col h-[calc(100vh-120px)]">
                {/* Header */}
                <div className="flex items-center justify-between mb-4 shrink-0">
                    <div className="flex items-center gap-3">
                        <div
                            className="w-9 h-9 rounded-xl flex items-center justify-center"
                            style={{ background: "linear-gradient(135deg,#6366f1,#4f46e5)" }}
                        >
                            <Bot size={16} className="text-white" />
                        </div>
                        <div>
                            <h1 className="font-semibold text-white">Chat IA RAG</h1>
                            <p className="text-xs text-slate-500">SIREN {siren}</p>
                        </div>
                    </div>
                    <Link
                        href={`/report/${siren}`}
                        className="btn btn-ghost text-xs flex items-center gap-1"
                    >
                        <FileText size={13} /> Voir le rapport <ChevronRight size={13} />
                    </Link>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4">
                    {/* Welcome */}
                    {messages.length === 0 && (
                        <div className="text-center py-12">
                            <div
                                className="w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center"
                                style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)" }}
                            >
                                <Bot size={24} className="text-indigo-400" />
                            </div>
                            <h3 className="font-semibold text-white mb-2">
                                Posez vos questions sur le rapport
                            </h3>
                            <p className="text-sm text-slate-500 mb-6 max-w-sm mx-auto">
                                Je peux répondre à toutes vos questions en m'appuyant
                                uniquement sur les données du rapport généré.
                            </p>
                            <div className="flex flex-wrap justify-center gap-2">
                                {SUGGESTED.map((s) => (
                                    <button
                                        key={s}
                                        onClick={() => send(s)}
                                        className="text-xs px-3 py-1.5 rounded-full border border-slate-700 text-slate-400 hover:border-indigo-500/40 hover:text-indigo-300 transition-colors"
                                    >
                                        {s}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                        >
                            {/* Avatar */}
                            <div
                                className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-1"
                                style={{
                                    background:
                                        msg.role === "user"
                                            ? "rgba(99,102,241,0.15)"
                                            : "rgba(16,185,129,0.12)",
                                }}
                            >
                                {msg.role === "user" ? (
                                    <User size={12} className="text-indigo-400" />
                                ) : (
                                    <Bot size={12} className="text-emerald-400" />
                                )}
                            </div>

                            {/* Bubble */}
                            <div className={`max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col gap-2`}>
                                <div
                                    className={`p-3.5 rounded-2xl text-sm leading-relaxed ${msg.role === "user"
                                            ? "bg-indigo-600/25 border border-indigo-500/20 text-white rounded-tr-sm"
                                            : msg.error
                                                ? "bg-rose-500/10 border border-rose-500/15 text-rose-300 rounded-tl-sm"
                                                : "bg-slate-800/60 border border-slate-700/40 text-slate-200 rounded-tl-sm"
                                        }`}
                                >
                                    {msg.content}
                                </div>

                                {/* Sources */}
                                {msg.sources && msg.sources.length > 0 && (
                                    <div className="flex flex-wrap gap-1.5">
                                        {msg.sources.map((s, si) => (
                                            <span
                                                key={si}
                                                className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/8 border border-indigo-500/15 text-indigo-400"
                                            >
                                                {s.section_type}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {/* Loading bubble */}
                    {loading && (
                        <div className="flex gap-3">
                            <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-emerald-500/10 shrink-0 mt-1">
                                <Bot size={12} className="text-emerald-400" />
                            </div>
                            <div className="p-3.5 rounded-2xl rounded-tl-sm bg-slate-800/60 border border-slate-700/40">
                                <Loader2 size={14} className="animate-spin text-indigo-400" />
                            </div>
                        </div>
                    )}

                    <div ref={bottomRef} />
                </div>

                {/* Input */}
                <div
                    className="shrink-0 flex gap-2 p-3 rounded-2xl"
                    style={{ background: "rgba(15,23,42,0.8)", border: "1px solid rgba(99,102,241,0.15)" }}
                >
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
                        placeholder="Posez votre question…"
                        className="flex-1 bg-transparent text-white text-sm placeholder-slate-600 focus:outline-none px-2"
                        disabled={loading}
                    />
                    <button
                        onClick={() => send()}
                        disabled={!input.trim() || loading}
                        className="btn btn-primary text-sm w-9 h-9 p-0 rounded-xl"
                    >
                        {loading ? (
                            <Loader2 size={14} className="animate-spin" />
                        ) : (
                            <Send size={14} />
                        )}
                    </button>
                </div>
            </div>
        </Layout>
    );
}
