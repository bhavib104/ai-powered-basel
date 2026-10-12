import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { AssistantPage } from "./pages/AssistantPage";
import { AuditPage } from "./pages/AuditPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DataQualityPage } from "./pages/DataQualityPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { ExposuresPage } from "./pages/ExposuresPage";
import { ReconciliationPage } from "./pages/ReconciliationPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="exposures" element={<ExposuresPage />} />
        <Route path="data-quality" element={<DataQualityPage />} />
        <Route path="reconciliation" element={<ReconciliationPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="audit" element={<AuditPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
