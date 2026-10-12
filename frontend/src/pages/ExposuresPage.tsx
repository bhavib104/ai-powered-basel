import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { ExposureDetail } from "../api/types";
import {
  Badge,
  Card,
  EmptyState,
  ErrorState,
  fmtDate,
  fmtMoney,
  keyValueRows,
  Pagination,
  PageHeader,
  Spinner,
  Table,
  tdClass,
  useFetch,
} from "../components/ui";

const CLASSES = ["SOVEREIGN", "BANK", "CORPORATE", "RETAIL", "REAL_ESTATE"];
const RATINGS = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "UNRATED"];
const CURRENCIES = ["USD", "EUR", "GBP", "INR", "JPY", "CHF"];
const PAGE_SIZE = 50;

const inputClass =
  "rounded-md border border-slate-300 px-2.5 py-1.5 text-sm text-slate-700 focus:border-indigo-500 focus:outline-none";

function ExposureDetailPanel({ exposureId, onClose }: { exposureId: number; onClose: () => void }) {
  const { data, loading, error, reload } = useFetch(
    () => api.exposureDetail(exposureId),
    [exposureId],
  );

  return (
    <div className="mt-6">
      <Card
        title={data ? `Exposure ${data.exposure_ref}` : "Exposure detail"}
        actions={
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-slate-300 px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50"
          >
            Close
          </button>
        }
      >
        {error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : loading || !data ? (
          <Spinner label="Loading detail…" />
        ) : (
          <DetailBody detail={data} />
        )}
      </Card>
    </div>
  );
}

