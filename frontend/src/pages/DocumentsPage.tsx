import { useRef, useState } from "react";

import { api } from "../api/client";
import { ApiError } from "../api/client";
import type { SearchHit } from "../api/types";
import {
  Badge,
  Card,
  EmptyState,
  ErrorState,
  fmtDate,
  fmtNumber,
  PageHeader,
  Spinner,
  Table,
  tdClass,
  useFetch,
} from "../components/ui";

const inputClass =
  "rounded-md border border-slate-300 px-2.5 py-1.5 text-sm text-slate-700 focus:border-indigo-500 focus:outline-none";

export function DocumentsPage() {
  const docs = useFetch(() => api.documents(), []);
  const fileRef = useRef<HTMLInputElement | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [documentIdentifier, setDocumentIdentifier] = useState("");
  const [issuingAuthority, setIssuingAuthority] = useState("");
  const [documentVersion, setDocumentVersion] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [isSample, setIsSample] = useState(true);
  const [ingesting, setIngesting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);

  async function runSearch() {
    if (!searchQuery.trim()) return;
    setSearching(true);
    setSearchError(null);
    try {
      const result = await api.documentSearch({ query: searchQuery.trim(), top_k: 8, min_score: 0.05 });
      setHits(result.hits);
      if (result.insufficient_evidence) {
        setSearchError("No indexed passages scored above the relevance floor — try a different phrasing.");
      }
    } catch (err) {
      setSearchError(err instanceof ApiError ? err.message : String(err));
      setHits(null);
    } finally {
      setSearching(false);
    }
  }

  async function ingest() {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setIngestError("Choose a .txt, .md or text-based .pdf file first.");
      return;
    }
    if (!title.trim()) {
      setIngestError("A title is required.");
      return;
    }
    setIngesting(true);
    setIngestError(null);
    setNotice(null);
    const form = new FormData();
    form.append("file", file);
    form.append("title", title.trim());
    if (documentIdentifier.trim()) form.append("document_identifier", documentIdentifier.trim());
    if (issuingAuthority.trim()) form.append("issuing_authority", issuingAuthority.trim());
    if (documentVersion.trim()) form.append("document_version", documentVersion.trim());
    if (sourceUrl.trim()) form.append("source_url", sourceUrl.trim());
    form.append("is_sample", String(isSample));

    try {
      const result = await api.documentIngest(form);
      setNotice(`Ingested "${result.title}" — ${result.page_count} page(s), ${result.chunk_count} chunk(s), status ${result.status}.`);
      setTitle("");
      setDocumentIdentifier("");
      setIssuingAuthority("");
      setDocumentVersion("");
      setSourceUrl("");
      if (fileRef.current) fileRef.current.value = "";
      docs.reload();
    } catch (err) {
      setIngestError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setIngesting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Regulatory Documents"
        subtitle="Ingest public regulatory text into the knowledge base, then search it semantically. Every citation the AI assistant returns points back here."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Ingest a document" subtitle="UTF-8 .txt / .md files work offline; text-based PDFs are also supported">
          <div className="flex flex-col gap-3">
            <input ref={fileRef} type="file" accept=".txt,.md,.pdf" className="text-sm" />
            <input
              className={inputClass}
              placeholder="Title (required)"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
            <div className="grid grid-cols-2 gap-3">
              <input
                className={inputClass}
                placeholder="Document identifier (e.g. BCBS-vanilla-001)"
                value={documentIdentifier}
                onChange={(event) => setDocumentIdentifier(event.target.value)}
              />
              <input
                className={inputClass}
                placeholder="Issuing authority (e.g. Basel Committee)"
                value={issuingAuthority}
                onChange={(event) => setIssuingAuthority(event.target.value)}
              />
              <input
                className={inputClass}
                placeholder="Document version (e.g. v2.1)"
                value={documentVersion}
                onChange={(event) => setDocumentVersion(event.target.value)}
              />
              <input
                className={inputClass}
                placeholder="Source URL (optional)"
                value={sourceUrl}
                onChange={(event) => setSourceUrl(event.target.value)}
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={isSample}
                onChange={(event) => setIsSample(event.target.checked)}
              />
              Mark as clearly-labelled sample content
            </label>
            <div className="flex items-center gap-3">
              <button
                type="button"
                disabled={ingesting}
                onClick={ingest}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {ingesting ? "Ingesting…" : "Ingest"}
              </button>
              {notice ? <p className="text-sm text-indigo-700">{notice}</p> : null}
              {ingestError ? <p className="text-sm text-rose-700">{ingestError}</p> : null}
            </div>
          </div>
        </Card>

        <Card title="Semantic search" subtitle="Embedding-based retrieval over indexed chunks (installable offline via sentence-transformers)">
          <div className="flex gap-2">
            <input
              className={`${inputClass} flex-1`}
              placeholder="e.g. capital treatment of corporate exposures"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void runSearch();
              }}
            />
            <button
              type="button"
              disabled={searching}
              onClick={runSearch}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-50"
            >
              {searching ? "Searching…" : "Search"}
            </button>
          </div>
          {searchError ? <p className="mt-2 text-sm text-amber-700">{searchError}</p> : null}

          <div className="mt-4 space-y-3">
            {hits !== null && hits.length === 0 && !searchError ? <EmptyState message="No matching passages found." /> : null}
            {hits?.map((hit) => (
              <div key={hit.chunk_id} className="rounded-lg border border-slate-200 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-slate-900">{hit.document_title}</p>
                  <Badge tone="blue">{hit.score !== null ? `${(hit.score * 100).toFixed(1)}%` : "—"}</Badge>
                </div>
                <p className="text-xs text-slate-500">
                  {hit.page !== null ? `Page ${hit.page}` : "No page"} {hit.section ? `· ${hit.section}` : ""}
                </p>
                <p className="mt-1 text-sm text-slate-700">
                  {hit.snippet}
                  <span className="text-slate-400"> …</span>
                </p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="mt-6">
        <Card
          title="Knowledge base"
          subtitle="Documents that have been ingested and chunked for retrieval"
          actions={<Badge tone="purple">{docs.data ? fmtNumber(docs.data.items.length) : "—"} documents</Badge>}
        >
          {docs.error ? (
            <ErrorState message={docs.error} onRetry={docs.reload} />
          ) : docs.loading || !docs.data ? (
            <Spinner label="Loading documents…" />
          ) : docs.data.items.length === 0 ? (
            <EmptyState message="No documents in the knowledge base yet — ingest one above." />
          ) : (
            <Table headers={["Title", "Authority", "Version", "Status", "Pages", "Chunks", "Sample", "Ingested"]}>
              {docs.data.items.map((doc) => (
                <tr key={doc.id}>
                  <td className={`${tdClass} font-medium text-indigo-700`}>
                    {doc.title}
                    {doc.document_identifier ? (
                      <span className="block text-xs font-normal text-slate-500">{doc.document_identifier}</span>
                    ) : null}
                  </td>
                  <td className={tdClass}>{doc.issuing_authority ?? "—"}</td>
                  <td className={tdClass}>{doc.document_version ?? "—"}</td>
                  <td className={tdClass}>
                    <Badge tone={doc.status === "INGESTED" ? "green" : doc.status.startsWith("FAILED") ? "red" : "amber"}>
                      {doc.status}
                    </Badge>
                  </td>
                  <td className={tdClass}>{doc.page_count}</td>
                  <td className={tdClass}>{doc.chunk_count}</td>
                  <td className={tdClass}>{doc.is_sample ? <Badge tone="amber">sample</Badge> : "—"}</td>
                  <td className={tdClass}>{fmtDate(doc.ingested_at)}</td>
                </tr>
              ))}
            </Table>
          )}
        </Card>
      </div>
    </>
  );
}