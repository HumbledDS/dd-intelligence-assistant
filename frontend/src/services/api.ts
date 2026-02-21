/**
 * DD Intelligence Assistant — API client
 * All calls to the FastAPI backend at http://localhost:8000
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Types ──────────────────────────────────────────────────────────────────

export interface Company {
  siren: string;
  nom_complet: string;
  sigle?: string;
  activite_principale?: string;
  categorie_entreprise?: string;
  tranche_effectif_salarie?: string;
  date_creation?: string;
  siege?: {
    adresse?: string;
    ville?: string;
    code_postal?: string;
    departement?: string;
    region?: string;
  };
  is_entrepreneur_individuel?: boolean;
  statut_diffusion?: string;
}

export interface ReportJob {
  job_id: string | null;
  status: "queued" | "processing" | "completed" | "failed" | "cache_hit";
  sections: ReportSection[];
  error?: string;
  completed_at?: string;
  report?: ReportJob; // cache hit
}

export interface ReportSection {
  type:
    | "identity"
    | "dirigeants"
    | "finances"
    | "inpi_dirigeants"
    | "bodacc"
    | "news"
    | "synthesis";
  data: unknown;
}

export interface Synthesis {
  executive_summary: string;
  sections: {
    identite?: string;
    finances?: string;
    reputation?: string;
    conclusion?: string;
  };
  red_flags: string[];
  recommendation: "Favorable" | "Prudence" | "Défavorable";
  confidence_score: number;
}

// ─── Search ─────────────────────────────────────────────────────────────────

export async function searchCompanies(query: string): Promise<Company[]> {
  if (!query.trim()) return [];
  const res = await fetch(
    `${API_BASE}/api/v1/search?q=${encodeURIComponent(query)}`
  );
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  const data = await res.json();
  return data.results ?? [];
}

export async function getCompany(siren: string): Promise<Company> {
  const res = await fetch(`${API_BASE}/api/v1/company/${siren}`);
  if (!res.ok) throw new Error(`Company fetch failed: ${res.status}`);
  return res.json();
}

// ─── Reports ────────────────────────────────────────────────────────────────

export async function generateReport(
  siren: string,
  reportType: "quick" | "standard" | "full" = "standard"
): Promise<ReportJob> {
  const res = await fetch(`${API_BASE}/api/v1/report/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ siren, report_type: reportType }),
  });
  if (!res.ok) throw new Error(`Generate report failed: ${res.status}`);
  return res.json();
}

export async function getReportStatus(jobId: string): Promise<ReportJob> {
  const res = await fetch(`${API_BASE}/api/v1/report/${jobId}`);
  if (!res.ok) throw new Error(`Get report failed: ${res.status}`);
  return res.json();
}

/**
 * Connect to the SSE stream and call onSection for every section received.
 * Returns a cleanup function.
 */
export function streamReport(
  jobId: string,
  onSection: (section: ReportSection) => void,
  onDone: (status: "completed" | "failed") => void
): () => void {
  const evtSource = new EventSource(
    `${API_BASE}/api/v1/report/${jobId}/stream`
  );

  evtSource.onmessage = (e) => {
    try {
      const payload = JSON.parse(e.data);
      if (payload.status === "completed" || payload.status === "failed") {
        onDone(payload.status);
        evtSource.close();
      } else if (payload.type) {
        onSection(payload as ReportSection);
      }
    } catch {
      /* ignore malformed */
    }
  };

  evtSource.onerror = () => {
    onDone("failed");
    evtSource.close();
  };

  return () => evtSource.close();
}

// ─── Chat ───────────────────────────────────────────────────────────────────

export async function sendChatMessage(
  siren: string,
  question: string
): Promise<{ answer: string; sources: { content: string; section_type: string }[] }> {
  const res = await fetch(`${API_BASE}/api/v1/chat/${siren}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Erreur inconnue" }));
    throw new Error(err.detail || `Chat failed: ${res.status}`);
  }
  return res.json();
}