function DetailBody({ detail }: { detail: ExposureDetail }) {
  const calc = detail.latest_calculation;
  const headerRows: Record<string, unknown> = {
    Counterparty: detail.counterparty ?? "—",
    "Counterparty type": detail.counterparty_type ?? "—",
    Portfolio: detail.portfolio_code ?? "—",
    "Exposure class": detail.exposure_class,
    "Product type": detail.product_type,
    Currency: detail.currency,
    "Original amount": detail.original_amount,
    "Drawn amount": detail.drawn_amount,
    "Undrawn amount": detail.undrawn_amount,
    Rating: detail.rating_grade,
    Issued: detail.issue_date,
    Maturity: detail.maturity_date,
    Defaulted: detail.is_defaulted ? "✓ Yes" : "No",
    "Source system": detail.source_system,
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div>
        <h3 className="mb-2 text-sm font-semibold text-slate-900">Attributes</h3>
        {keyValueRows(headerRows)}
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-slate-900">
          Latest risk calculation {calc ? <Badge tone="green">{calc.status}</Badge> : null}
        </h3>
        {calc ? (
          <>
            <dl className="mb-3 grid grid-cols-2 gap-2">
              <div className="rounded-lg bg-slate-50 p-3">
                <dt className="text-xs text-slate-500">Eligible amount</dt>
                <dd className="text-sm font-semibold text-slate-900">{fmtMoney(calc.eligible_amount)}</dd>
              </div>
              <div className="rounded-lg bg-slate-50 p-3">
                <dt className="text-xs text-slate-500">Risk weight</dt>
                <dd className="text-sm font-semibold text-slate-900">
                  {calc.risk_weight === null ? "—" : `${(calc.risk_weight * 100).toFixed(2)}%`}
                </dd>
              </div>
            </dl>
            {calc.explanation ? (
              <>
                <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Step-by-step explanation
                </h4>
                <pre className="max-h-56 overflow-auto rounded-md bg-slate-900 p-3 text-xs text-slate-100">
                  {JSON.stringify(calc.explanation, null, 2)}
                </pre>
              </>
            ) : null}
          </>
        ) : (
          <p className="text-sm text-slate-500">This exposure has not been through a calculation run yet.</p>
        )}
      </div>

      <div className="lg:col-span-2">
        <h3 className="mb-2 text-sm font-semibold text-slate-900">Linked collateral</h3>
        {detail.collateral.length === 0 ? (
          <p className="text-sm text-slate-500">No collateral linked.</p>
        ) : (
          <Table headers={["Reference", "Type", "Allocated amount", "Eligible"]}>
            {detail.collateral.map((item) => (
              <tr key={item.collateral_ref ?? item.collateral_type ?? `${item.allocated_amount}`}>
                <td className={tdClass}>{item.collateral_ref ?? "—"}</td>
                <td className={tdClass}>{item.collateral_type ?? "—"}</td>
                <td className={tdClass}>{fmtMoney(item.allocated_amount)}</td>
                <td className={tdClass}>
                  <Badge tone={item.eligible ? "green" : "red"}>{item.eligible ? "Eligible" : "Not eligible"}</Badge>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </div>
    </div>
  );
}

export function ExposuresPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [committedSearch, setCommittedSearch] = useState("");
  const [exposureClass, setExposureClass] = useState("");
  const [rating, setRating] = useState("");
  const [currency, setCurrency] = useState("");
  const [defaulted, setDefaulted] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setCommittedSearch(search);
      setPage(1);
    }, 350);
    return () => clearTimeout(timer);
  }, [search]);

  const { data, loading, error, reload } = useFetch(
    () =>
      api.exposures({
        page,
        page_size: PAGE_SIZE,
        search: committedSearch || undefined,
        exposure_class: exposureClass || undefined,
        rating_grade: rating || undefined,
        currency: currency || undefined,
        is_defaulted: defaulted ? defaulted === "true" : undefined,
      }),
    [page, committedSearch, exposureClass, rating, currency, defaulted],
  );

  return (
    <>
      <PageHeader
        title="Exposure Register"
        subtitle="Searchable, filterable list of all counterparty exposures from the seeded dataset."
        actions={<Badge tone="blue">{data ? `${data.page.total} exposures` : "Loading…"}</Badge>}
      />

      <Card>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
          <input
            className={`${inputClass} col-span-2 md:col-span-1 lg:col-span-2`}
            placeholder="Search ref or product…"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <select className={inputClass} value={exposureClass} onChange={(e) => { setExposureClass(e.target.value); setPage(1); }}>
            <option value="">All classes</option>
            {CLASSES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select className={inputClass} value={rating} onChange={(e) => { setRating(e.target.value); setPage(1); }}>
            <option value="">All ratings</option>
            {RATINGS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select className={inputClass} value={currency} onChange={(e) => { setCurrency(e.target.value); setPage(1); }}>
            <option value="">All currencies</option>
            {CURRENCIES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select className={inputClass} value={defaulted} onChange={(e) => { setDefaulted(e.target.value); setPage(1); }}>
            <option value="">Defaulted: all</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        </div>
      </Card>

      <div className="mt-4">
        {error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : loading || !data ? (
          <Spinner label="Loading exposures…" />
        ) : data.items.length === 0 ? (
          <EmptyState message="No exposures match the current filters." />
        ) : (
          <>
            <Card padded={false}>
              <Table
                headers={[
                  "Reference",
                  "Counterparty",
                  "Class",
                  "Product",
                  "Currency",
                  "Drawn amount",
                  "Rating",
                  "Defaulted",
                  "Maturity",
                  "Source",
                ]}
              >
                {data.items.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => setSelectedId(selectedId === item.id ? null : item.id)}
                    className={`cursor-pointer transition-colors hover:bg-indigo-50/50 ${
                      selectedId === item.id ? "bg-indigo-50" : ""
                    }`}
                  >
                    <td className={`${tdClass} font-medium text-indigo-700`}>{item.exposure_ref}</td>
                    <td className={tdClass}>{item.counterparty ?? "—"}</td>
                    <td className={tdClass}>
                      <Badge tone="slate">{item.exposure_class}</Badge>
                    </td>
                    <td className={tdClass}>{item.product_type}</td>
                    <td className={tdClass}>{item.currency}</td>
                    <td className={tdClass}>{fmtMoney(item.drawn_amount)}</td>
                    <td className={tdClass}>{item.rating_grade}</td>
                    <td className={tdClass}>
                      {item.is_defaulted ? <Badge tone="red">Yes</Badge> : <Badge tone="green">No</Badge>}
                    </td>
                    <td className={tdClass}>{fmtDate(item.maturity_date)}</td>
                    <td className={tdClass}>{item.source_system}</td>
                  </tr>
                ))}
              </Table>
            </Card>
            <Pagination page={page} pages={data.page.pages} onPage={setPage} />
          </>
        )}
      </div>

      {selectedId !== null ? (
        <ExposureDetailPanel exposureId={selectedId} onClose={() => setSelectedId(null)} />
      ) : null}
    </>
  );
}